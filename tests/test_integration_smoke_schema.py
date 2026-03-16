"""Unit tests for integration smoke summary schema metadata."""

from __future__ import annotations

import re

import pytest

import scripts.integration_smoke as smoke_module


@pytest.mark.unit
def test_run_smoke_summary_includes_run_and_config_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_run_command(name, cmd, *, critical=True, timeout=180):
        return smoke_module.StepResult(
            name=name,
            status="succeeded",
            critical=critical,
            duration_sec=0.0,
            detail="ok",
        )

    config_map = {
        "master_orchestrator": smoke_module.REPO_ROOT / "config" / "master_orchestrator.yaml",
        "quantum_autorun": smoke_module.REPO_ROOT / "config" / "quantum" / "quantum_autorun.yaml",
        "evaluation_autorun": smoke_module.REPO_ROOT / "config" / "evaluation" / "evaluation_autorun.yaml",
    }

    monkeypatch.setattr(
        smoke_module,
        "_check_config_paths",
        lambda: [
            smoke_module.StepResult(
                name="master_orchestrator_config",
                status="succeeded",
                critical=True,
                duration_sec=0.0,
                detail="resolved=config/master_orchestrator.yaml",
            )
        ],
    )
    monkeypatch.setattr(smoke_module, "_run_command", _fake_run_command)
    monkeypatch.setattr(
        smoke_module,
        "_probe_functions_endpoint",
        lambda strict: smoke_module.StepResult(
            name="functions_ai_status_endpoint",
            status="skipped",
            critical=False,
            duration_sec=0.0,
            detail="functions host not running (non-strict mode)",
        ),
    )
    monkeypatch.setattr(
        smoke_module,
        "resolve_existing_config_path",
        lambda _repo_root, key: config_map.get(key),
    )

    summary = smoke_module.run_smoke(strict_endpoints=False)

    assert summary["config_path"] is None
    assert summary["config_paths"]["master_orchestrator"] == "config/master_orchestrator.yaml"
    assert summary["config_paths"]["quantum_autorun"] == "config/quantum/quantum_autorun.yaml"
    assert summary["config_paths"]["evaluation_autorun"] == "config/evaluation/evaluation_autorun.yaml"
    assert re.match(r"^\d{8}T\d{6}Z$", summary["run_id"])
    assert summary["generated_at"].endswith("Z")
