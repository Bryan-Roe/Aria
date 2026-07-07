from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from tests.workflow_test_helpers import (
    EXPECTED_HARDEN_RUNNER_ACTION,
    EXPECTED_SETUP_PYTHON_ACTION,
)

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
        python_steps = [step for step in steps if step.get("uses") == EXPECTED_SETUP_PYTHON_ACTION]

        assert len(python_steps) == 1, f"Expected reusable Python setup in {job_name}"
        assert python_steps[0]["with"]["install-requirements"] == "false"
        assert all(not step.get("uses", "").startswith("actions/cache@") for step in steps)


@pytest.mark.unit
@pytest.mark.parametrize("workflow_name", tuple(EXPECTED_SINGLE_JOB_BY_WORKFLOW))
def test_workflows_use_reusable_python_setup_without_installing_repo_requirements(workflow_name: str) -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / workflow_name
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    steps = workflow["jobs"][EXPECTED_SINGLE_JOB_BY_WORKFLOW[workflow_name]]["steps"]
    python_steps = [step for step in steps if step.get("uses") == EXPECTED_SETUP_PYTHON_ACTION]

    assert len(python_steps) == 1, f"Expected reusable Python setup in {workflow_name}"
    assert python_steps[0]["with"]["install-requirements"] == "false"


@pytest.mark.unit
@pytest.mark.parametrize("workflow_name", tuple(EXPECTED_SINGLE_JOB_BY_WORKFLOW))
def test_workflows_harden_runner_and_use_bash_shell(workflow_name: str) -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / workflow_name
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

    steps = workflow["jobs"][EXPECTED_SINGLE_JOB_BY_WORKFLOW[workflow_name]]["steps"]
    assert workflow["defaults"]["run"]["shell"] == "bash"
    assert steps[0]["name"] == "Harden runner"
    assert steps[0]["uses"] == EXPECTED_HARDEN_RUNNER_ACTION
    assert steps[0]["with"]["egress-policy"] == "audit"
    assert steps[0]["with"]["disable-sudo"] is True


@pytest.mark.unit
def test_ruleset_template_is_valid_json_with_required_merge_gate_check() -> None:
    ruleset_path = Path(__file__).resolve().parents[1] / ".github" / "rulesets" / "main-default-automation.ruleset.json"
    ruleset = json.loads(ruleset_path.read_text(encoding="utf-8"))

    assert ruleset["target"] == "branch"
    assert ruleset["enforcement"] == "active"

    required_status_checks_rule = next(rule for rule in ruleset["rules"] if rule["type"] == "required_status_checks")
    contexts = {
        check["context"]
        for check in required_status_checks_rule["parameters"]["required_status_checks"]
        if isinstance(check, dict) and "context" in check
    }

    assert "Merge Gate / All Gates Passed" in contexts
