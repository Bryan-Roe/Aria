from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


def _load_workflow() -> dict:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "dependabot-automerge.yml"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def _step(workflow: dict, step_name: str) -> dict:
    step = next((entry for entry in workflow["jobs"]["automerge"]["steps"] if entry.get("name") == step_name), None)
    assert step is not None, f"Expected step '{step_name}' in dependabot-automerge workflow"
    return step


def test_dependabot_automerge_timeout_is_ten_minutes() -> None:
    workflow = _load_workflow()
    assert workflow["jobs"]["automerge"]["timeout-minutes"] == 10


def test_dependabot_automerge_waits_for_status_checks() -> None:
    workflow = _load_workflow()
    step = _step(workflow, "Wait for required status checks")
    script = step["run"]

    assert "statusCheckRollup" in script
    assert "Timed out waiting for required status checks" in script


def test_dependabot_automerge_enable_step_retries_on_transient_failures() -> None:
    workflow = _load_workflow()
    step = _step(workflow, "Enable auto-merge (squash)")
    script = step["run"]

    assert "for attempt in 1 2 3" in script
    assert "retrying in 5 seconds" in script
    assert "Failed to enable auto-merge after 3 attempts" in script


def test_dependabot_automerge_comment_dedup_queries_use_length() -> None:
    workflow = _load_workflow()
    major_comment_script = _step(workflow, "Comment on major updates")["run"]
    skipped_comment_script = _step(workflow, "Comment on skipped non-major updates")["run"]

    assert "| length" in major_comment_script
    assert "| length" in skipped_comment_script
    assert "leng[" not in major_comment_script
    assert "leng[" not in skipped_comment_script
