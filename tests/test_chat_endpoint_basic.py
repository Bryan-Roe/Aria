import json
import sys
from pathlib import Path
import pytest

# Add workspace root to path so we can import function_app
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

# Azure Functions HttpRequest import
try:
    import azure.functions as func
except ImportError:  # pragma: no cover
    pytest.skip("azure.functions not available", allow_module_level=True)

# Import the function_app module
import function_app  # noqa: E402


def make_request(body: dict):
    data = json.dumps(body).encode("utf-8")
    req = func.HttpRequest(
        method="POST",
        url="http://localhost/api/chat",
        headers={"Content-Type": "application/json"},
        params={},
        route_params={},
        body=data,
    )
    return req


def test_chat_endpoint_basic_local_provider():
    """Ensure /api/chat logic returns a valid payload with provider fallback.

    Memory injection should be zero when DB unavailable or no prior messages.
    Provider can be lmstudio (if running) or local (fallback).
    """
    req = make_request({
        "messages": [{"role": "user", "content": "Hello test endpoint"}],
        "session_id": "pytest-session"
    })
    resp = function_app.chat(req)
    assert resp.status_code == 200, resp.get_body()
    payload = json.loads(resp.get_body())
    # Provider can be lmstudio (if LM Studio is running) or local (fallback)
    assert payload["provider"] in ["local", "lmstudio"], f"Unexpected provider: {payload['provider']}"
    assert isinstance(payload.get("response"), str)
    assert "memory_injected" in payload
    assert isinstance(payload["memory_injected"], int)
    assert payload["memory_injected"] >= 0
    # Pruning stats present
    pruning = payload.get("pruning")
    assert pruning is not None
    assert "original_tokens" in pruning
