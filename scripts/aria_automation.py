#!/usr/bin/env python3
"""
Aria Automation Orchestrator

Comprehensive automation system for Aria AI character platform:
- Auto-start web server and backend
- Continuous training with Aria datasets
- Auto-execution of LLM commands
- Health monitoring and recovery
- Integration with master orchestrator

Usage:
    # Start full automation (server + training + monitoring)
    python scripts/aria_automation.py --mode full

    # Server only (no training)
    python scripts/aria_automation.py --mode server

    # Training only (no server)
    python scripts/aria_automation.py --mode training

    # Single training cycle
    python scripts/aria_automation.py --mode training --once

    # Check status
    python scripts/aria_automation.py --status

    # Stop all Aria processes
    python scripts/aria_automation.py --stop

Features:
    ✅ Auto-start Aria web server on port 8080
    ✅ Auto-start Azure Functions backend
    ✅ Continuous training with dataset monitoring
    ✅ Health checks and auto-recovery
    ✅ LLM-powered auto-execution
    ✅ Process management and cleanup
"""

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import psutil

REPO_ROOT = Path(__file__).resolve().parents[1]
ARIA_WEB_DIR = REPO_ROOT / "aria_web"
DATA_OUT = REPO_ROOT / "data_out" / "aria_automation"
STATUS_FILE = DATA_OUT / "status.json"
PID_FILE = DATA_OUT / "processes.json"

# Ensure output directory exists
DATA_OUT.mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessInfo:
    """Track running processes"""

    name: str
    pid: int
    command: str
    started: str
    status: str = "running"
    port: Optional[int] = None
    health_url: Optional[str] = None


@dataclass
class AriaAutomationStatus:
    """Overall automation status"""

    mode: str
    started: str
    uptime_seconds: float = 0
    server_running: bool = False
    backend_running: bool = False
    training_active: bool = False
    last_health_check: Optional[str] = None
    processes: list[dict[str, Any]] = field(default_factory=list)
    training_cycles: int = 0
    errors: list[str] = field(default_factory=list)


class AriaAutomation:
    """Main automation orchestrator for Aria"""

    def __init__(self, mode: str = "full"):
        self.mode = mode
        self.processes: dict[str, ProcessInfo] = {}
        self.running = True
        self.start_time = datetime.now()
        self.training_cycles = 0
        self.errors: list[str] = []

        # Performance optimization: cache port checks
        self._port_cache: dict[int, tuple[bool, float]] = {}
        self._port_cache_ttl = 5.0  # Cache port checks for 5 seconds

        # Performance optimization: cache process listings
        self._process_cache: list[psutil.Process] | None = None
        self._process_cache_time = 0
        self._process_cache_ttl = 10.0  # Cache process list for 10 seconds
        self._status_dirty = True  # Track if status needs saving

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n⚠️  Received signal {signum}, shutting down gracefully...")
        self.running = False
        self.stop_all()
        sys.exit(0)

    def save_status(self, force: bool = False):
        """Save current status to JSON (only if changed or forced)"""
        # Skip if status hasn't changed and not forced
        if not self._status_dirty and not force:
            return

        status = AriaAutomationStatus(
            mode=self.mode,
            started=self.start_time.isoformat(),
            uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
            server_running=self._is_process_running("aria_server"),
            backend_running=self._is_process_running("functions_backend"),
            training_active=self._is_process_running("training"),
            last_health_check=datetime.now().isoformat(),
            processes=[vars(p) for p in self.processes.values()],
            training_cycles=self.training_cycles,
            errors=self.errors[-10:],  # Last 10 errors
        )

        with open(STATUS_FILE, "w") as f:
            json.dump(vars(status), f, indent=2)

        self._status_dirty = False

    def load_pids(self) -> dict[str, int]:
        """Load PIDs from previous run"""
        if not PID_FILE.exists():
            return {}

        try:
            with open(PID_FILE) as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load PIDs: {e}")
            return {}

    def save_pids(self):
        """Save current process PIDs"""
        pids = {name: p.pid for name, p in self.processes.items()}
        with open(PID_FILE, "w") as f:
            json.dump(pids, f, indent=2)

    def _is_process_running(self, name: str) -> bool:
        """Check if named process is running"""
        if name not in self.processes:
            return False

        try:
            process = psutil.Process(self.processes[name].pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def _check_port(self, port: int) -> bool:
        """Check if port is in use with caching"""
        import socket

        current_time = time.time()

        # Check cache
        if port in self._port_cache:
            cached_result, cache_time = self._port_cache[port]
            if current_time - cache_time < self._port_cache_ttl:
                return cached_result

        # Cache miss or expired - check port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("localhost", port)) == 0

        # Update cache
        self._port_cache[port] = (result, current_time)
        return result

    def _get_process_list(self) -> list[psutil.Process]:
        """Get cached process listing to avoid expensive psutil.process_iter() calls"""
        current_time = time.time()

        # Check cache
        if self._process_cache is not None:
            if current_time - self._process_cache_time < self._process_cache_ttl:
                return self._process_cache

        # Cache miss or expired - get process list
        self._process_cache = list(
            psutil.process_iter(["pid", "name", "cmdline"]))
        self._process_cache_time = current_time
        return self._process_cache

    def start_aria_server(self) -> bool:
        """Start Aria web server"""
        print("\n🚀 Starting Aria web server...")

        # Check if already running
        if self._check_port(8080):
            print("⚠️  Port 8080 already in use")
            # Try to find existing process using cached process list
            for proc in self._get_process_list():
                try:
                    cmdline = proc.info["cmdline"]
                    if cmdline:
                        cmdline_str = " ".join(cmdline)
                        if "server.py" in cmdline_str:
                            print(
                                f"ℹ️  Found existing server (PID {proc.info['pid']})")
                            self.processes["aria_server"] = ProcessInfo(
                                name="aria_server",
                                pid=proc.info["pid"],
                                command="python server.py",
                                started=datetime.now().isoformat(),
                                port=8080,
                                health_url="http://localhost:8080",
                            )
                            return True
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    continue
            return False

        try:
            # Start server process
            proc = subprocess.Popen(
                [sys.executable, "server.py"],
                cwd=ARIA_WEB_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to start with exponential backoff
            print("⏳ Waiting for server to start...")
            max_wait = 10  # seconds
            check_interval = 0.1  # Start with 100ms checks
            elapsed = 0

            while elapsed < max_wait:
                if self._check_port(8080):
                    print(
                        f"✅ Aria server started on http://localhost:8080 (PID {proc.pid})")
                    self.processes["aria_server"] = ProcessInfo(
                        name="aria_server",
                        pid=proc.pid,
                        command="python server.py",
                        started=datetime.now().isoformat(),
                        port=8080,
                        health_url="http://localhost:8080",
                    )
                    self.save_pids()
                    return True

                # Exponential backoff: 0.1s, 0.2s, 0.4s, 0.8s, then cap at 1s
                time.sleep(check_interval)
                elapsed += check_interval
                check_interval = min(check_interval * 2, 1.0)

            print(f"❌ Server failed to start within {max_wait} seconds")
            proc.terminate()
            return False

        except Exception as e:
            error = f"Failed to start Aria server: {e}"
            print(f"❌ {error}")
            self.errors.append(error)
            self._status_dirty = True
            return False

    def start_functions_backend(self) -> bool:
        """Start Azure Functions backend"""
        print("\n🚀 Starting Azure Functions backend...")

        # Check if already running
        if self._check_port(7071):
            print("⚠️  Port 7071 already in use")
            return True

        try:
            # Check if func is available
            result = subprocess.run(
                ["func", "--version"], capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                print("⚠️  Azure Functions Core Tools not installed")
                print(
                    "   Install from: https://docs.microsoft.com/azure/azure-functions/functions-run-local")
                return False

            # Start Functions host
            proc = subprocess.Popen(
                ["func", "host", "start"],
                cwd=REPO_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for backend to start
            print("⏳ Waiting for Functions backend to start...")
            for _i in range(15):
                time.sleep(1)
                if self._check_port(7071):
                    print(
                        f"✅ Functions backend started on http://localhost:7071 (PID {proc.pid})")
                    self.processes["functions_backend"] = ProcessInfo(
                        name="functions_backend",
                        pid=proc.pid,
                        command="func host start",
                        started=datetime.now().isoformat(),
                        port=7071,
                        health_url="http://localhost:7071/api/ai/status",
                    )
                    self.save_pids()
                    return True

            print("❌ Backend failed to start within 15 seconds")
            proc.terminate()
            return False

        except FileNotFoundError:
            print("⚠️  Azure Functions Core Tools not found in PATH")
            return False
        except Exception as e:
            error = f"Failed to start Functions backend: {e}"
            print(f"❌ {error}")
            self.errors.append(error)
            return False

    def run_training_cycle(self, quick: bool = True) -> bool:
        """Run single training cycle"""
        print(f"\n📚 Running training cycle #{self.training_cycles + 1}")

        try:
            # Use aria_quick_train for fast iterations
            script = REPO_ROOT / "scripts" / "aria_quick_train.py"

            if not script.exists():
                print(
                    "⚠️  aria_quick_train.py not found, using automate_aria_movement.py")
                script = REPO_ROOT / "scripts" / "automate_aria_movement.py"

            cmd = [sys.executable, str(script)]
            if quick:
                cmd.append("--quick")

            print(f"Command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if result.returncode == 0:
                self.training_cycles += 1
                self._status_dirty = True
                print(f"✅ Training cycle #{self.training_cycles} completed")
                return True
            else:
                error = f"Training cycle failed: {result.stderr[-200:]}"
                print(f"❌ {error}")
                self.errors.append(error)
                self._status_dirty = True
                return False

        except subprocess.TimeoutExpired:
            error = "Training cycle timed out after 10 minutes"
            print(f"❌ {error}")
            self.errors.append(error)
            self._status_dirty = True
            return False
        except Exception as e:
            error = f"Training cycle error: {e}"
            print(f"❌ {error}")
            self.errors.append(error)
            self._status_dirty = True
            return False

    def health_check(self) -> dict[str, bool]:
        """Check health of all components"""
        health = {"aria_server": False,
                  "functions_backend": False, "training": False}

        # Check Aria server
        if self._is_process_running("aria_server"):
            if self._check_port(8080):
                health["aria_server"] = True

        # Check Functions backend
        if self._is_process_running("functions_backend"):
            if self._check_port(7071):
                health["functions_backend"] = True

        # Check if training is active
        health["training"] = self._is_process_running("training")

        return health

    def auto_recovery(self, health: dict[str, bool]):
        """Attempt to recover failed components"""
        if not health["aria_server"] and self.mode in ["full", "server"]:
            print("\n🔄 Attempting to recover Aria server...")
            self.start_aria_server()

        if not health["functions_backend"] and self.mode == "full":
            print("\n🔄 Attempting to recover Functions backend...")
            self.start_functions_backend()

    def monitoring_loop(self, interval: int = 60):
        """Continuous monitoring with auto-recovery"""
        print(f"\n👁️  Starting monitoring loop (interval: {interval}s)")

        while self.running:
            time.sleep(interval)

            health = self.health_check()
            print(f"\n🔍 Health check: {json.dumps(health, indent=2)}")

            # Auto-recovery
            self.auto_recovery(health)

            # Save status
            self.save_status()

    def training_loop(self, interval: int = 1800, once: bool = False):
        """Continuous training loop"""
        print(
            f"\n🎓 Starting training loop (interval: {interval}s, once: {once})")

        while self.running:
            success = self.run_training_cycle(quick=True)

            if once:
                print(
                    f"\n✅ Single training cycle completed (success: {success})")
                break

            if success:
                print(f"\n⏳ Waiting {interval}s until next training cycle...")
                time.sleep(interval)
            else:
                print("\n⚠️  Training failed, waiting 5 minutes before retry...")
                time.sleep(300)

    def start(self, once: bool = False):
        """Start automation based on mode"""
        print(f"\n{'='*80}")
        print(f"🤖 Aria Automation Starting - Mode: {self.mode}")
        print(f"{'='*80}\n")

        if self.mode in ["full", "server"]:
            # Start Aria server
            if not self.start_aria_server():
                print("❌ Failed to start Aria server")
                if self.mode == "server":
                    return

        if self.mode == "full":
            # Start Functions backend
            if not self.start_functions_backend():
                print("⚠️  Functions backend not started (continuing anyway)")

        if self.mode in ["full", "training"]:
            # Start training loop in separate thread
            training_thread = threading.Thread(
                target=self.training_loop,
                args=(1800, once),  # 30 minute interval
                daemon=True,
            )
            training_thread.start()

        if self.mode in ["full", "server"]:
            # Start monitoring loop
            try:
                self.monitoring_loop(interval=60)  # Check every minute
            except KeyboardInterrupt:
                print("\n⚠️  Monitoring stopped by user")
        elif self.mode == "training":
            # Wait for training to complete
            if once:
                training_thread.join()
            else:
                try:
                    while self.running:
                        time.sleep(10)
                        self.save_status()
                except KeyboardInterrupt:
                    print("\n⚠️  Training stopped by user")

    def stop_all(self):
        """Stop all managed processes"""
        print("\n🛑 Stopping all Aria processes...")

        for name, proc_info in self.processes.items():
            try:
                process = psutil.Process(proc_info.pid)
                print(f"   Stopping {name} (PID {proc_info.pid})...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    print(f"   Force killing {name}...")
                    process.kill()

                print(f"   ✅ {name} stopped")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"   ⚠️  {name} already stopped")

        # Clear PID file
        if PID_FILE.exists():
            PID_FILE.unlink()

        print("✅ All processes stopped")

    @staticmethod
    def show_status():
        """Display current automation status"""
        if not STATUS_FILE.exists():
            print("❌ No automation currently running")
            return

        try:
            with open(STATUS_FILE) as f:
                status = json.load(f)

            print("\n" + "=" * 80)
            print("🤖 Aria Automation Status")
            print("=" * 80)
            print(f"Mode: {status['mode']}")
            print(f"Started: {status['started']}")
            print(
                f"Uptime: {timedelta(seconds=int(status['uptime_seconds']))}")
            print(f"Training Cycles: {status['training_cycles']}")
            print("\nComponents:")
            print(
                f"  - Aria Server: {'✅ Running' if status['server_running'] else '❌ Stopped'}")
            print(
                f"  - Functions Backend: {'✅ Running' if status['backend_running'] else '❌ Stopped'}")
            print(
                f"  - Training: {'✅ Active' if status['training_active'] else '❌ Inactive'}")

            if status["errors"]:
                print(f"\nRecent Errors ({len(status['errors'])}):")
                for error in status["errors"][-5:]:
                    print(f"  - {error}")

            print("\nProcesses:")
            for proc in status["processes"]:
                print(
                    f"  - {proc['name']} (PID {proc['pid']}): {proc['status']}")

            print("=" * 80 + "\n")

        except Exception as e:
            print(f"❌ Error reading status: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Aria Automation Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start full automation (recommended)
  python scripts/aria_automation.py --mode full

  # Server only (no training)
  python scripts/aria_automation.py --mode server

  # Single training run
  python scripts/aria_automation.py --mode training --once

  # Check status
  python scripts/aria_automation.py --status

  # Stop all
  python scripts/aria_automation.py --stop
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["full", "server", "training"],
        default="full",
        help="Automation mode: full (server+training), server only, or training only",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run training once and exit (only applies to training mode)",
    )
    parser.add_argument("--status", action="store_true",
                        help="Show current automation status")
    parser.add_argument("--stop", action="store_true",
                        help="Stop all Aria automation processes")

    args = parser.parse_args()

    # Handle status check
    if args.status:
        AriaAutomation.show_status()
        return

    # Handle stop
    if args.stop:
        automation = AriaAutomation()
        automation.processes = {
            name: ProcessInfo(name=name, pid=pid, command="", started="")
            for name, pid in automation.load_pids().items()
        }
        automation.stop_all()
        return

    # Start automation
    automation = AriaAutomation(mode=args.mode)
    automation.start(once=args.once)


if __name__ == "__main__":
    main()
