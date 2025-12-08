#!/usr/bin/env python3
"""Repository-Wide Automation System

This script provides lightweight management for repository-level
automation components: starting/stopping processes, tracking PIDs and
status, performing health checks and automatically attempting to
install Python package dependencies when needed.
"""

import argparse
import importlib
import json
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

REPO_ROOT = Path(__file__).resolve().parent.parent
PID_FILE = REPO_ROOT / "processes.json"
STATUS_FILE = REPO_ROOT / "automation_status.json"


class _ExistingProcessWrapper:

    def __init__(self, pid: int):
        self.pid = pid

    def poll(self):  # Returns None if running, non-zero if not
        try:
            if psutil is None:
                # Without psutil we cannot confirm; assume running
                return None
            proc = psutil.Process(self.pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                return None
            return 1
        except Exception:
            return 1


@dataclass
class ComponentConfig:
    # Configuration for automated component
    # required_packages: list of importable module names (pip names assumed identical unless
    # a tuple 'pip_name:import_name' is provided). These will be verified/installed prior
    # to component start to achieve zero manual intervention.
    name: str
    enabled: bool = True
    script: Optional[str] = None
    command: Optional[List[str]] = None
    auto_restart: bool = True
    health_check_interval: int = 300  # 5 minutes
    dependencies: List[str] = field(default_factory=list)
    required_packages: List[str] = field(default_factory=list)


@dataclass
class AutomationStatus:
    # Overall automation status
    started: str
    uptime_seconds: float = 0
    components_running: Dict[str, bool] = field(default_factory=dict)
    dependency_status: Dict[str, bool] = field(default_factory=dict)
    last_health_check: Optional[str] = None
    total_cycles: int = 0
    errors: List[str] = field(default_factory=list)


class RepoAutomation:
    """
    """

    def __init__(self):
        self.components: Dict[str, ComponentConfig] = self._init_components()
        self.processes: Dict[str, Any] = {}
        self.running = True
        self.start_time = datetime.now()
        self.total_cycles = 0
        self.errors: List[str] = []
        self.dependency_status: Dict[str, bool] = {}

        # Attempt to auto-enable components based on config presence
        self._auto_enable_components()

        # Attach to any existing processes from previous run (if processes.json exists)
        self._attach_existing_from_pidfile()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _init_components(self) -> Dict[str, ComponentConfig]:
        """Initialize all automation components with dependency metadata"""
        return {
            "aria": ComponentConfig(
                name="Aria Character Automation",
                script="scripts/aria_automation.py",
                command=["python3", "scripts/aria_automation.py",
                         "--mode", "full"],
                auto_restart=True,
                health_check_interval=60,
                required_packages=["psutil"],
            ),
            "training": ComponentConfig(
                name="Autonomous Training System",
                script="scripts/autonomous_training_orchestrator.py",
                command=["python3", "scripts/autonomous_training_orchestrator.py"],
                auto_restart=True,
                health_check_interval=300,
                # Use proper pip/import mapping for PyYAML
                required_packages=[
                    "pandas",
                    "torch",
                    "numpy",
                    "PyYAML:yaml",
                ],
            ),
            "quantum": ComponentConfig(
                name="Quantum Computing Workflows",
                script="scripts/quantum_autorun.py",
                command=["python3", "scripts/quantum_autorun.py"],
                auto_restart=False,
                health_check_interval=600,
                enabled=False,  # Will be enabled if quantum_autorun.yaml exists
                required_packages=[],  # Add azure quantum SDK here when environment ready
            ),
            "evaluation": ComponentConfig(
                name="Model Evaluation System",
                script="scripts/evaluation_autorun.py",
                command=["python3", "scripts/evaluation_autorun.py"],
                auto_restart=False,
                health_check_interval=300,
                dependencies=["training"],
                enabled=False,  # Enabled if evaluation_autorun.yaml exists
                required_packages=["scikit-learn",
                                   "numpy", "matplotlib", "seaborn"],
            ),
            "datasets": ComponentConfig(
                name="Dataset Auto-Discovery (Integrated in training)",
                script="scripts/autonomous_training_orchestrator.py",
                command=["python3", "scripts/autonomous_training_orchestrator.py"],
                auto_restart=False,
                health_check_interval=3600,
                enabled=False,  # Included in training component
            ),
            "monitoring": ComponentConfig(
                name="Status Dashboard",
                script="scripts/status_dashboard.py",
                command=["python3", "scripts/status_dashboard.py"],
                auto_restart=False,
                health_check_interval=60,
                enabled=False,
                # Correct pip/import names
                required_packages=[
                    "Flask",
                    "Flask-SocketIO:flask_socketio",
                    "python-socketio:socketio",
                ],
            ),
            "backup": ComponentConfig(
                name="Backup Manager",
                script="scripts/backup_manager.py",
                command=["python3", "scripts/backup_manager.py"],
                auto_restart=False,
                health_check_interval=3600,
                enabled=False,
            ),
        }

    def _auto_enable_components(self):
        """Enable optional components based on presence of their config files"""
        config_checks = {
            "quantum": REPO_ROOT / "quantum_autorun.yaml",
            "evaluation": REPO_ROOT / "evaluation_autorun.yaml",
        }
        for name, path in config_checks.items():
            if name in self.components and path.exists():
                self.components[name].enabled = True

    def _attach_existing_from_pidfile(self):
        """Attach to previously recorded processes if still running"""
        if not PID_FILE.exists():
            return
        if psutil is None:
            return
        try:
            with open(PID_FILE, "r") as f:
                mapping = json.load(f)
            for name, pid in mapping.items():
                if name in self.components:
                    try:
                        proc = psutil.Process(pid)
                        if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                            self.processes[name] = _ExistingProcessWrapper(pid)
                    except Exception:
                        continue
        except Exception:
            pass

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n⚠️  Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all()
        sys.exit(0)

    def _get_pid_map(self) -> Dict[str, int]:
        """Load PID mapping from file if present"""
        if not PID_FILE.exists():
            return {}
        try:
            with open(PID_FILE, "r") as f:
                data = json.load(f)
                # Ensure only int PIDs
                return {k: int(v) for k, v in data.items() if v is not None}
        except Exception:
            return {}

    def _remove_pid_entry(self, name: str):
        """Remove a single component entry from PID file"""
        try:
            mapping = self._get_pid_map()
            if name in mapping:
                mapping.pop(name, None)
                with open(PID_FILE, "w") as f:
                    json.dump(mapping, f, indent=2)
        except Exception:
            pass

    def save_status(self):
        """Save current status to JSON"""
        status = AutomationStatus(
            started=self.start_time.isoformat(),
            uptime_seconds=(datetime.now() - self.start_time).total_seconds(),
            components_running={
                name: self._is_component_running(name)
                for name in self.components.keys()
            },
            dependency_status=self.dependency_status,
            last_health_check=datetime.now().isoformat(),
            total_cycles=self.total_cycles,
            errors=self.errors[-20:],  # Last 20 errors
        )

        with open(STATUS_FILE, "w") as f:
            json.dump(vars(status), f, indent=2)

    def _is_component_running(self, name: str) -> bool:
        """Check if component is running"""
        if name not in self.processes:
            return False

        proc = self.processes[name]
        if proc is None:
            return False

        try:
            return proc.poll() is None
        except Exception:
            return False

    def start_component(self, name: str) -> bool:
        """Start a single component"""
        if name not in self.components:
            print(f"❌ Unknown component: {name}")
            return False

        component = self.components[name]

        if not component.enabled:
            print(f"⚠️  Component '{component.name}' is disabled")
            return False

        # Check dependencies
        for dep in component.dependencies:
            if not self._is_component_running(dep):
                print(
                    f"⚠️  Dependency '{dep}' not running, starting it first...")
                if not self.start_component(dep):
                    print(f"❌ Failed to start dependency '{dep}'")
                    return False

        # Detect and attach to existing process (prevents duplicates)
        existing = self._find_existing_process(component)
        if existing is not None:
            print(
                f"\n🔗 Found existing process for {component.name} (PID {existing.pid}), attaching instead of starting new instance")
            self.processes[name] = _ExistingProcessWrapper(existing.pid)
            # Assume satisfied if already running
            self.dependency_status[name] = True
            self.save_status()
            self._save_process_pids()
            # Enforce single-instance: terminate any duplicates beyond the attached one
            self._enforce_single_instance(component, keep_pid=existing.pid)
            return True

        # Ensure dependencies (auto-install if missing)
        if not self._ensure_dependencies(name, component.required_packages):
            print(
                f"❌ Cannot start {component.name} due to dependency installation failure")
            return False

        print(f"\n🚀 Starting {component.name}...")

        try:
            # Start process
            proc = subprocess.Popen(
                component.command,
                cwd=REPO_ROOT,
                stdout=subprocess.DEVNULL,  # Avoid pipe blocking
                stderr=subprocess.DEVNULL,
            )

            self.processes[name] = proc
            time.sleep(2)  # Give it time to start

            if self._is_component_running(name):
                print(f"✅ {component.name} started (PID {proc.pid})")
                self._save_process_pids()
                # Enforce single-instance: ensure no stray duplicates remain
                self._enforce_single_instance(component, keep_pid=proc.pid)
                return True
            else:
                print(f"❌ {component.name} failed to start")
                return False

        except Exception as e:
            error = f"Failed to start {component.name}: {e}"
            print(f"❌ {error}")
            self.errors.append(error)
            return False

    def stop_component(self, name: str):
        """Stop a single component"""
                """
            return

        component = self.components[name]
        proc = self.processes[name]

        print(f"🛑 Stopping {component.name}...")

        try:
            # Handle both subprocess.Popen and _ExistingProcessWrapper
            if hasattr(proc, "terminate"):
                proc.terminate()
                proc.wait(timeout=10)
            elif psutil is not None and hasattr(proc, "pid"):
                p = psutil.Process(proc.pid)
                p.terminate()
                try:
                    p.wait(timeout=10)
                except Exception:
                    pass
            print(f"✅ {component.name} stopped")
        except subprocess.TimeoutExpired:
            print(f"⚠️  Force killing {component.name}...")
            try:
                if hasattr(proc, "kill"):
                    proc.kill()
                    proc.wait()
                elif psutil is not None and hasattr(proc, "pid"):
                    p = psutil.Process(proc.pid)
                    p.kill()
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️  Error stopping {component.name}: {e}")

        self.processes[name] = None
        # Update PID file to reflect stop
        self._remove_pid_entry(name)
        self._save_process_pids()

    def start_all(self, components: Optional[List[str]] = None):
        """Start all or specified components"""
        print("\n" + "=" * 80)
        print("🤖 Repository-Wide Automation Starting")
        print("=" * 80)

        components_to_start = components or list(self.components.keys())

        for name in components_to_start:
            if name in self.components:
                self.start_component(name)
            else:
                print(f"⚠️  Unknown component: {name}")

        self.save_status()

    def stop_all(self):
        """Stop all components"""
        print("\n🛑 Stopping all components...")

        for name in self.components.keys():
            self.stop_component(name)

        self.save_status()
        # Clear PID file
        if PID_FILE.exists():
            try:
                PID_FILE.unlink()
            except Exception:
                pass
        print("✅ All components stopped")

    def health_check(self) -> Dict[str, bool]:
        """Check health of all components"""
        health = {}

        for name, component in self.components.items():
            is_running = self._is_component_running(name)
            health[name] = is_running

            if component.enabled and not is_running and component.auto_restart:
                print(f"\n🔄 Auto-restarting {component.name}...")
                self.start_component(name)

        return health

    def _enforce_single_instance(self, component: ComponentConfig, keep_pid: Optional[int] = None):
        # Ensure only one process for the given component's script is running.
        # Terminates any extra instances beyond keep_pid.
        if psutil is None or not component.script:
            return
        script_name = Path(component.script).name
        duplicates = []
        try:
            for proc in psutil.process_iter(['pid', 'cmdline', 'create_time']):
                cmd = proc.info.get('cmdline') or []
                if any(script_name in part for part in cmd):
                    if keep_pid is not None and proc.pid == keep_pid:
                        continue
                    duplicates.append(proc)
        except Exception:
            return
        if len(duplicates) > 0:
            print(
                f"\n⚖️  Enforcing single-instance for {component.name}: {len(duplicates)} duplicate(s) found")
            for p in duplicates:
                try:
                    p.terminate()
                    p.wait(timeout=5)
                    print(f"   • Terminated duplicate PID {p.pid}")
                except Exception:
                    try:
                        p.kill()
                        print(f"   • Killed duplicate PID {p.pid}")
                    except Exception:
                        print(
                            f"   • Unable to terminate duplicate PID {p.pid}")

    def _find_existing_process(self, component: ComponentConfig):
        """Attempt to find an already-running process for the component's script"""
        if psutil is None or not component.script:
            return None
        script_name = Path(component.script).name
        try:
            for proc in psutil.process_iter(['pid', 'cmdline']):
                cmd = proc.info.get('cmdline') or []
                if any(script_name in part for part in cmd):
                    return proc
        except Exception:
            return None
        return None

    def _ensure_dependencies(self, name: str, required: List[str]) -> bool:
        """Ensure required Python packages are installed. Returns True if all satisfied."""
        if not required:
            self.dependency_status[name] = True
            return True
        missing: List[str] = []
        for spec in required:
            pip_name, import_name = (spec.split(
                ":", 1) + [spec])[:2] if ":" in spec else (spec, spec)
            try:
                importlib.import_module(import_name)
            except Exception:
                missing.append(pip_name)
        if not missing:
            self.dependency_status[name] = True
            return True
        print(
            f"🔧 Installing missing dependencies for {name}: {', '.join(missing)}")
        for pkg in missing:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg], capture_output=True, text=True)
                if result.returncode != 0:
                    err = result.stderr.strip().splitlines(
                    )[-1] if result.stderr else f"Unknown error installing {pkg}"
                    self.errors.append(
                        f"Dependency install failed ({name}): {pkg} -> {err}")
                    self.dependency_status[name] = False
                    return False
            except Exception as e:
                self.errors.append(
                    f"Dependency install exception ({name}): {pkg} -> {e}")
                self.dependency_status[name] = False
                return False
        # Verify imports post-install
        post_missing = []
        for spec in required:
            pip_name, import_name = (spec.split(
                ":", 1) + [spec])[:2] if ":" in spec else (spec, spec)
            try:
                importlib.import_module(import_name)
            except Exception:
                post_missing.append(pip_name)
        if post_missing:
            self.errors.append(
                f"Dependencies still missing after install ({name}): {', '.join(post_missing)}")
            self.dependency_status[name] = False
            return False
        self.dependency_status[name] = True
        return True

    def _save_process_pids(self):
        """Persist current process PIDs for continuity"""
        mapping = {name: getattr(proc, 'pid', None) for name,
                   proc in self.processes.items() if proc is not None}
        try:
            with open(PID_FILE, 'w') as f:
                json.dump(mapping, f, indent=2)
        except Exception:
            pass

    def monitoring_loop(self, interval: int = 60):
        """Continuous monitoring with auto-recovery"""
        print(f"\n👁️  Starting monitoring loop (interval: {interval}s)")

        while self.running:
            time.sleep(interval)

            self.total_cycles += 1
            health = self.health_check()

            print(
                f"\n🔍 Health check #{self.total_cycles}: "
                f"{sum(health.values())}/{len(health)} components running"
            )

            self.save_status()

    def show_status(self):
        """Display current status"""
        pid_map = self._get_pid_map()
        status = None
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r") as f:
                    status = json.load(f)
            except Exception:
                status = None

        print("\n" + "=" * 80)
        print("🤖 Repository Automation Status")
        print("=" * 80)

        if status:
            print(f"Started: {status.get('started', 'unknown')}")
            print(
                f"Uptime: {timedelta(seconds=int(status.get('uptime_seconds', 0)))}")
            print(f"Health Checks: {status.get('total_cycles', 0)}")
        else:
            print("Started: unknown (status file missing)")
            print("Uptime: n/a")
            print("Health Checks: n/a")

        print("\n📊 Components:")
        # Build a dynamic running map using PID file and psutil
        dynamic_running: Dict[str, bool] = {}
        if psutil is not None:
            for name, pid in pid_map.items():
                try:
                    p = psutil.Process(pid)
                    dynamic_running[name] = p.is_running(
                    ) and p.status() != psutil.STATUS_ZOMBIE
                except Exception:
                    dynamic_running[name] = False

        # Prefer dynamic running info; fall back to status file content
        components_running = status.get(
            "components_running", {}) if status else {}
        for name in self.components.keys():
            running = dynamic_running.get(
                name, components_running.get(name, False))
            component = self.components.get(name)
            if component:
                status_icon = "✅" if running else "❌"
                dep_ok = (status.get("dependency_status", {}).get(
                    # Fallback: if PID not recorded, try discovering existing processes
                    for name, component in self.components.items():
                        if name not in dynamic_running:
                            try:
                                proc=self._find_existing_process(component)
                                dynamic_running[name]=proc is not None
                            except Exception:
                                dynamic_running[name]=False
                    name, True) if status else True)
                dep_icon = "🧩" if dep_ok else "⚠️"
                pid_info = f" (PID {pid_map.get(name)})" if name in pid_map else ""
                print(
                    f"  {status_icon} {component.name}{pid_info} ({dep_icon} deps)")

        # Recent errors
        if status and status.get("errors"):
            print(f"\n⚠️  Recent Errors ({len(status['errors'])}):")
            for error in status["errors"][-5:]:
                print(f"  - {error}")

        if not status and not pid_map:
            print("\nℹ️  No status or PID information found. If automation is running in another session, it may not have written status yet.")

        print("=" * 80 + "\n")

    def run_daemon(self):
        """Run as background daemon"""
        print("\n🌙 Running in daemon mode...")

        # Start monitoring in background thread
        monitor_thread = threading.Thread(
            target=self.monitoring_loop, daemon=True)
        monitor_thread.start()

        try:
            while self.running:
                time.sleep(10)
                self.save_status()
        except KeyboardInterrupt:
            print("\n⚠️  Daemon stopped by user")


def main():
    parser = argparse.ArgumentParser(
        description="Repository-Wide Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start all automation
  python scripts/repo_automation.py --start

  # Start specific components
  python scripts/repo_automation.py --start --components aria,training

  # Check status
  python scripts/repo_automation.py --status

  # Stop all
  python scripts/repo_automation.py --stop

  # Run as daemon
  python scripts/repo_automation.py --daemon
        """,
    )

    parser.add_argument(
        "--start", action="store_true", help="Start automation components"
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop all automation components"
    )
    parser.add_argument(
        "--status", action="store_true", help="Show current status"
    )
    parser.add_argument(
        "--daemon", action="store_true", help="Run as background daemon"
    )
    parser.add_argument(
        "--components",
        help="Comma-separated list of components to start (aria,training,quantum,etc.)",
    )

    args = parser.parse_args()

    automation = RepoAutomation()

    if args.status:
        automation.show_status()
        return

    if args.stop:
        # Load existing processes if any
        automation.stop_all()
        return

    if args.start:
        components = None
        if args.components:
            components = [c.strip() for c in args.components.split(",")]

        automation.start_all(components)

        if args.daemon:
            automation.run_daemon()
        else:
            # Keep running with monitoring
            try:
                automation.monitoring_loop()
            except KeyboardInterrupt:
                print("\n⚠️  Stopped by user")
                automation.stop_all()
        return

    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
