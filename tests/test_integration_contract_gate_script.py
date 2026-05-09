"""Contract tests for the integration contract gate shell wrapper."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_integration_contract_gate_script_has_expected_commands() -> None:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "integration_contract_gate.sh"
    )
    assert script_path.exists(), "Expected gate wrapper script to exist"

    content = script_path.read_text(encoding="utf-8")

    assert content.startswith("#!/usr/bin/env bash")
    assert "set -euo pipefail" in content
    assert "python scripts/integration_smoke.py" in content
    assert "python scripts/ci_orchestrator.py --integration-contract-tests" in content
    assert "python scripts/ci_orchestrator.py --validate-all" in content
