"""Tests for dependabot-automerge.yml reliability and correctness guardrails."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "dependabot-automerge.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _get_step(workflow: dict, name: str) -> dict:
    steps = workflow["jobs"]["automerge"]["steps"]
    for step in steps:
        if step.get("name") == name:
            return step
    raise AssertionError(f"Step not found: {name}")


def test_dependabot_automerge_timeout_is_10_minutes() -> None:
    workflow = _load_workflow()
    assert workflow["jobs"]["automerge"]["timeout-minutes"] == 10


def test_read_pr_state_is_gated_by_automerge_decision() -> None:
    workflow = _load_workflow()
    step = _get_step(workflow, "Read PR state")
    assert step.get("if") == "steps.gate.outputs.automerge == 'true'"


def test_wait_for_required_status_checks_step_exists_and_polls_rollup() -> None:
    workflow = _load_workflow()
    step = _get_step(workflow, "Wait for required status checks")
    run = step.get("run", "")
    assert step.get("if") == "steps.gate.outputs.automerge == 'true'"
    assert "statusCheckRollup" in run
    assert "max_wait_seconds=600" in run
    assert 'sleep "${poll_interval_seconds}"' in run


def test_enable_auto_merge_step_has_retry_logic() -> None:
    workflow = _load_workflow()
    step = _get_step(workflow, "Enable auto-merge (squash)")
    run = step.get("run", "")
    assert "for attempt in 1 2 3; do" in run
    assert 'gh pr merge --auto --squash --delete-branch "$PR_URL"' in run
    assert "sleep 5" in run
    assert "Failed to enable auto-merge after 3 attempts." in run


def test_major_update_comment_dedup_query_uses_complete_length_filter() -> None:
    workflow = _load_workflow()
    step = _get_step(workflow, "Comment on major updates")
    run = step.get("run", "")
    # Regression guard: this jq expression was previously truncated mid-token.
    assert 'gh pr view "$PR_URL" --json comments --jq' in run
    assert 'contains("Major version update detected")' in run
    assert "| length')" in run
    assert "leng[..." not in run
