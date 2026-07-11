from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


@pytest.mark.unit
def test_code_coverage_workflow_no_triple_blank_before_permissions() -> None:
    content = _read(".github/workflows/code-coverage.yml")
    assert "\n\n\npermissions:" not in content


@pytest.mark.unit
def test_dataset_integrity_harden_runner_with_block_indentation() -> None:
    content = _read(".github/workflows/dataset-integrity.yml")
    assert content.count("with:\n                  egress-policy: audit") == 3


@pytest.mark.unit
def test_workflow_files_end_with_newline() -> None:
    for rel_path in (
        ".github/workflows/github_workflows_autofix-pr.yml",
        ".github/workflows/github_workflows_validate-workflows.yml",
    ):
        assert _read(rel_path).endswith("\n")


@pytest.mark.unit
def test_ossar_workflow_steps_and_branch_spacing_regression() -> None:
    content = _read(".github/workflows/ossar.yml")
    assert 'branches: ["main"]' in content
    assert "    steps:\n      - name: Checkout repository" in content


@pytest.mark.unit
def test_summary_workflow_has_no_trailing_whitespace() -> None:
    content = _read(".github/workflows/summary.yml")
    assert all(line == line.rstrip(" \t") for line in content.splitlines())
