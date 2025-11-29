#!/usr/bin/env python
"""Test Runner - Automated Test Orchestrator

Runs pytest with intelligent filtering, parallel execution, and result aggregation.

Features:
- Auto-detect test suites (unit, integration, slow, azure)
- Parallel execution of independent test suites
- Coverage collection with focused reporting
- Generate test reports in JSON + Markdown
- CI-friendly exit codes and artifacts

Usage:
  python .\\scripts\\test_runner.py --all                  # Run all non-slow tests
  python .\\scripts\\test_runner.py --unit                 # Unit tests only
  python .\\scripts\\test_runner.py --integration          # Integration tests
  python .\\scripts\\test_runner.py --suite autotrain      # Specific suite
  python .\\scripts\\test_runner.py --coverage             # With coverage
  python .\\scripts\\test_runner.py --watch                # Watch mode (re-run on change)
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
DATA_OUT = REPO_ROOT / "data_out" / "test_runner"


@dataclass
class TestSuite:
    """Represents a test suite configuration"""
    name: str
    patterns: List[str] = field(default_factory=list)
    markers: List[str] = field(default_factory=list)
    exclude_markers: List[str] = field(default_factory=list)
    timeout: int = 300  # seconds
    
    def build_pytest_args(self) -> List[str]:
        args = []
        
        # Expand glob patterns to actual file paths
        if self.patterns:
            for pattern in self.patterns:
                # Use pathlib glob to expand wildcards
                matches = list(TESTS_DIR.glob(pattern))
                if matches:
                    args.extend([str(p) for p in matches])
                else:
                    # If no matches, add the pattern anyway (pytest will report no tests)
                    args.append(str(TESTS_DIR / pattern))
        else:
            args.append(str(TESTS_DIR))
        
        # Add marker expressions only if we have markers to filter
        # Important: The marker expression must be passed as a single argument
        # to avoid shell parsing issues when subprocess.run splits by spaces
        if self.markers or self.exclude_markers:
            marker_expr = []
            for m in self.markers:
                marker_expr.append(m)
            for m in self.exclude_markers:
                marker_expr.append(f"not {m}")
            
            if marker_expr:
                # Join the expressions with ' and ' to create a single string argument
                # This ensures pytest receives the complete expression as one value
                args.extend(["-m", " and ".join(marker_expr)])
        
        return args


# Predefined test suites
SUITES = {
    "unit": TestSuite(
        name="unit",
        patterns=["test_*_unit.py"],
        markers=[],
        exclude_markers=[],  # No marker filtering for unit tests
    ),
    "integration": TestSuite(
        name="integration",
        patterns=["test_*_integration.py"],
        markers=[],
        exclude_markers=[],  # No marker filtering for integration tests
    ),
    "autotrain": TestSuite(
        name="autotrain",
        patterns=["test_autotrain*.py"],
        exclude_markers=["slow", "azure"],
    ),
    "quantum": TestSuite(
        name="quantum",
        patterns=["test_quantum*.py", "test_validate_qiskit*.py"],
        exclude_markers=["azure"],
    ),
    "database": TestSuite(
        name="database",
        patterns=["test_database*.py"],
        exclude_markers=["slow"],
    ),
    "chat": TestSuite(
        name="chat",
        patterns=["test_chat*.py"],
        exclude_markers=["slow"],
    ),
    "all_fast": TestSuite(
        name="all_fast",
        patterns=["test_*.py"],
        exclude_markers=["slow", "azure"],  # Only exclude explicitly marked tests
    ),
    "all": TestSuite(
        name="all",
        patterns=["test_*.py"],
        exclude_markers=["azure"],  # Include slow tests, but exclude azure
        timeout=1800,
    ),
}


@dataclass
class TestResult:
    """Test execution result"""
    suite: str
    status: str  # "passed" | "failed" | "error"
    duration_sec: float
    tests_collected: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    exit_code: int = 0
    output: str = ""
    coverage_pct: Optional[float] = None


def run_pytest(suite: TestSuite, coverage: bool = False, verbose: int = 1) -> TestResult:
    """Execute pytest for a test suite"""
    print(f"\n[test_runner] Running suite: {suite.name}")
    
    cmd = [sys.executable, "-m", "pytest"]
    
    # Verbosity
    if verbose > 0:
        cmd.append("-" + "v" * verbose)
    
    # Add suite-specific args
    cmd.extend(suite.build_pytest_args())
    
    # Coverage
    if coverage:
        cmd.extend([
            "--cov=scripts",
            "--cov=shared",
            "--cov-report=term-missing:skip-covered",
            "--cov-report=json",
        ])
    
    # Additional pytest options
    cmd.extend([
        "--tb=short",
        "--disable-warnings",
    ])
    
    start = time.time()
    result = TestResult(
        suite=suite.name,
        status="error",
        duration_sec=0.0,
    )
    
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=suite.timeout + 30,
        )
        
        result.exit_code = proc.returncode
        result.output = proc.stdout + "\n" + proc.stderr
        result.duration_sec = time.time() - start
        
        # Strip ANSI escape codes for easier parsing
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        clean_output = ansi_escape.sub('', result.output)
        
        # Parse pytest output for stats using regex for robustness
        # Look for patterns like "40 passed in 0.13s" or "5 passed, 2 failed in 10.5s"
        passed_match = re.search(r'(\d+)\s+passed', clean_output)
        if passed_match:
            result.tests_passed = int(passed_match.group(1))
        
        failed_match = re.search(r'(\d+)\s+failed', clean_output)
        if failed_match:
            result.tests_failed = int(failed_match.group(1))
        
        skipped_match = re.search(r'(\d+)\s+skipped', clean_output)
        if skipped_match:
            result.tests_skipped = int(skipped_match.group(1))
        
        collected_match = re.search(r'collected\s+(\d+)\s+items?', clean_output)
        if collected_match:
            result.tests_collected = int(collected_match.group(1))
        
        # Parse coverage if present
        if coverage:
            cov_json = REPO_ROOT / "coverage.json"
            if cov_json.exists():
                try:
                    with cov_json.open("r") as f:
                        cov_data = json.load(f)
                        result.coverage_pct = cov_data.get("totals", {}).get("percent_covered")
                except Exception as e:
                    result.output += f"\n[coverage-parse-error] {e}" if result.output else f"[coverage-parse-error] {e}"
        
        # Determine status
        if proc.returncode == 0:
            result.status = "passed"
        elif result.tests_failed > 0:
            result.status = "failed"
        else:
            result.status = "error"
            
    except subprocess.TimeoutExpired:
        result.status = "timeout"
        result.duration_sec = suite.timeout
        result.output = f"Test suite timed out after {suite.timeout}s"
    except Exception as e:
        result.status = "error"
        result.output = f"Exception during test execution: {e}"
        result.duration_sec = time.time() - start
    
    # Summary
    status_symbols = {
        "passed": "[OK]",
        "failed": "[FAIL]",
        "error": "[ERR]",
        "timeout": "[TIMEOUT]"
    }
    status_mark = status_symbols.get(result.status, "[?]")
    print(f"[test_runner] {status_mark} {suite.name}: {result.tests_passed} passed, {result.tests_failed} failed in {result.duration_sec:.1f}s")
    
    return result


def write_results(results: List[TestResult]) -> None:
    """Write test results to JSON and Markdown"""
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    
    # JSON
    json_data = {
        "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "suites": [
            {
                "name": r.suite,
                "status": r.status,
                "duration_sec": round(r.duration_sec, 2),
                "tests_collected": r.tests_collected,
                "tests_passed": r.tests_passed,
                "tests_failed": r.tests_failed,
                "tests_skipped": r.tests_skipped,
                "exit_code": r.exit_code,
                "coverage_pct": round(r.coverage_pct, 2) if r.coverage_pct else None,
            }
            for r in results
        ],
        "summary": {
            "total_suites": len(results),
            "passed": sum(1 for r in results if r.status == "passed"),
            "failed": sum(1 for r in results if r.status == "failed"),
            "total_tests": sum(r.tests_collected for r in results),
            "total_passed": sum(r.tests_passed for r in results),
            "total_failed": sum(r.tests_failed for r in results),
            "total_duration_sec": round(sum(r.duration_sec for r in results), 2),
        },
    }
    
    json_path = DATA_OUT / "results.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    
    # Markdown
    lines = [
        "# Test Results",
        "",
        f"_Generated: {json_data['generated_at']}_",
        "",
        "## Summary",
        "",
        f"- **Total Suites**: {json_data['summary']['total_suites']}",
        f"- **Passed**: {json_data['summary']['passed']}",
        f"- **Failed**: {json_data['summary']['failed']}",
        f"- **Total Tests**: {json_data['summary']['total_tests']}",
        f"- **Total Passed**: {json_data['summary']['total_passed']}",
        f"- **Total Failed**: {json_data['summary']['total_failed']}",
        f"- **Total Duration**: {json_data['summary']['total_duration_sec']}s",
        "",
        "## Test Suites",
        "",
        "| Suite | Status | Tests | Passed | Failed | Skipped | Duration | Coverage |",
        "|-------|--------|-------|--------|--------|---------|----------|----------|",
    ]
    
    for r in results:
        status_symbols = {
            "passed": "[OK]",
            "failed": "[FAIL]",
            "error": "[ERR]",
            "timeout": "[TIMEOUT]"
        }
        status_mark = status_symbols.get(r.status, "[?]")
        cov_str = f"{r.coverage_pct:.1f}%" if r.coverage_pct else "-"
        lines.append(
            f"| {r.suite} | {status_mark} {r.status} | {r.tests_collected} | "
            f"{r.tests_passed} | {r.tests_failed} | {r.tests_skipped} | "
            f"{r.duration_sec:.1f}s | {cov_str} |"
        )
    
    md_path = DATA_OUT / "results.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    print(f"\n[test_runner] Results written:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


def watch_mode(suites: List[str], coverage: bool) -> None:
    """Watch mode - re-run tests on file changes"""
    print("[test_runner] Watch mode - monitoring for changes (Ctrl+C to exit)")
    
    # Track modification times
    watched_paths = [
        TESTS_DIR,
        REPO_ROOT / "scripts",
        REPO_ROOT / "shared",
    ]
    
    def get_mtimes() -> Dict[Path, float]:
        mtimes = {}
        for base in watched_paths:
            if not base.exists():
                continue
            for f in base.rglob("*.py"):
                try:
                    mtimes[f] = f.stat().st_mtime
                except Exception:
                    pass
        return mtimes
    
    last_mtimes = get_mtimes()
    
    try:
        while True:
            time.sleep(0.5)  # Faster watch mode response
            current_mtimes = get_mtimes()
            
            changed = [
                str(f) for f, mtime in current_mtimes.items()
                if last_mtimes.get(f, 0) != mtime
            ]
            
            if changed:
                print(f"\n[test_runner] Detected changes in {len(changed)} file(s)")
                for c in changed[:5]:
                    print(f"  - {Path(c).relative_to(REPO_ROOT)}")
                
                # Re-run tests
                results = []
                for suite_name in suites:
                    suite = SUITES.get(suite_name)
                    if suite:
                        result = run_pytest(suite, coverage=coverage, verbose=0)
                        results.append(result)
                
                write_results(results)
                last_mtimes = current_mtimes
                
    except KeyboardInterrupt:
        print("\n[test_runner] Watch stopped")


def main() -> None:
    ap = argparse.ArgumentParser(description="Automated test runner")
    ap.add_argument("--all", action="store_true", help="Run all tests (exclude slow, azure)")
    ap.add_argument("--unit", action="store_true", help="Run unit tests only")
    ap.add_argument("--integration", action="store_true", help="Run integration tests")
    ap.add_argument("--suite", nargs="+", help="Run specific suite(s)")
    ap.add_argument("--coverage", action="store_true", help="Collect coverage")
    ap.add_argument("--watch", action="store_true", help="Watch mode (re-run on change)")
    ap.add_argument("--verbose", "-v", action="count", default=1, help="Increase verbosity")
    ap.add_argument("--list-suites", action="store_true", help="List available test suites")
    args = ap.parse_args()
    
    if args.list_suites:
        print("Available test suites:")
        for name, suite in SUITES.items():
            print(f"  {name:15} - patterns={suite.patterns}, markers={suite.markers}")
        return
    
    # Determine which suites to run
    suite_names: List[str] = []
    
    if args.all:
        suite_names = ["all_fast"]
    elif args.unit:
        suite_names = ["unit"]
    elif args.integration:
        suite_names = ["integration"]
    elif args.suite:
        suite_names = args.suite
    else:
        # Default: run fast suites
        suite_names = ["unit", "integration"]
    
    # Validate suite names
    invalid = [s for s in suite_names if s not in SUITES]
    if invalid:
        print(f"Error: Unknown suite(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(SUITES.keys())}")
        sys.exit(1)
    
    # Watch mode
    if args.watch:
        watch_mode(suite_names, args.coverage)
        return
    
    # Run tests
    results: List[TestResult] = []
    for suite_name in suite_names:
        suite = SUITES[suite_name]
        result = run_pytest(suite, coverage=args.coverage, verbose=args.verbose)
        results.append(result)
    
    # Write results
    write_results(results)
    
    # Exit code
    if any(r.status in ("failed", "error", "timeout") for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
