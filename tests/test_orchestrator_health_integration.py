"""Tests for orchestrator health integration in /api/ai/status endpoint.

Verifies that orchestrator status files are correctly aggregated and exposed
through the status endpoint for real-time monitoring.
"""

import importlib.util
import json
import sys
from datetime import datetime
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
    sys.modules["function_app"] = module
    spec.loader.exec_module(module)
    return module


class MockRequest:
    """Mock Azure Functions HttpRequest."""

    def __init__(self, method="GET", route_params=None):
        self.method = method
        self.route_params = route_params if route_params is not None else {}

    def get_json(self):
        return {}


def test_orchestrator_health_aggregates_autonomous_training(app_module: ModuleType):
    """
    Conditional test: Verifies autonomous_training orchestrator is included if status file exists.
    If the status file does not exist, the test is explicitly skipped.
    """
    repo_root = Path(__file__).resolve().parents[1]
    status_file = repo_root / "data_out" / "autonomous_training_status.json"

    if not status_file.exists():
        pytest.skip("autonomous_training_status.json does not exist; skipping test.")

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
