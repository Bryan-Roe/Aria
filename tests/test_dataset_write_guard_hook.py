"""Tests for .github/hooks/scripts/dataset_write_guard.py.

Validates:
- blocking direct writes into datasets/
- allowing writes outside datasets/
- blocking shell commands that redirect into datasets/
- reminder injection on dataset-oriented prompts
- graceful handling of invalid JSON input
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
    / "dataset_write_guard.py"
)


def _run_hook(payload: str | dict, *, event: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COPILOT_HOOK_EVENT"] = event
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=raw,
        capture_output=True,
        text=True,
        env=env,
    )


class TestPreToolUse:
    def test_blocks_direct_write_to_datasets(self):
        payload = {
            "toolName": "write_file",
            "filePath": "datasets/chat/new.jsonl",
            "content": "{}",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 1
        assert "READ-ONLY" in result.stderr

    def test_allows_write_outside_datasets(self):
        payload = {
            "toolName": "write_file",
            "filePath": "data_out/test/output.json",
            "content": "{}",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_blocks_shell_redirect_into_datasets(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": 'echo "hi" > datasets/chat/train.jsonl',
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 1
        assert "Shell command appears to write into `datasets/`" in result.stderr


class TestUserPromptSubmit:
    def test_dataset_prompt_injects_reminder(self):
        payload = {"userMessage": "append a row to datasets/chat/train.jsonl"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "DATASET IMMUTABILITY REMINDER" in result.stdout


class TestInvalidInput:
    def test_invalid_json_is_ignored(self):
        result = _run_hook("not json", event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""
