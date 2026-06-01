"""Integration-style tests for AriaRequestHandler HTTP endpoints.

These tests start the actual HTTPServer on a dynamic port in a thread so
that AI consumers (and CI) get real end-to-end coverage of:

- /api/aria/schema  → returns ARIA_ACTIONS contract for agent discovery
- /api/aria/command → returns inferred actions even in fallback mode
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PATH = REPO_ROOT / "apps" / "aria" / "server.py"


def _load_server_module():
    """Load apps/aria/server.py as a module without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "aria_server_under_test", SERVER_PATH)
    assert spec and spec.loader, "Could not create import spec for server.py"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


@pytest.fixture(scope="module")
def aria_server():
    mod = _load_server_module()
    handler_cls = mod.AriaRequestHandler

    httpd = HTTPServer(("127.0.0.1", 0), handler_cls)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield {"port": port, "module": mod}
    finally:
        httpd.shutdown()
        httpd.server_close()


def _get_json(port: int, path: str):
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=5) as resp:
        assert resp.status == 200
        return json.loads(resp.read().decode("utf-8"))


def _post_json(port: int, path: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        return json.loads(resp.read().decode("utf-8"))


def test_schema_endpoint_returns_action_contract(aria_server):
    body = _get_json(aria_server["port"], "/api/aria/schema")
    assert "actions" in body
    assert "valid_gestures" in body
    assert "limits" in body

    # All core actions must be present
    for action in ("move", "say", "pickup", "drop", "throw", "gesture", "look", "wait"):
        assert action in body["actions"], f"Missing action {action}"

    # Limits sanity checks (AI consumers rely on these)
    limits = body["limits"]
    assert limits["max_actions_per_sequence"] == 25
    assert limits["coordinate_range"] == [0, 100]
    assert limits["max_say_text_chars"] == 200
    assert limits["max_wait_seconds"] == 30


def test_state_endpoint_shape(aria_server):
    body = _get_json(aria_server["port"], "/api/aria/state")
    assert "aria" in body
    assert "objects" in body
    assert "environment" in body


def test_command_endpoint_returns_actions_for_wave(aria_server):
    body = _post_json(aria_server["port"],
                      "/api/aria/command", {"command": "wave"})
    # Response should contain either tags or actions (or both); for wave we
    # expect a gesture action via fallback or tag inference.
    assert "actions" in body or "tags" in body
    if body.get("actions"):
        assert any(a.get("action") == "gesture" for a in body["actions"])


def test_presets_endpoint_returns_curated_commands(aria_server):
    body = _get_json(aria_server["port"], "/api/aria/presets")
    assert "presets" in body
    assert isinstance(body["presets"], list) and body["presets"]
    # Every preset entry should have a name and at least one command string
    for entry in body["presets"]:
        assert isinstance(entry.get("name"), str) and entry["name"]
        assert isinstance(entry.get("commands"), list) and entry["commands"]
        for cmd in entry["commands"]:
            assert isinstance(cmd, str) and cmd.strip()


def test_execute_plan_mode_returns_actions_without_side_effects(aria_server):
    """Plan mode should return parsed actions without mutating stage_state."""
    mod = aria_server["module"]
    pos_before = dict(mod.stage_state["aria"].get("position", {}))
    body = _post_json(
        aria_server["port"],
        "/api/aria/execute",
        {"command": "wave", "auto_execute": False},
    )
    pos_after = dict(mod.stage_state["aria"].get("position", {}))
    # Plan mode must not move Aria
    assert pos_before == pos_after
    # Response should expose either an 'actions' or 'plan' field for AI consumers
    assert any(k in body for k in ("actions", "plan", "tags"))
