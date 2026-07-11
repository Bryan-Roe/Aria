#!/usr/bin/env python3
"""Hook: emit PR checklist at Stop when git changes are present.

Conversation-derived policy this enforces:
- The PR checklist in copilot-instructions.md has 9 items that must be
  verified before merging.  Agents regularly commit and push without
  explicitly checking the list.
- On Stop: if the working copy has staged/committed changes relative to the
  remote (or any uncommitted changes), print the full checklist so the user
  can verify before opening a PR.

Non-blocking (exit 0) — purely informational.  The intent is to surface the
checklist at the last moment before the session ends, not to hard-block.

Override: ARIA_SKIP_PR_CHECKLIST=1 silences the reminder.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# ---------------------------------------------------------------------------
# PR Checklist (from .github/copilot-instructions.md)
# ---------------------------------------------------------------------------

PR_CHECKLIST = [
    ("Dry-run orchestrators", "If modifying YAML configs or orchestrators, run `--dry-run` first."),
    (
        "Provider detection intact",
        "Changes to shared/chat_providers.py or function_app.py verified via /api/ai/status.",
    ),
    ("Dataset immutability", "No modifications to datasets/ — all outputs written to data_out/."),
    ("Status.json compliance", "Orchestrators write data_out/<name>/status.json."),
    ("Test suite passes", "Run `python scripts/test_runner.py --unit` (or --all)."),
    ("No hardcoded secrets", "All API keys/connection strings use env vars or local.settings.json."),
    ("Quantum cost gates", "QPU jobs include azure_confirm_cost: true in YAML configs."),
    ("LoRA adapter validity", "Training output includes adapter_config.json + adapter_model.safetensors."),
    ("Documentation sync", "READMEs/instruction files updated if core workflows changed."),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event_name() -> str:
    return os.environ.get("COPILOT_HOOK_EVENT", "Stop")


def _allowed_by_env() -> bool:
    return os.environ.get("ARIA_SKIP_PR_CHECKLIST", "").strip() == "1"


def _run_git(*args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip()
    except Exception:
        return -1, ""


def _has_local_changes() -> bool:
    """Return True if there are any staged, unstaged, or unpushed changes."""
    # Check for staged changes
    code, staged = _run_git("diff", "--cached", "--name-only")
    if code == 0 and staged:
        return True

    # Check for unstaged tracked changes
    code, unstaged = _run_git("diff", "--name-only")
    if code == 0 and unstaged:
        return True

    # Check for commits ahead of upstream
    code, ahead = _run_git("rev-list", "--count", "@{u}..HEAD")
    if code == 0 and ahead and ahead.strip() != "0":
        return True

    return False


def _last_commit_message() -> str:
    _, msg = _run_git("log", "-1", "--pretty=%s")
    return msg


def _format_checklist() -> str:
    lines = ["📋  PR Checklist — verify before opening / merging a PR:\n"]
    for i, (title, detail) in enumerate(PR_CHECKLIST, 1):
        lines.append(f"  {i}. [ ] {title}")
        lines.append(f"         {detail}")
    lines.append("")
    lines.append("Silence with: ARIA_SKIP_PR_CHECKLIST=1")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    raw = sys.stdin.read().strip()

    # Parse but tolerate missing/empty payload (Stop payloads may be sparse).
    if raw:
        try:
            json.loads(raw)
        except json.JSONDecodeError:
            pass

    if _allowed_by_env():
        sys.exit(0)

    event = _event_name()
    if event != "Stop":
        sys.exit(0)

    if _has_local_changes():
        print(_format_checklist())

    sys.exit(0)


if __name__ == "__main__":
    main()
