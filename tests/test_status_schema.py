"""Unit tests for standardized orchestrator status schema metadata."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.ci_orchestrator as ci_module
import scripts.master_orchestrator as master_module
import scripts.repo_automation as repo_module


@pytest.mark.unit
def test_repo_automation_save_status_includes_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    automation = repo_module.RepoAutomation()
    status_file = tmp_path / "status.json"

    monkeypatch.setattr(automation, "_status_files", lambda: [status_file])
    monkeypatch.setattr(
        automation,
        "_resolved_optional_config_paths",
        lambda: {"quantum": None, "evaluation": None},
    )
    monkeypatch.setattr(automation, "_is_component_running", lambda _name: False)

    automation.save_status()

    payload = json.loads(status_file.read_text(encoding="utf-8"))
    assert payload["run_id"] == automation.run_id
    assert payload["config_path"] is None
    assert payload["generated_at"].endswith("Z")
    assert payload["last_health_check"].endswith("Z")


@pytest.mark.unit
def test_master_get_status_includes_metadata() -> None:
    orchestrator = master_module.MasterOrchestrator.__new__(
        master_module.MasterOrchestrator
    )
    orchestrator.run_id = "20260313T000000Z"
    orchestrator.config_path = (
        master_module.REPO_ROOT / "config" / "master_orchestrator.yaml"
    )
    orchestrator.list_orchestrators = lambda: []
    orchestrator.list_workflows = lambda: []
    orchestrator._get_resource_usage = lambda: {"available": False}

    status = master_module.MasterOrchestrator.get_status(orchestrator)

    assert status["run_id"] == "20260313T000000Z"
    assert status["config_path"] == "config/master_orchestrator.yaml"
    assert status["generated_at"].endswith("Z")


@pytest.mark.unit
def test_ci_results_include_run_and_config_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    ci = ci_module.CIOrchestrator()
    ci.data_out = tmp_path
    ci.results = [{"name": "dummy", "status": "succeeded"}]

    monkeypatch.setattr(
        ci,
        "_resolved_config_paths",
        lambda: {
            "autotrain": None,
            "quantum_autorun": "config/quantum/quantum_autorun.yaml",
            "evaluation_autorun": "config/evaluation/evaluation_autorun.yaml",
            "master_orchestrator": "config/master_orchestrator.yaml",
        },
    )

    ci._save_results()

    payload = json.loads((tmp_path / "ci_results.json").read_text(encoding="utf-8"))
    assert payload["run_id"] == ci.run_id
    assert payload["config_path"] is None
    assert (
        payload["config_paths"]["master_orchestrator"]
        == "config/master_orchestrator.yaml"
    )
