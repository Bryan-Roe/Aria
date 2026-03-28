from tests.test_orchestrator_health_integration import MockRequest


import json
from types import ModuleType


def test_orchestrator_health_in_status_endpoint(app_module: ModuleType) -> None:
    """Verify /api/ai/status includes orchestrator_health section."""
    req = MockRequest("GET")
    resp = app_module.ai_status(req)

    assert resp.status_code == 200
    data = json.loads(resp.get_body())

    # Verify orchestrator_health section exists
    assert "orchestrator_health" in data, "orchestrator_health section missing from /api/ai/status"

    # Verify required fields
    orchestrator_health = data["orchestrator_health"]
    assert orchestrator_health["enabled"] is True
    assert isinstance(orchestrator_health["orchestrators"], dict)
    assert orchestrator_health["overall_status"] in [
        "healthy", "degraded", "idle", "error", "unknown"]
    assert "last_checked" in orchestrator_health
    assert isinstance(orchestrator_health["active_count"], int)
    assert isinstance(orchestrator_health["failed_count"], int)
