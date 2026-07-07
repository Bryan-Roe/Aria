from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit


def _load_workflow() -> dict:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "markdown-quality.yml"
    return yaml.safe_load(workflow_path.read_text(encoding="utf-8"))


def test_markdown_quality_workflow_selects_changed_markdown_targets() -> None:
    workflow = _load_workflow()
    steps = workflow["jobs"]["markdownlint"]["steps"]

    checkout_step = next(step for step in steps if step["name"] == "Checkout")
    assert checkout_step["with"]["fetch-depth"] == 0

    select_step = next(step for step in steps if step["name"] == "Select markdown targets")
    lint_step = next(step for step in steps if step["name"] == "Lint Markdown files")

    assert "git diff --name-only --diff-filter=ACMR -z" in select_step["run"]
    assert 'git fetch --no-tags origin "$DEFAULT_BRANCH"' in select_step["run"]
    assert "No Markdown files changed for this run" in lint_step["run"]
    assert lint_step["env"]["EVENT_NAME"] == "${{ github.event_name }}"
    assert 'markdownlint-cli2 "${args[@]}" "${markdown_files[@]}"' in lint_step["run"]
    assert "uses" not in lint_step, "Lint step should run only on selected markdown files, not the entire repo."
