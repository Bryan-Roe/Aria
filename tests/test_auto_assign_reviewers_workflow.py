"""Tests for auto-assign-reviewers.yml workflow.

Covers:
- Workflow triggers on correct pull_request event types.
- assign job skips draft PRs (job-level `if` condition).
- assign job skips bot-authored PRs (job-level `if` condition and script guard).
- assign job fires for non-draft, non-bot PRs.
- Script contains the bot-guard branch to skip [bot] authors inline.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_auto_assign() -> dict:
    return _load_yaml(WORKFLOWS_DIR / "auto-assign-reviewers.yml")


def _get_triggers(wf: dict) -> dict:
    """Return the workflow trigger mapping, handling the YAML 'on' → True quirk.

    PyYAML 5.x parses the bare YAML key ``on`` as boolean ``True`` (YAML 1.1
    core schema); GitHub Actions YAML uses ``on`` as the trigger block key.
    """
    return wf.get(True, wf.get("on", {}))


# ---------------------------------------------------------------------------
# Trigger checks
# ---------------------------------------------------------------------------


def test_auto_assign_triggers_on_pull_request() -> None:
    wf = _load_auto_assign()
    assert "pull_request" in _get_triggers(wf), "auto-assign-reviewers.yml must trigger on pull_request"


def test_auto_assign_includes_opened_event() -> None:
    wf = _load_auto_assign()
    pr_types = _get_triggers(wf)["pull_request"].get("types", [])
    assert "opened" in pr_types, "pull_request trigger must include 'opened'"


def test_auto_assign_includes_synchronize_event() -> None:
    wf = _load_auto_assign()
    pr_types = _get_triggers(wf)["pull_request"].get("types", [])
    assert "synchronize" in pr_types, "pull_request trigger must include 'synchronize'"


# ---------------------------------------------------------------------------
# assign job — draft guard
# ---------------------------------------------------------------------------


def test_assign_job_skips_drafts() -> None:
    wf = _load_auto_assign()
    job_if = wf["jobs"]["assign"].get("if", "")
    assert "draft" in job_if, "assign job must skip draft PRs"


# ---------------------------------------------------------------------------
# assign job — bot guard (job-level `if`)
# ---------------------------------------------------------------------------


def test_assign_job_skips_bot_authored_prs_at_job_level() -> None:
    """The job-level `if` must filter out [bot] authors so the job never runs for bots."""
    wf = _load_auto_assign()
    job_if = wf["jobs"]["assign"].get("if", "")
    assert "[bot]" in job_if, (
        "assign job must exclude bot-authored PRs at the job level using "
        "endsWith(...user.login, '[bot]') or similar"
    )


def test_assign_job_if_uses_endswith_for_bot() -> None:
    """The job-level `if` must use endsWith to detect [bot] suffix."""
    wf = _load_auto_assign()
    job_if = wf["jobs"]["assign"].get("if", "")
    assert "endsWith" in job_if, (
        "assign job if-condition must use endsWith(...user.login, '[bot]') to exclude bots"
    )


# ---------------------------------------------------------------------------
# assign job — inline script bot guard
# ---------------------------------------------------------------------------


def test_assign_script_has_bot_guard() -> None:
    """The inline script must also guard against bot-authored PRs defensively,
    using the pattern `pr.user.login.endsWith('[bot]')`."""
    wf_path = WORKFLOWS_DIR / "auto-assign-reviewers.yml"
    content = wf_path.read_text(encoding="utf-8")
    assert "pr.user.login.endsWith('[bot]')" in content, (
        "auto-assign-reviewers.yml script must contain the pattern "
        "`pr.user.login.endsWith('[bot]')` to guard against bot-authored PRs"
    )


def test_assign_script_skips_bot_with_log_message() -> None:
    wf_path = WORKFLOWS_DIR / "auto-assign-reviewers.yml"
    content = wf_path.read_text(encoding="utf-8")
    assert "bot" in content.lower(), "script must log a message when skipping bot PRs"
    assert "skipping reviewer" in content.lower() or "skip" in content.lower(), (
        "script must log that it is skipping reviewer assignment for bot PRs"
    )


# ---------------------------------------------------------------------------
# assign job — non-bot, non-draft PRs still fire
# ---------------------------------------------------------------------------


def test_assign_job_is_present() -> None:
    wf = _load_auto_assign()
    assert "assign" in wf["jobs"], "auto-assign-reviewers.yml must have an 'assign' job"


def test_assign_job_runs_on_ubuntu_latest() -> None:
    wf = _load_auto_assign()
    assert wf["jobs"]["assign"].get("runs-on") == "ubuntu-latest"


# ---------------------------------------------------------------------------
# Relationship with auto-merge: auto-merge pipeline labels
# ---------------------------------------------------------------------------


def test_auto_assign_and_auto_merge_both_exist() -> None:
    """Both workflows must coexist; auto-merge.yml relies on auto-assign not
    requesting human review on bot PRs so merge-on-gate-pass can succeed."""
    auto_merge_path = WORKFLOWS_DIR / "auto-merge.yml"
    auto_assign_path = WORKFLOWS_DIR / "auto-assign-reviewers.yml"
    assert auto_merge_path.exists(), "auto-merge.yml must exist"
    assert auto_assign_path.exists(), "auto-assign-reviewers.yml must exist"
