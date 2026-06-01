#!/usr/bin/env python3
"""Hook: Run pip-audit on requirements files before they are saved.

Intercepts PreToolUse writes to any *requirements*.txt or pyproject.toml and
runs pip-audit against the new content. Emits a structured warning if known
vulnerabilities are found, but does NOT block (the agent should still save
the file and address issues in a follow-up step).

Events handled:
  PreToolUse  (write_file, create_file, replace_string_in_file, etc.)
  PostToolUse (runs audit after a replacement, to confirm clean state)

Exit codes:
  0  → always (this hook warns; it never hard-blocks, to avoid infinite loops
       where an agent tries to fix vulns but keeps getting blocked)

Env vars:
  COPILOT_HOOK_SEVERITY_BLOCK=true  → flip to hard-block (exit 1) on HIGH vulns
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from typing import Any

_REQ_PATTERN = re.compile(r"requirements[^/]*\.txt$|pyproject\.toml$", re.IGNORECASE)
_WRITE_TOOLS = {
    "write_file",
    "create_file",
    "replace_string_in_file",
    "str_replace_editor",
    "multi_replace_string_in_file",
    "insert_content_into_file",
    "overwrite_file",
}

_SEVERITY_BLOCK = os.environ.get("COPILOT_HOOK_SEVERITY_BLOCK", "false").lower() == "true"


def _walk(obj: Any):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _get_tool_name(payload: dict) -> str:
    return (payload.get("toolName") or payload.get("tool_name") or payload.get("name") or "").lower()


def _get_file_path(payload: dict) -> str:
    for key in ("filePath", "file_path", "path", "filename", "target"):
        val = payload.get(key) or payload.get("parameters", {}).get(key, "")
        if val:
            return str(val)
    return ""


def _get_new_content(payload: dict) -> str:
    """Try to extract the new file content from various tool payload shapes."""
    # write_file / create_file have a 'content' field
    for key in ("content", "newContent", "new_content", "newString", "new_string"):
        val = payload.get(key) or payload.get("parameters", {}).get(key, "")
        if val:
            return str(val)
    return ""


def _requirements_from_pyproject(pyproject_text: str) -> str:
    """Extract dependency lines from pyproject.toml content.

    Supports PEP 621-style project dependencies and optional dependencies,
    plus build-system requirements when present.
    """
    data = tomllib.loads(pyproject_text)
    lines: list[str] = []

    build_system = data.get("build-system", {})
    for req in build_system.get("requires", []) or []:
        if isinstance(req, str) and req.strip():
            lines.append(req.strip())

    project = data.get("project", {})
    for req in project.get("dependencies", []) or []:
        if isinstance(req, str) and req.strip():
            lines.append(req.strip())

    optional = project.get("optional-dependencies", {}) or {}
    for reqs in optional.values():
        for req in reqs or []:
            if isinstance(req, str) and req.strip():
                lines.append(req.strip())

    # De-duplicate while preserving order.
    deduped = list(dict.fromkeys(lines))
    return "\n".join(deduped) + ("\n" if deduped else "")


def _pip_audit_available() -> bool:
    return shutil.which("pip-audit") is not None


def _run_audit(req_content: str, filename: str) -> tuple[bool, str]:
    """Write content to a temp file and run pip-audit on it.

    Returns (has_vulns: bool, output: str).
    """
    if filename.endswith(".toml"):
        try:
            req_content = _requirements_from_pyproject(req_content)
        except tomllib.TOMLDecodeError as exc:
            return False, f"Unable to parse pyproject.toml for dependency audit: {exc}"
        if not req_content.strip():
            return False, "No dependency declarations found in pyproject.toml"

    suffix = ".txt"
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, prefix="hook_audit_") as tmp:
        tmp.write(req_content)
        tmp_path = tmp.name

    try:
        cmd = ["pip-audit", "-r", tmp_path, "--format", "json"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        # pip-audit exits 1 when vulnerabilities found
        has_vulns = result.returncode != 0
        raw_output = result.stdout or result.stderr

        # Try to parse JSON output for a human-readable summary
        try:
            data = json.loads(raw_output)
            vuln_lines = []
            for dep in data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    vuln_lines.append(
                        f"  • {dep.get('name')}=={dep.get('version')} "
                        f"→ {vuln.get('id')} ({vuln.get('fix', 'no fix available')})"
                    )
            summary = "\n".join(vuln_lines) if vuln_lines else raw_output.strip()
        except (json.JSONDecodeError, AttributeError):
            summary = raw_output.strip()

        return has_vulns, summary
    except subprocess.TimeoutExpired:
        return False, "pip-audit timed out (>60s) — run manually: pip-audit -r <file>"
    except Exception as exc:  # noqa: BLE001
        return False, f"pip-audit failed to run: {exc}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    event = os.environ.get("COPILOT_HOOK_EVENT", "PreToolUse")
    if event not in ("PreToolUse", "PostToolUse"):
        sys.exit(0)

    tool = _get_tool_name(payload)
    if tool not in _WRITE_TOOLS:
        sys.exit(0)

    path = _get_file_path(payload)
    if not path or not _REQ_PATTERN.search(path):
        sys.exit(0)

    # ── Found a requirements file write ─────────────────────────────────────────
    if not _pip_audit_available():
        print(
            f"⚠️  SECURITY REMINDER: Modifying `{path}` — run `pip-audit -r {path}` "
            "to check for vulnerabilities before committing."
        )
        sys.exit(0)

    content = _get_new_content(payload)
    if not content:
        # PostToolUse: file already written, audit from disk
        try:
            with open(path) as f:
                content = f.read()
        except OSError:
            sys.exit(0)

    has_vulns, summary = _run_audit(content, os.path.basename(path))

    if has_vulns:
        msg = (
            f"\n🔒  SECURITY GATE — `{path}` contains packages with known CVEs:\n"
            f"{summary}\n"
            f"    Fix by pinning to a patched version or removing the dependency.\n"
            f"    Re-run: pip-audit -r {path}\n"
        )
        if _SEVERITY_BLOCK:
            print(msg, file=sys.stderr)
            sys.exit(1)
        else:
            print(msg)
    elif summary and (
        summary.startswith("Unable to parse pyproject.toml")
        or summary.startswith("No dependency declarations found in pyproject.toml")
        or summary.startswith("pip-audit timed out")
        or summary.startswith("pip-audit failed to run")
    ):
        print(
            f"⚠️  SECURITY REMINDER: `{path}` could not be fully audited. {summary}\n"
            f"    Review dependencies manually and re-run: pip-audit -r {path}"
        )
    else:
        # Quiet success — don't clutter
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
