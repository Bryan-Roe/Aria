#!/usr/bin/env python
"""
Centralized test orchestrator with intelligent filtering and result aggregation.

Test Suites:
  unit        — Fast unit tests (excludes slow, azure, integration, quantum, gpu)
  integration — Integration tests only
  all_fast    — All tests except slow and azure
  all         — Every test
  autotrain   — Autotrain-related tests
  quantum     — Quantum-related tests
  database    — Database integration tests
  chat        — Chat provider tests

Usage:
  python scripts/test_runner.py --unit
  python scripts/test_runner.py --unit --coverage
  python scripts/test_runner.py --all
  python scripts/test_runner.py --integration
  python scripts/test_runner.py --list-suites
  python scripts/test_runner.py --unit --integration --watch
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
DATA_OUT = REPO_ROOT / "data_out"

# ---------------------------------------------------------------------------
# Suite Definitions
# ---------------------------------------------------------------------------
SUITES = {
    "unit": {
        "description": "Fast unit tests (~0.5s)",
        "pytest_args": [
            "-m",
            "not slow and not azure and not integration and not quantum and not gpu",
        ],
    },
    "integration": {
        "description": "Integration / external-service tests (~3s)",
        "pytest_args": ["-m", "integration"],
    },
    "all_fast": {
        "description": "All tests except slow & azure (~10s)",
        "pytest_args": ["-m", "not slow and not azure"],
    },
    "all": {
        "description": "Full test suite (may be slow)",
        "pytest_args": [],
    },
    "autotrain": {
        "description": "Autotrain-related tests",
        "pytest_args": ["-k", "autotrain or train"],
    },
    "quantum": {
        "description": "Quantum ML tests",
        "pytest_args": ["-m", "quantum"],
    },
    "database": {
        "description": "Database integration tests",
        "pytest_args": ["-k", "database or sql"],
    },
    "chat": {
        "description": "Chat provider tests",
        "pytest_args": ["-k", "provider or chat or lmstudio"],
    },
}

# ---------------------------------------------------------------------------
# Result Parsing
# ---------------------------------------------------------------------------
_RESULT_RE = re.compile(
    r"=+ (?:(\d+) passed)?"
    r"(?:,? ?(\d+) failed)?"
    r"(?:,? ?(\d+) error)?"
    r"(?:,? ?(\d+) skipped)?"
    r"(?:,? ?(\d+) warning)?"
    r".*=+",
)


def _parse_pytest_summary(output: str) -> dict:
    """Extract counts from pytest's one-line summary."""
    m = _RESULT_RE.search(output)
    if not m:
        return {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    return {
        "passed": int(m.group(1) or 0),
        "failed": int(m.group(2) or 0),
        "errors": int(m.group(3) or 0),
        "skipped": int(m.group(4) or 0),
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_suite(name: str, *, coverage: bool = False, verbose: int = 1) -> dict:
    """Run a single pytest suite and return structured results."""
    suite = SUITES[name]
    cmd = [sys.executable, "-m", "pytest", str(TESTS_DIR)]
    cmd.extend(suite["pytest_args"])

    if coverage:
        cmd.extend(["--cov=shared", "--cov=scripts", "--cov-report=term-missing"])

    if verbose == 0:
        cmd.append("-q")
    elif verbose >= 2:
        cmd.append("-v")

    # Strip ANSI codes for parsing
    cmd.extend(["--tb=short", "--no-header"])

    start = time.monotonic()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    elapsed = round(time.monotonic() - start, 2)

    # Remove ANSI escape sequences for reliable regex
    clean = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout + result.stderr)

    summary = _parse_pytest_summary(clean)
    summary.update(
        {
            "suite": name,
            "returncode": result.returncode,
            "duration_s": elapsed,
            "success": result.returncode == 0,
        }
    )

    return summary, result.stdout, result.stderr


def list_suites() -> None:
    """Print available test suites."""
    print("Available test suites:\n")
    for name, info in SUITES.items():
        print(f"  {name:15s}  {info['description']}")
    print(f"\nUsage: python {Path(__file__).name} --<suite> [--coverage]")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(results: list[dict]) -> Path:
    """Write JSON + Markdown reports to data_out/."""
    out_dir = DATA_OUT / "test_runner"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    report = {
        "timestamp": ts,
        "suites": results,
        "overall_success": all(r["success"] for r in results),
    }

    json_path = out_dir / "latest_results.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Markdown summary
    md_lines = [f"# Test Runner Results — {ts}\n"]
    for r in results:
        icon = "✅" if r["success"] else "❌"
        md_lines.append(
            f"| {icon} | **{r['suite']}** | passed={r['passed']} failed={r['failed']} "
            f"errors={r['errors']} skipped={r['skipped']} | {r['duration_s']}s |"
        )
    md_path = out_dir / "latest_results.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    return json_path


# ---------------------------------------------------------------------------
# Watch Mode
# ---------------------------------------------------------------------------
def _watch_loop(suites: list[str], coverage: bool, verbose: int) -> None:
    """Re-run suites when Python files change (poll-based, 2 s interval)."""
    print("👀 Watch mode — press Ctrl+C to stop\n")
    last_mtime: float = 0.0

    while True:
        current = max(
            (
                p.stat().st_mtime
                for p in REPO_ROOT.rglob("*.py")
                if "venv" not in str(p)
            ),
            default=0.0,
        )
        if current > last_mtime:
            last_mtime = current
            _run_selected(suites, coverage=coverage, verbose=verbose)
        time.sleep(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def _run_selected(suites: list[str], *, coverage: bool, verbose: int) -> bool:
    """Run requested suites, print output, return overall success."""
    results = []
    overall = True

    for name in suites:
        print(f"\n{'='*60}")
        print(f"  Running suite: {name}  ({SUITES[name]['description']})")
        print(f"{'='*60}\n")

        summary, stdout, stderr = run_suite(name, coverage=coverage, verbose=verbose)
        results.append(summary)

        # Print pytest output (preserving colours in terminal)
        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        icon = "✅" if summary["success"] else "❌"
        print(
            f"\n{icon} {name}: passed={summary['passed']} failed={summary['failed']} "
            f"errors={summary['errors']} skipped={summary['skipped']}  "
            f"({summary['duration_s']}s)"
        )
        if not summary["success"]:
            overall = False

    report_path = write_report(results)
    print(f"\n📋 Report written to {report_path.relative_to(REPO_ROOT)}")

    if overall:
        print("\n✅ All suites passed!")
    else:
        print("\n❌ Some suites failed — see output above.")

    return overall


def main() -> None:
    ap = argparse.ArgumentParser(
        description="QAI centralized test runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--unit", action="store_true", help="Run unit tests")
    ap.add_argument("--integration", action="store_true", help="Run integration tests")
    ap.add_argument("--all", action="store_true", help="Run all tests")
    ap.add_argument("--all-fast", action="store_true", help="All except slow & azure")
    ap.add_argument("--autotrain", action="store_true", help="Autotrain tests")
    ap.add_argument("--quantum", action="store_true", help="Quantum tests")
    ap.add_argument("--database", action="store_true", help="Database tests")
    ap.add_argument("--chat", action="store_true", help="Chat tests")
    ap.add_argument("--coverage", action="store_true", help="Enable coverage reporting")
    ap.add_argument("--watch", action="store_true", help="Re-run on file changes")
    ap.add_argument("--list-suites", action="store_true", help="List available suites")
    ap.add_argument(
        "--verbose",
        type=int,
        default=1,
        help="Verbosity (0=quiet, 1=normal, 2=verbose)",
    )
    args = ap.parse_args()

    if args.list_suites:
        list_suites()
        return

    # Collect requested suites
    selected: list[str] = []
    if args.unit:
        selected.append("unit")
    if args.integration:
        selected.append("integration")
    if args.all:
        selected.append("all")
    if args.all_fast:
        selected.append("all_fast")
    if args.autotrain:
        selected.append("autotrain")
    if args.quantum:
        selected.append("quantum")
    if args.database:
        selected.append("database")
    if args.chat:
        selected.append("chat")

    if not selected:
        selected = ["unit"]  # Default to unit tests

    if args.watch:
        try:
            _watch_loop(selected, coverage=args.coverage, verbose=args.verbose)
        except KeyboardInterrupt:
            print("\n⏹  Watch mode stopped.")
            return

    success = _run_selected(selected, coverage=args.coverage, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
