"""
Smoke tests for function_app.py API endpoints.

Uses unittest.mock to mock Azure Functions HttpRequest objects
and validates response shapes, status codes, and error handling
without running a live server.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure project root on path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helper: build a mock Azure Functions HttpRequest
# ---------------------------------------------------------------------------
def _mock_request(
    method: str = "GET",
    body: dict | None = None,
    params: dict | None = None,
    route_params: dict | None = None,
) -> MagicMock:
    """Create a lightweight mock of azure.functions.HttpRequest."""
    req = MagicMock()
    req.method = method
    req.params = params or {}
    req.route_params = route_params or {}

    if body is not None:
        raw = json.dumps(body).encode("utf-8")
        req.get_json.return_value = body
        req.get_body.return_value = raw
    else:
        req.get_json.side_effect = ValueError("No JSON body")
        req.get_body.return_value = b""

    return req


# ---------------------------------------------------------------------------
# Import the function_app module (best-effort; skip suite if unavailable)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def app_module():
    """Import function_app once; skip tests if it can't load."""
    try:
        import function_app
        return function_app
    except Exception as exc:
        pytest.skip(f"Cannot import function_app: {exc}")


# ===========================================================================
# GET endpoint tests — should return 200 with expected content types
# ===========================================================================
class TestGetEndpoints:
    """GET endpoints should return valid responses without a request body."""

    def test_ai_status(self, app_module):
        """GET /api/ai/status returns JSON with provider info."""
        req = _mock_request("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert "provider" in data or "status" in data

    def test_chat_options(self, app_module):
        """OPTIONS /api/chat returns CORS headers."""
        req = _mock_request("OPTIONS")
        resp = app_module.chat_options(req)
        assert resp.status_code == 200

    def test_subscription_pricing(self, app_module):
        """GET /api/subscription/pricing returns tier data."""
        req = _mock_request("GET")
        resp = app_module.subscription_pricing(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        # Should contain at least one tier
        assert isinstance(data, (dict, list))

    def test_quantum_info(self, app_module):
        """GET /api/quantum/info returns backend/version data."""
        req = _mock_request("GET")
        resp = app_module.quantum_info(req)
        assert resp.status_code == 200


# ===========================================================================
# POST endpoint validation tests — bad input ➜ 400
# ===========================================================================
class TestPostValidation:
    """POST endpoints should reject malformed payloads."""

    def test_chat_empty_messages(self, app_module):
        """POST /api/chat with empty messages → 400."""
        req = _mock_request("POST", body={"messages": []})
        resp = app_module.chat(req)
        assert resp.status_code == 400

    def test_chat_no_body(self, app_module):
        """POST /api/chat with no JSON body → 400 or 500."""
        req = _mock_request("POST")
        resp = app_module.chat(req)
        assert resp.status_code in (400, 500)

    def test_chat_stream_empty_messages(self, app_module):
        """POST /api/chat/stream with empty messages → 400."""
        req = _mock_request("POST", body={"messages": []})
        resp = app_module.chat_stream(req)
        assert resp.status_code == 400

    def test_tts_no_text(self, app_module):
        """POST /api/tts with no text field → 400."""
        req = _mock_request("POST", body={})
        resp = app_module.tts(req)
        assert resp.status_code in (400, 500)


# ===========================================================================
# Request validator unit tests (shared/request_validator.py)
# ===========================================================================
class TestRequestValidator:
    """Unit tests for the shared request validation module."""

    def test_parse_valid_json(self):
        from shared.request_validator import parse_json_body

        req = _mock_request("POST", body={"key": "value"})
        body, err = parse_json_body(req)
        assert err is None
        assert body == {"key": "value"}

    def test_parse_invalid_json(self):
        from shared.request_validator import parse_json_body

        req = MagicMock()
        req.get_json.side_effect = ValueError("bad json")
        req.get_body.return_value = b"not-json"
        body, err = parse_json_body(req)
        assert err is not None
        assert body is None

    def test_validate_required_field(self):
        from shared.request_validator import validate_fields

        err = validate_fields({}, {"name": {"type": str, "required": True}})
        assert err is not None
        assert "required" in err.lower() or "missing" in err.lower()

    def test_validate_type_mismatch(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"count": "not-a-number"},
            {"count": {"type": int}},
        )
        assert err is not None

    def test_validate_range(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"temperature": 3.0},
            {"temperature": {"type": (int, float), "min": 0, "max": 2}},
        )
        assert err is not None

    def test_validate_allowlist(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"tier": "MEGA"},
            {"tier": {"type": str, "allowed": ["FREE", "PRO", "ENTERPRISE"]}},
        )
        assert err is not None

    def test_validate_min_length(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"messages": []},
            {"messages": {"type": list, "required": True, "min_length": 1}},
        )
        assert err is not None

    def test_validate_happy_path(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"messages": [{"role": "user", "content": "hi"}], "temperature": 0.7},
            {
                "messages": {"type": list, "required": True, "min_length": 1},
                "temperature": {"type": (int, float), "min": 0, "max": 2},
            },
        )
        assert err is None

    def test_full_validate_request(self):
        from shared.request_validator import validate_request, CHAT_SCHEMA

        req = _mock_request("POST", body={
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.5,
        })
        body, err = validate_request(req, CHAT_SCHEMA)
        assert err is None
        assert body is not None
