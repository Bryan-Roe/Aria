#!/usr/bin/env python3
"""Hook: enforce safer git staging/commit behavior for this repository.

Conversation-derived policy this enforces:
- Block risky blanket staging commands (`git add .`, `git add -A`, `git add --all`)
- Block explicit staging of local-only/sensitive/runtime artifact files
- Block `git commit`/`git push` if protected files are already staged

This helps prevent accidental commits of local settings, runtime logs, and
generated artifacts observed during autonomous sessions.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath
from typing import Any, Iterable

EXEC_TOOLS = {"run_in_terminal", "execution_subagent", "terminal"}

_ADD_ALL_RE = re.compile(
    r"(?:^|[\s;|&])git\s+add\s+(?:\.|-A|--all)(?:$|[\s;|&])",
    re.IGNORECASE,
)
_ADD_EXPLICIT_RE = re.compile(r"\bgit\s+add\s+([^\n;&|]+)", re.IGNORECASE)
_COMMIT_OR_PUSH_RE = re.compile(r"\bgit\s+(?:commit|push)\b", re.IGNORECASE)

# Paths/patterns we do not want committed from automated sessions.
PROTECTED_EXACT = {
    "local.settings.json",
    "automation_status.json",
}
PROTECTED_PREFIXES = (
    "ai-projects/chat-cli/logs/",
    "ai-projects/generated_sites/",
    "ai-projects/llm-maker/generated_sites/",
)
PROTECTED_SUFFIXES = (".jsonl",)


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
    keys = {
        "command",
        "cmd",
        "query",
        "prompt",
        "input",
        "description",
        "goal",
        "usermessage",
        "message",
        "text",
    }
    for key, val in _walk(payload):
        if isinstance(val, str) and key.lower() in keys:
            chunks.append(val)
    return "\n".join(chunks)


def _normalize(path: str) -> str:
    p = path.strip().strip('"').strip("'")
    return str(PurePosixPath(p.replace("\\", "/")))


def _is_protected_path(path: str) -> bool:
    p = _normalize(path)
    if p in PROTECTED_EXACT:
        return True
    if any(p.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return True
    if p.endswith(PROTECTED_SUFFIXES) and p.startswith("ai-projects/chat-cli/logs/"):
        return True
    return False


def _extract_add_targets(cmd_text: str) -> list[str]:
    out: list[str] = []
    for match in _ADD_EXPLICIT_RE.finditer(cmd_text):
        chunk = match.group(1)
        for token in re.split(r"\s+", chunk.strip()):
            if token and not token.startswith("-"):
                out.append(_normalize(token))
    return out


def _staged_files() -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _warn_message() -> str:
    return (
        "⚠️  Git hygiene reminder: avoid blanket staging (`git add .`/`-A`) in this repo. "
        "Stage only intentional files and avoid local runtime artifacts."
    )


def _block(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = _event_name()
    text = _extract_text(payload)

    if event == "UserPromptSubmit":
        if _ADD_ALL_RE.search(text):
            print(_warn_message())
        sys.exit(0)

    if event != "PreToolUse":
        sys.exit(0)

    tool = _tool_name(payload)
    if tool not in EXEC_TOOLS:
        sys.exit(0)

    if _ADD_ALL_RE.search(text):
        _block(
            "🛑  BLOCKED: Detected risky blanket staging command (`git add .` / `git add -A` / `git add --all`).\n"
            "Use explicit file paths with `git add <file1> <file2>` to avoid accidental commits."
        )

    add_targets = _extract_add_targets(text)
    protected_targets = [p for p in add_targets if _is_protected_path(p)]
    if protected_targets:
        _block(
            "🛑  BLOCKED: Attempted to stage protected local/runtime artifacts:\n"
            + "\n".join(f"  - {p}" for p in protected_targets)
            + "\nUnstage/remove these files or add safer explicit paths."
        )

    if _COMMIT_OR_PUSH_RE.search(text):
        staged = _staged_files()
        protected_staged = [p for p in staged if _is_protected_path(p)]
        if protected_staged:
            _block(
                "🛑  BLOCKED: Protected files are currently staged; commit/push halted:\n"
                + "\n".join(f"  - {p}" for p in protected_staged)
                + "\nRun `git restore --staged <path>` (or adjust .gitignore) and retry."
            )

    sys.exit(0)


if __name__ == "__main__":
    main()
