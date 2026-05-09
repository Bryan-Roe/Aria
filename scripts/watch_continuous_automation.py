#!/usr/bin/env python3
"""
Watch status for the perpetual continuous automation loop.

Monitors:
- loop worker process (loop.pid)
- watchdog process (watchdog.pid)
- loop log activity (cycle starts/ends, recent test summary)

Usage:
    python scripts/watch_continuous_automation.py
    python scripts/watch_continuous_automation.py --watch --interval 5
    python scripts/watch_continuous_automation.py --lines 25
"""

from __future__ import annotations

import argparse
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTINUOUS_DIR = REPO_ROOT / "data_out" / "continuous_automation"
LOOP_PID_FILE = CONTINUOUS_DIR / "loop.pid"
WATCHDOG_PID_FILE = CONTINUOUS_DIR / "watchdog.pid"
LOOP_LOG_FILE = CONTINUOUS_DIR / "loop.log"
WATCHDOG_LOG_FILE = CONTINUOUS_DIR / "watchdog.log"

CYCLE_START_RE = re.compile(r"^===\s+(?P<ts>[^=]+?)\s+cycle start\s+===")
CYCLE_END_RE = re.compile(r"^===\s+(?P<ts>[^=]+?)\s+cycle end\s+===")
PYTEST_PASS_RE = re.compile(
    r"^(?P<count>\d+)\s+passed(?:,\s+(?P<skipped>\d+)\s+skipped)?"
)
GATE_PASS_RE = re.compile(r"\[integration_contract_gate\]\s+passed")
GATE_FAIL_RE = re.compile(r"\[integration_contract_gate\]\s+failed")


@dataclass
class ProcessStatus:
    name: str
    pid: Optional[int]
    running: bool
    detail: str


def _read_pid(path: Path) -> Optional[int]:
    if not path.exists():
        return None
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _pid_running(pid: Optional[int]) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _process_status(name: str, pid_file: Path) -> ProcessStatus:
    pid = _read_pid(pid_file)
    if pid is None:
        return ProcessStatus(
            name=name,
            pid=None,
            running=False,
            detail=f"missing pid file ({pid_file.name})",
        )
    running = _pid_running(pid)
    if running:
        return ProcessStatus(name=name, pid=pid, running=True, detail="running")
    return ProcessStatus(
        name=name, pid=pid, running=False, detail="stopped (stale pid)"
    )


def _safe_read_lines(path: Path, max_lines: int = 4000) -> list[str]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    if len(lines) > max_lines:
        return lines[-max_lines:]
    return lines


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(ts.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _format_age(when: Optional[datetime]) -> str:
    if when is None:
        return "n/a"
    now = datetime.now(timezone.utc)
    delta = now - when
    secs = int(delta.total_seconds())
    if secs < 0:
        return "0s"
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m {secs % 60}s"
    if secs < 86400:
        h = secs // 3600
        m = (secs % 3600) // 60
        return f"{h}h {m}m"
    d = secs // 86400
    h = (secs % 86400) // 3600
    return f"{d}d {h}h"


def _tail(lines: Iterable[str], n: int) -> list[str]:
    as_list = list(lines)
    if n <= 0:
        return []
    return as_list[-n:]


def _analyze_loop_log(lines: list[str]) -> dict[str, object]:
    raw_start_lines = 0
    raw_end_lines = 0
    start_times: set[str] = set()
    end_times: set[str] = set()
    last_start: Optional[datetime] = None
    last_end: Optional[datetime] = None
    last_pytest_summary: Optional[str] = None
    last_gate_status = "unknown"

    for line in lines:
        start_match = CYCLE_START_RE.match(line)
        if start_match:
            raw_start_lines += 1
            ts = start_match.group("ts").strip()
            start_times.add(ts)
            parsed = _parse_iso(ts)
            if parsed is not None and (last_start is None or parsed >= last_start):
                last_start = parsed
            continue

        end_match = CYCLE_END_RE.match(line)
        if end_match:
            raw_end_lines += 1
            ts = end_match.group("ts").strip()
            end_times.add(ts)
            parsed = _parse_iso(ts)
            if parsed is not None and (last_end is None or parsed >= last_end):
                last_end = parsed
            continue

        pytest_match = PYTEST_PASS_RE.match(line.strip())
        if pytest_match:
            skipped = pytest_match.group("skipped")
            if skipped:
                last_pytest_summary = (
                    f"{pytest_match.group('count')} passed, {skipped} skipped"
                )
            else:
                last_pytest_summary = f"{pytest_match.group('count')} passed"

        if GATE_PASS_RE.search(line):
            last_gate_status = "passed"
        elif GATE_FAIL_RE.search(line):
            last_gate_status = "failed"

    cycle_starts = len(start_times)
    cycle_ends = len(end_times)
    # Prefer temporal ordering over raw counts in case log windows are truncated
    # or duplicate workers emit mirrored entries.
    in_progress = False
    if last_start is not None and last_end is not None:
        in_progress = last_start > last_end
    elif last_start is not None and last_end is None:
        in_progress = True

    return {
        "cycle_starts": cycle_starts,
        "cycle_ends": cycle_ends,
        "duplicate_start_markers": max(0, raw_start_lines - cycle_starts),
        "duplicate_end_markers": max(0, raw_end_lines - cycle_ends),
        "in_progress": in_progress,
        "last_start": last_start,
        "last_end": last_end,
        "last_pytest_summary": last_pytest_summary,
        "last_gate_status": last_gate_status,
    }


def _print_snapshot(lines_to_show: int) -> None:
    loop_status = _process_status("loop", LOOP_PID_FILE)
    watchdog_status = _process_status("watchdog", WATCHDOG_PID_FILE)

    log_lines = _safe_read_lines(LOOP_LOG_FILE)
    analysis = _analyze_loop_log(log_lines)
    last_lines = _tail(log_lines, lines_to_show)

    last_start_dt = analysis.get("last_start")
    if not isinstance(last_start_dt, datetime):
        last_start_dt = None

    last_end_dt = analysis.get("last_end")
    if not isinstance(last_end_dt, datetime):
        last_end_dt = None

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("\n" + "=" * 78)
    print(f" Continuous Automation Watcher @ {now}")
    print("=" * 78)

    def fmt_proc(p: ProcessStatus) -> str:
        icon = "🟢" if p.running else "🔴"
        pid = p.pid if p.pid is not None else "n/a"
        return f"{icon} {p.name:<8} pid={pid:<8} {p.detail}"

    print(fmt_proc(loop_status))
    print(fmt_proc(watchdog_status))
    dup_starts = analysis.get("duplicate_start_markers", 0)
    dup_ends = analysis.get("duplicate_end_markers", 0)
    if (
        isinstance(dup_starts, int)
        and isinstance(dup_ends, int)
        and (dup_starts > 0 or dup_ends > 0)
    ):
        print(f"⚠️  duplicate log markers detected: start+{dup_starts}, end+{dup_ends}")
    else:
        print("🟢 duplicate log markers: none")

    print("-" * 78)
    print(
        "cycles: "
        f"starts={analysis['cycle_starts']} "
        f"ends={analysis['cycle_ends']} "
        f"in_progress={'yes' if analysis['in_progress'] else 'no'}"
    )
    print(
        "last cycle start: "
        f"{last_start_dt or 'n/a'} "
        f"(age {_format_age(last_start_dt)})"
    )
    print(
        "last cycle end:   "
        f"{last_end_dt or 'n/a'} "
        f"(age {_format_age(last_end_dt)})"
    )
    print(f"last gate status:  {analysis['last_gate_status']}")
    print(f"last pytest:       {analysis['last_pytest_summary'] or 'n/a'}")

    if LOOP_LOG_FILE.exists():
        mtime = datetime.fromtimestamp(LOOP_LOG_FILE.stat().st_mtime, tz=timezone.utc)
        print(f"loop.log updated:  {mtime.isoformat()} (age {_format_age(mtime)})")
    else:
        print("loop.log updated:  n/a")

    print("-" * 78)
    print(f"last {len(last_lines)} loop.log lines:")
    if not last_lines:
        print("(no log lines yet)")
    else:
        for line in last_lines:
            print(line)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch continuous automation loop activity"
    )
    parser.add_argument(
        "--watch", action="store_true", help="continuously refresh view"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="seconds between refreshes in --watch mode",
    )
    parser.add_argument(
        "--lines",
        type=int,
        default=20,
        help="how many tail lines to show from loop.log",
    )
    args = parser.parse_args()

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                _print_snapshot(lines_to_show=args.lines)
                print(f"\nRefreshing every {args.interval}s (Ctrl+C to stop)")
                time.sleep(max(args.interval, 1))
        except KeyboardInterrupt:
            print("\nwatch stopped")
        return

    _print_snapshot(lines_to_show=args.lines)


if __name__ == "__main__":
    main()
