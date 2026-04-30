"""Tests for .github/hooks/scripts/no_verify_bypass_guard.py."""

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
    / "no_verify_bypass_guard.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("no_verify_bypass_guard", HOOK_PATH)
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
    event: str = "PreToolUse",
    allow_env: str = "",
):
    monkeypatch.setenv("COPILOT_HOOK_EVENT", event)
    monkeypatch.setenv("ARIA_ALLOW_NO_VERIFY", allow_env)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    try:
        module.main()
    except SystemExit as exc:
        out = capsys.readouterr()
        return exc.code, out.out, out.err
    raise AssertionError("main() did not exit")


# ---------------------------------------------------------------------------
# PreToolUse — blocking scenarios
# ---------------------------------------------------------------------------


class TestPreToolUseBlocking:
    def test_blocks_commit_no_verify(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit --no-verify -m 'bypass hooks'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2
        assert out == ""
        assert "BLOCKED" in err
        assert "--no-verify" in err

    def test_blocks_push_no_verify(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git push --no-verify origin main",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2
        assert out == ""
        assert "BLOCKED" in err

    def test_blocks_chained_command_with_no_verify(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git add . && git commit --no-verify -m 'fix'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2
        assert "BLOCKED" in err

    def test_blocks_no_verify_with_flags_before(self, monkeypatch, capsys):
        """Flags can appear before --no-verify: `git commit -m 'msg' --no-verify`."""
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit -m 'skip hooks' --no-verify",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2

    def test_blocks_execution_subagent_tool(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "execution_subagent",
            "query": "Run: git commit --no-verify -m 'auto-commit'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2

    def test_blocks_terminal_tool(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "name": "terminal",
            "command": "cd /workspaces/Aria && git commit --no-verify -m 'test'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 2

    def test_block_message_lists_hooks(self, monkeypatch, capsys):
        """Block message should mention which hooks are bypassed."""
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit --no-verify -m 'msg'",
        }
        _, _, err = _run_main(module, payload, monkeypatch, capsys)
        assert "secrets-leak-guard" in err
        assert "dataset-write-guard" in err
        assert "requirements-security-gate" in err

    def test_block_message_mentions_override(self, monkeypatch, capsys):
        """Block message should tell the user about the emergency override."""
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit --no-verify -m 'msg'",
        }
        _, _, err = _run_main(module, payload, monkeypatch, capsys)
        assert "ARIA_ALLOW_NO_VERIFY" in err


# ---------------------------------------------------------------------------
# PreToolUse — allowed scenarios
# ---------------------------------------------------------------------------


class TestPreToolUseAllowed:
    def test_allows_normal_commit(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit -m 'clean commit'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 0

    def test_allows_normal_push(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git push origin main",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 0

    def test_allows_unrelated_command(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 -m pytest tests/ -q",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        assert code == 0

    def test_allows_non_exec_tool_even_with_no_verify(self, monkeypatch, capsys):
        """Non-execution tools (e.g. read_file) should not be blocked."""
        module = _load_module()
        payload = {
            "toolName": "read_file",
            "command": "git commit --no-verify -m 'in description'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys)
        # Non-exec tools should not be blocked
        assert code == 0

    def test_allows_with_env_override(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit --no-verify -m 'emergency'",
        }
        code, out, err = _run_main(module, payload, monkeypatch, capsys, allow_env="1")
        assert code == 0

    def test_empty_payload_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "PreToolUse")
        monkeypatch.setattr(sys, "stdin", io.StringIO(""))
        try:
            module.main()
        except SystemExit as exc:
            assert exc.code == 0

    def test_malformed_json_exits_cleanly(self, monkeypatch, capsys):
        module = _load_module()
        monkeypatch.setenv("COPILOT_HOOK_EVENT", "PreToolUse")
        monkeypatch.setattr(sys, "stdin", io.StringIO("{not json}"))
        try:
            module.main()
        except SystemExit as exc:
            assert exc.code == 0


# ---------------------------------------------------------------------------
# UserPromptSubmit — non-blocking warn
# ---------------------------------------------------------------------------


class TestUserPromptSubmit:
    def test_warns_on_prompt_containing_no_verify(self, monkeypatch, capsys):
        module = _load_module()
        payload = {"userMessage": "run git commit --no-verify -m 'fix ci'"}
        code, out, err = _run_main(
            module, payload, monkeypatch, capsys, event="UserPromptSubmit"
        )
        assert code == 0  # non-blocking
        assert "Warning" in out or "warning" in out.lower()
        assert "--no-verify" in out

    def test_no_warn_on_clean_prompt(self, monkeypatch, capsys):
        module = _load_module()
        payload = {"userMessage": "commit the staged changes with a good message"}
        code, out, err = _run_main(
            module, payload, monkeypatch, capsys, event="UserPromptSubmit"
        )
        assert code == 0
        assert out == ""
        assert err == ""

    def test_warn_mentions_override(self, monkeypatch, capsys):
        module = _load_module()
        payload = {"userMessage": "git commit --no-verify is the only way"}
        code, out, err = _run_main(
            module, payload, monkeypatch, capsys, event="UserPromptSubmit"
        )
        assert code == 0
        assert "ARIA_ALLOW_NO_VERIFY" in out


# ---------------------------------------------------------------------------
# PostToolUse — audit warning
# ---------------------------------------------------------------------------


class TestPostToolUse:
    def test_audit_warning_after_no_verify_command(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit --no-verify -m 'slipped through'",
        }
        code, out, err = _run_main(
            module, payload, monkeypatch, capsys, event="PostToolUse"
        )
        assert code == 0  # non-blocking audit
        assert "Audit" in err or "manually" in err

    def test_no_audit_on_clean_post_use(self, monkeypatch, capsys):
        module = _load_module()
        payload = {
            "toolName": "run_in_terminal",
            "command": "git commit -m 'clean'",
        }
        code, out, err = _run_main(
            module, payload, monkeypatch, capsys, event="PostToolUse"
        )
        assert code == 0
        assert err == ""


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_has_no_verify_detects_commit(self):
        module = _load_module()
        assert module._has_no_verify("git commit --no-verify -m 'x'")

    def test_has_no_verify_detects_push(self):
        module = _load_module()
        assert module._has_no_verify("git push --no-verify origin main")

    def test_has_no_verify_case_insensitive(self):
        module = _load_module()
        assert module._has_no_verify("GIT COMMIT --NO-VERIFY -m 'x'")

    def test_has_no_verify_negative_clean_commit(self):
        module = _load_module()
        assert not module._has_no_verify("git commit -m 'clean'")

    def test_has_no_verify_negative_no_verify_in_message(self):
        """The string --no-verify in a commit message should not false-positive."""
        module = _load_module()
        # This shouldn't match since it's after the message flag value start
        assert not module._has_no_verify("git commit -m 'do not use --skip-verify'")
