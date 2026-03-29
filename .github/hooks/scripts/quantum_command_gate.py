#!/usr/bin/env python3
"""Guardrail hook for real-QPU command execution.

Events handled:
  - PreToolUse: warn/block potentially paid real-QPU execution commands lacking confirmation
  - UserPromptSubmit: inject reminder when prompt asks to run/submit on real QPU hardware

Exit codes:
  - 0 allow (or warn/inject)
  - 1 hard block when ARIA_QUANTUM_COMMAND_BLOCK=true and policy violation detected
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterable

EXEC_TOOLS = {
    "run_in_terminal",
    "execution_subagent",
}

PROMPT_QPU_PATTERN = re.compile(
    r"\b(run|submit|execute).*(qpu|real\s+hardware|ionq|quantinuum|rigetti)\b|\b(qpu|real\s+hardware)\b.*\b(run|submit|execute)\b",
    re.IGNORECASE,
)
REAL_QPU_PATTERN = re.compile(
    r"\b(ionq[._-]?qpu|quantinuum[._-]?qpu|rigetti[._-]?qpu|real\s+hardware|backend\s*[:=].*qpu|target\s*[:=].*qpu|\.qpu\b|\b\w+_qpu\b)\b",
    re.IGNORECASE,
)
EXECUTION_INTENT_PATTERN = re.compile(
    r"\b(az\s+quantum\s+job\s+submit|submit|execute|run|python\s+.*quantum|quantum_autorun\.py|qiskit)\b",
    re.IGNORECASE,
)
SAFE_SIM_PATTERN = re.compile(r"\b(simulator|\.sim\.|\.qvm\b|--dry-run\b|\bdry-run\b)\b", re.IGNORECASE)
COST_CONFIRM_PATTERN = re.compile(
    r"\b(azure_confirm_cost\s*[:=]\s*true|confirm_cost\s*[:=]\s*true|--confirm-cost\b|confirm-cost\b)\b",
    re.IGNORECASE,
)

BLOCK_MODE = os.environ.get("ARIA_QUANTUM_COMMAND_BLOCK", "false").lower() == "true"


def _walk(obj: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _tool_name(payload: dict[str, Any]) -> str:
    params = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else {}
    name = (
        payload.get("toolName")
        or payload.get("tool_name")
        or payload.get("name")
        or params.get("toolName")
        or params.get("tool_name")
        or params.get("name")
    )
    return name if isinstance(name, str) else ""


def _text_from_payload(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    interesting_keys = {
        "command",
        "cmd",
        "query",
        "prompt",
        "input",
        "text",
        "usermessage",
        "message",
        "description",
        "goal",
    }
    for key, val in _walk(payload):
        if isinstance(val, str) and key.lower() in interesting_keys:
            chunks.append(val)
    return "\n".join(chunks)


def _is_unsafe_real_qpu_command(text: str) -> bool:
    if not text.strip():
        return False
    if not REAL_QPU_PATTERN.search(text):
        return False
    if not EXECUTION_INTENT_PATTERN.search(text):
        return False
    if SAFE_SIM_PATTERN.search(text):
        return False
    if COST_CONFIRM_PATTERN.search(text):
        return False
    return True


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")
    text = _text_from_payload(payload)

    if event == "UserPromptSubmit":
        if PROMPT_QPU_PATTERN.search(text):
            print(
                "⚠️  Quantum execution reminder: simulate first and include explicit cost confirmation "
                "(e.g., `azure_confirm_cost: true`) before real QPU runs.",
                file=sys.stdout,
            )
        sys.exit(0)

    if event == "PreToolUse":
        tool = _tool_name(payload).lower()
        if tool in EXEC_TOOLS and _is_unsafe_real_qpu_command(text):
            msg = (
                "🛑  BLOCKED: Potential real-QPU execution command detected without explicit cost confirmation. "
                "Use simulator or add explicit cost confirmation in workflow/config first."
            )
            if BLOCK_MODE:
                print(msg, file=sys.stderr)
                sys.exit(1)
            print(msg.replace("🛑  BLOCKED", "⚠️  WARNING"), file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
