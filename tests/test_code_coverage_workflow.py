from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_code_coverage_workflow_pins_valid_github_script_sha() -> None:
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "code-coverage.yml"
    assert workflow_path.exists(), "Expected code-coverage workflow to exist"

    content = workflow_path.read_text(encoding="utf-8")

    assert "uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1aad16ab12" not in content
    assert "uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea" in content
