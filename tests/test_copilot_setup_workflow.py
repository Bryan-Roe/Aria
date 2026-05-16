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
