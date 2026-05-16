"""Tests for orchestrator health integration in /api/ai/status endpoint.

Verifies that orchestrator status files are correctly aggregated and exposed
through the status endpoint for real-time monitoring.
"""

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType

import pytest


# Import function_app module
@pytest.fixture(scope="function")
def app_module():
    """Dynamically import function_app for testing."""
    spec = importlib.util.spec_from_file_location(
        "function_app", Path(__file__).resolve().parents[1] / "function_app.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load function_app module")
    module = importlib.util.module_from_spec(spec)
    prev_module = sys.modules.get("function_app")
    sys.modules["function_app"] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        if prev_module is None:
            sys.modules.pop("function_app", None)
        else:
            sys.modules["function_app"] = prev_module
        raise
    return module


class MockRequest:
    """Mock Azure Functions HttpRequest."""

    def __init__(self, method="GET", route_params=None):
        self.method = method
        self.route_params = route_params if route_params is not None else {}

    def get_json(self):
        return {}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _read_bytes_or_none(path: Path) -> bytes | None:
    if not path.exists():
        return None
    return path.read_bytes()


def _restore_bytes_or_unlink(path: Path, original: bytes | None) -> None:
    if original is None:
        if path.exists():
            path.unlink()
        return
    path.write_bytes(original)


def test_orchestrator_health_aggregates_autonomous_training(app_module: ModuleType):
    """
    Conditional test: Verifies autonomous_training orchestrator is included if status file exists.
    If the status file does not exist, the test is explicitly skipped.
    """
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "autonomous_training_status.json"

    if not status_file.exists():
        pytest.skip(
            "autonomous_training_status.json does not exist; skipping test.")

    req = MockRequest("GET")
    resp = app_module.ai_status(req)
    body = resp.get_body()
    if isinstance(body, bytes):
        body = body.decode()
    data = json.loads(body)
    orchestrators = data["orchestrator_health"]["orchestrators"]

    # If status file exists, should be included
    assert (
        "autonomous_training" in orchestrators
    ), "autonomous_training orchestrator missing despite status file present."
    orch = orchestrators["autonomous_training"]
    assert "status" in orch
    assert "cycles_completed" in orch or "error" in orch


def test_orchestrator_health_status_endpoint(app_module: ModuleType):
    """Verify standard orchestrators are included if status files exist."""

    req = MockRequest("GET")
    resp = app_module.ai_status(req)
    body = resp.get_body()
    if isinstance(body, bytes):
        body = body.decode()
    data = json.loads(body)
    orchestrators = data["orchestrator_health"]["orchestrators"]

    # Check that standard orchestrators are properly formatted if present
    for name in ["autotrain", "quantum_autorun", "evaluation_autorun"]:
        if name in orchestrators:
            orch = orchestrators[name]
            assert "status" in orch
            assert orch["status"] in ["ok", "degraded", "idle", "error"]
            # Should have either success metrics or error
            assert "total_jobs" in orch or "error" in orch


def test_orchestrator_health_overall_status_logic(app_module: ModuleType):
    """Verify overall_status correctly reflects orchestrator states."""

    req = MockRequest("GET")
    resp = app_module.ai_status(req)
    body = resp.get_body()
    if isinstance(body, bytes):
        body = body.decode()
    data = json.loads(body)

    orchestrator_health = data["orchestrator_health"]
    overall = orchestrator_health["overall_status"]
    active = orchestrator_health["active_count"]
    failed = orchestrator_health["failed_count"]

    # Logic verification
    if failed > 0:
        assert overall == "degraded"
    elif active > 0:
        assert overall == "healthy"
    else:
        # If no orchestrators running, should be idle or unknown
        assert overall in ["idle", "unknown"]


def test_orchestrator_health_endpoint_resilience(app_module: ModuleType):
    """Verify /api/ai/status doesn't crash if status files are malformed."""
    # This test just verifies the endpoint returns 200 even if
    # orchestrator status files are missing or broken
    req = MockRequest("GET")

    # Should not raise even if files don't exist
    resp = app_module.ai_status(req)
    assert resp.status_code == 200

    body = resp.get_body()
    if isinstance(body, bytes):
        body = body.decode()
    data = json.loads(body)
    assert "orchestrator_health" in data
    # Should gracefully degrade to empty orchestrators dict
    assert isinstance(data["orchestrator_health"]["orchestrators"], dict)


def test_orchestrator_health_last_checked_utc_z(app_module: ModuleType):
    """Verify orchestrator_health.last_checked is UTC ISO-8601 ending in Z."""
    req = MockRequest("GET")
    resp = app_module.ai_status(req)
    assert resp.status_code == 200

    body = resp.get_body()
    if isinstance(body, bytes):
        body = body.decode()
    data = json.loads(body)
    last_checked = data["orchestrator_health"]["last_checked"]
    assert isinstance(last_checked, str)
    assert last_checked.endswith("Z")

    # Parseability guard: convert trailing Z to +00:00 for fromisoformat.
    datetime.fromisoformat(last_checked.replace("Z", "+00:00"))


def test_orchestrator_heartbeat_completed_not_running(app_module: ModuleType):
    """Completed heartbeat should not be reported as running."""
    repo_root = Path(__file__).resolve().parents[1]
    data_out = repo_root / "data_out"
    status_file = data_out / "autonomous_training_status.json"
    heartbeat_file = data_out / "autonomous_training_heartbeat.json"

    original_status = _read_bytes_or_none(status_file)
    original_heartbeat = _read_bytes_or_none(heartbeat_file)

    try:
        _write_json(
            status_file,
            {
                "cycles_completed": 3,
                "best_accuracy": 0.88,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "performance_history": [{"accuracy": 0.8}, {"accuracy": 0.88}],
            },
        )
        _write_json(
            heartbeat_file,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state": "completed",
                "pid": 12345,
                "current_cycle": 3,
            },
        )

        req = MockRequest("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200

        body = resp.get_body()
        if isinstance(body, bytes):
            body = body.decode()
        data = json.loads(body)
        orch = data["orchestrator_health"]["orchestrators"]["autonomous_training"]

        assert isinstance(orch["heartbeat_running"], bool)
        assert orch["heartbeat_running"] is False
    finally:
        _restore_bytes_or_unlink(status_file, original_status)
        _restore_bytes_or_unlink(heartbeat_file, original_heartbeat)


def test_orchestrator_heartbeat_training_running(app_module: ModuleType):
    """Fresh training heartbeat should be reported as running."""
    repo_root = Path(__file__).resolve().parents[1]
    data_out = repo_root / "data_out"
    status_file = data_out / "autonomous_training_status.json"
    heartbeat_file = data_out / "autonomous_training_heartbeat.json"

    original_status = _read_bytes_or_none(status_file)
    original_heartbeat = _read_bytes_or_none(heartbeat_file)

    try:
        _write_json(
            status_file,
            {
                "cycles_completed": 4,
                "best_accuracy": 0.9,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "performance_history": [{"accuracy": 0.82}, {"accuracy": 0.9}],
            },
        )
        _write_json(
            heartbeat_file,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "state": "training",
                "pid": 23456,
                "current_cycle": 4,
            },
        )

        req = MockRequest("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200

        body = resp.get_body()
        if isinstance(body, bytes):
            body = body.decode()
        data = json.loads(body)
        orch = data["orchestrator_health"]["orchestrators"]["autonomous_training"]

        assert isinstance(orch["heartbeat_running"], bool)
        assert orch["heartbeat_running"] is True
    finally:
        _restore_bytes_or_unlink(status_file, original_status)
        _restore_bytes_or_unlink(heartbeat_file, original_heartbeat)


def test_orchestrator_heartbeat_stale_not_running(app_module: ModuleType):
    """Stale heartbeat timestamps should not be treated as active."""
    repo_root = Path(__file__).resolve().parents[1]
    data_out = repo_root / "data_out"
    status_file = data_out / "autonomous_training_status.json"
    heartbeat_file = data_out / "autonomous_training_heartbeat.json"

    original_status = _read_bytes_or_none(status_file)
    original_heartbeat = _read_bytes_or_none(heartbeat_file)

    try:
        _write_json(
            status_file,
            {
                "cycles_completed": 5,
                "best_accuracy": 0.91,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "performance_history": [{"accuracy": 0.84}, {"accuracy": 0.91}],
            },
        )
        _write_json(
            heartbeat_file,
            {
                "timestamp": (
                    datetime.now(timezone.utc) - timedelta(minutes=10)
                ).isoformat(),
                "state": "training",
                "pid": 34567,
                "current_cycle": 5,
            },
        )

        req = MockRequest("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200

        body = resp.get_body()
        if isinstance(body, bytes):
            body = body.decode()
        data = json.loads(body)
        orch = data["orchestrator_health"]["orchestrators"]["autonomous_training"]

        assert orch["heartbeat_running"] is False
    finally:
        _restore_bytes_or_unlink(status_file, original_status)
        _restore_bytes_or_unlink(heartbeat_file, original_heartbeat)
