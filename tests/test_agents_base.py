"""Tests for the automation agent base framework (scripts/agents/base.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agents.base import (  # noqa: E402
    AgentResult,
    AutomationAgent,
    get_registered_agents,
    iter_source_files,
    register,
)


def test_agent_result_rejects_invalid_status():
    with pytest.raises(ValueError):
        AgentResult(name="x", status="bogus", summary="")


def test_agent_result_ok_property_and_serialization():
    res = AgentResult(name="x", status="ok", summary="fine", metrics={"n": 1})
    assert res.ok is True
    data = res.to_dict()
    assert data["name"] == "x"
    assert data["status"] == "ok"
    assert data["metrics"] == {"n": 1}
    assert "timestamp" in data
    # round-trips through JSON
    assert json.loads(json.dumps(data))["summary"] == "fine"


def test_agent_result_warning_and_error_not_ok():
    assert AgentResult(name="x", status="warning", summary="").ok is False
    assert AgentResult(name="x", status="error", summary="").ok is False


def test_make_result_tags_agent_name():
    class _A(AutomationAgent):
        name = "tagger"

    res = _A().make_result(status="warning", summary="hi", findings=[{"a": 1}])
    assert res.name == "tagger"
    assert res.status == "warning"
    assert res.findings == [{"a": 1}]


def test_write_status_writes_json(tmp_path, monkeypatch):
    import scripts.agents.base as base

    monkeypatch.setattr(base, "AGENTS_DATA_DIR", tmp_path / "agents")

    class _A(AutomationAgent):
        name = "writer-agent"

    agent = _A()
    result = agent.make_result(status="ok", summary="done")
    path = agent.write_status(result)

    assert path == tmp_path / "agents" / "writer-agent" / "status.json"
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["name"] == "writer-agent"
    assert loaded["status"] == "ok"


def test_iter_source_files_filters_extensions_and_excludes(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text("x = 1\n")
    (tmp_path / "pkg" / "b.txt").write_text("hello\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.py").write_text("ignored = 1\n")
    (tmp_path / "datasets").mkdir()
    (tmp_path / "datasets" / "d.py").write_text("ignored = 2\n")

    py_files = list(iter_source_files(tmp_path, extensions={"py"}))
    names = {p.name for p in py_files}
    assert names == {"a.py"}  # txt skipped, excluded dirs skipped


def test_iter_source_files_extension_normalization(tmp_path):
    (tmp_path / "a.PY").write_text("x = 1\n")
    # leading-dot and bare, mixed case all match
    assert list(iter_source_files(tmp_path, extensions={".py"}))
    assert list(iter_source_files(tmp_path, extensions={"py"}))


def test_iter_source_files_missing_root_returns_empty(tmp_path):
    assert list(iter_source_files(tmp_path / "does-not-exist")) == []


def test_iter_source_files_is_sorted(tmp_path):
    for name in ["z.py", "a.py", "m.py"]:
        (tmp_path / name).write_text("x = 1\n")
    files = list(iter_source_files(tmp_path, extensions={"py"}))
    assert files == sorted(files)


def test_register_requires_unique_name():
    @register
    class _Registered(AutomationAgent):
        name = "uniq-test-agent-xyz"

    assert "uniq-test-agent-xyz" in get_registered_agents()

    # Re-registering the same class is idempotent.
    register(_Registered)

    # A different class with the same name conflicts.
    with pytest.raises(ValueError):

        @register
        class _Conflict(AutomationAgent):
            name = "uniq-test-agent-xyz"


def test_register_rejects_default_name():
    with pytest.raises(ValueError):

        @register
        class _NoName(AutomationAgent):
            pass
