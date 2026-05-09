import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

from tests.test_orchestrator_health_integration import MockRequest


def _load_function_app() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "function_app",
        Path(__file__).resolve().parents[1] / "function_app.py",
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


def test_orchestrator_health_in_status_endpoint() -> None:
    """Verify /api/ai/status includes orchestrator_health section."""
    app_module = _load_function_app()
    """Verify /api/ai/status includes orchestrator_health section."""
    req = MockRequest("GET")
    resp = app_module.ai_status(req)

    assert resp.status_code == 200
    data = json.loads(resp.get_body())

    # Verify orchestrator_health section exists
    assert (
        "orchestrator_health" in data
    ), "orchestrator_health section missing from /api/ai/status"

    # Verify required fields
    orchestrator_health = data["orchestrator_health"]
    assert orchestrator_health["enabled"] is True
    assert isinstance(orchestrator_health["orchestrators"], dict)
    assert orchestrator_health["overall_status"] in [
        "healthy",
        "degraded",
        "idle",
        "error",
        "unknown",
    ]
    assert "last_checked" in orchestrator_health
    assert isinstance(orchestrator_health["active_count"], int)
    assert isinstance(orchestrator_health["failed_count"], int)
