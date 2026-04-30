#!/usr/bin/env python3
"""Hook: block git commit/push with --no-verify flag.

Conversation-derived policy this enforces:
- `git commit --no-verify` and `git push --no-verify` bypass ALL git hooks,
  defeating every safety gate in this repo:
    • secrets-leak-guard       • dataset-write-guard
    • requirements-security-gate • lora-adapter-completeness-guard
    • git-commit-hygiene
- On PreToolUse: BLOCK the command from running (exit 2).
- On UserPromptSubmit: WARN via printed message (non-blocking).
- Emergency override: set ARIA_ALLOW_NO_VERIFY=1 in the environment when
  absolutely required (e.g., a git merge that already validated all checks).

This hook is intentionally simple and fast (no subprocesses, no network).
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXEC_TOOLS = {"run_in_terminal", "execution_subagent", "terminal"}

# Match  git commit --no-verify  or  git push --no-verify  anywhere in a
# command string, including when flags appear in various orders.
_NO_VERIFY_PATTERN = re.compile(
    r"\bgit\s+(?:commit|push)\b[^\n]*?--no-verify",
    re.IGNORECASE,
)

# Alternate: flags before the subcommand alias (uncommon but valid in scripts)
_NO_VERIFY_ALT_PATTERN = re.compile(
    r"\bgit\s+--no-verify\s+(?:commit|push)\b",
    re.IGNORECASE,
)

_COMMAND_KEYS = {
    "command",
    "cmd",
    "query",
    "prompt",
    "input",
    "description",
    "goal",
    "userMessage",
    "usermessage",
    "message",
    "text",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _walk(obj: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _event_name() -> str:
    return os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")


def _tool_name(payload: dict[str, Any]) -> str:
    return (
        payload.get("toolName")
        or payload.get("tool_name")
        or payload.get("name")
        or payload.get("parameters", {}).get("toolName")
        or payload.get("parameters", {}).get("tool_name")
        or payload.get("parameters", {}).get("name")
        or ""
    ).lower()


def _extract_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key, val in _walk(payload):
        if isinstance(val, str) and key.lower() in _COMMAND_KEYS:
            chunks.append(val)
    return "\n".join(chunks)


def _has_no_verify(text: str) -> bool:
    return bool(_NO_VERIFY_PATTERN.search(text) or _NO_VERIFY_ALT_PATTERN.search(text))


def _allowed_by_env() -> bool:
    return os.environ.get("ARIA_ALLOW_NO_VERIFY", "").strip() == "1"


def _block_message() -> str:
    return (
        "🛑  BLOCKED: `git commit --no-verify` / `git push --no-verify` is "
        "prohibited in this repository.\n\n"
        "Using --no-verify bypasses ALL pre-commit hooks, including:\n"
        "  • secrets-leak-guard\n"
        "  • dataset-write-guard\n"
        "  • requirements-security-gate\n"
        "  • lora-adapter-completeness-guard\n"
        "  • git-commit-hygiene\n\n"
        "Fix the underlying issue instead of skipping hooks.\n"
        "Emergency override (use sparingly): ARIA_ALLOW_NO_VERIFY=1 git commit …"
    )


def _warn_message() -> str:
    return (
        "⚠️  Warning: `--no-verify` in your request bypasses ALL commit/push "
        "safety hooks. Remove it and address the underlying validation failure instead.\n"
        "Emergency override: ARIA_ALLOW_NO_VERIFY=1 git commit …"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    if _allowed_by_env():
        sys.exit(0)

    event = _event_name()
    text = _extract_text(payload)

    if not _has_no_verify(text):
        sys.exit(0)

    if event == "UserPromptSubmit":
        # Non-blocking warn: print to stdout so it surfaces as a system message.
        print(_warn_message())
        sys.exit(0)

    if event == "PreToolUse":
        tool = _tool_name(payload)
        if tool in EXEC_TOOLS:
            print(_block_message(), file=sys.stderr)
            sys.exit(2)

    # For PostToolUse or other events — non-blocking audit warning.
    if event == "PostToolUse" and _has_no_verify(text):
        print(
            "⚠️  Audit: a `--no-verify` git command was executed; "
            "verify that all safety gates were satisfied manually.",
            file=sys.stderr,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
