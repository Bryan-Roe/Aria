from __future__ import annotations

from pathlib import Path

import pytest
import yaml

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
    bad_indent = "with:\n                egress-policy: audit"  # 16 leading spaces on egress-policy
    good_indent = "with:\n                  egress-policy: audit"  # 18 leading spaces on egress-policy
    assert bad_indent not in content
    assert content.count(good_indent) == 3


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
    workflow = yaml.safe_load(content)
    triggers = workflow.get("on", workflow.get(True))
    assert triggers is not None, "Expected workflow triggers under key 'on' (or YAML-1.1 boolean True fallback)."
    steps = workflow["jobs"]["OSSAR-Scan"]["steps"]

    assert triggers["push"]["branches"] == ["main"]
    assert triggers["pull_request"]["branches"] == ["main"]
    assert steps[0]["name"] == "Checkout repository"


@pytest.mark.unit
def test_summary_workflow_has_no_trailing_whitespace() -> None:
    content = _read(".github/workflows/summary.yml")
    trailing_ws_lines = [
        line_number for line_number, line in enumerate(content.splitlines(), start=1) if line != line.rstrip(" \t")
    ]
    assert not trailing_ws_lines, f"Trailing whitespace found on lines: {trailing_ws_lines}"
