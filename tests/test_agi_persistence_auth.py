"""
Tests for AGI persistence endpoint auth gating.
"""

import json
import time
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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
    try:
        import function_app

        return function_app
    except Exception as exc:
        pytest.skip(f"Cannot import function_app: {exc}")


def test_agi_persistence_requires_token(monkeypatch, tmp_path, app_module):
    monkeypatch.setenv("QAI_AGI_PERSIST_READ_TOKEN", "secret123")
    monkeypatch.setenv("QAI_AGI_PERSIST", "1")
    path = tmp_path / "agi_audit.jsonl"
    monkeypatch.setenv("QAI_AGI_PERSIST_PATH", str(path))

    # Write sample file so endpoint chooses JSONL backend
    sample = {"id": "t1", "ts": time.time(), "type": "reasoning_chain", "meta": {}, "chain": []}
    path.write_text(json.dumps(sample, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")

    req = _mock_request("GET", params={"limit": "10"})
    # No header provided -> should be unauthorized
    resp = app_module.agi_persistence(req)
    assert resp.status_code == 401


def test_agi_persistence_token_allows(monkeypatch, tmp_path, app_module):
    monkeypatch.setenv("QAI_AGI_PERSIST_READ_TOKEN", "secret123")
    monkeypatch.setenv("QAI_AGI_PERSIST", "1")
    path = tmp_path / "agi_audit.jsonl"
    monkeypatch.setenv("QAI_AGI_PERSIST_PATH", str(path))

    sample = {"id": "t2", "ts": time.time(), "type": "reasoning_chain", "meta": {}, "chain": []}
    path.write_text(json.dumps(sample, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")

    req = _mock_request("GET", params={"limit": "10"})
    # Provide token via headers mapping
    req.headers = {"X-AGI-AUDIT-TOKEN": "secret123"}
    resp = app_module.agi_persistence(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data.get("status") == "ok"
    assert data.get("backend") == "jsonl"
