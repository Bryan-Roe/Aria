from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit
WORKFLOW_PATH = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "summary.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _workflow_triggers(workflow: dict) -> dict:
    # PyYAML parses an unquoted `on` key as boolean True per the YAML 1.1
    # rules, so support both parsed forms here.
    return workflow["on"] if "on" in workflow else workflow.get(True, {})


def test_summary_workflow_retains_required_permissions() -> None:
    workflow = _load_workflow()

    assert workflow["permissions"] == {
        "contents": "read",
        "issues": "write",
        "models": "read",
    }


def test_summary_workflow_allows_github_models_endpoint() -> None:
    workflow = _load_workflow()

    harden_runner = workflow["jobs"]["summary"]["steps"][0]
    allowed_endpoints = harden_runner["with"]["allowed-endpoints"].split()

    assert "models.github.ai:443" in allowed_endpoints, (
        "summary.yml blocks runner egress, so it must explicitly allow the "
        "GitHub Models endpoint used by actions/ai-inference."
    )


def test_summary_workflow_comments_without_checkout_repo_context() -> None:
    content = WORKFLOW_PATH.read_text(encoding="utf-8")
    workflow = yaml.safe_load(content)
    steps = workflow["jobs"]["summary"]["steps"]
    gh_comment_lines = [line.strip() for line in content.splitlines() if "gh issue comment" in line]

    assert all(not step.get("uses", "").startswith("actions/checkout") for step in steps)
    assert len(gh_comment_lines) == 2
    assert all('--repo "$GITHUB_REPOSITORY"' in line for line in gh_comment_lines)


def test_summary_workflow_only_runs_for_opened_issues() -> None:
    workflow = _load_workflow()

    assert _workflow_triggers(workflow) == {"issues": {"types": ["opened"]}}
