#!/usr/bin/env python3
"""Automate repeated repo health validation/fix cycles.

This script is intended to reduce manual repetition when stabilizing the Aria
workspace. It can run a one-shot health cycle or watch mode loops.

Health cycle steps:
1) Optional Ruff auto-fix on changed Python files
2) pre_commit_check.py
3) integration_contract_gate.sh (strict optional)
4) Optional full pytest smoke (tests/ -q --maxfail=1)

Outputs:
- Console summary per cycle
- JSON status at data_out/repo_health_automation/status.json

Examples:
  python scripts/repo_health_automation.py --once
  python scripts/repo_health_automation.py --once --strict-endpoints --full-pytest
  python scripts/repo_health_automation.py --watch --interval 300 --auto-fix-ruff
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_OUT = REPO_ROOT / "data_out" / "repo_health_automation"
STATUS_PATH = DATA_OUT / "status.json"


@dataclass
class StepResult:
    name: str
    command: List[str]
    returncode: int
    duration_sec: float
    succeeded: bool
    stdout_tail: str
    stderr_tail: str


@dataclass
class CycleResult:
    cycle: int
    started_at: str
    finished_at: str
    duration_sec: float
    succeeded: bool
    steps: List[StepResult]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tail(text: str, max_chars: int = 1800) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _run_command(name: str, command: Sequence[str]) -> StepResult:
    started = time.perf_counter()
    proc = subprocess.run(
        list(command),
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    duration = round(time.perf_counter() - started, 2)
    return StepResult(
        name=name,
        command=list(command),
        returncode=proc.returncode,
        duration_sec=duration,
        succeeded=proc.returncode == 0,
        stdout_tail=_tail(proc.stdout or ""),
        stderr_tail=_tail(proc.stderr or ""),
    )


def _changed_python_files() -> List[str]:
    """Return changed tracked Python files (staged + unstaged)."""
    commands = [
        ["git", "diff", "--name-only", "--", "*.py"],
        ["git", "diff", "--cached", "--name-only", "--", "*.py"],
    ]
    files: set[str] = set()

    for cmd in commands:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            continue
        for line in proc.stdout.splitlines():
            p = line.strip()
            if p:
                files.add(p)

    return sorted(files)


def _build_steps(args: argparse.Namespace) -> List[tuple[str, List[str]]]:
    steps: List[tuple[str, List[str]]] = []

    if args.auto_fix_ruff:
        changed_py = _changed_python_files()
        if changed_py:
            steps.append(
                (
                    "ruff_fix_changed_python",
                    [sys.executable, "-m", "ruff", "check", "--fix", *changed_py],
                )
            )

    steps.append(("pre_commit_check", [sys.executable, "scripts/pre_commit_check.py"]))

    gate_cmd = ["bash", "scripts/integration_contract_gate.sh"]
    if args.strict_endpoints:
        gate_cmd.append("--strict-endpoints")
    steps.append(("integration_contract_gate", gate_cmd))

    if args.full_pytest:
        steps.append(
            (
                "pytest_full_smoke",
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests",
                    "-q",
                    "--maxfail=1",
                    "--tb=short",
                ],
            )
        )

    return steps


def _write_status(history: List[CycleResult]) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": _now_iso(),
        "total_cycles": len(history),
        "successful_cycles": sum(1 for h in history if h.succeeded),
        "failed_cycles": sum(1 for h in history if not h.succeeded),
        "last_cycle": asdict(history[-1]) if history else None,
        "recent_cycles": [asdict(c) for c in history[-20:]],
    }
    STATUS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_cycle(cycle: int, args: argparse.Namespace) -> CycleResult:
    started_at = _now_iso()
    cycle_start = time.perf_counter()

    print("\n" + "=" * 78)
    print(f"[repo_health_automation] cycle={cycle} started_at={started_at}")
    print("=" * 78)

    steps_out: List[StepResult] = []

    for name, cmd in _build_steps(args):
        print(f"\n--> {name}: {' '.join(cmd)}")
        result = _run_command(name, cmd)
        steps_out.append(result)
        icon = "PASS" if result.succeeded else "FAIL"
        print(
            f"[{icon}] {name} rc={result.returncode} duration={result.duration_sec:.2f}s"
        )

        if not result.succeeded and not args.continue_on_fail:
            break

    succeeded = all(step.succeeded for step in steps_out)
    finished_at = _now_iso()
    duration_sec = round(time.perf_counter() - cycle_start, 2)

    cycle_result = CycleResult(
        cycle=cycle,
        started_at=started_at,
        finished_at=finished_at,
        duration_sec=duration_sec,
        succeeded=succeeded,
        steps=steps_out,
    )

    print("\n" + "-" * 78)
    print(
        f"[repo_health_automation] cycle={cycle} "
        f"succeeded={succeeded} duration={duration_sec:.2f}s"
    )
    print("-" * 78)

    if not succeeded:
        failed = next((s for s in steps_out if not s.succeeded), None)
        if failed:
            print(f"First failed step: {failed.name}")
            if failed.stdout_tail.strip():
                print("--- stdout tail ---")
                print(failed.stdout_tail)
            if failed.stderr_tail.strip():
                print("--- stderr tail ---")
                print(failed.stderr_tail)

    return cycle_result


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Automate Aria repo health cycles")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--once", action="store_true", help="Run a single cycle (default)"
    )
    mode.add_argument("--watch", action="store_true", help="Run cycles continuously")

    ap.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between cycles in watch mode (default: 300)",
    )
    ap.add_argument(
        "--strict-endpoints",
        action="store_true",
        help="Use strict endpoint mode for integration contract gate",
    )
    ap.add_argument(
        "--full-pytest",
        action="store_true",
        help="Include full pytest smoke step after contract gate",
    )
    ap.add_argument(
        "--auto-fix-ruff",
        action="store_true",
        help="Run ruff --fix for changed Python files before checks",
    )
    ap.add_argument(
        "--continue-on-fail",
        action="store_true",
        help="Continue remaining steps even after a failed step",
    )

    return ap.parse_args()


def main() -> int:
    args = parse_args()
    history: List[CycleResult] = []

    watch = args.watch
    if not args.watch and not args.once:
        # Default behavior: one-shot cycle
        watch = False

    cycle = 1
    while True:
        result = run_cycle(cycle=cycle, args=args)
        history.append(result)
        _write_status(history)

        if not watch:
            return 0 if result.succeeded else 1

        print(f"Sleeping {args.interval}s before next cycle...")
        time.sleep(max(1, args.interval))
        cycle += 1


if __name__ == "__main__":
    raise SystemExit(main())
