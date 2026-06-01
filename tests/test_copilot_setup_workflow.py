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


@pytest.mark.unit
def test_expected_copilot_entrypoint_files_exist_with_key_pointers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    copilot_md = repo_root / ".github" / "COPILOT.md"
    copilot_yml = repo_root / ".github" / "copilot.yml"

    assert copilot_md.exists(), "Expected .github/COPILOT.md to exist"
    assert copilot_yml.exists(), "Expected .github/copilot.yml to exist"

    copilot_md_content = copilot_md.read_text(encoding="utf-8")
    assert ".github/copilot-instructions.md" in copilot_md_content
    assert ".github/copilot-instructions.full.md" in copilot_md_content

    copilot_yml_content = copilot_yml.read_text(encoding="utf-8")
    assert "quick_instructions: .github/copilot-instructions.md" in copilot_yml_content
    assert "full_instructions: .github/copilot-instructions.full.md" in copilot_yml_content
