"""Tests for .github/hooks/scripts/pr_checklist_guard.py."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "pr_checklist_guard.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("pr_checklist_guard", HOOK_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_main(
    module,
    payload: dict,
    monkeypatch,
    capsys,
    *,
    event: str = "Stop",
    skip_env: str = "",
):
    monkeypatch.setenv("COPILOT_HOOK_EVENT", event)
    monkeypatch.setenv("ARIA_SKIP_PR_CHECKLIST", skip_env)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    try:
        module.main()
    except SystemExit as exc:
        out = capsys.readouterr()
        return exc.code, out.out, out.err
    raise AssertionError("main() did not exit")


# ---------------------------------------------------------------------------
# Stop event with changes present → print checklist
# ---------------------------------------------------------------------------

class TestStopWithChanges:
    def test_prints_checklist_when_staged_changes(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert "PR Checklist" in out
        assert err == ""

    def test_checklist_contains_all_nine_items(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        expected_items = [
            "Dry-run orchestrators",
            "Provider detection intact",
            "Dataset immutability",
            "Status.json compliance",
            "Test suite passes",
            "No hardcoded secrets",
            "Quantum cost gates",
            "LoRA adapter validity",
            "Documentation sync",
        ]
        for item in expected_items:
            assert item in out, f"Missing checklist item: {item}"

    def test_checklist_contains_nine_checkboxes(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        # Each item has "[ ]"
        assert out.count("[ ]") == 9

    def test_checklist_mentions_override(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "ARIA_SKIP_PR_CHECKLIST" in out

    def test_checklist_mentions_dry_run_detail(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "--dry-run" in out

    def test_checklist_mentions_test_runner(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        _, out, _ = _run_main(module, {}, monkeypatch, capsys)
        assert "test_runner.py" in out


# ---------------------------------------------------------------------------
# Stop event with no changes → silent
# ---------------------------------------------------------------------------

class TestStopNoChanges:
    def test_silent_when_no_local_changes(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: False)
        code, out, err = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0
        assert out == ""
        assert err == ""


# ---------------------------------------------------------------------------
# Non-Stop events → silent
# ---------------------------------------------------------------------------

class TestNonStopEvents:
    def test_silent_on_pre_tool_use(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, event="PreToolUse"
        )
        assert code == 0
        assert out == ""

    def test_silent_on_user_prompt_submit(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, event="UserPromptSubmit"
        )
        assert code == 0
        assert out == ""

    def test_silent_on_session_start(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, event="SessionStart"
        )
        assert code == 0
        assert out == ""


# ---------------------------------------------------------------------------
# Environment override
# ---------------------------------------------------------------------------

class TestEnvOverride:
    def test_skip_env_silences_checklist(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, skip_env="1"
        )
        assert code == 0
        assert out == ""

    def test_skip_env_zero_does_not_suppress(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, out, err = _run_main(
            module, {}, monkeypatch, capsys, skip_env="0"
        )
        assert code == 0
        assert "PR Checklist" in out


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_stdin_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "Stop")
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        monkeypatch.setattr(sys, "stdin", io.StringIO(""))
        try:
            module.main()
        except SystemExit as exc:
            out = capsys.readouterr()
            assert exc.code == 0
            assert "PR Checklist" in out.out

    def test_malformed_json_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "Stop")
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        monkeypatch.setattr(sys, "stdin", io.StringIO("{bad json}"))
        try:
            module.main()
        except SystemExit as exc:
            out = capsys.readouterr()
            assert exc.code == 0
            # Still prints checklist even if payload is bad
            assert "PR Checklist" in out.out

    def test_returns_zero_exit_always(self, monkeypatch, capsys):
        """PR checklist guard must never hard-block (exit non-zero)."""
        module = _load_module()
        monkeypatch.setattr(module, "_has_local_changes", lambda: True)
        code, _, _ = _run_main(module, {}, monkeypatch, capsys)
        assert code == 0


# ---------------------------------------------------------------------------
# Helper tests (minimal; _has_local_changes is patched in most tests)
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_format_checklist_contains_all_items(self):
        module = _load_module()
        text = module._format_checklist()
        assert text.count("[ ]") == 9
        assert "Dry-run orchestrators" in text
        assert "ARIA_SKIP_PR_CHECKLIST" in text

    def test_pr_checklist_length(self):
        module = _load_module()
        assert len(module.PR_CHECKLIST) == 9
