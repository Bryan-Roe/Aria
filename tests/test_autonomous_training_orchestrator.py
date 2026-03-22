"""Unit tests for scripts/autonomous_training_orchestrator.py."""

from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "autonomous_training_orchestrator.py"

_spec = importlib.util.spec_from_file_location(
    "_autonomous_training_orchestrator", SCRIPT_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load orchestrator module from {SCRIPT_PATH}")

orchestrator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(orchestrator)


def test_should_run_quantum_cycle_respects_interval() -> None:
    status = {
        "cycles_completed": 1,
        "quantum_llm": {},
    }
    config = {
        "autonomous_mode": {"cycle_interval_minutes": 30},
        "quantum_llm": {
            "enabled": True,
            "training_interval_minutes": 60,
        },
    }

    # Every 2 cycles for this configuration, so cycle 1 should skip.
    assert orchestrator._should_run_quantum_cycle(status, config) is False

    status["cycles_completed"] = 2
    assert orchestrator._should_run_quantum_cycle(status, config) is True


def test_should_run_quantum_cycle_disabled() -> None:
    status = {"cycles_completed": 10, "quantum_llm": {}}
    config = {
        "autonomous_mode": {"cycle_interval_minutes": 30},
        "quantum_llm": {
            "enabled": False,
            "training_interval_minutes": 60,
        },
    }

    assert orchestrator._should_run_quantum_cycle(status, config) is False


def test_should_run_quantum_cycle_when_last_run_is_stale() -> None:
    stale_run = (datetime.now() - timedelta(minutes=90)).isoformat()
    status = {
        "cycles_completed": 1,
        "quantum_llm": {"last_run": stale_run},
    }
    config = {
        "autonomous_mode": {"cycle_interval_minutes": 30},
        "quantum_llm": {
            "enabled": True,
            "training_interval_minutes": 60,
        },
    }

    assert orchestrator._should_run_quantum_cycle(status, config) is True


def test_run_quantum_llm_training_disabled_sets_state() -> None:
    status = {}
    config = {
        "quantum_llm": {
            "enabled": False,
        }
    }

    orchestrator.run_quantum_llm_training(status, config)

    qstatus = status["quantum_llm"]
    assert qstatus["enabled"] is False
    assert qstatus["status"] == "disabled"
    assert qstatus["last_error"] is None


def test_run_autonomously_one_cycle_skip_quantum_writes_status(tmp_path: Path, monkeypatch) -> None:
    status_file = tmp_path / "autonomous_training_status.json"
    heartbeat_file = tmp_path / "autonomous_training_heartbeat.json"

    monkeypatch.setattr(orchestrator, "STATUS_FILE", status_file)
    monkeypatch.setattr(orchestrator, "HEARTBEAT_FILE", heartbeat_file)
    monkeypatch.setattr(orchestrator, "DATA_OUT_ROOT", tmp_path)
    monkeypatch.setattr(orchestrator, "REPO_ROOT", tmp_path)

    monkeypatch.setattr(
        orchestrator,
        "discover_datasets",
        lambda: {"chat": {"count": 1, "paths": [
            "datasets/chat/sample/train.json"]}},
    )
    monkeypatch.setattr(
        orchestrator,
        "simulate_training_cycle",
        lambda cycle_num, **kwargs: {
            "cycle": cycle_num,
            "accuracy": 0.8,
            "datasets_trained": 1,
            "samples_processed": 100,
            "training_time_sec": 0,
            "timestamp": datetime.now().isoformat(),
        },
    )
    monkeypatch.setattr(orchestrator, "promote_model", lambda status: None)

    config = {
        "autonomous_mode": {
            "cycle_interval_minutes": 30,
            "max_cycles": 1,
        },
        "quantum_llm": {
            "enabled": True,
            "training_interval_minutes": 60,
        },
    }

    rc = orchestrator.run_autonomously(
        config=config,
        max_cycles=1,
        cycle_interval_sec=0,
        skip_quantum=True,
    )

    assert rc == 0
    assert status_file.exists()
    assert heartbeat_file.exists()

    payload = json.loads(status_file.read_text(encoding="utf-8"))
    assert payload["cycles_completed"] == 1
    assert payload["status"] == "completed"
    assert payload["quantum_llm"]["enabled"] is True
    assert payload["quantum_llm"]["status"] == "idle"
