from __future__ import annotations

import re
from pathlib import Path

import pytest


def _repo_root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / ".github" / "workflows").exists():
            return path
    raise AssertionError("Expected to find repository root containing .github/workflows")


@pytest.mark.unit
def test_code_coverage_workflow_pins_valid_github_script_sha() -> None:
    workflow_path = _repo_root() / ".github" / "workflows" / "code-coverage.yml"
    assert workflow_path.exists(), "Expected code-coverage workflow to exist"

    content = workflow_path.read_text(encoding="utf-8")
    match = re.search(r"uses: actions/github-script@([0-9a-f]{40})", content)

    assert "uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1aad16ab12" not in content
    assert "uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea" in content
    assert match, "Expected code-coverage workflow to pin actions/github-script to a full commit SHA"
