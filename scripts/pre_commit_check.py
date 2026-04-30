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
import os
import re
import subprocess
import sys
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


def _staged_files(*pathspecs: str) -> List[str]:
    """Return staged files filtered by optional git pathspecs."""
    cmd = ["git", "diff", "--cached", "--name-only"]
    if pathspecs:
        cmd.extend(["--", *pathspecs])
    code, stdout, _ = run_command(cmd)
    if code != 0:
        return []
    return [line.strip() for line in stdout.splitlines() if line.strip()]


def _find_repo_doc(doc_name: str) -> Path | None:
    """Find a documentation file by basename anywhere in the repo."""
    direct = REPO_ROOT / doc_name
    if direct.exists():
        return direct

    for path in REPO_ROOT.rglob(doc_name):
        text = str(path)
        if any(part in text for part in ["venv/", ".venv/", "__pycache__/"]):
            continue
        return path
    return None


def print_header(text: str):
    print(f"\n{CYAN}{BOLD}{text}{RESET}")


def print_success(text: str):
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text: str):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text: str):
    print(f"{RED}✗ {text}{RESET}")


def run_command(
    cmd: List[str], cwd: Path = REPO_ROOT, timeout_seconds: int = 120
) -> Tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout_seconds}s"
    except Exception as e:
        return 1, "", str(e)


def check_unit_tests() -> bool:
    """Run pytest on all test files."""
    print_header("[1/5] Running unit tests...")

    default_timeout = 600
    raw_timeout = os.environ.get("PRE_COMMIT_TEST_TIMEOUT", str(default_timeout))
    try:
        test_timeout = max(60, int(raw_timeout))
    except ValueError:
        test_timeout = default_timeout

    pytest_exe = REPO_ROOT / "venv" / "Scripts" / "python.exe"
    if not pytest_exe.exists():
        pytest_exe = Path(sys.executable)

    code, stdout, stderr = run_command(
        [str(pytest_exe), "-m", "pytest", "tests/", "-v", "--tb=short"],
        timeout_seconds=test_timeout,
    )

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
        if stderr:
            print(stderr[-300:] if len(stderr) > 300 else stderr)
        return False


def check_linting() -> bool:
    """Run linting checks on Python files."""
    print_header("[2/5] Linting code...")

    staged_python_files = _staged_files("*.py")
    if not staged_python_files:
        print_success("No staged Python files to lint")
        return True

    # Try ruff first (fast, modern linter).
    # We intentionally gate on high-signal, correctness/safety-focused rules
    # to avoid blocking commits on large-scale formatting debt in unrelated
    # staged files.
    critical_rules = ["E9", "F63", "F7", "F82", "B904"]
    code, stdout, stderr = run_command(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            *staged_python_files,
            "--select",
            ",".join(critical_rules),
        ]
    )

    if code == 5:  # ruff not installed
        print_warning(
            "ruff not installed, skipping linting (install with: pip install ruff)"
        )
        return True

    if code == 0:
        print_success("No linting issues found")
        return True
    else:
        issues = [line for line in stdout.splitlines() if line.strip()]
        print_error(
            "Found critical linting issues "
            f"({','.join(critical_rules)}) in {len(staged_python_files)} staged file(s)"
        )
        for issue in issues[:10]:
            print(f"  {issue}")
        return False


def check_security() -> bool:
    """Scan for hardcoded secrets and security issues."""
    print_header("[3/5] Security scan...")

    issues = []

    # Check for common secret patterns
    secret_patterns = [
        (r'api[_-]?key\s*=\s*["\'][^"\']{20,}["\']', "Potential API key"),
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
        (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API key"),
        (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    ]

    py_files = list(REPO_ROOT.glob("**/*.py"))
    py_files = [
        f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)
    ]

    for py_file in py_files[:50]:  # Limit to first 50 files for speed
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, desc in secret_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    # Exclude test files and env templates
                    if (
                        "test_" not in py_file.name
                        and "example" not in py_file.name.lower()
                    ):
                        issues.append(f"{py_file.name}: {desc}")
        except Exception:
            continue

    # Check if .env is being committed
    code, stdout, _ = run_command(["git", "diff", "--cached", "--name-only"])
    if code == 0:
        staged_files = stdout.split("\n")
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

    staged_files = stdout.split("\n")
    issues = []

    for file_path in staged_files:
        if not file_path.strip():
            continue

        full_path = REPO_ROOT / file_path

        # Check for unwanted files
        if any(
            pattern in file_path
            for pattern in ["__pycache__", ".pyc", "venv/", ".venv/", "__azurite_db"]
        ):
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

    missing = [doc for doc in required_docs if _find_repo_doc(doc) is None]

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
