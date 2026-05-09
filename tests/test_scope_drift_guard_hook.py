"""Tests for .github/hooks/scripts/scope_drift_guard.py.

Validates:
- reminder injected when expansion phrases are present
- reminder injected when high-impact drift words are present
- no reminder for normal prompts
- short prompts ignored regardless of content
- ARIA_ALLOW_SCOPE_DRIFT=1 silences the hook
- non-UserPromptSubmit events are silently ignored
- graceful handling of empty stdin and invalid JSON
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "scope_drift_guard.py"
)

_DRIFT_PHRASES = [
    "also fix the tests while you're at it",
    "and also update the README",
    "one more thing, clean up the imports",
    "oh, and add error handling",
    "can you also refactor the module",
    "let's also improve the performance",
]

_CLEAN_PROMPTS = [
    "Fix the failing unit test in test_foo.py",
    "Why does the function return None?",
    "Run the integration gate",
    "Explain the provider detection chain",
]


def _run_hook(
    payload: dict,
    env_overrides: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Invoke the hook and return (exit_code, stdout, stderr)."""
    raw = json.dumps(payload)
    env = os.environ.copy()
    env.pop("ARIA_ALLOW_SCOPE_DRIFT", None)
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=raw,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Drift triggers — reminder should be printed
# ---------------------------------------------------------------------------


class TestDriftTriggers:
    def test_also_fix_phrase_triggers(self):
        payload = {"prompt": "also fix the CSS while you're in there"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert "scope" in out.lower() or "drift" in out.lower() or "⚠" in out

    def test_while_youre_at_it_triggers(self):
        payload = {"prompt": "while you're at it, please improve performance too"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert "scope" in out.lower() or "⚠" in out

    def test_and_also_phrase_triggers(self):
        payload = {"prompt": "and also update the README with new endpoints"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() != ""

    def test_refactor_word_triggers(self):
        payload = {"prompt": "while fixing the bug please refactor the entire module"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() != ""

    def test_overhaul_word_triggers(self):
        payload = {"prompt": "this is a good chance to overhaul the error handling"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() != ""

    def test_cleanup_word_triggers(self):
        payload = {"message": "let's also do a cleanup of the dead code in shared"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() != ""

    def test_one_more_thing_triggers(self):
        payload = {"prompt": "one more thing, can you add type hints throughout"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() != ""


# ---------------------------------------------------------------------------
# Clean prompts — no reminder should be printed
# ---------------------------------------------------------------------------


class TestCleanPrompts:
    def test_simple_fix_request_no_drift(self):
        payload = {"prompt": "Fix the failing unit test in test_foo.py"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""

    def test_question_no_drift(self):
        payload = {"prompt": "Why does the provider detection fallback to local?"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""

    def test_run_gate_no_drift(self):
        payload = {"prompt": "Run the integration contract gate now"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""

    def test_explain_request_no_drift(self):
        payload = {"prompt": "Explain the provider detection chain step by step"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""


# ---------------------------------------------------------------------------
# Short prompts — below threshold, never trigger
# ---------------------------------------------------------------------------


class TestShortPrompts:
    def test_short_drift_phrase_ignored(self):
        """Fewer than 6 words → no reminder, even if drift word present."""
        payload = {"prompt": "also fix imports"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""

    def test_single_word_ignored(self):
        payload = {"prompt": "refactor"}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""


# ---------------------------------------------------------------------------
# Override env var silences hook
# ---------------------------------------------------------------------------


class TestEnvOverride:
    def test_allow_env_silences_drift_reminder(self):
        payload = {"prompt": "also refactor the whole module while you're at it"}
        code, out, _ = _run_hook(
            payload,
            env_overrides={"ARIA_ALLOW_SCOPE_DRIFT": "1"},
        )
        assert code == 0
        assert out.strip() == ""


# ---------------------------------------------------------------------------
# Non-UserPromptSubmit events are silently ignored
# ---------------------------------------------------------------------------


class TestNonUserPromptEvent:
    def test_stop_event_ignored(self):
        payload = {"hookEventName": "Stop", "prompt": "also refactor everything now"}
        code, out, _ = _run_hook(
            payload,
            env_overrides={"COPILOT_HOOK_EVENT": "Stop"},
        )
        assert code == 0
        assert out.strip() == ""

    def test_pretooluse_event_ignored(self):
        payload = {"hookEventName": "PreToolUse", "prompt": "also fix all the things"}
        code, out, _ = _run_hook(
            payload,
            env_overrides={"COPILOT_HOOK_EVENT": "PreToolUse"},
        )
        assert code == 0
        assert out.strip() == ""


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_stdin_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_invalid_json_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input="not valid JSON }{",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_empty_payload_no_output(self):
        payload: dict = {}
        code, out, _ = _run_hook(payload)
        assert code == 0
        assert out.strip() == ""
