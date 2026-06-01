from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_copilot_setup_workflow_concurrency_is_ref_scoped() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "copilot-setup-steps.yml"
    assert workflow_path.exists(), "Expected copilot setup workflow to exist"

    content = workflow_path.read_text(encoding="utf-8")

    assert "concurrency:" in content
    assert "group: copilot-setup-check-${{ github.event.pull_request.number || github.ref }}" in content


@pytest.mark.unit
def test_copilot_setup_workflow_has_selective_lint_logic() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "copilot-setup-steps.yml"
    assert workflow_path.exists(), "Expected copilot setup workflow to exist"

    content = workflow_path.read_text(encoding="utf-8")

    assert "fetch-depth: 0" in content
    assert "id: targets" in content
    assert "NULL_SHA=" in content
    assert "git diff --name-only" in content
    assert "--diff-filter=ACMR -z" in content
    assert "load_changed_targets() {" in content
    assert 'load_changed_targets "${PR_BASE_SHA}" "${PR_HEAD_SHA}" || load_default_targets' in content
    assert 'load_changed_targets "${PUSH_BEFORE_SHA}" "${HEAD_SHA}" || load_default_targets' in content
    assert 'YAML_LIST_FILE="${{ steps.targets.outputs.yaml_list_file }}"' in content
    assert 'MD_LIST_FILE="${{ steps.targets.outputs.md_list_file }}"' in content
