from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


def _load_merge_gate() -> dict:
    workflow_path = Path(__file__).resolve().parents[1] / ".github/workflows/merge-gate.yml"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def test_merge_gate_defines_setup_guardrails_job() -> None:
    workflow = _load_merge_gate()
    jobs = workflow["jobs"]

    assert "setup-guardrails" in jobs
    assert jobs["setup-guardrails"]["name"] == "Setup Guardrails"


def test_merge_gate_fan_in_requires_setup_guardrails() -> None:
    workflow = _load_merge_gate()
    gates_passed = workflow["jobs"]["gates-passed"]

    assert "setup-guardrails" in gates_passed["needs"]


def test_merge_gate_defines_dependency_submission_job() -> None:
    workflow = _load_merge_gate()
    jobs = workflow["jobs"]

    assert "dependency-submission" in jobs
    assert jobs["dependency-submission"]["name"] == "Dependency Submission"
    wait_step = next(
        (step for step in jobs["dependency-submission"]["steps"] if step["name"] == "Wait for submit-nuget check"),
        None,
    )
    assert wait_step is not None, "dependency-submission must define a 'Wait for submit-nuget check' step"
    assert wait_step["name"] == "Wait for submit-nuget check"
    assert wait_step["env"]["CHECK_NAME"] == "submit-nuget"


def test_merge_gate_fan_in_requires_dependency_submission() -> None:
    workflow = _load_merge_gate()
    gates_passed = workflow["jobs"]["gates-passed"]

    assert "dependency-submission" in gates_passed["needs"]


def test_pr_validation_has_stale_gitlink_check() -> None:
    """PR Validation must include a stale-gitlink guard step.

    Stale gitlinks (mode 160000 in the index without a .gitmodules entry) cause
    ``actions/checkout`` post-job cleanup to fail with:
        fatal: No url found for submodule path '<name>' in .gitmodules
    Catching this in the merge gate prevents it from silently breaking unrelated
    workflows such as Dependency Review.
    """
    workflow = _load_merge_gate()
    steps = workflow["jobs"]["pr-validation"]["steps"]
    step_names = [s["name"] for s in steps]

    assert "Check for stale gitlinks" in step_names, (
        "pr-validation must include a 'Check for stale gitlinks' step to catch "
        "stale mode-160000 gitlinks before they break other CI workflows"
    )


def test_stale_gitlink_check_uses_git_ls_files() -> None:
    """Stale-gitlink step must use ``git ls-files --stage`` to detect mode 160000 entries."""
    workflow = _load_merge_gate()
    steps = workflow["jobs"]["pr-validation"]["steps"]
    check_step = next(s for s in steps if s["name"] == "Check for stale gitlinks")

    assert "git ls-files --stage" in check_step["run"]
    assert "160000" in check_step["run"]
