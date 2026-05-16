#!/usr/bin/env python3
"""
Aria Continuous Automation Daemon
Runs automation continuously in the background with configurable intervals.
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

# Use .venv environment if available
workspace_root = Path(__file__).parent
venv_python = workspace_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")

if venv_python.exists():
    # Prepend venv bin to PATH so subprocess uses venv Python
    venv_bin = venv_python.parent
    os.environ["PATH"] = str(venv_bin) + os.pathsep + os.environ.get("PATH", "")
    # Also explicitly use venv python for subprocess calls
    _PYTHON_EXECUTABLE = str(venv_python)
else:
    _PYTHON_EXECUTABLE = sys.executable

# Set UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except:
        pass

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def get_marker(name: str) -> str:
    """Get platform-appropriate marker."""
    markers = {
        "ok": "[OK]" if sys.platform == "win32" else "✓",
        "error": "[ERROR]" if sys.platform == "win32" else "✗",
        "warning": "[WARN]" if sys.platform == "win32" else "⚠",
        "info": "[INFO]" if sys.platform == "win32" else "ℹ",
        "sync": "[SYNC]" if sys.platform == "win32" else "⟳",
    }
    return markers.get(name, "[*]")


def print_section(title: str) -> None:
    """Print a section header."""
    print(
        f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}"
    )
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(
        f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}"
    )


def print_ok(msg: str) -> None:
    """Print a success message."""
    print(f"{GREEN}{get_marker('ok')}{RESET} {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    print(f"{RED}{get_marker('error')}{RESET} {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    print(f"{YELLOW}{get_marker('warning')}{RESET} {msg}")


def print_info(msg: str) -> None:
    """Print an info message."""
    print(f"{BLUE}{get_marker('info')}{RESET} {msg}")


def print_sync(msg: str) -> None:
    """Print a sync message."""
    print(f"{BLUE}{get_marker('sync')}{RESET} {msg}")


class ContinuousAutomationDaemon:
    """Manages continuous background automation."""

    def __init__(self, workspace_root: Path, interval_minutes: int = 60):
        """Initialize the daemon."""
        self.workspace_root = workspace_root
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.automation_script = workspace_root / "run_automation.py"
        self.log_file = workspace_root / "logs" / "continuous_automation.log"
        self.running = True
        self.run_count = 0

        # Create logs directory
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""

        def signal_handler(signum, frame):
            print_warning("Shutdown signal received...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def log_message(self, message: str) -> None:
        """Write message to log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print_error(f"Failed to write log: {e}")

    def run_automation(self) -> bool:
        """Run the automation script."""
        self.run_count += 1

        try:
            print_sync(f"Running automation cycle #{self.run_count}...")
            self.log_message(f"Starting automation cycle #{self.run_count}")

            result = subprocess.run(
                [_PYTHON_EXECUTABLE, str(self.automation_script)],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=600,  # 10 minute timeout
            )

            if result.returncode == 0:
                print_ok(f"Automation cycle #{self.run_count} completed successfully")
                self.log_message(f"Automation cycle #{self.run_count} completed successfully")
                return True
            else:
                print_warning(f"Automation cycle #{self.run_count} completed with warnings")
                self.log_message(f"Automation cycle #{self.run_count} completed with warnings")
                if result.stdout:
                    self.log_message(f"Output: {result.stdout[:500]}")
                return True  # Don't stop on failures

        except subprocess.TimeoutExpired:
            print_warning(f"Automation cycle #{self.run_count} timed out")
            self.log_message(f"Automation cycle #{self.run_count} timed out")
            return False
        except Exception as e:
            print_error(f"Failed to run automation: {e}")
            self.log_message(f"Error running automation: {e}")
            return False

    def calculate_next_run(self) -> str:
        """Calculate and format the next run time."""
        next_run = datetime.now().timestamp() + self.interval_seconds
        from datetime import datetime as dt

        next_run_dt = dt.fromtimestamp(next_run)
        return next_run_dt.strftime("%Y-%m-%d %H:%M:%S")

    def run(self) -> None:
        """Run the continuous automation daemon."""
        self.setup_signal_handlers()

        print_section("Aria Continuous Automation Daemon")
        print_ok(f"Workspace: {self.workspace_root}")
        print_ok(f"Interval: {self.interval_minutes} minutes")
        print_ok(f"Log file: {self.log_file}")
        print_info("Press Ctrl+C to stop the daemon")

        self.log_message("Continuous automation daemon started")

        try:
            while self.running:
                print_section(
                    f"Automation Cycle #{self.run_count + 1} at {datetime.now().strftime('%H:%M:%S')}"
                )

                self.run_automation()

                if self.running:
                    next_run = self.calculate_next_run()
                    print_info(f"Next automtion run: {next_run}")
                    print_info(f"Waiting {self.interval_minutes} minutes...")

                    # Sleep in 1-minute intervals to allow graceful shutdown
                    for i in range(self.interval_minutes):
                        if not self.running:
                            break
                        time.sleep(60)

        except KeyboardInterrupt:
            print_warning("Interrupted by user")
            self.shutdown()
        except Exception as e:
            print_error(f"Daemon error: {e}")
            self.log_message(f"Daemon error: {e}")
            self.shutdown()

    def shutdown(self) -> None:
        """Shutdown the daemon gracefully."""
        print_warning("Shutting down continuous automation daemon...")
        self.running = False
        self.log_message("Continuous automation daemon stopped")
        print_ok("Daemon shut down complete")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Aria Continuous Automation Daemon",
        epilog="Example: python3 run_continuous_automation.py --interval 30",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Automation interval in minutes (default: 60)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).parent,
        help="Workspace root directory (default: script directory)",
    )

    args = parser.parse_args()

    daemon = ContinuousAutomationDaemon(
        workspace_root=args.workspace, interval_minutes=args.interval
    )
    daemon.run()


if __name__ == "__main__":
    main()
