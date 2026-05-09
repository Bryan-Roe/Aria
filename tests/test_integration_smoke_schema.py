"""Unit tests for integration smoke summary schema metadata."""

from __future__ import annotations

import re
from typing import Any

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
    assert (
        summary["config_paths"]["master_orchestrator"]
        == "config/master_orchestrator.yaml"
    )
    assert (
        summary["config_paths"]["quantum_autorun"]
        == "config/quantum/quantum_autorun.yaml"
    )
    assert (
        summary["config_paths"]["evaluation_autorun"]
        == "config/evaluation/evaluation_autorun.yaml"
    )
    assert re.match(r"^\d{8}T\d{6}Z$", summary["run_id"])
    assert summary["generated_at"].endswith("Z")


@pytest.mark.unit
def test_probe_with_local_dev_adapter_allows_slow_ready_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyProc:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> None:
            return None

        def kill(self) -> None:
            return None

    clock = {"now": 0.0}

    def fake_time() -> float:
        return clock["now"]

    def fake_sleep(seconds: float) -> None:
        clock["now"] += seconds

    def fake_fetch(url: str, timeout: int = 1) -> dict[str, Any]:
        if clock["now"] < 8.5:
            raise TimeoutError("still warming up")
        return {"active_provider": "local"}

    monkeypatch.setattr(
        smoke_module.subprocess, "Popen", lambda *args, **kwargs: DummyProc()
    )
    monkeypatch.setattr(smoke_module.time, "time", fake_time)
    monkeypatch.setattr(smoke_module.time, "sleep", fake_sleep)
    monkeypatch.setattr(smoke_module, "_fetch_local_functions_payload", fake_fetch)

    payload = smoke_module._probe_with_local_dev_adapter(
        "http://localhost:7071/api/ai/status"
    )

    assert payload == {"active_provider": "local"}
    assert smoke_module.LOCAL_DEV_ADAPTER_PROBE_TIMEOUT_SEC > 8.5


@pytest.mark.unit
def test_probe_with_local_dev_adapter_uses_long_request_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class DummyProc:
        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            return None

        def wait(self, timeout: float | None = None) -> None:
            return None

        def kill(self) -> None:
            return None

    observed_timeouts: list[float] = []

    def fake_fetch(url: str, timeout: int = 1) -> dict[str, Any]:
        observed_timeouts.append(timeout)
        if timeout < 8:
            raise TimeoutError("request timeout too short")
        return {"active_provider": "local"}

    monkeypatch.setattr(
        smoke_module.subprocess, "Popen", lambda *args, **kwargs: DummyProc()
    )
    monkeypatch.setattr(smoke_module.time, "time", lambda: 100.0)
    monkeypatch.setattr(smoke_module.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(smoke_module, "_fetch_local_functions_payload", fake_fetch)

    payload = smoke_module._probe_with_local_dev_adapter(
        "http://localhost:7071/api/ai/status"
    )

    assert payload == {"active_provider": "local"}
    assert observed_timeouts
    assert observed_timeouts[0] >= 8
