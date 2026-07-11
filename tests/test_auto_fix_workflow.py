from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


def _load_workflow() -> dict:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "auto-fix.yml"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def test_auto_fix_ruff_autofix_is_non_blocking() -> None:
    workflow = _load_workflow()
    step = next(step for step in workflow["jobs"]["autofix"]["steps"] if step["name"] == "Run Ruff autofixes")
    assert "--fix --exit-zero" in step["run"]


def test_auto_fix_includes_pyyaml_in_extra_packages() -> None:
    """pyyaml must be in extra-packages so shared/config_validator.py can be imported."""
    workflow = _load_workflow()
    step = next(
        step for step in workflow["jobs"]["autofix"]["steps"] if step["name"] == "Set up Python and autofix tooling"
    )
    assert "pyyaml" in step["with"]["extra-packages"], "pyyaml is required to prevent INTERNALERROR in pytest"


def test_auto_fix_detect_step_does_not_create_detect_output_txt() -> None:
    """detect_output.txt must not be created as it would be unintentionally committed."""
    workflow = _load_workflow()
    step = next(step for step in workflow["jobs"]["autofix"]["steps"] if step["name"] == "Detect safe Python targets")
    assert "detect_output.txt" not in step["run"], (
        "detect_output.txt must not be written to disk; write to $GITHUB_OUTPUT directly to avoid committing it"
    )
    assert "GITHUB_OUTPUT" in step["run"], "Must write outputs directly to $GITHUB_OUTPUT"


def test_auto_fix_has_rebase_on_latest_main_step() -> None:
    """Rebase step must exist to prevent push rejection due to workflow file race conditions."""
    workflow = _load_workflow()
    step_names = [step["name"] for step in workflow["jobs"]["autofix"]["steps"]]
    assert "Rebase autofix changes on latest origin/main" in step_names, (
        "Rebase step is required to prevent push rejection when codeql.yml or other "
        "workflow files are updated on main while this job is running"
    )


def test_auto_fix_quality_gates_are_best_effort() -> None:
    workflow = _load_workflow()
    steps = {step["name"]: step for step in workflow["jobs"]["autofix"]["steps"]}

    assert steps["Run Black formatting"]["continue-on-error"] is True
    assert steps["Verify Ruff"]["continue-on-error"] is True
    assert steps["Verify Black"]["continue-on-error"] is True
    assert steps["Run targeted pytest"]["continue-on-error"] is True


def test_auto_fix_has_cleanup_step() -> None:
    """A cleanup step must strip workflow-file changes and remove stray files
    before the PR is created.  Without this, peter-evans/create-pull-request
    can include accidental workflow-file edits in the pushed branch, which
    GitHub rejects when GITHUB_TOKEN lacks workflows permission."""
    workflow = _load_workflow()
    steps = workflow["jobs"]["autofix"]["steps"]
    step_names = [step["name"] for step in steps]
    assert "Revert workflow file changes and remove stray files" in step_names, (
        "Cleanup step is required to prevent push rejection when workflow files "
        "are accidentally included in the autofix branch"
    )

    cleanup_step = next(step for step in steps if step["name"] == "Revert workflow file changes and remove stray files")
    assert "detect_output.txt" in cleanup_step["run"], "Must remove stray detect_output.txt"
    assert ".github/workflows" in cleanup_step["run"], "Must revert workflow file changes"
    assert "git restore" in cleanup_step["run"], "Must use git restore to revert workflow changes"

    # Cleanup step must appear BEFORE 'Detect changes' so that reverted files
    # are not counted as outstanding changes.
    cleanup_index = step_names.index("Revert workflow file changes and remove stray files")
    detect_index = step_names.index("Detect changes")
    assert cleanup_index < detect_index, "Cleanup step must precede 'Detect changes'"
