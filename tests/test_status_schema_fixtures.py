"""Fixture-backed schema contract tests for orchestrator status outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import scripts.ci_orchestrator as ci_module
import scripts.integration_smoke as smoke_module

_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "status_schema"


def _load_fixture(filename: str) -> dict:
    return json.loads((_FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def _assert_required_keys(payload: dict, required_keys: list[str]) -> None:
    missing = [key for key in required_keys if key not in payload]
    assert not missing, f"Missing required keys: {missing}"


@pytest.mark.unit
def test_ci_results_matches_fixture_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture = _load_fixture("ci_results.required.json")

    ci = ci_module.CIOrchestrator()
    ci.data_out = tmp_path
    ci.results = [{"name": "fixture_probe", "status": "succeeded"}]

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
    _assert_required_keys(payload, fixture["top_level_required"])
    _assert_required_keys(payload["config_paths"], fixture["config_paths_required"])
    assert payload["results"], "Expected at least one result item"
    _assert_required_keys(payload["results"][0], fixture["result_required"])
    assert re.match(r"^\d{8}T\d{6}Z$", payload["run_id"])
    assert payload["generated_at"].endswith("Z")


@pytest.mark.unit
def test_integration_smoke_matches_fixture_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _load_fixture("integration_smoke.required.json")

    def _fake_run_command(name, cmd, *, critical=True, timeout=180):
        return smoke_module.StepResult(
            name=name,
            status="succeeded",
            critical=critical,
            duration_sec=0.0,
            detail="ok",
        )

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
        lambda _repo_root, key: {
            "master_orchestrator": smoke_module.REPO_ROOT
            / "config"
            / "master_orchestrator.yaml",
            "quantum_autorun": smoke_module.REPO_ROOT
            / "config"
            / "quantum"
            / "quantum_autorun.yaml",
            "evaluation_autorun": smoke_module.REPO_ROOT
            / "config"
            / "evaluation"
            / "evaluation_autorun.yaml",
        }.get(key),
    )

    payload = smoke_module.run_smoke(strict_endpoints=False)
    _assert_required_keys(payload, fixture["top_level_required"])
    _assert_required_keys(payload["config_paths"], fixture["config_paths_required"])
    assert payload["results"], "Expected at least one result item"
    _assert_required_keys(payload["results"][0], fixture["result_required"])
    assert re.match(r"^\d{8}T\d{6}Z$", payload["run_id"])
    assert payload["generated_at"].endswith("Z")
