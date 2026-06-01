#!/usr/bin/env python3
"""Hook: Enforce LoRA adapter completeness before deployment.

Policy (from copilot-instructions.md):
    'LoRA adapters need both adapter_config.json + adapter_model.safetensors'

Events handled:
    PreToolUse       — warn when writing one adapter file without the companion
    PostToolUse      — verify companion file exists on disk after the write
    UserPromptSubmit — inject a reminder when prompt mentions deploying LoRA

Exit codes:
    0  → allow (or warn-only mode)
    1  → block (ARIA_LORA_BLOCK=true and a confirmed incomplete adapter detected)

Env vars:
    ARIA_LORA_BLOCK=true  → flip to hard-block on missing companion file
    ARIA_LORA_SKIP=true   → disable all checks
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterator

# ── Tunable constants ────────────────────────────────────────────────────────

_BLOCK = os.environ.get("ARIA_LORA_BLOCK", "false").lower() == "true"
_SKIP = os.environ.get("ARIA_LORA_SKIP", "false").lower() == "true"

_WRITE_TOOLS = {
    "write_file",
    "create_file",
    "replace_string_in_file",
    "str_replace_editor",
    "multi_replace_string_in_file",
    "insert_content_into_file",
    "overwrite_file",
}

# The two required files that make a complete LoRA adapter
_REQUIRED_PAIR = frozenset({"adapter_config.json", "adapter_model.safetensors"})

# Match either required file anywhere in a path
_ADAPTER_FILE_RE = re.compile(
    r"(adapter_config\.json|adapter_model\.safetensors)$",
    re.IGNORECASE,
)

# Prompt patterns that imply LoRA deployment
_PROMPT_DEPLOY_PATTERN = re.compile(
    r"\b(deploy|promote|push|publish|register|release|export)\b.{0,60}"
    r"\b(lora|adapter|fine.?tun|checkpoint)\b"
    r"|\b(lora|adapter|fine.?tun|checkpoint)\b.{0,60}"
    r"\b(deploy|promote|push|publish|register|release|export)\b",
    re.IGNORECASE,
)

_REMINDER = (
    "\n🔗  LORA COMPLETENESS REMINDER: A deployable LoRA adapter requires BOTH files:\n"
    "    • adapter_config.json\n"
    "    • adapter_model.safetensors\n"
    "Deploying without the companion file will cause silent inference failures.\n"
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


def _get_path(payload: dict[str, Any]) -> str:
    return payload.get("filePath") or payload.get("path") or payload.get("file_path") or ""


def _companion_file(adapter_path: str) -> str:
    """Given one adapter file, return the name of the required companion."""
    basename = Path(adapter_path).name.lower()
    if "adapter_config" in basename:
        return "adapter_model.safetensors"
    return "adapter_config.json"


def _companion_exists_on_disk(adapter_path: str) -> bool:
    """Check if the companion file already exists in the same directory."""
    parent = Path(adapter_path).parent
    companion = _companion_file(adapter_path)
    return (parent / companion).is_file()


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

    # ── UserPromptSubmit: inject reminder on deploy intent ───────────────────
    if event == "UserPromptSubmit":
        user_msg = " ".join(_walk_strings(payload))
        if _PROMPT_DEPLOY_PATTERN.search(user_msg):
            print(_REMINDER)
        sys.exit(0)

    # ── PreToolUse: warn early ───────────────────────────────────────────────
    if event == "PreToolUse":
        tool = (payload.get("toolName") or payload.get("name") or "").lower()
        if tool not in _WRITE_TOOLS:
            sys.exit(0)

        file_path = _get_path(payload)
        if not _ADAPTER_FILE_RE.search(file_path):
            sys.exit(0)

        companion = _companion_file(file_path)
        companion_exists = _companion_exists_on_disk(file_path)

        if not companion_exists:
            msg = (
                f"⚠️  LORA ADAPTER WARNING: Writing `{Path(file_path).name}` but "
                f"`{companion}` is not yet present in the same directory. "
                "Ensure both adapter files are present before deploying."
            )
            if _BLOCK:
                print(f"🛑  LORA ADAPTER BLOCKED: {msg}", file=sys.stderr)
                sys.exit(1)
            print(msg)
        sys.exit(0)

    # ── PostToolUse: verify on disk after write ──────────────────────────────
    if event == "PostToolUse":
        tool = (payload.get("toolName") or payload.get("name") or "").lower()
        if tool not in _WRITE_TOOLS:
            sys.exit(0)

        file_path = _get_path(payload)
        if not _ADAPTER_FILE_RE.search(file_path):
            sys.exit(0)

        # After the write: the written file should now exist; check companion
        companion = _companion_file(file_path)
        companion_exists = _companion_exists_on_disk(file_path)

        if not companion_exists:
            print(
                f"⚠️  LORA ADAPTER INCOMPLETE: `{Path(file_path).name}` was written but "
                f"`{companion}` is missing from `{Path(file_path).parent}`. "
                "The adapter cannot be loaded until both files exist."
            )
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
