"""Tests for .github/hooks/scripts/quantum_cost_gate.py.

Validates:
- reminder injection on QPU-oriented prompts
- no false positives from simulator configs or option comments
- warning/block behavior for real-QPU config without cost confirmation
- support for both azure_confirm_cost and confirm_cost keys
- apply_patch handling using added lines only
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
    / "quantum_cost_gate.py"
)


def _run_hook(
    payload: dict, *, event: str, block_mode: bool = False
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["COPILOT_HOOK_EVENT"] = event
    env["ARIA_QUANTUM_COST_BLOCK"] = "true" if block_mode else "false"
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


class TestUserPromptSubmit:
    def test_qpu_prompt_injects_reminder(self):
        payload = {"userMessage": "run this on ionq qpu hardware"}
        result = _run_hook(payload, event="UserPromptSubmit")
        assert result.returncode == 0
        assert "azure_confirm_cost: true" in result.stdout


class TestPreToolUse:
    def test_simulator_config_is_allowed(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum/quantum_autorun.yaml",
            "content": """
- name: azure_quantinuum_simulator
  mode: azure_hardware
  azure_backend: quantinuum.sim.h2-1sc
  enabled: true
""",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_comment_only_qpu_reference_does_not_trigger(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum_llm_config.yaml",
            "content": """
azure:
  target_backend: ionq.simulator  # Options: ionq.simulator, ionq.qpu, quantinuum.sim.h1-1e
  confirm_cost: false  # Must be true for paid QPU backends
""",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_qpu_without_cost_confirmation_warns_by_default(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum/quantum_autorun.yaml",
            "content": """
- name: azure_ionq_qpu_test
  mode: azure_hardware
  azure_backend: ionq.qpu
  azure_confirm_cost: false
  enabled: false
""",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert "WARNING" in result.stdout
        assert "azure_confirm_cost: true" in result.stdout

    def test_qpu_without_cost_confirmation_blocks_in_block_mode(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum/quantum_autorun.yaml",
            "content": """
- name: azure_ionq_qpu_test
  mode: azure_hardware
  azure_backend: ionq.qpu
  azure_confirm_cost: false
  enabled: false
""",
        }
        result = _run_hook(payload, event="PreToolUse", block_mode=True)
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_underscore_qpu_backend_without_cost_confirmation_blocks(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum/job.yaml",
            "content": """
backend: ionq_qpu
shots: 100
""",
        }
        result = _run_hook(payload, event="PreToolUse", block_mode=True)
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_qpu_with_azure_confirm_cost_true_is_allowed(self):
        payload = {
            "toolName": "write_file",
            "filePath": "tests/test_azure_jobs.yaml",
            "content": """
- name: test_azure_qpu_confirmed
  mode: azure_hardware
  azure_backend: ionq.qpu
  azure_confirm_cost: true
  enabled: true
""",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_qpu_with_confirm_cost_true_is_allowed(self):
        payload = {
            "toolName": "write_file",
            "filePath": "config/quantum_llm_config.yaml",
            "content": """
azure:
  target_backend: ionq.qpu
  confirm_cost: true
""",
        }
        result = _run_hook(payload, event="PreToolUse")
        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_apply_patch_uses_added_lines_only(self):
        patch = """*** Begin Patch
*** Update File: /workspaces/Aria/config/quantum/quantum_autorun.yaml
@@
-    azure_backend: ionq.simulator
-    azure_confirm_cost: true
+    azure_backend: ionq.qpu
+    azure_confirm_cost: false
*** End Patch
"""
        payload = {"toolName": "apply_patch", "input": patch}
        result = _run_hook(payload, event="PreToolUse", block_mode=True)
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr

    def test_posttool_reads_saved_yaml_from_disk_and_blocks(self, tmp_path):
        config = tmp_path / "config" / "quantum" / "job.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("backend: ionq_qpu\nshots: 100\n", encoding="utf-8")
        payload = {
            "toolName": "write_file",
            "filePath": str(config),
        }
        result = _run_hook(payload, event="PostToolUse", block_mode=True)
        assert result.returncode == 1
        assert "BLOCKED" in result.stderr
