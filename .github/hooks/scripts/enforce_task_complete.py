#!/usr/bin/env python3
"""Hook helper to enforce end-of-session task_complete usage.

Behavior:
- On UserPromptSubmit: injects a concise reminder message.
- On Stop: blocks stop if no evidence of a `task_complete` tool call appears
  in the hook payload.

This script is intentionally conservative and auditable.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _walk(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _contains_task_complete(payload: Any) -> bool:
    for k, v in _walk(payload):
        if isinstance(k, str) and "task_complete" in k:
            return True
        if isinstance(v, str) and "task_complete" in v:
            return True
    return False


def _event_name(payload: dict[str, Any]) -> str:
    for key in ("hookEventName", "event", "hook_event", "type"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    hso = payload.get("hookSpecificOutput")
    if isinstance(hso, dict):
        val = hso.get("hookEventName")
        if isinstance(val, str) and val:
            return val
    return ""


def _emit(obj: dict[str, Any], exit_code: int = 0) -> None:
    print(json.dumps(obj, ensure_ascii=False))
    raise SystemExit(exit_code)


def main() -> None:
    raw = sys.stdin.read().strip()
    payload: dict[str, Any] = {}
    if not raw:
        _emit({"continue": True})
        return

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        _emit({"continue": True, "systemMessage": "Hook warning: could not parse hook payload JSON."})
        return

    event = _event_name(payload)

    if event == "UserPromptSubmit":
        _emit(
            {
                "continue": True,
                "systemMessage": "Reminder: before ending work, send a brief summary and call the task_complete tool.",
            }
        )

    if event == "Stop":
        if _contains_task_complete(payload):
            _emit({"continue": True})
        _emit(
            {
                "continue": False,
                "stopReason": "Session cannot stop yet: task_complete tool call not detected.",
                "systemMessage": "Please provide a brief summary and call task_complete before stopping.",
            },
            exit_code=2,
        )

    _emit({"continue": True})


if __name__ == "__main__":
    main()
