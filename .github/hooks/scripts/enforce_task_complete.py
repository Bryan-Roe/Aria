#!/usr/bin/env python3
"""Hook helper to enforce end-of-session task_complete usage.

Behavior:
- On UserPromptSubmit: injects a single-line reminder (once per session).
- On Stop: blocks stop if no evidence of a task_complete tool call appears
  in the hook payload, unless the agent has already been blocked ≥ 3 times
  in this session (loop-escape to prevent infinite retry loops).

Design goals:
- Conservative and auditable.
- Escape hatch prevents infinite agent retry loops when tool results are
  cleared server-side before the Stop payload is assembled.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

# Number of times the block message can appear before we allow stop (loop escape).
_MAX_BLOCK_RETRIES = 3
_BLOCK_MARKER = "You have not yet marked the task as complete"
_PRIOR_REMINDER_MARKER = "before ending work"
_TODO_LINE_RE = re.compile(r"^\s*[-*]\s*\[(?P<mark>[ xX\-])\]\s*(?P<title>.+?)\s*$")
_SCOPE_DRIFT_KEYWORDS = (
    "refactor",
    "redesign",
    "rewrite",
    "cleanup",
    "polish",
    "research",
    "explore",
    "nice-to-have",
    "follow-up",
)
_ALLOW_STOP_OVERRIDE_ENV = "ARIA_ALLOW_STOP_WITHOUT_TASK_COMPLETE"


def _walk(obj: Any):
    """Recursively yield (key, value) pairs from nested dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _count_occurrences(payload: Any, needle: str) -> int:
    """Count how many string values (or keys) contain needle."""
    count = 0
    for k, v in _walk(payload):
        if isinstance(k, str) and needle in k:
            count += 1
        if isinstance(v, str) and needle in v:
            count += 1
    return count


def _contains_task_complete(payload: Any) -> bool:
    """Return True if the payload contains evidence of a task_complete call.

    Matches:
    - Literal key/value containing 'task_complete'
    - Case-insensitive 'task complete' (with space)
    - Variant 'taskComplete' (camelCase)
    - Cleared-result sentinel alongside a surrounding task_complete reference
    """
    for k, v in _walk(payload):
        if isinstance(k, str):
            lk = k.lower()
            if "task_complete" in lk or "taskcomplete" in lk:
                return True
        if isinstance(v, str):
            lv = v.lower().replace(" ", "_")
            if "task_complete" in lv or "taskcomplete" in lv.replace("_", ""):
                return True
    return False


def _loop_escape_triggered(payload: Any) -> bool:
    """Return True if the stop-block message appears ≥ _MAX_BLOCK_RETRIES times.

    This prevents an infinite loop when the agent has genuinely tried to call
    task_complete multiple times but the tool result keeps getting cleared
    before the Stop payload is assembled.
    """
    count = _count_occurrences(payload, _BLOCK_MARKER)
    return count >= _MAX_BLOCK_RETRIES


def _reminder_already_injected(payload: Any) -> bool:
    """Return True if a prior UserPromptSubmit already injected the reminder."""
    return _count_occurrences(payload, _PRIOR_REMINDER_MARKER) > 0


def _walk_nodes(obj: Any):
    """Yield all nested nodes for structural checks."""
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from _walk_nodes(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_nodes(item)


def _collect_incomplete_todo_titles(payload: Any) -> list[str]:
    """Best-effort extraction of incomplete todo item titles from payload.

    We look for dict nodes that resemble todo entries:
      {"title": "...", "status": "not-started|in-progress|completed"}
    """
    incomplete: list[str] = []
    for node in _walk_nodes(payload):
        if isinstance(node, dict):
            status = node.get("status")
            if isinstance(status, str) and status in {"not-started", "in-progress"}:
                title = node.get("title")
                if isinstance(title, str) and title.strip():
                    incomplete.append(title.strip())
                else:
                    incomplete.append("(untitled todo)")
            continue

        if isinstance(node, str):
            for line in node.splitlines():
                match = _TODO_LINE_RE.match(line)
                if not match:
                    continue
                mark = match.group("mark")
                if mark in {" ", "-"}:
                    title = match.group("title").strip() or "(untitled todo)"
                    incomplete.append(title)
    return incomplete


def _has_incomplete_todos(payload: Any) -> tuple[bool, list[str]]:
    """Return whether payload appears to contain unfinished todo items."""
    items = _collect_incomplete_todo_titles(payload)
    return (len(items) > 0), items


def _find_scope_drift_todos(todo_titles: list[str]) -> list[str]:
    """Return unfinished todo titles that look like likely scope creep."""
    drift: list[str] = []
    for title in todo_titles:
        lowered = title.lower()
        if any(keyword in lowered for keyword in _SCOPE_DRIFT_KEYWORDS):
            drift.append(title)
    return drift


def _event_name(payload: dict[str, Any]) -> str:
    for key in ("hookEventName", "hook_event_name", "event", "hook_event", "type"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    hso = payload.get("hookSpecificOutput")
    if isinstance(hso, dict):
        val = hso.get("hookEventName")
        if isinstance(val, str) and val:
            return val
    return ""


def _is_truthy_env(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
        _emit(
            {
                "continue": True,
                "systemMessage": "Hook warning: could not parse hook payload JSON.",
            }
        )
        return

    event = _event_name(payload)

    # ------------------------------------------------------------------
    # UserPromptSubmit — inject a one-line reminder, but only once.
    # ------------------------------------------------------------------
    if event == "UserPromptSubmit":
        if not _reminder_already_injected(payload):
            _emit(
                {
                    "continue": True,
                    "systemMessage": (
                        "Reminder: when done, provide a brief summary then call the "
                        "task_complete tool. Both are required before ending work. "
                        "Stay on the active user request and keep todo items accurate."
                    ),
                }
            )
        _emit({"continue": True})

    # ------------------------------------------------------------------
    # Stop — block unless task_complete was called OR loop escape fires.
    # ------------------------------------------------------------------
    if event == "Stop":
        if _contains_task_complete(payload):
            _emit({"continue": True})

        has_incomplete_todos, todo_titles = _has_incomplete_todos(payload)
        if has_incomplete_todos:
            if _loop_escape_triggered(payload):
                _emit(
                    {
                        "continue": True,
                        "systemMessage": (
                            "Loop-escape: incomplete todo blocks detected repeatedly; "
                            "allowing stop to prevent infinite loop."
                        ),
                    }
                )
            preview = ", ".join(todo_titles[:3])
            if len(todo_titles) > 3:
                preview += ", ..."
            scope_drift = _find_scope_drift_todos(todo_titles)
            scope_suffix = ""
            if scope_drift:
                scope_preview = ", ".join(scope_drift[:2])
                if len(scope_drift) > 2:
                    scope_preview += ", ..."
                scope_suffix = (
                    " | scope warning: unfinished items may be drifting"
                    f" from the active request -> {scope_preview}"
                )
            _emit(
                {
                    "continue": False,
                    "stopReason": (
                        "Stop blocked: incomplete todo items are still present. "
                        "Finish the active work, update todo statuses, then stop."
                    ),
                    "systemMessage": (
                        f"incomplete todo guard: unresolved items -> {preview}{scope_suffix}"
                    ),
                },
                exit_code=2,
            )

        if _loop_escape_triggered(payload):
            _emit(
                {
                    "continue": True,
                    "systemMessage": (
                        "Loop-escape: task_complete attempts detected but result "
                        "may have been cleared. Allowing stop."
                    ),
                }
            )

        if _is_truthy_env(os.getenv(_ALLOW_STOP_OVERRIDE_ENV)):
            _emit(
                {
                    "continue": True,
                    "systemMessage": (
                        "task_complete guard bypassed by explicit env override "
                        f"({_ALLOW_STOP_OVERRIDE_ENV}=true)."
                    ),
                }
            )

        _emit(
            {
                "continue": False,
                "stopReason": (
                    "Stop blocked: missing task_complete call. If the task is truly "
                    "finished, send a brief summary and then call task_complete. "
                    "If work remains, continue instead of stopping."
                ),
                "systemMessage": (
                    "Finish the work or send a brief summary and call task_complete before stopping."
                ),
            },
            exit_code=2,
        )

    _emit({"continue": True})


if __name__ == "__main__":
    main()
