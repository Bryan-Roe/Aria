#!/usr/bin/env python3
"""Hook: Block any file write that targets the datasets/ directory.

datasets/ is read-only by convention (see copilot-instructions.md Safety Rules).
All training outputs must go to data_out/<orchestrator>/ instead.

Events handled:
  PreToolUse  - intercepts write_file, replace_string_in_file, multi_replace_string_in_file,
                create_file, run_in_terminal (write via shell)
  UserPromptSubmit - injects a reminder if the prompt mentions writing to datasets/

Exit codes:
  0  → allow (no dataset/ write detected)
  1  → block (dataset/ write detected)
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

_DATASETS_PATTERN = re.compile(r"\bdatasets/", re.IGNORECASE)
_REMINDER = (
    "\n⚠️  DATASET IMMUTABILITY REMINDER: `datasets/` is READ-ONLY. "
    "Write all outputs to `data_out/<orchestrator>/` instead.\n"
)

# Tool names that write files
_WRITE_TOOLS = {
    "write_file",
    "create_file",
    "replace_string_in_file",
    "str_replace_editor",
    "multi_replace_string_in_file",
    "insert_content_into_file",
    "overwrite_file",
}
# Shell-execution tools — check the command string for datasets/ writes
_SHELL_TOOLS = {"run_in_terminal", "execute_code", "terminal"}

_SHELL_WRITE_RE = re.compile(
    r'(?:>""|>>|tee|cp\s|mv\s|touch\s|cat\s.*?>|write|echo.*?>)\s*["\']?datasets/',
    re.IGNORECASE,
)


def _walk(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _get_event() -> str:
    return os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")


def _get_tool_name(payload: dict) -> str:
    return (payload.get("toolName") or payload.get("tool_name") or payload.get("name") or "").lower()


def _get_file_path(payload: dict) -> str:
    """Extract the target file path from any write-tool payload."""
    for key in ("filePath", "file_path", "path", "filename", "target"):
        val = payload.get(key) or payload.get("parameters", {}).get(key, "")
        if val:
            return str(val)
    # Walk entire payload for any string that looks like a path
    for _, v in _walk(payload):
        if isinstance(v, str) and "/" in v:
            return v
    return ""


def _get_command(payload: dict) -> str:
    for key in ("command", "cmd", "code", "input"):
        val = payload.get(key) or payload.get("parameters", {}).get(key, "")
        if val:
            return str(val)
    return ""


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # If payload isn't JSON (e.g. plain text from UserPromptSubmit), check for datasets/ refs
        if _DATASETS_PATTERN.search(raw) and _SHELL_WRITE_RE.search(raw):
            print(_REMINDER)
        sys.exit(0)

    event = _get_event()

    # ── UserPromptSubmit ────────────────────────────────────────────────────────
    if event == "UserPromptSubmit":
        text = payload.get("userMessage", "") or payload.get("message", "") or raw
        if _DATASETS_PATTERN.search(text):
            # Inject reminder without blocking
            print(_REMINDER)
        sys.exit(0)

    # ── PreToolUse ──────────────────────────────────────────────────────────────
    if event == "PreToolUse":
        tool = _get_tool_name(payload)

        if tool in _WRITE_TOOLS:
            path = _get_file_path(payload)
            if path and _DATASETS_PATTERN.search(path):
                print(
                    f"🛑  BLOCKED: Writing to `{path}` is not allowed.\n"
                    f"    `datasets/` is READ-ONLY (copilot-instructions.md Safety Rules).\n"
                    f"    Write outputs to `data_out/<orchestrator>/` instead.",
                    file=sys.stderr,
                )
                sys.exit(1)

        elif tool in _SHELL_TOOLS:
            cmd = _get_command(payload)
            if _SHELL_WRITE_RE.search(cmd):
                print(
                    "🛑  BLOCKED: Shell command appears to write into `datasets/`.\n"
                    "    `datasets/` is READ-ONLY (copilot-instructions.md Safety Rules).\n"
                    "    Redirect all outputs to `data_out/<orchestrator>/` instead.",
                    file=sys.stderr,
                )
                sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
