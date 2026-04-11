"""Tests for .github/hooks/scripts/secrets_leak_guard.py.

Validates:
- warning/blocking when an API key literal is written to a source file
- blocking when ARIA_SECRETS_BLOCK=true
- allowing writes that only reference env vars (no literal secret)
- allowing writes to safe paths (tests/, .github/, local.settings.json)
- reminder injection when the prompt asks to hardcode a secret
- graceful handling of empty stdin and invalid JSON
- connection-string password detection
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
    / "secrets_leak_guard.py"
)

_FAKE_OPENAI_KEY = "sk-abcdefghijklmnopqrstuvwxyz12345678"


def _run_hook(
    payload: str | dict,
    *,
    event: str,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COPILOT_HOOK_EVENT"] = event
    if extra_env:
        env.update(extra_env)
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=raw,
        capture_output=True,
        text=True,
        env=env,
    )


class TestPreToolUseWarn:
    def test_warns_on_openai_api_key_literal(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/prod.py",
            "content": f'openai_api_key = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0, "should warn not block by default"
        assert "WARNING" in result.stdout
        assert "OpenAI API key" in result.stdout

    def test_warns_on_connection_string_password(self):
        payload = {
            "toolName": "create_file",
            "filePath": "shared/db.py",
            "content": "conn = 'Server=prod.db.net;Password=SuperSecret123!;'",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout

    def test_warns_on_postToolUse_event(self):
        payload = {
            "toolName": "write_file",
            "filePath": "app/config.py",
            "content": f'api_key = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PostToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout

    def test_warns_on_multireplace_newstring(self):
        payload = {
            "toolName": "multi_replace_string_in_file",
            "replacements": [
                {"oldString": "placeholder", "newString": f'openai_api_key = "{_FAKE_OPENAI_KEY}"'},
            ],
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout


class TestPreToolUseBlock:
    def test_blocks_when_block_env_set(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/prod.py",
            "content": f'openai_api_key = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_SECRETS_BLOCK": "true"})
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_block_message_on_stderr(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/prod.py",
            "content": f'openai_api_key = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_SECRETS_BLOCK": "true"})
        assert result.returncode == 1
        assert result.stdout == "" or "SECRETS" not in result.stdout  # message on stderr, not stdout


class TestPreToolUseAllow:
    def test_allows_env_var_reference(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/settings.py",
            "content": 'api_key = os.environ.get("OPENAI_API_KEY")',
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_allows_safe_tests_path(self):
        payload = {
            "toolName": "write_file",
            "filePath": "tests/test_integration.py",
            "content": f'FAKE_KEY = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_safe_github_path(self):
        payload = {
            "toolName": "write_file",
            "filePath": ".github/workflows/ci.yml",
            "content": "AZURE_OPENAI_API_KEY: ${{ secrets.AZURE_OPENAI_API_KEY }}",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0

    def test_allows_local_settings_json(self):
        payload = {
            "toolName": "write_file",
            "filePath": "local.settings.json",
            "content": '{"Values": {"AZURE_OPENAI_API_KEY": "real-key-here"}}',
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_allows_non_write_tool(self):
        payload = {
            "toolName": "read_file",
            "filePath": "config/prod.py",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_skip_env_var_disables_hook(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/prod.py",
            "content": f'openai_api_key = "{_FAKE_OPENAI_KEY}"',
        }
        result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_SECRETS_SKIP": "true"})
        assert result.returncode == 0
        assert result.stdout == ""


class TestUserPromptSubmit:
    def test_injects_reminder_on_hardcode_intent(self):
        payload = {"userMessage": "I want to hardcode the API key directly in the config file"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "SECRETS REMINDER" in result.stdout

    def test_injects_reminder_on_paste_key_intent(self):
        payload = {"userMessage": "Can I paste the API key directly into the settings?"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "SECRETS REMINDER" in result.stdout

    def test_no_reminder_on_unrelated_prompt(self):
        payload = {"userMessage": "Refactor the chat provider to support streaming"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert result.stdout == ""


class TestEdgeCases:
    def test_empty_stdin_exits_zero(self):
        result = _run_hook("", event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_invalid_json_exits_zero(self):
        result = _run_hook("not valid json {{", event="PreToolUse")
        assert result.returncode == 0

    def test_missing_content_no_warning(self):
        payload = {"toolName": "write_file", "filePath": "config/prod.py"}
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
