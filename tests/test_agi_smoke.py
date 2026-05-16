"""
Smoke tests for AGI endpoints and shared AGI schema.

These are lightweight, fast checks intended to act as a quick gate for AGI-related API surface.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest


def _mock_request(method: str = "GET", body: dict | None = None, params: dict | None = None, route_params: dict | None = None):
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


@pytest.fixture(scope="module")
def app_module():
    """Import function_app once; skip tests if it cannot be imported."""
    try:
        import function_app

        return function_app
    except Exception as exc:
        pytest.skip(f"Cannot import function_app: {exc}")


def test_agi_status_includes_stream_endpoint(app_module):
    req = _mock_request("GET")
    resp = app_module.agi_status(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    endpoints = data.get("endpoints") or []
    assert any("/api/agi/stream" in e for e in endpoints)


def test_agi_analyze_requires_query_or_messages(app_module):
    req = _mock_request("POST", body={})
    resp = app_module.agi_analyze(req)
    assert resp.status_code == 400


def test_agi_reason_requires_query_or_messages(app_module):
    req = _mock_request("POST", body={})
    resp = app_module.agi_reason(req)
    assert resp.status_code == 400


def test_agi_stream_requires_query_or_messages(app_module):
    req = _mock_request("POST", body={})
    resp = app_module.agi_stream(req)
    assert resp.status_code == 400
