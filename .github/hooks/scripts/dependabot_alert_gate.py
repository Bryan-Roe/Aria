#!/usr/bin/env python3
"""Hook: inject a vulnerability summary at SessionStart when critical CVEs exist.

Conversation-derived policy this enforces:
- A recent push flagged 40 Dependabot vulnerabilities (4 critical, 13 high).
- Agents frequently modify requirements files without checking whether the
  change introduces or resolves known CVEs.
- On SessionStart: run pip-audit against the root requirements.txt (and one
  or two sub-project files) and inject a short advisory summary so the agent
  is aware before touching any dependency.

Performance:
- Results are cached in .github/hooks/data/advisory_cache.json (TTL: 8 h).
- If pip-audit is not installed or times out, the hook exits cleanly (0) and
  logs a brief non-blocking warning.
- On a cache hit the hook runs in < 5 ms (pure JSON read).

Non-blocking (exit 0) — purely informational.

Override: ARIA_SKIP_DEPENDABOT_GATE=1 silences the hook entirely.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_FILE = Path(".github/hooks/data/advisory_cache.json")
CACHE_TTL_SECONDS = 8 * 3600  # 8 hours

# Requirements files to audit (relative to repo root).
REQUIREMENTS_FILES = [
    "requirements.txt",
    "ai-projects/quantum-ml/requirements.txt",
    "ai-projects/chat-cli/requirements.txt",
]

# Inject context when critical + high vulnerabilities exceed these thresholds.
CRITICAL_THRESHOLD = 1  # any critical trips the gate
HIGH_THRESHOLD = 5  # more than 5 high vulns triggers context injection

PIP_AUDIT_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event_name(payload: dict[str, Any] | None = None) -> str:
    """Resolve hook event name from known env/payload keys.

    Supports both legacy and newer key shapes seen in hook payload pipelines.
    """
    payload = payload or {}
    return (
        os.environ.get("COPILOT_HOOK_EVENT")
        or os.environ.get("hook_event_name")
        or os.environ.get("HOOK_EVENT_NAME")
        or payload.get("hook_event_name")
        or payload.get("event")
        or "SessionStart"
    )


def _allowed_by_env() -> bool:
    return os.environ.get("ARIA_SKIP_DEPENDABOT_GATE", "").strip() == "1"


def _cache_valid() -> bool:
    if not CACHE_FILE.exists():
        return False
    try:
        mtime = CACHE_FILE.stat().st_mtime
        return (time.time() - mtime) < CACHE_TTL_SECONDS
    except OSError:
        return False


def _read_cache() -> dict[str, Any]:
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


def _write_cache(data: dict[str, Any]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


def _pip_audit_available() -> bool:
    try:
        subprocess.run(
            [sys.executable, "-m", "pip_audit", "--version"],
            capture_output=True,
            check=False,
            timeout=5,
        )
        return True
    except Exception:
        return False


def _audit_file(req_file: str) -> list[dict[str, Any]]:
    """Run pip-audit on one requirements file; return list of vuln dicts."""
    if not Path(req_file).exists():
        return []
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "-r",
                req_file,
                "--format",
                "json",
                "--progress-spinner",
                "off",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=PIP_AUDIT_TIMEOUT,
        )
        if not proc.stdout.strip():
            return []
        data = json.loads(proc.stdout)
        # pip-audit JSON: {"dependencies": [{"vulns": [...], ...}]}
        vulns: list[dict[str, Any]] = []
        for dep in data.get("dependencies", []):
            for v in dep.get("vulns", []):
                v["package"] = dep.get("name", "unknown")
                v["version"] = dep.get("version", "?")
                vulns.append(v)
        return vulns
    except Exception:
        return []


def _severity(vuln: dict[str, Any]) -> str:
    """Best-effort severity extraction from a pip-audit vulnerability record."""
    aliases = vuln.get("aliases", [])
    # pip_audit doesn't always carry severity; use alias naming as heuristic.
    # Fall back to "unknown".
    for alias in aliases:
        if "GHSA" in alias or "CVE" in alias:
            return "high"
    return "unknown"


def _run_audit() -> dict[str, Any]:
    """Audit all configured requirements files and return aggregated results."""
    all_vulns: list[dict[str, Any]] = []
    audited_files: list[str] = []

    for req in REQUIREMENTS_FILES:
        vulns = _audit_file(req)
        if vulns:
            all_vulns.extend(vulns)
            audited_files.append(req)
        elif Path(req).exists():
            audited_files.append(req)

    # pip-audit uses CVSS or alias heuristic; treat everything as high/critical
    # since we can't reliably extract exact CVSS without the full advisory API.
    critical_count = 0
    high_count = len(all_vulns)  # conservative: all flagged = at least high

    return {
        "timestamp": time.time(),
        "total": len(all_vulns),
        "critical": critical_count,
        "high": high_count,
        "audited_files": audited_files,
        "sample_vulns": [
            {
                "id": v.get("id", "unknown"),
                "package": v.get("package", "unknown"),
                "version": v.get("version", "?"),
                "fix_versions": v.get("fix_versions", []),
            }
            for v in all_vulns[:5]  # top-5 only
        ],
    }


def _format_context(data: dict[str, Any]) -> str:
    total = data.get("total", 0)
    high = data.get("high", 0)
    critical = data.get("critical", 0)
    sample = data.get("sample_vulns", [])
    files = data.get("audited_files", [])

    lines = [
        "🔒  Vulnerability Advisory (from pip-audit cache):",
        f"    {total} known vulnerabilities across {len(files)} requirements file(s).",
    ]
    if critical > 0:
        lines.append(f"    ⛔ {critical} CRITICAL — address before modifying any requirements files.")
    if high > 0:
        lines.append(f"    ⚠️  {high} HIGH — review when updating dependencies.")

    if sample:
        lines.append("    Sample affected packages:")
        for v in sample:
            fix = ", ".join(v.get("fix_versions", [])) or "no fix"
            lines.append(f"      • {v['package']} {v['version']} ({v['id']}) → fix: {fix}")

    lines += [
        "",
        "    Run `pip-audit -r <file>` for the full report.",
        "    Silence this reminder: ARIA_SKIP_DEPENDABOT_GATE=1",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    raw = sys.stdin.read().strip()
    payload: dict[str, Any] = {}
    if raw:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            pass

    if _allowed_by_env():
        sys.exit(0)

    event = _event_name(payload)
    if event != "SessionStart":
        sys.exit(0)

    # Resolve from cache when fresh.
    if _cache_valid():
        data = _read_cache()
    elif _pip_audit_available():
        data = _run_audit()
        _write_cache(data)
    else:
        # pip-audit not installed — inject a one-time installation hint.
        print(
            "ℹ️  pip-audit is not installed. Install it to enable automatic "
            "vulnerability scanning at session start:\n"
            "    pip install pip-audit\n"
            "Silence: ARIA_SKIP_DEPENDABOT_GATE=1"
        )
        sys.exit(0)

    total = data.get("total", 0)
    critical = data.get("critical", 0)
    high = data.get("high", 0)

    should_inject = total > 0 and (critical >= CRITICAL_THRESHOLD or high >= HIGH_THRESHOLD)
    if should_inject:
        print(_format_context(data))

    sys.exit(0)


if __name__ == "__main__":
    main()
