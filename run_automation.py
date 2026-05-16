#!/usr/bin/env python3
"""
Aria Automation Runner
Automatically runs core Aria systems and utilities.
"""

import os
import sys
import subprocess
import signal
from pathlib import Path
from typing import List

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
    marker = "[OK]" if sys.platform == "win32" else "✓"
    print(f"{GREEN}{marker}{RESET} {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    marker = "[ERROR]" if sys.platform == "win32" else "✗"
    print(f"{RED}{marker}{RESET} {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    marker = "[WARN]" if sys.platform == "win32" else "⚠"
    print(f"{YELLOW}{marker}{RESET} {msg}")


def print_info(msg: str) -> None:
    """Print an info message."""
    marker = "[INFO]" if sys.platform == "win32" else "ℹ"
    print(f"{BLUE}{marker}{RESET} {msg}")


class AutomationRunner:
    """Manages automatic execution of Aria systems."""

    def __init__(self, workspace_root: Path):
        """Initialize the automation runner."""
        self.workspace_root = workspace_root
        self.processes: List[subprocess.Popen] = []
        self.running = True

    def setup_signal_handlers(self) -> None:
        """Setup SIGINT and SIGTERM handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            print_warning("Shutdown signal received...")
            self.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def validate_environment(self) -> bool:
        """Validate that the environment is set up correctly."""
        print_section("Environment Validation")

        # Check Python version
        if sys.version_info < (3, 8):
            print_error(f"Python 3.8+ required (current: {sys.version})")
            return False
        print_ok(f"Python version: {sys.version.split()[0]}")

        # Check workspace exists
        if not self.workspace_root.exists():
            print_error(f"Workspace root not found: {self.workspace_root}")
            return False
        print_ok(f"Workspace found: {self.workspace_root}")

        # Check key directories
        key_dirs = ["scripts", "apps", "tests"]
        for dir_name in key_dirs:
            dir_path = self.workspace_root / dir_name
            if dir_path.exists():
                print_ok(f"Directory found: {dir_name}/")
            else:
                print_warning(f"Directory not found: {dir_name}/")

        return True

    def run_env_setup_check(self) -> bool:
        """Run the environment setup check."""
        print_section("Running Environment Setup Check")

        check_script = self.workspace_root / "scripts" / "setup_env_check.py"
        if not check_script.exists():
            print_warning(f"Setup check script not found: {check_script}")
            return True

        try:
            result = subprocess.run(
                [_PYTHON_EXECUTABLE, str(check_script)],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
            )

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if result.returncode == 0:
                print_ok("Environment check passed")
                return True
            else:
                print_warning("Environment check completed with warnings")
                return True  # Don't block on warnings

        except subprocess.TimeoutExpired:
            print_warning("Environment check timed out")
            return True
        except Exception as e:
            print_error(f"Failed to run environment check: {e}")
            return True

    def run_tests(self) -> bool:
        """Run the test suite."""
        print_section("Running Test Suite")

        tests_dir = self.workspace_root / "tests"
        if not tests_dir.exists():
            print_warning(f"Test directory not found: {tests_dir}")
            return False

        try:
            print_info("Starting pytest...")
            result = subprocess.run(
                [_PYTHON_EXECUTABLE, "-m", "pytest", "tests", "-q", "--tb=short"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=300,
            )

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if result.returncode == 0:
                print_ok("All tests passed")
                return True
            if "No module named pytest" in (result.stderr or ""):
                print_error(
                    "pytest is not installed in the active Python environment"
                )
                return False
            if result.returncode == 5:
                print_warning("pytest collected no tests")
                return False
            else:
                print_warning("Test suite failed")
                return False

        except subprocess.TimeoutExpired:
            print_warning("Test suite timed out after 5 minutes")
            return False
        except Exception as e:
            print_error(f"Failed to run tests: {e}")
            return False

    def run_validation(self) -> bool:
        """Run integration validation checks."""
        print_section("Running Integration Validation")

        validation_script = self.workspace_root / "scripts" / "fast_validate.py"
        if not validation_script.exists():
            print_info("Fast validation script not found, skipping")
            return True

        try:
            print_info("Starting validation checks...")
            result = subprocess.run(
                [sys.executable, str(validation_script)],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,
            )

            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)

            if result.returncode == 0:
                print_ok("Validation passed")
                return True
            else:
                print_warning("Validation completed with warnings")
                return False

        except subprocess.TimeoutExpired:
            print_warning("Validation timed out")
            return False
        except Exception as e:
            print_error(f"Failed to run validation: {e}")
            return False

    def display_status(self) -> None:
        """Display current automation status."""
        print_section("Automation Status")
        print_info(f"Running {len(self.processes)} background processes")
        for i, proc in enumerate(self.processes, 1):
            status = "Running" if proc.poll() is None else "Stopped"
            print_info(f"  [{i}] {status} (PID: {proc.pid})")

    def shutdown(self) -> None:
        """Gracefully shutdown all running processes."""
        print_warning("Shutting down automation runner...")

        for proc in self.processes:
            if proc.poll() is None:  # Process is still running
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                    print_ok(f"Process {proc.pid} terminated gracefully")
                except subprocess.TimeoutExpired:
                    proc.kill()
                    print_warning(f"Process {proc.pid} killed forcefully")
                except Exception as e:
                    print_error(f"Error terminating process {proc.pid}: {e}")

        self.running = False
        print_ok("Automation runner shut down complete")

    def run(self) -> bool:
        """Run the complete automation workflow."""
        self.setup_signal_handlers()

        try:
            # Validate environment
            if not self.validate_environment():
                print_error("Environment validation failed")
                return False

            # Run environment setup check
            env_ok = self.run_env_setup_check()

            # Run tests
            print_info("Running test suite...")
            tests_ok = self.run_tests()

            # Run validation
            validation_ok = self.run_validation()

            overall_ok = env_ok and tests_ok and validation_ok

            # Display final status
            print_section("Automation Complete")
            if overall_ok:
                print_ok("All automated tasks completed successfully!")
            else:
                print_warning(
                    "Automation finished with issues. Review the warnings/errors above."
                )
            self.display_status()
            return overall_ok

        except KeyboardInterrupt:
            print_warning("Interrupted by user")
            self.shutdown()
            return False
        except Exception as e:
            print_error(f"Automation runner error: {e}")
            self.shutdown()
            return False


def main() -> int:
    """Main entry point for the automation runner."""
    workspace_root = Path(__file__).parent

    runner = AutomationRunner(workspace_root)
    return 0 if runner.run() else 1


if __name__ == "__main__":
    raise SystemExit(main())
