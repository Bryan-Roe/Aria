"""Tests for .github/hooks/scripts/enforce_task_complete.py.

Validates:
- task_complete detection (various naming conventions)
- Loop-escape trigger at _MAX_BLOCK_RETRIES
- UserPromptSubmit de-duplication
- Stop block and allow paths
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "enforce_task_complete.py"
)
BLOCK_MARKER = "You have not yet marked the task as complete"


_ALLOW_ENV_KEY = "ARIA_ALLOW_STOP_WITHOUT_TASK_COMPLETE"


def _run_hook(payload: dict, env_overrides: dict[str, str] | None = None) -> dict:
    raw = json.dumps(payload)
    env = os.environ.copy()
    # Strip the ambient bypass flag so blocking tests are not affected by the
    # current shell environment.  Individual tests that want to test the bypass
    # path can re-add it explicitly via env_overrides.
    env.pop(_ALLOW_ENV_KEY, None)
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=raw,
        capture_output=True,
        text=True,
        env=env,
    )
    try:
        return {"exit": result.returncode, **json.loads(result.stdout)}
    except Exception:
        return {
            "exit": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


_FLAG_FILE = Path("/tmp/task_complete.flag")


@pytest.fixture(autouse=True)
def _clean_task_complete_flag():
    """Remove the flag-file bypass artifact before/after every test.

    The flag is a one-shot mechanism for external callers; a stale flag from a
    previous session or a prior test would inadvertently allow the Stop hook to
    pass, causing false positives in the blocking test cases.
    """
    _FLAG_FILE.unlink(missing_ok=True)
    yield
    _FLAG_FILE.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Stop — allow paths
# ---------------------------------------------------------------------------


class TestStopAllow:
    def test_task_complete_in_message_content(self):
        payload = {
            "hookEventName": "Stop",
            "messages": [{"content": "I called task_complete to finish"}],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True

    def test_task_complete_as_tool_key(self):
        payload = {
            "hookEventName": "Stop",
            "toolCalls": [{"name": "task_complete"}],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True

    def test_camel_case_taskComplete(self):
        payload = {
            "hookEventName": "Stop",
            "toolCalls": [{"name": "taskComplete", "args": {}}],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True

    def test_loop_escape_at_max_retries(self):
        """After _MAX_BLOCK_RETRIES (3) repeated blocks, the hook allows stop."""
        payload = {
            "hookEventName": "Stop",
            "messages": [
                {"content": BLOCK_MARKER},
                {"content": BLOCK_MARKER},
                {"content": BLOCK_MARKER},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True
        assert (
            "loop" in r.get("systemMessage", "").lower()
            or "escape" in r.get("systemMessage", "").lower()
        )

    def test_loop_escape_more_than_max(self):
        """5 occurrences of block marker → still escape."""
        payload = {
            "hookEventName": "Stop",
            "messages": [{"content": BLOCK_MARKER}] * 5,
        }
        r = _run_hook(payload)
        assert r.get("continue") is True

    def test_env_override_allows_stop_without_task_complete(self):
        payload = {
            "hookEventName": "Stop",
            "messages": [{"content": "done"}],
        }
        r = _run_hook(
            payload,
            env_overrides={"ARIA_ALLOW_STOP_WITHOUT_TASK_COMPLETE": "true"},
        )
        assert r.get("continue") is True
        assert "explicit env override" in (r.get("systemMessage") or "").lower()


# ---------------------------------------------------------------------------
# Stop — block paths
# ---------------------------------------------------------------------------


class TestStopBlock:
    def test_no_task_complete_blocks(self):
        payload = {
            "hookEventName": "Stop",
            "messages": [{"content": "I am quite done now, wrapping up."}],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        assert r.get("exit") != 0

    def test_fewer_than_max_retries_still_blocks(self):
        """2 occurrences of block marker (below threshold) → still blocked."""
        payload = {
            "hookEventName": "Stop",
            "messages": [
                {"content": BLOCK_MARKER},
                {"content": BLOCK_MARKER},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False

    def test_incomplete_todos_block_stop(self):
        """Stop should be blocked when todo items are still in-progress/not-started."""
        payload = {
            "hookEventName": "Stop",
            "messages": [{"content": "finishing up"}],
            "todoList": [
                {"id": 1, "title": "Trace bug", "status": "completed"},
                {"id": 2, "title": "Run tests", "status": "in-progress"},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        system_msg = (r.get("systemMessage") or "").lower()
        assert "incomplete todo guard" in system_msg

    def test_incomplete_todos_block_preview_shows_titles(self):
        payload = {
            "hookEventName": "Stop",
            "todoList": [
                {"id": 1, "title": "A", "status": "not-started"},
                {"id": 2, "title": "B", "status": "in-progress"},
                {"id": 3, "title": "C", "status": "in-progress"},
                {"id": 4, "title": "D", "status": "in-progress"},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        system_msg = r.get("systemMessage") or ""
        assert "A" in system_msg and "B" in system_msg and "C" in system_msg
        assert "..." in system_msg

    def test_task_complete_still_allows_stop_even_with_incomplete_todos(self):
        """task_complete evidence remains the highest-priority allow path."""
        payload = {
            "hookEventName": "Stop",
            "toolCalls": [{"name": "task_complete"}],
            "todoList": [
                {"id": 1, "title": "leftover", "status": "in-progress"},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True

    def test_markdown_todo_block_with_unfinished_items_blocks_stop(self):
        payload = {
            "hookEventName": "Stop",
            "messages": [
                {
                    "content": "# Todo List\n- [x] finished\n- [-] patch hook\n- [ ] rerun tests"
                }
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        system_msg = r.get("systemMessage") or ""
        assert "patch hook" in system_msg
        assert "rerun tests" in system_msg

    def test_markdown_todo_block_all_completed_does_not_trigger_todo_guard(self):
        payload = {
            "hookEventName": "Stop",
            "messages": [
                {"content": "# Todo List\n- [x] finished\n- [X] also finished"}
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        # Should still block because task_complete is missing, but not due to todo guard.
        assert "incomplete todo guard" not in (r.get("systemMessage") or "").lower()

    def test_scope_warning_added_for_likely_scope_drift_todos(self):
        payload = {
            "hookEventName": "Stop",
            "todoList": [
                {
                    "id": 1,
                    "title": "Refactor chat provider layer",
                    "status": "in-progress",
                },
                {"id": 2, "title": "Run focused tests", "status": "in-progress"},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        system_msg = r.get("systemMessage") or ""
        assert "scope warning" in system_msg.lower()
        assert "Refactor chat provider layer" in system_msg

    def test_no_scope_warning_for_normal_unfinished_todos(self):
        payload = {
            "hookEventName": "Stop",
            "todoList": [
                {"id": 1, "title": "Patch validation bug", "status": "in-progress"},
                {"id": 2, "title": "Run focused tests", "status": "not-started"},
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is False
        assert "scope warning" not in (r.get("systemMessage") or "").lower()


# ---------------------------------------------------------------------------
# UserPromptSubmit
# ---------------------------------------------------------------------------


class TestUserPromptSubmit:
    def test_first_submission_injects_reminder(self):
        payload = {"hookEventName": "UserPromptSubmit", "messages": []}
        r = _run_hook(payload)
        assert r.get("continue") is True
        msg = r.get("systemMessage", "")
        assert "task_complete" in msg.lower() or "ending work" in msg.lower()

    def test_deduplication_skips_reminder_when_already_injected(self):
        """If a prior reminder is already in the payload, don't inject again."""
        payload = {
            "hookEventName": "UserPromptSubmit",
            "messages": [
                {"content": "Reminder: before ending work call task_complete"}
            ],
        }
        r = _run_hook(payload)
        assert r.get("continue") is True
        # systemMessage may be absent or empty when de-duplicated
        msg = r.get("systemMessage", "")
        # Should not contain a fresh reminder (the key should be absent or empty)
        assert "ending work" not in msg or msg == ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_stdin(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        r = json.loads(result.stdout)
        assert r.get("continue") is True

    def test_invalid_json_input(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="{not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        r = json.loads(result.stdout)
        assert r.get("continue") is True

    def test_unknown_event_passes_through(self):
        payload = {"hookEventName": "SomeUnknownEvent", "data": "hello"}
        r = _run_hook(payload)
        assert r.get("continue") is True
