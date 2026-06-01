from __future__ import annotations

from pathlib import Path

import pytest
import yaml

EXPECTED_PYTHON_SETUP_ACTION = "./.github/actions/setup-python-env"
EXPECTED_SINGLE_JOB_BY_WORKFLOW = {
    "ruleset-json-validation.yml": "validate-rulesets",
    "default-github-automation.yml": "baseline",
}


@pytest.mark.unit
def test_workflow_validation_uses_reusable_python_setup_without_duplicate_pip_cache() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "workflow-validation.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    for job_name in ("validate-workflows", "test-workflows"):
        steps = workflow["jobs"][job_name]["steps"]
        python_steps = [step for step in steps if step.get("uses") == EXPECTED_PYTHON_SETUP_ACTION]

        assert len(python_steps) == 1, f"Expected reusable Python setup in {job_name}"
        assert python_steps[0]["with"]["install-requirements"] == "false"
        assert all(not step.get("uses", "").startswith("actions/cache@") for step in steps)


@pytest.mark.unit
@pytest.mark.parametrize(
    "workflow_name",
    ("ruleset-json-validation.yml", "default-github-automation.yml"),
)
def test_workflows_use_reusable_python_setup_without_installing_repo_requirements(workflow_name: str) -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / workflow_name
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    steps = workflow["jobs"][EXPECTED_SINGLE_JOB_BY_WORKFLOW[workflow_name]]["steps"]
    python_steps = [step for step in steps if step.get("uses") == EXPECTED_PYTHON_SETUP_ACTION]

    assert len(python_steps) == 1, f"Expected reusable Python setup in {workflow_name}"
    assert python_steps[0]["with"]["install-requirements"] == "false"
