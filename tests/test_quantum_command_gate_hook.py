"""Tests for .github/hooks/scripts/quantum_command_gate.py."""

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
    / "quantum_command_gate.py"
)


def _run_hook(payload: dict, *, event: str, block_mode: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COPILOT_HOOK_EVENT"] = event
    env["ARIA_QUANTUM_COMMAND_BLOCK"] = "true" if block_mode else "false"
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


def test_user_prompt_injects_reminder_for_real_qpu_intent() -> None:
    payload = {"userMessage": "run this on ionq qpu hardware"}
    result = _run_hook(payload, event="UserPromptSubmit")
    assert result.returncode == 0
    assert "simulate first" in result.stdout.lower()


def test_prettool_real_qpu_command_warns_by_default() -> None:
    payload = {
        "toolName": "run_in_terminal",
        "parameters": {
            "command": "az quantum job submit --target ionq.qpu --shots 100",
        },
    }
    result = _run_hook(payload, event="PreToolUse")
    assert result.returncode == 0
    assert "WARNING" in result.stdout


def test_pretool_real_qpu_command_blocks_in_block_mode() -> None:
    payload = {
        "toolName": "run_in_terminal",
        "parameters": {
            "command": "az quantum job submit --target ionq.qpu --shots 100",
        },
    }
    result = _run_hook(payload, event="PreToolUse", block_mode=True)
    assert result.returncode == 1
    assert "BLOCKED" in result.stderr


def test_pretool_simulator_command_allowed() -> None:
    payload = {
        "toolName": "run_in_terminal",
        "parameters": {
            "command": "az quantum job submit --target ionq.simulator --shots 100",
        },
    }
    result = _run_hook(payload, event="PreToolUse", block_mode=True)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_pretool_real_qpu_with_confirm_flag_allowed() -> None:
    payload = {
        "toolName": "execution_subagent",
        "parameters": {
            "query": "Run az quantum job submit --target ionq_qpu --confirm-cost",
        },
    }
    result = _run_hook(payload, event="PreToolUse", block_mode=True)
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_empty_and_invalid_json_exit_zero() -> None:
    env = os.environ.copy()
    env["COPILOT_HOOK_EVENT"] = "PreToolUse"

    empty = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="",
        capture_output=True,
        text=True,
        env=env,
    )
    assert empty.returncode == 0

    invalid = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
    )
    assert invalid.returncode == 0
