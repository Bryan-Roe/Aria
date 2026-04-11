#!/usr/bin/env python3
"""Hook: Remind about --dry-run before GPU/QPU/orchestrator execution.

Policy (from copilot-instructions.md):
    'Always `--dry-run` orchestrators before GPU/QPU execution'
    'Quantum: simulate locally first, then use azure_ionq_simulator,
    only then real QPU'

Events handled:
    PreToolUse       — warn when running an orchestrator without --dry-run
    UserPromptSubmit — inject reminder when prompt asks to run training/jobs

Exit codes:
    0  → always (this hook is reminder-only by default)
    1  → hard block only when ARIA_DRYRUN_BLOCK=true

Env vars:
    ARIA_DRYRUN_BLOCK=true  → flip to hard-block (exit 1)
    ARIA_DRYRUN_SKIP=true   → disable all checks
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterator

# ── Tunable constants ────────────────────────────────────────────────────────

_BLOCK = os.environ.get("ARIA_DRYRUN_BLOCK", "false").lower() == "true"
_SKIP = os.environ.get("ARIA_DRYRUN_SKIP", "false").lower() == "true"

_EXEC_TOOLS = {"run_in_terminal", "execution_subagent", "terminal"}

# Orchestrator / training scripts that require --dry-run validation first
_ORCHESTRATOR_SCRIPTS = (
    "autotrain.py",
    "quantum_autorun.py",
    "evaluation_autorun.py",
    "automated_training_pipeline.py",
    "train_and_promote.py",
    "autonomous_training_orchestrator.py",
    "master_orchestrator.py",
    "repo_automation.py",
    "aria_automation.py",
    "autotrain_fast.py",
)
_ORCHESTRATOR_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _ORCHESTRATOR_SCRIPTS) + r")\b",
    re.IGNORECASE,
)

# Patterns signalling GPU/large-compute training commands
_GPU_TRAINING_RE = re.compile(
    r"\b(python3?\s+.*train|torchrun|deepspeed|accelerate\s+launch|"
    r"transformers-cli\s+train|finetune|lora.train|peft)\b",
    re.IGNORECASE,
)

# What a valid --dry-run flag looks like
# Note: \b doesn't work before -- (both are non-word chars), so use (?<!\S) or a simple search
_DRY_RUN_RE = re.compile(r"--dry-run", re.IGNORECASE)

# Prompt patterns that imply wanting to run training/jobs RIGHT NOW
_PROMPT_RUN_PATTERN = re.compile(
    r"\b(start|run|kick\s*off|execute|launch|trigger|submit)\b.{0,80}"
    r"\b(train|training|autotrain|orchestrator|job|pipeline|fine.?tun|lora)\b"
    r"|\b(train|training|autotrain|orchestrator|fine.?tun|lora)\b.{0,80}"
    r"\b(start|run|kick\s*off|execute|launch|trigger|submit)\b",
    re.IGNORECASE,
)

# Prompt patterns that suggest the user already intends a dry-run or simulation
_PROMPT_SAFE_PATTERN = re.compile(
    r"\b(dry.?run|simulate|simulation|--dry|preview|plan\s+mode|validate)\b",
    re.IGNORECASE,
)

_REMINDER = (
    "\n🧪  DRY-RUN REMINDER: Always validate orchestrators with `--dry-run` before "
    "real GPU/QPU execution to avoid wasted compute and costs.\n"
    "  • Training:  python scripts/autotrain.py --dry-run\n"
    "  • Quantum:   python scripts/quantum_autorun.py --dry-run\n"
    "  • Eval:      python scripts/evaluation_autorun.py --dry-run\n"
    "  • Full repo: python scripts/repo_automation.py --start (includes gate checks)\n"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _walk_strings(obj: Any) -> Iterator[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_strings(item)


def _extract_command(payload: dict[str, Any]) -> str:
    """Pull the shell command text from a run_in_terminal / execution_subagent payload."""
    for key in ("command", "cmd", "query", "input"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    # Sometimes nested under 'parameters'
    params = payload.get("parameters") or payload.get("input")
    if isinstance(params, dict):
        for key in ("command", "cmd", "query"):
            val = params.get(key)
            if isinstance(val, str) and val.strip():
                return val
    return ""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    if _SKIP:
        sys.exit(0)

    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")

    # ── UserPromptSubmit: inject reminder when training is the intent ─────────
    if event == "UserPromptSubmit":
        user_msg = " ".join(_walk_strings(payload))
        if _PROMPT_RUN_PATTERN.search(user_msg) and not _PROMPT_SAFE_PATTERN.search(user_msg):
            print(_REMINDER)
        sys.exit(0)

    # ── PreToolUse: intercept shell execution of orchestrators ────────────────
    if event != "PreToolUse":
        sys.exit(0)

    tool = (payload.get("toolName") or payload.get("name") or "").lower()
    if tool not in _EXEC_TOOLS:
        sys.exit(0)

    command = _extract_command(payload)
    if not command:
        command = " ".join(_walk_strings(payload))

    # Only flag if an orchestrator script (or GPU training) is being run
    is_orchestrator = bool(_ORCHESTRATOR_RE.search(command))
    is_gpu_training = bool(_GPU_TRAINING_RE.search(command))
    if not (is_orchestrator or is_gpu_training):
        sys.exit(0)

    # If --dry-run is already present, we're good
    if _DRY_RUN_RE.search(command):
        sys.exit(0)

    hint = "orchestrator" if is_orchestrator else "training command"
    if _BLOCK:
        print(
            f"🛑  DRY-RUN BLOCKED: Running a {hint} without `--dry-run`. "
            "Validate with --dry-run first. Set ARIA_DRYRUN_SKIP=true to override.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"⚠️  DRY-RUN WARNING: Running a {hint} without first validating with `--dry-run`. "
        "Consider running with --dry-run to check config and dependencies before "
        "consuming GPU/CPU resources."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
