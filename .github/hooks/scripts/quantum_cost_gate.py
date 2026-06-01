#!/usr/bin/env python3
"""Guardrail hook for real-QPU cost confirmation in quantum YAML edits.

Events handled:
    - PreToolUse: warn/block when writing real-QPU config without explicit cost confirmation
    - UserPromptSubmit: inject reminder when prompt suggests real QPU execution

Exit codes:
    - 0 allow (or warn/inject)
    - 1 hard block when ARIA_QUANTUM_COST_BLOCK=true and policy violation detected
"""

import json
import os
import re
import sys
from typing import Any, Iterable

WRITE_TOOLS = {
    "write_file",
    "create_file",
    "replace_string_in_file",
    "multi_replace_string_in_file",
    "apply_patch",
}

PROMPT_QPU_PATTERN = re.compile(
    r"\b(qpu|real\s+hardware|ionq|quantinuum|rigetti|ionq_qpu|ionq-qpu)\b",
    re.IGNORECASE,
)
YAML_PATH_PATTERN = re.compile(r"\.ya?ml$", re.IGNORECASE)
QUANTUM_SCOPE_PATH_PATTERN = re.compile(r"(quantum|qpu|azure_jobs).*\.ya?ml$", re.IGNORECASE)
QUANTUM_SCOPE_TEXT_PATTERN = re.compile(
    r"\b(azure_backend|target_backend|backend|azure_quantum_target|azure_confirm_cost|confirm_cost|mode\s*:\s*azure_hardware)\b",
    re.IGNORECASE,
)
QPU_ASSIGNMENT_PATTERN = re.compile(
    r"^\s*(azure_backend|target_backend|backend|azure_quantum_target)\s*:\s*[\"']?(?P<value>[^\s\"'#]+)",
    re.IGNORECASE,
)
COST_CONFIRM_PATTERN = re.compile(r"^\s*(azure_confirm_cost|confirm_cost)\s*:\s*true\b", re.IGNORECASE)
COST_DENY_PATTERN = re.compile(r"^\s*(azure_confirm_cost|confirm_cost)\s*:\s*false\b", re.IGNORECASE)

BLOCK_MODE = os.environ.get("ARIA_QUANTUM_COST_BLOCK", "false").lower() == "true"


def _walk(obj: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _text_from_payload(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key, val in _walk(payload):
        if isinstance(val, str) and key.lower() in {
            "content",
            "input",
            "patch",
            "command",
            "cmd",
            "text",
            "usermessage",
            "message",
            "newcontent",
            "newstring",
        }:
            chunks.append(val)
    return "\n".join(chunks)


def _added_text_from_patch(patch_text: str) -> str:
    added_lines: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("+++"):
            continue
        if line.startswith("+"):
            added_lines.append(line[1:])
    return "\n".join(added_lines)


def _paths_from_patch_text(patch_text: str) -> list[str]:
    paths: list[str] = []
    for line in patch_text.splitlines():
        if line.startswith("*** Update File: ") or line.startswith("*** Add File: "):
            path = line.split(": ", 1)[1].strip()
            if path:
                paths.append(path)
    return paths


def _params_dict(payload: dict[str, Any]) -> dict[str, Any]:
    params = payload.get("parameters")
    return params if isinstance(params, dict) else {}


def _path_from_payload(payload: dict[str, Any]) -> str:
    params = _params_dict(payload)
    candidates = [
        payload.get("filePath"),
        payload.get("path"),
        payload.get("target"),
        params.get("filePath"),
        params.get("path"),
        params.get("target"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate

    for key, val in _walk(payload):
        if key.lower() in {"filepath", "path", "target"} and isinstance(val, str):
            if val.strip():
                return val
    return ""


def _tool_name(payload: dict[str, Any]) -> str:
    params = _params_dict(payload)
    name = (
        payload.get("toolName")
        or payload.get("tool_name")
        or payload.get("name")
        or params.get("toolName")
        or params.get("tool_name")
        or params.get("name")
    )
    return name if isinstance(name, str) else ""


def _strip_inline_comment(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def _value_is_real_qpu(value: str) -> bool:
    normalized = value.strip().strip("\"'").lower().replace("-", "_")
    if "simulator" in normalized:
        return False
    if ".qpu" in normalized or normalized == "qpu" or normalized.startswith("qpu."):
        return True
    return normalized.endswith("_qpu") or "_qpu_" in normalized


def _mentions_real_qpu(text: str) -> bool:
    for raw_line in text.splitlines():
        line = _strip_inline_comment(raw_line)
        match = QPU_ASSIGNMENT_PATTERN.search(line)
        if not match:
            continue
        if _value_is_real_qpu(match.group("value")):
            return True
    return False


def _has_cost_confirmation(text: str) -> bool:
    return any(COST_CONFIRM_PATTERN.search(_strip_inline_comment(line)) for line in text.splitlines())


def _sets_cost_denied(text: str) -> bool:
    return any(COST_DENY_PATTERN.search(_strip_inline_comment(line)) for line in text.splitlines())


def _in_quantum_scope(path: str, text: str) -> bool:
    return bool(
        (path and YAML_PATH_PATTERN.search(path) and QUANTUM_SCOPE_PATH_PATTERN.search(path))
        or QUANTUM_SCOPE_TEXT_PATTERN.search(text)
    )


def _read_posttool_file(path: str) -> str:
    if not path or not path.lower().endswith((".yaml", ".yml")):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = os.environ.get("COPILOT_HOOK_EVENT") or payload.get("hookEventName") or "PreToolUse"
    tool = _tool_name(payload).lower()
    payload_text = _text_from_payload(payload)
    patch_text = payload_text if tool == "apply_patch" else ""
    analysis_text = _added_text_from_patch(patch_text) if patch_text else payload_text

    if event == "UserPromptSubmit":
        if PROMPT_QPU_PATTERN.search(payload_text):
            print(
                "⚠️  Quantum cost reminder: real QPU jobs must include `azure_confirm_cost: true` "
                "(or `confirm_cost: true`) and should run simulator-first before hardware.",
                file=sys.stdout,
            )
        sys.exit(0)

    if event in {"PreToolUse", "PostToolUse"}:
        if tool not in WRITE_TOOLS:
            sys.exit(0)

        path = _path_from_payload(payload)
        if not path and patch_text:
            patch_paths = _paths_from_patch_text(patch_text)
            path = patch_paths[0] if patch_paths else ""

        if event == "PostToolUse":
            disk_text = _read_posttool_file(path)
            if disk_text:
                analysis_text = f"{analysis_text}\n{disk_text}"

        if not _in_quantum_scope(path, analysis_text):
            sys.exit(0)

        mentions_qpu = _mentions_real_qpu(analysis_text)
        has_cost_confirm = _has_cost_confirmation(analysis_text)
        sets_cost_denied = _sets_cost_denied(analysis_text)

        if mentions_qpu and (not has_cost_confirm or sets_cost_denied):
            msg = (
                "🛑  BLOCKED: Real-QPU config appears to be written without explicit cost confirmation. "
                "Set `azure_confirm_cost: true` (or `confirm_cost: true`) and keep simulator-first progression "
                "per repo safety rules."
            )
            if BLOCK_MODE:
                print(msg, file=sys.stderr)
                sys.exit(1)
            print(msg.replace("🛑  BLOCKED", "⚠️  WARNING"), file=sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
