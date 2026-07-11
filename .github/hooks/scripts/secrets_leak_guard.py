#!/usr/bin/env python3
"""Hook: Detect and warn about hardcoded secrets in file writes.

Convention: Never hardcode secrets — use local.settings.json (dev) or
Azure App Settings (prod). See copilot-instructions.md 'Safety Rules'.

Events handled:
    PreToolUse      — scans new file content for secret patterns before writing
    PostToolUse     — re-scans after write to catch anything that slipped through
    UserPromptSubmit — injects a reminder when the prompt mentions hardcoding

Exit codes:
    0  → allow (no confirmed secret detected, or warn-only mode)
    1  → block (ARIA_SECRETS_BLOCK=true and a high-confidence secret found)

Env vars:
    ARIA_SECRETS_BLOCK=true   → flip to hard-block on high-confidence findings
    ARIA_SECRETS_SKIP=true    → disable all checks (emergency override)
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Iterator
from typing import Any

# ── Tunable constants ────────────────────────────────────────────────────────

_BLOCK = os.environ.get("ARIA_SECRETS_BLOCK", "false").lower() == "true"
_SKIP = os.environ.get("ARIA_SECRETS_SKIP", "false").lower() == "true"

_WRITE_TOOLS = {
    "write_file",
    "create_file",
    "replace_string_in_file",
    "str_replace_editor",
    "multi_replace_string_in_file",
    "insert_content_into_file",
    "overwrite_file",
}

# Files where secret patterns are expected (skip scanning)
_SAFE_PATH_PATTERNS = (
    re.compile(r"local\.settings\.json$", re.IGNORECASE),
    re.compile(r"local\.settings\.json\.example$", re.IGNORECASE),
    re.compile(r"\.env\.example$", re.IGNORECASE),
    re.compile(r"tests/", re.IGNORECASE),
    re.compile(r"\.github/", re.IGNORECASE),
    re.compile(r"SECURITY\.md$", re.IGNORECASE),
    re.compile(r"README\.md$", re.IGNORECASE),
    re.compile(r"CONTRIBUTING\.md$", re.IGNORECASE),
)

# High-confidence secret patterns (value must be non-placeholder, non-env-var-reference)
# Each entry: (name, pattern)
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # OpenAI API key (sk-proj-... or sk-...)
    (
        "OpenAI API key",
        re.compile(
            r"""(?:openai_api_key|api[_-]?key)\s*[=:]\s*['"]?(sk-[A-Za-z0-9\-_]{20,})['"]?""",
            re.IGNORECASE,
        ),
    ),
    # Azure OpenAI key (32-hex or base64-looking long value in an assignment)
    (
        "Azure API key assignment",
        re.compile(
            r"""(?:azure_openai_api_key|azure_api_key|openai_api_key|api[_-]?key)\s*[=:]\s*['"]([0-9a-fA-F]{32,}|[A-Za-z0-9+/]{40,}={0,2})['"]""",
            re.IGNORECASE,
        ),
    ),
    # Bearer token with a non-placeholder value in code/config
    (
        "Bearer token literal",
        re.compile(
            r"""Authorization\s*[=:]\s*['"]?Bearer\s+(?!<|%|{|\$|your|MY_|placeholder|xxx|TOKEN)[A-Za-z0-9\-_\.]{20,}['"]?""",
            re.IGNORECASE,
        ),
    ),
    # SQL / Cosmos connection string with inline password
    (
        "Connection string password",
        re.compile(
            r"""(?:AccountKey|Password|Pwd)\s*=\s*(?!<|%|{|\$|your|placeholder|xxx|PASS)[A-Za-z0-9+/=!@#$%^&*\-_]{8,}""",
            re.IGNORECASE,
        ),
    ),
    # Generic high-entropy secret assignment (api_secret, client_secret, access_token, etc.)
    (
        "Secret/token literal assignment",
        re.compile(
            r"""(?:client_secret|access_token|secret_key|app_secret|auth_token|private_key)\s*[=:]\s*['"](?!<|%|{|\$|your|placeholder|xxx|MY_|REPLACE|test|mock|fake)[A-Za-z0-9+/\-_\.!@#]{16,}['"]""",
            re.IGNORECASE,
        ),
    ),
    # Cosmos / Storage account key (looks like base64, 88+ chars ending in ==)
    (
        "Storage/Cosmos account key",
        re.compile(
            r"""['"][A-Za-z0-9+/]{86,88}={0,2}['"]""",
        ),
    ),
]

# Prompt-level reminder trigger words
_PROMPT_SECRET_PATTERN = re.compile(
    r"\b(hardcode|hard-code|paste.*(key|secret|token|password)|"
    r"copy.*(key|secret|token)|put.*(api.?key|secret|password).*(file|code|config))\b",
    re.IGNORECASE,
)

_REMINDER = (
    "\n🔐  SECRETS REMINDER: Never hardcode API keys, secrets, or connection strings in source files. "
    "Use `local.settings.json` (dev) or Azure App Settings (prod) and reference them via "
    "environment variables (os.environ.get('MY_KEY')). "
    "See copilot-instructions.md → Safety Rules.\n"
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _walk_strings(obj: Any) -> Iterator[str]:
    """Recursively yield all string values from nested dicts/lists."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_strings(item)


def _is_safe_path(path: str) -> bool:
    return any(p.search(path) for p in _SAFE_PATH_PATTERNS)


def _scan_content(content: str) -> list[str]:
    """Return list of matched secret type names found in content."""
    findings: list[str] = []
    for name, pattern in _SECRET_PATTERNS:
        if pattern.search(content):
            findings.append(name)
    return findings


def _find_content_field(payload: dict[str, Any]) -> str:
    """Extract the file content being written from a write-tool payload."""
    for key in ("content", "newString", "new_str", "text", "data"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    # Recurse into replacements list (multi_replace_string_in_file)
    replacements = payload.get("replacements")
    if isinstance(replacements, list):
        parts: list[str] = []
        for r in replacements:
            if isinstance(r, dict):
                ns = r.get("newString") or r.get("new_str") or ""
                if ns:
                    parts.append(ns)
        return "\n".join(parts)
    return ""


def _get_path(payload: dict[str, Any]) -> str:
    return payload.get("filePath") or payload.get("path") or payload.get("file_path") or ""


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

    # ── UserPromptSubmit: inject reminder ────────────────────────────────────
    if event == "UserPromptSubmit":
        user_msg = ""
        for val in _walk_strings(payload):
            user_msg += val + " "
        if _PROMPT_SECRET_PATTERN.search(user_msg):
            print(_REMINDER)
        sys.exit(0)

    # ── PreToolUse / PostToolUse: scan file content ──────────────────────────
    if event not in ("PreToolUse", "PostToolUse"):
        sys.exit(0)

    tool = (payload.get("toolName") or payload.get("name") or "").lower()
    if tool not in _WRITE_TOOLS:
        sys.exit(0)

    file_path = _get_path(payload)
    if file_path and _is_safe_path(file_path):
        sys.exit(0)

    content = _find_content_field(payload)
    if not content:
        sys.exit(0)

    findings = _scan_content(content)
    if not findings:
        sys.exit(0)

    path_hint = f" in `{file_path}`" if file_path else ""
    finding_count_hint = f" ({len(findings)} pattern(s))" if findings else ""
    finding_names_hint = f": {', '.join(dict.fromkeys(findings))}" if findings else ""
    if _BLOCK:
        print(
            f"🛑  SECRETS BLOCKED: Detected possible hardcoded secret{finding_count_hint}{path_hint}"
            f"{finding_names_hint}. Move credentials to environment variables or local.settings.json.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(
            f"⚠️  SECRETS WARNING: Possible hardcoded secret detected{finding_count_hint}{path_hint}"
            f"{finding_names_hint}. Verify this is not a real credential. Use env vars or local.settings.json for secrets."
        )
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        # Fail open: a crash must never block the developer.
        # Set ARIA_SECRETS_SKIP=true for an intentional bypass.
        sys.exit(0)
