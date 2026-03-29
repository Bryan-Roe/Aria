"""Tests for .github/hooks/scripts/lora_adapter_completeness_guard.py.

Validates:
- warning when adapter_config.json is written without adapter_model.safetensors
- warning when adapter_model.safetensors is written without adapter_config.json
- no warning when non-adapter files are written
- reminder injection when the prompt asks to deploy a LoRA adapter
- PostToolUse verification that companion file exists on disk
- graceful handling of empty stdin and invalid JSON
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK_SCRIPT = (
    Path(__file__).resolve().parent.parent
    / ".github"
    / "hooks"
    / "scripts"
    / "lora_adapter_completeness_guard.py"
)


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
    def test_warns_when_adapter_config_written_without_companion(self):
        """Writing adapter_config.json when adapter_model.safetensors doesn't exist → warn."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {
                "toolName": "write_file",
                "filePath": adapter_path,
                "content": '{"r": 8, "lora_alpha": 16}',
            }
            result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout
        assert "adapter_model.safetensors" in result.stdout

    def test_warns_when_safetensors_written_without_adapter_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            safetensors_path = str(Path(tmpdir) / "adapter_model.safetensors")
            payload = {
                "toolName": "create_file",
                "filePath": safetensors_path,
                "content": "binary_data",
            }
            result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout
        assert "adapter_config.json" in result.stdout

    def test_no_warning_when_companion_already_exists(self):
        """If companion file already exists on disk, no warning should be emitted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Pre-create the companion file
            companion = Path(tmpdir) / "adapter_model.safetensors"
            companion.write_text("placeholder")
            adapter_config_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {
                "toolName": "write_file",
                "filePath": adapter_config_path,
                "content": '{"r": 8}',
            }
            result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_blocks_when_lora_block_env_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {"toolName": "write_file", "filePath": adapter_path, "content": "{}"}
            result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_LORA_BLOCK": "true"})
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr


class TestPostToolUseVerify:
    def test_warns_when_companion_missing_after_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {"toolName": "write_file", "filePath": adapter_path, "content": "{}"}
            result = _run_hook(payload, event="PostToolUse")
        assert result.returncode == 0
        assert "INCOMPLETE" in result.stdout

    def test_no_warning_when_both_files_exist_after_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "adapter_model.safetensors").write_text("weights")
            adapter_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {"toolName": "write_file", "filePath": adapter_path, "content": "{}"}
            result = _run_hook(payload, event="PostToolUse")
        assert result.returncode == 0
        assert result.stdout == ""


class TestNonAdapterFiles:
    def test_ignores_non_adapter_filename(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/training_config.yaml",
            "content": "lr: 0.001",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_ignores_non_write_tool(self):
        payload = {"toolName": "read_file", "filePath": "deployed_models/v1/adapter_config.json"}
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""


class TestUserPromptSubmit:
    def test_injects_reminder_on_deploy_lora(self):
        payload = {"userMessage": "deploy the lora adapter to production"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "LORA COMPLETENESS REMINDER" in result.stdout

    def test_injects_reminder_on_promote_adapter(self):
        payload = {"userMessage": "promote the fine-tuned adapter to the serving endpoint"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "LORA COMPLETENESS REMINDER" in result.stdout

    def test_no_reminder_on_unrelated_prompt(self):
        payload = {"userMessage": "Update the chat provider to support streaming"}
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
        result = _run_hook("definitely not json {{{", event="PreToolUse")
        assert result.returncode == 0

    def test_skip_env_var_disables_hook(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter_path = str(Path(tmpdir) / "adapter_config.json")
            payload = {"toolName": "write_file", "filePath": adapter_path, "content": "{}"}
            result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_LORA_SKIP": "true"})
        assert result.returncode == 0
        assert result.stdout == ""
