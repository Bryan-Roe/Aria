"""Tests for .github/hooks/scripts/dry_run_reminder.py.

Validates:
- warning when an orchestrator script is run without --dry-run
- no warning when --dry-run is present in the command
- blocking when ARIA_DRYRUN_BLOCK=true
- reminder injection when the prompt asks to run training/jobs
- no reminder when prompt already implies dry-run or simulation
- no action for non-exec tools
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
    / "dry_run_reminder.py"
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
    def test_warns_autotrain_without_dry_run(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/autotrain.py --epochs 50",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "DRY-RUN WARNING" in result.stdout

    def test_warns_quantum_autorun_without_dry_run(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python scripts/quantum_autorun.py --backend azure_ionq_simulator",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "DRY-RUN WARNING" in result.stdout

    def test_warns_evaluation_autorun_without_dry_run(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/evaluation_autorun.py",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "DRY-RUN WARNING" in result.stdout

    def test_warns_train_and_promote_without_dry_run(self):
        payload = {
            "toolName": "execution_subagent",
            "query": "python3 scripts/train_and_promote.py --quick --auto-promote",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "DRY-RUN WARNING" in result.stdout


class TestPreToolUseAllow:
    def test_no_warning_with_dry_run_flag(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/autotrain.py --dry-run --epochs 50",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_no_warning_for_quantum_autorun_with_dry_run(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python scripts/quantum_autorun.py --dry-run",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_warning_for_non_orchestrator_command(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/fast_validate.py",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_warning_for_write_tool(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/autotrain.yaml",
            "content": "jobs:\n  - name: test",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_skip_env_var_disables_hook(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/autotrain.py --epochs 100",
        }
        result = _run_hook(payload, event="PreToolUse", extra_env={"ARIA_DRYRUN_SKIP": "true"})
        assert result.returncode == 0
        assert result.stdout == ""


class TestPreToolUseBlock:
    def test_blocks_orchestrator_when_block_env_set(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/autonomous_training_orchestrator.py",
        }
        result = _run_hook(
            payload, event="PreToolUse", extra_env={"ARIA_DRYRUN_BLOCK": "true"}
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_block_message_on_stderr(self):
        payload = {
            "toolName": "run_in_terminal",
            "command": "python3 scripts/autotrain.py",
        }
        result = _run_hook(
            payload, event="PreToolUse", extra_env={"ARIA_DRYRUN_BLOCK": "true"}
        )
        assert result.returncode == 1
        # Message should be on stderr, not stdout
        assert result.stdout == ""


class TestUserPromptSubmit:
    def test_injects_reminder_on_run_training_intent(self):
        payload = {"userMessage": "start the training pipeline now please"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "DRY-RUN REMINDER" in result.stdout

    def test_injects_reminder_on_kick_off_orchestrator(self):
        payload = {"userMessage": "kick off autotrain with the latest dataset"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "DRY-RUN REMINDER" in result.stdout

    def test_no_reminder_when_dry_run_already_mentioned(self):
        payload = {"userMessage": "run autotrain.py with --dry-run first to validate"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_reminder_when_simulation_mentioned(self):
        payload = {"userMessage": "simulate the training run before executing"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_no_reminder_on_unrelated_prompt(self):
        payload = {"userMessage": "Update the dashboard to show GPU memory usage"}
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
        result = _run_hook("not valid JSON at all", event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""

    def test_unknown_event_exits_zero(self):
        payload = {"toolName": "run_in_terminal", "command": "python3 scripts/autotrain.py"}
        result = _run_hook(payload, event="SomeUnknownEvent")
        assert result.returncode == 0
