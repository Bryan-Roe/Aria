"""
Tests for the read-only AGI persistence audit endpoint (/api/agi/persistence).
"""

import json
import time
import os
from unittest.mock import MagicMock
from pathlib import Path

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
    try:
        import function_app

        return function_app
    except Exception as exc:
        pytest.skip(f"Cannot import function_app: {exc}")


def test_agi_persistence_endpoint_jsonl(monkeypatch, tmp_path, app_module):
    # Configure JSONL persistence
    path = tmp_path / "agi_audit.jsonl"
    monkeypatch.setenv("QAI_AGI_PERSIST", "1")
    monkeypatch.setenv("QAI_AGI_PERSIST_PATH", str(path))

    # Write a sample reasoning_chain entry
    sample = {
        "id": "test1",
        "ts": time.time(),
        "type": "reasoning_chain",
        "meta": {"source": "test"},
        "chain": [{"step_type": "analysis", "content": "hello"}],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sample, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")

    req = _mock_request("GET", params={"limit": "10"})
    resp = app_module.agi_persistence(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data.get("status") == "ok"
    assert data.get("backend") == "jsonl"
    entries = data.get("entries")
    assert isinstance(entries, list)
    assert any(e.get("id") == "test1" or e.get("chain") for e in entries)


def test_agi_persistence_endpoint_sqlite(monkeypatch, tmp_path, app_module):
    # Configure SQLite persistence
    db_path = tmp_path / "agi.db"
    monkeypatch.setenv("QAI_AGI_PERSIST_DB", str(db_path))

    # Use the SQLite adapter to write an entry
    from shared.agi_persistence_sqlite import SQLiteAGIPersistence

    backend = SQLiteAGIPersistence(str(db_path))
    chain = [{"step_type": "analysis", "content": "sqlite hello"}]
    backend.write_reasoning_chain(chain, meta={"source": "test_sqlite"})

    req = _mock_request("GET", params={"limit": "10"})
    resp = app_module.agi_persistence(req)
    assert resp.status_code == 200
    data = json.loads(resp.get_body())
    assert data.get("status") == "ok"
    assert data.get("backend") == "sqlite"
    entries = data.get("entries")
    assert isinstance(entries, list)
    assert any(e.get("meta", {}).get("source") == "test_sqlite" or e.get("chain") for e in entries)

    backend.close()
