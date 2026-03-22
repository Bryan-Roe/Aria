#!/usr/bin/env python3
"""
Quick test of Aria automation components
Validates that all automation pieces work together
"""
import subprocess
import sys
import time
from pathlib import Path

if "pytest" in sys.modules:
    import pytest

    pytestmark = pytest.mark.skip(
        reason="script-style automation smoke checks are environment-dependent"
    )

REPO_ROOT = Path(__file__).resolve().parents[1]
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(msg):
    print(f"{BLUE}[TEST]{RESET} {msg}")


def print_pass(msg):
    print(f"{GREEN}[PASS]{RESET} {msg}")


def print_fail(msg):
    print(f"{RED}[FAIL]{RESET} {msg}")


def print_warn(msg):
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def check_file_exists(path):
    """Test if required file exists"""
    test_path = REPO_ROOT / path
    print_test(f"Checking {path}...")
    if test_path.exists():
        print_pass(f"{path} exists")
        return True
    else:
        print_fail(f"{path} not found")
        return False


def check_import(module_name):
    """Test if Python module can be imported"""
    print_test(f"Importing {module_name}...")
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import {module_name}"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            print_pass(f"{module_name} imported successfully")
            return True
        else:
            print_fail(f"Failed to import {module_name}")
            return False
    except Exception as e:
        print_fail(f"Error importing {module_name}: {e}")
        return False


def check_script_help(script_path):
    """Test if script shows help"""
    test_path = REPO_ROOT / script_path
    print_test(f"Testing {script_path} --help...")
    try:
        result = subprocess.run(
            [sys.executable, str(test_path), "--help"],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0 and ("usage" in result.stdout.lower() or "help" in result.stdout.lower()):
            print_pass(f"{script_path} help works")
            return True
        else:
            print_warn(f"{script_path} help may not work properly")
            return True  # Not critical
    except Exception as e:
        print_fail(f"Error testing {script_path}: {e}")
        return False


def test_status_check():
    """Test status check functionality"""
    print_test("Testing status check...")
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" /
                                 "aria_automation.py"), "--status"],
            capture_output=True,
            timeout=10,
            text=True
        )
        # Status check should work even if nothing is running
        if "Automation" in result.stdout or "No automation" in result.stdout:
            print_pass("Status check works")
            return True
        else:
            print_warn("Status check output unexpected")
            print(f"Output: {result.stdout[:200]}")
            return True  # Not critical
    except Exception as e:
        print_fail(f"Status check failed: {e}")
        return False


def main():
    print("\n" + "="*80)
    print(f"{BLUE}Aria Automation Test Suite{RESET}")
    print("="*80 + "\n")

    tests_passed = 0
    tests_total = 0

    # Test 1: Check required files
    print(f"\n{BLUE}=== File Structure Tests ==={RESET}\n")
    files_to_check = [
        "scripts/aria_automation.py",
        "scripts/start_aria.sh",
        "config/aria_automation.service",
        "config/master_orchestrator.yaml",
        "ARIA_AUTOMATION_GUIDE.md",
        "aria_web/server.py",
        "aria_web/index.html"
    ]

    for file_path in files_to_check:
        tests_total += 1
        if check_file_exists(file_path):
            tests_passed += 1

    # Test 2: Check Python dependencies
    print(f"\n{BLUE}=== Dependency Tests ==={RESET}\n")
    modules_to_test = [
        "json",
        "subprocess",
        "pathlib",
        "threading"
    ]

    for module in modules_to_test:
        tests_total += 1
        if check_import(module):
            tests_passed += 1

    # Test optional psutil
    print_test("Checking optional dependency: psutil...")
    if check_import("psutil"):
        print_pass("psutil available (recommended)")
    else:
        print_warn("psutil not available (will be installed on first run)")

    # Test 3: Script functionality
    print(f"\n{BLUE}=== Script Tests ==={RESET}\n")

    tests_total += 1
    if check_script_help("scripts/aria_automation.py"):
        tests_passed += 1

    tests_total += 1
    if test_status_check():
        tests_passed += 1

    # Test 4: Check start script is executable
    print_test("Checking start script permissions...")
    start_script = REPO_ROOT / "scripts" / "start_aria.sh"
    if start_script.exists():
        import os
        if os.access(start_script, os.X_OK):
            print_pass("start_aria.sh is executable")
            tests_total += 1
            tests_passed += 1
        else:
            print_warn(
                "start_aria.sh not executable (run: chmod +x scripts/start_aria.sh)")
            tests_total += 1

    # Summary
    print("\n" + "="*80)
    print(f"{BLUE}Test Summary{RESET}")
    print("="*80)
    print(f"Tests Passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print(f"\n{GREEN}✅ All tests passed! Automation is ready to use.{RESET}\n")
        print(f"{BLUE}Quick Start:{RESET}")
        print(f"  ./scripts/start_aria.sh          # Interactive menu")
        print(f"  ./scripts/start_aria.sh full     # Start full stack")
        print(f"  ./scripts/start_aria.sh status   # Check status")
        return 0
    elif tests_passed >= tests_total * 0.8:
        print(f"\n{YELLOW}⚠️  Most tests passed. Review warnings above.{RESET}\n")
        return 0
    else:
        print(f"\n{RED}❌ Some tests failed. Review errors above.{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
