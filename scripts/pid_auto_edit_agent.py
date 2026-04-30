#!/usr/bin/env python3
"""
PID-managed autonomous file-editing agent daemon.

This wraps scripts/autonomous_code_agent.py with a queue + daemon lifecycle:
- start: launch background worker, write PID
- stop: stop worker by PID
- status: inspect worker + queue stats
- enqueue: add a task to queue
- run: internal worker loop (do not call manually unless debugging)

Queue format (JSON Lines): data_out/pid_auto_edit_agent/queue.jsonl
Each line:
{
  "task": "fix failing tests in scripts/watch_continuous_automation.py",
  "llm_type": "echo",
  "model": null,
  "dry_run": false,
  "skip_tests": false
}
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "autonomous_code_agent.py"
STATE_DIR = REPO_ROOT / "data_out" / "pid_auto_edit_agent"
PID_FILE = STATE_DIR / "agent.pid"
LOG_FILE = STATE_DIR / "agent.log"
QUEUE_FILE = STATE_DIR / "queue.jsonl"
DONE_FILE = STATE_DIR / "done.jsonl"
FAILED_FILE = STATE_DIR / "failed.jsonl"
STATE_FILE = STATE_DIR / "state.json"


@dataclass
class QueueTask:
    task: str
    llm_type: str = "echo"
    model: Optional[str] = None
    dry_run: bool = False
    skip_tests: bool = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text("", encoding="utf-8")


def _read_pid() -> Optional[int]:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        return None


def _is_running(pid: Optional[int]) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _write_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    out.append(obj)
            except json.JSONDecodeError:
                # Skip malformed line, keep daemon resilient
                continue
    return out


def _run_task(task: QueueTask) -> tuple[int, str]:
    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--task",
        task.task,
        "--llm-type",
        task.llm_type,
    ]
    if task.model:
        cmd.extend(["--model", task.model])
    if task.dry_run:
        cmd.append("--dry-run")
    if task.skip_tests:
        cmd.append("--skip-tests")

    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    output = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, output.strip()


def run_loop(interval: int = 5) -> int:
    _ensure_dirs()

    queue_index = 0
    # Resume from previous state if present
    if STATE_FILE.exists():
        try:
            st = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            queue_index = int(st.get("queue_index", 0))
        except Exception:
            queue_index = 0

    with LOG_FILE.open("a", encoding="utf-8") as log:
        log.write(f"{_now_iso()} daemon started pid={os.getpid()}\n")

    while True:
        tasks_raw = _load_jsonl(QUEUE_FILE)
        pending = max(0, len(tasks_raw) - queue_index)

        _write_state(
            {
                "updated_at": _now_iso(),
                "pid": os.getpid(),
                "queue_index": queue_index,
                "queue_total": len(tasks_raw),
                "pending": pending,
                "status": "idle" if pending == 0 else "working",
            }
        )

        if queue_index >= len(tasks_raw):
            time.sleep(max(1, interval))
            continue

        task_raw = tasks_raw[queue_index]
        queue_index += 1

        _write_state(
            {
                "updated_at": _now_iso(),
                "pid": os.getpid(),
                "queue_index": queue_index,
                "queue_total": len(tasks_raw),
                "pending": max(0, len(tasks_raw) - queue_index),
                "status": "working",
                "current_task": str(task_raw.get("task", ""))[:200],
            }
        )

        # Validate task payload
        task_text = str(task_raw.get("task", "")).strip()
        if not task_text:
            _append_jsonl(
                FAILED_FILE,
                {
                    "timestamp": _now_iso(),
                    "reason": "missing_task_text",
                    "input": task_raw,
                },
            )
            continue

        task = QueueTask(
            task=task_text,
            llm_type=str(task_raw.get("llm_type", "echo") or "echo"),
            model=(
                str(task_raw.get("model"))
                if task_raw.get("model") is not None
                else None
            ),
            dry_run=bool(task_raw.get("dry_run", False)),
            skip_tests=bool(task_raw.get("skip_tests", False)),
        )

        started = _now_iso()
        rc, output = _run_task(task)
        finished = _now_iso()

        # Keep logs compact-ish
        snippet = output[-8000:] if output else ""
        record = {
            "started_at": started,
            "finished_at": finished,
            "return_code": rc,
            "task": task.__dict__,
            "output_tail": snippet,
        }
        if rc == 0:
            _append_jsonl(DONE_FILE, record)
        else:
            _append_jsonl(FAILED_FILE, record)

        _write_state(
            {
                "updated_at": _now_iso(),
                "pid": os.getpid(),
                "queue_index": queue_index,
                "queue_total": len(tasks_raw),
                "pending": max(0, len(tasks_raw) - queue_index),
                "status": "idle" if queue_index >= len(tasks_raw) else "working",
                "last_task_rc": rc,
                "last_task": task.task[:200],
            }
        )

        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(
                f"{finished} task rc={rc} llm={task.llm_type} dry_run={task.dry_run} text={task.task[:120]}\n"
            )


def cmd_start(args: argparse.Namespace) -> int:
    _ensure_dirs()
    pid = _read_pid()
    if _is_running(pid):
        print(f"Already running (pid={pid})")
        return 0

    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "run",
        "--interval",
        str(args.interval),
    ]

    with LOG_FILE.open("a", encoding="utf-8") as log:
        proc = subprocess.Popen(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=log,
            stderr=log,
            start_new_session=True,
        )

    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(f"Started pid-auto-edit agent (pid={proc.pid})")
    return 0


def cmd_stop(_: argparse.Namespace) -> int:
    pid = _read_pid()
    if not _is_running(pid):
        print("Agent is not running")
        if PID_FILE.exists():
            PID_FILE.unlink(missing_ok=True)
        return 0

    assert pid is not None
    os.kill(pid, signal.SIGTERM)
    # brief wait
    for i in range(20):
        if not _is_running(pid):
            break
        time.sleep(0.1)

    if _is_running(pid):
        os.kill(pid, signal.SIGKILL)

    PID_FILE.unlink(missing_ok=True)
    print(f"Stopped pid-auto-edit agent (pid={pid})")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    _ensure_dirs()
    pid = _read_pid()
    running = _is_running(pid)

    queue_items = _load_jsonl(QUEUE_FILE)
    done_items = _load_jsonl(DONE_FILE)
    failed_items = _load_jsonl(FAILED_FILE)

    queue_index = 0
    daemon_state: dict[str, Any] = {}
    if STATE_FILE.exists():
        try:
            daemon_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            queue_index = int(daemon_state.get("queue_index", 0))
        except Exception:
            queue_index = 0

    pending = max(0, len(queue_items) - queue_index)

    print("PID Auto-Edit Agent Status")
    print("=" * 28)
    print(f"running: {running}")
    print(f"pid: {pid if pid is not None else 'n/a'}")
    print(f"queue total: {len(queue_items)}")
    print(f"queue processed index: {queue_index}")
    print(f"queue pending: {pending}")
    print(f"done: {len(done_items)}")
    print(f"failed: {len(failed_items)}")
    if daemon_state:
        print(f"last update: {daemon_state.get('updated_at', 'n/a')}")
        print(f"daemon status: {daemon_state.get('status', 'n/a')}")

    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    _ensure_dirs()
    if not args.task.strip():
        print("Task text cannot be empty")
        return 1

    record = {
        "task": args.task.strip(),
        "llm_type": args.llm_type,
        "model": args.model,
        "dry_run": bool(args.dry_run),
        "skip_tests": bool(args.skip_tests),
        "enqueued_at": _now_iso(),
    }
    _append_jsonl(QUEUE_FILE, record)
    print("Enqueued task")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PID-managed autonomous file-editing agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("start", help="start daemon worker")
    p_start.add_argument(
        "--interval", type=int, default=5, help="idle poll interval seconds"
    )
    p_start.set_defaults(func=cmd_start)

    p_stop = sub.add_parser("stop", help="stop daemon worker")
    p_stop.set_defaults(func=cmd_stop)

    p_status = sub.add_parser("status", help="show daemon + queue status")
    p_status.set_defaults(func=cmd_status)

    p_enqueue = sub.add_parser("enqueue", help="enqueue edit task")
    p_enqueue.add_argument(
        "--task", required=True, help="task description for autonomous_code_agent"
    )
    p_enqueue.add_argument(
        "--llm-type", default="echo", choices=["echo", "ollama", "lmstudio"]
    )
    p_enqueue.add_argument("--model", default=None)
    p_enqueue.add_argument("--dry-run", action="store_true")
    p_enqueue.add_argument("--skip-tests", action="store_true")
    p_enqueue.set_defaults(func=cmd_enqueue)

    p_run = sub.add_parser("run", help="internal daemon loop")
    p_run.add_argument("--interval", type=int, default=5)
    p_run.set_defaults(func=lambda args: run_loop(interval=args.interval))

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
