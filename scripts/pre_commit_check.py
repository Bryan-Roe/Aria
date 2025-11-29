#!/usr/bin/env python3
"""Pre-commit validation script for QAI workspace.

Runs automated checks before committing code changes:
- Unit tests (pytest)
- Linting (ruff/pycodestyle)
- Security scan (secrets detection)
- Git hygiene (file sizes, unwanted files)

Usage:
    python scripts/pre_commit_check.py
    python scripts/pre_commit_check.py --checks tests,lint
    python scripts/pre_commit_check.py --skip security
"""
import argparse
import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple

# ANSI color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

REPO_ROOT = Path(__file__).resolve().parent.parent


def print_header(text: str):
    print(f"\n{CYAN}{BOLD}{text}{RESET}")


def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")


def run_command(cmd: List[str], cwd: Path = REPO_ROOT) -> Tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out after 120s"
    except Exception as e:
        return 1, "", str(e)


def check_unit_tests() -> bool:
    """Run pytest on all test files."""
    print_header("[1/5] Running unit tests...")
    
    pytest_exe = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    if not pytest_exe.exists():
        pytest_exe = Path(sys.executable)
    
    code, stdout, stderr = run_command([str(pytest_exe), "-m", "pytest", "tests/", "-v", "--tb=short"])
    
    if code == 0:
        # Parse test count from output
        match = re.search(r"(\d+) passed", stdout)
        if match:
            print_success(f"{match.group(1)} tests passed")
        else:
            print_success("All tests passed")
        return True
    else:
        print_error("Tests failed")
        print(stdout[-500:] if len(stdout) > 500 else stdout)  # Show last 500 chars
        return False


def check_linting() -> bool:
    """Run linting checks on Python files."""
    print_header("[2/5] Linting code...")
    
    # Try ruff first (fast, modern linter)
    code, stdout, stderr = run_command([sys.executable, "-m", "ruff", "check", ".", "--exclude", "venv,__pycache__,.venv,.pytest_cache"])
    
    if code == 5:  # ruff not installed
        print_warning("ruff not installed, skipping linting (install with: pip install ruff)")
        return True
    
    if code == 0:
        print_success("No linting issues found")
        return True
    else:
        # Show issues but don't fail (warnings only)
        issues = stdout.split('\n')
        critical = [line for line in issues if "error" in line.lower()]
        
        if critical:
            print_error(f"Found {len(critical)} critical linting issues")
            for issue in critical[:5]:  # Show first 5
                print(f"  {issue}")
            return False
        else:
            warnings = [line for line in issues if line.strip() and not line.startswith("Found")]
            if warnings:
                print_warning(f"Found {len(warnings)} linting warnings (non-critical)")
                for warn in warnings[:3]:  # Show first 3
                    print(f"  {warn}")
            else:
                print_success("No linting issues")
            return True


def check_security() -> bool:
    """Scan for hardcoded secrets and security issues."""
    print_header("[3/5] Security scan...")
    
    issues = []
    
    # Check for common secret patterns
    secret_patterns = [
        (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Potential API key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r'sk-[a-zA-Z0-9]{20,}', "OpenAI API key"),
        (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    ]
    
    py_files = list(REPO_ROOT.glob("**/*.py"))
    py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]
    
    for py_file in py_files[:50]:  # Limit to first 50 files for speed
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Exclude test files and env templates
                    if "test_" not in py_file.name and "example" not in py_file.name.lower():
                        issues.append(f"{py_file.name}: {desc}")
        except Exception:
            continue
    
    # Check if .env is being committed
    code, stdout, _ = run_command(["git", "diff", "--cached", "--name-only"])
    if code == 0:
        staged_files = stdout.split('\n')
        if any(".env" in f and "example" not in f for f in staged_files):
            issues.append(".env file in staging (should be in .gitignore)")
    
    if issues:
        print_error(f"Found {len(issues)} potential security issues:")
        for issue in issues[:5]:
            print(f"  {issue}")
        return False
    else:
        print_success("No security issues detected")
        return True


def check_git_hygiene() -> bool:
    """Check for large files and unwanted files in staging."""
    print_header("[4/5] Git hygiene...")
    
    code, stdout, _ = run_command(["git", "diff", "--cached", "--name-only"])
    
    if code != 0:
        print_warning("Not in a git repository or no staged files")
        return True
    
    staged_files = stdout.split('\n')
    issues = []
    
    for file_path in staged_files:
        if not file_path.strip():
            continue
        
        full_path = REPO_ROOT / file_path
        
        # Check for unwanted files
        if any(pattern in file_path for pattern in ["__pycache__", ".pyc", "venv/", ".venv/", "__azurite_db"]):
            issues.append(f"Unwanted file: {file_path}")
        
        # Check file size (warn if >10MB)
        if full_path.exists() and full_path.is_file():
            size_mb = full_path.stat().st_size / (1024 * 1024)
            if size_mb > 10:
                issues.append(f"Large file ({size_mb:.1f}MB): {file_path}")
    
    if issues:
        print_warning(f"Found {len(issues)} git hygiene issues:")
        for issue in issues[:5]:
            print(f"  {issue}")
        # Don't fail, just warn
        return True
    else:
        print_success("Git staging area looks clean")
        return True


def check_documentation() -> bool:
    """Verify documentation is up-to-date."""
    print_header("[5/5] Checking documentation...")
    
    # Check if README exists and is non-empty
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        print_error("README.md not found")
        return False
    
    if readme.stat().st_size < 100:
        print_error("README.md is suspiciously small")
        return False
    
    # Check for recent enhancements docs
    required_docs = [
        "ENHANCEMENTS_SUMMARY.md",
        "TELEMETRY_COSMOS_ENABLEMENT.md",
        "QUICK_REFERENCE.md",
    ]
    
    missing = [doc for doc in required_docs if not (REPO_ROOT / doc).exists()]
    
    if missing:
        print_warning(f"Missing documentation: {', '.join(missing)}")
        # Don't fail, just warn
    else:
        print_success("All key documentation present")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Pre-commit validation for QAI")
    parser.add_argument(
        "--checks",
        help="Comma-separated list of checks to run (tests,lint,security,git,docs)",
        default="tests,lint,security,git,docs",
    )
    parser.add_argument(
        "--skip",
        help="Comma-separated list of checks to skip",
        default="",
    )
    args = parser.parse_args()
    
    enabled_checks = set(args.checks.split(","))
    skipped_checks = set(args.skip.split(",")) if args.skip else set()
    enabled_checks -= skipped_checks
    
    print(f"\n{BOLD}{'═' * 67}{RESET}")
    print(f"{BOLD}{CYAN}QAI PRE-COMMIT VALIDATION{RESET}")
    print(f"{BOLD}{'═' * 67}{RESET}")
    
    results = {}
    
    if "tests" in enabled_checks:
        results["tests"] = check_unit_tests()
    
    if "lint" in enabled_checks:
        results["lint"] = check_linting()
    
    if "security" in enabled_checks:
        results["security"] = check_security()
    
    if "git" in enabled_checks:
        results["git"] = check_git_hygiene()
    
    if "docs" in enabled_checks:
        results["docs"] = check_documentation()
    
    # Summary
    print(f"\n{BOLD}{'═' * 67}{RESET}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}{BOLD}RESULT: All checks passed ✓ ({passed}/{total}){RESET}")
        print(f"{BOLD}{'═' * 67}{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}RESULT: Some checks failed ({passed}/{total} passed){RESET}")
        print(f"{BOLD}{'═' * 67}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
