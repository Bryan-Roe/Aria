from __future__ import annotations

from pathlib import Path

import pytest
import yaml


pytestmark = pytest.mark.unit


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_target_workflows_end_with_newline() -> None:
    for rel_path in (
        ".github/workflows/github_workflows_autofix-pr.yml",
        ".github/workflows/github_workflows_validate-workflows.yml",
    ):
        file_path = REPO_ROOT / rel_path
        assert file_path.read_bytes().endswith(b"\n"), f"{rel_path} must end with a newline"


def test_ossar_workflow_is_valid_yaml_with_steps_list() -> None:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/ossar.yml").read_text(encoding="utf-8"))
    assert isinstance(workflow, dict)
    assert "jobs" in workflow and isinstance(workflow["jobs"], dict)
    assert "OSSAR-Scan" in workflow["jobs"] and isinstance(workflow["jobs"]["OSSAR-Scan"], dict)
    steps = workflow["jobs"]["OSSAR-Scan"].get("steps")
    assert isinstance(steps, list) and len(steps) >= 3


def test_summary_workflow_has_no_trailing_whitespace() -> None:
    summary_path = REPO_ROOT / ".github/workflows/summary.yml"
    with summary_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            assert line.rstrip("\n") == line.rstrip(), f"Trailing whitespace in summary.yml at line {line_number}"
