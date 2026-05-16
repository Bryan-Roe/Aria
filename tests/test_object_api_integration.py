"""Integration tests for the Aria object API (/api/aria/object, /api/aria/objects).

These tests start a real Aria server in a background thread, send HTTP requests
to the object API, and verify the JSON responses.

Marked with pytest.mark.integration — run via:
    pytest tests/test_object_api_integration.py -v
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# Ensure apps/aria is on the path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "aria"))


# ---------------------------------------------------------------------------
# Server fixture
# ---------------------------------------------------------------------------


def _get_free_loopback_port() -> int:
    """Reserve and return a free loopback TCP port for the test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def aria_server():
    """Start the Aria server in a background thread for the test module."""

    import server as aria_module

    # Reset global state for a clean test run
    aria_module.stage_state.clear()
    aria_module.stage_state.update(
        {
            "aria": {"position": {"x": 50, "y": 50}, "expression": "idle"},
            "objects": {},
            "environment": {
                "table": {"position": {"x": 60, "y": 20}},
                "stage_bounds": {"width": 100, "height": 100},
            },
        }
    )

    from http.server import HTTPServer

    server_port = _get_free_loopback_port()
    httpd = HTTPServer(("127.0.0.1", server_port), aria_module.AriaRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    # Wait for server to be ready
    base = f"http://127.0.0.1:{server_port}"
    for _ in range(40):
        try:
            urllib.request.urlopen(f"{base}/api/aria/state", timeout=1)
            break
        except Exception:
            time.sleep(0.1)
    else:
        httpd.shutdown()
        httpd.server_close()
        raise RuntimeError(f"Aria test server failed to start on {base}")

    yield base

    httpd.shutdown()
    httpd.server_close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read())


def _post(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Tests — GET /api/aria/objects
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_get_objects_returns_dict(aria_server):
    resp = _get(f"{aria_server}/api/aria/objects")
    assert "objects" in resp, "Response must contain 'objects' key"
    assert isinstance(resp["objects"], dict)


@pytest.mark.integration
def test_get_state_alias(aria_server):
    """GET /api/aria/state must return the same structure as /api/aria/objects."""
    obj = _get(f"{aria_server}/api/aria/objects")
    state = _get(f"{aria_server}/api/aria/state")
    assert "objects" in state
    assert "aria" in state
    assert obj["objects"] == state["objects"]


# ---------------------------------------------------------------------------
# Tests — POST /api/aria/object — add action
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_add_object(aria_server):
    payload = {
        "action": "add",
        "object": {"id": "ball", "position": {"x": 30, "y": 40}, "state": "on_stage"},
    }
    resp = _post(f"{aria_server}/api/aria/object", payload)
    assert resp.get("status") == "added"
    assert resp.get("id") == "ball"
    assert resp["object"]["position"] == {"x": 30, "y": 40}


@pytest.mark.integration
def test_add_object_shows_in_get(aria_server):
    """Newly added object must appear in GET /api/aria/objects."""
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "cup", "position": {"x": 60, "y": 20}}},
    )
    resp = _get(f"{aria_server}/api/aria/objects")
    assert "cup" in resp["objects"]


@pytest.mark.integration
def test_add_object_default_position(aria_server):
    """Adding an object without explicit position should get default (50, 50)."""
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "cube"}},
    )
    assert resp.get("status") == "added"
    pos = resp["object"]["position"]
    assert "x" in pos and "y" in pos


@pytest.mark.integration
def test_add_object_using_name_field(aria_server):
    """Object payload may use 'name' instead of 'id'."""
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"name": "apple", "position": {"x": 10, "y": 10}}},
    )
    assert resp.get("status") == "added"
    assert resp.get("id") == "apple"


# ---------------------------------------------------------------------------
# Tests — POST /api/aria/object — update action
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_update_object_position(aria_server):
    # Add first
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "box", "position": {"x": 10, "y": 10}}},
    )
    # Update positon
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "update", "object": {"id": "box", "position": {"x": 80, "y": 90}}},
    )
    assert resp.get("status") == "updated"
    assert resp["object"]["position"] == {"x": 80, "y": 90}


@pytest.mark.integration
def test_update_object_state(aria_server):
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "lamp", "state": "on_stage"}},
    )
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "update", "object": {"id": "lamp", "state": "held"}},
    )
    assert resp.get("status") == "updated"
    assert resp["object"]["state"] == "held"


@pytest.mark.integration
def test_drop_object_state_persisted(aria_server):
    """Dropping an object (held → on_stage/on_table) must be reflected by GET /api/aria/state."""
    obj_id = "drop_test_obj"
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": obj_id, "position": {"x": 50, "y": 50}, "state": "on_stage"}},
    )
    # Pick up
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "update", "object": {"id": obj_id, "state": "held"}},
    )
    # Drop — update state to on_stage with a new position
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "update", "object": {"id": obj_id, "position": {"x": 30, "y": 20}, "state": "on_stage"}},
    )
    assert resp.get("status") == "updated"
    assert resp["object"]["state"] == "on_stage"
    assert resp["object"]["position"] == {"x": 30, "y": 20}

    # Verify GET /api/aria/state reflects the drop
    obj_state = _get(f"{aria_server}/api/aria/state").get("objects", {}).get(obj_id)
    assert obj_state is not None, f"Object {obj_id!r} missing from /api/aria/state"
    assert obj_state["state"] == "on_stage", f"Expected on_stage, got: {obj_state['state']}"
    assert obj_state["position"] == {"x": 30, "y": 20}


# ---------------------------------------------------------------------------
# Tests — POST /api/aria/object — remove action
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_remove_object(aria_server):
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "to_remove", "position": {"x": 1, "y": 1}}},
    )
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "remove", "object": {"id": "to_remove"}},
    )
    assert resp.get("status") == "removed"
    assert resp.get("id") == "to_remove"


@pytest.mark.integration
def test_remove_object_no_longer_in_get(aria_server):
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "gone", "position": {"x": 5, "y": 5}}},
    )
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "remove", "object": {"id": "gone"}},
    )
    resp = _get(f"{aria_server}/api/aria/objects")
    assert "gone" not in resp["objects"]


@pytest.mark.integration
def test_delete_alias(aria_server):
    """Action 'delete' should be an alias for 'remove'."""
    _post(
        f"{aria_server}/api/aria/object",
        {"action": "add", "object": {"id": "del_me"}},
    )
    resp = _post(
        f"{aria_server}/api/aria/object",
        {"action": "delete", "object": {"id": "del_me"}},
    )
    assert resp.get("status") == "removed"


# ---------------------------------------------------------------------------
# Tests — POST /api/aria/objects — bulk update
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_bulk_update_objects(aria_server):
    payload = {
        "objects": {
            "bulk1": {"position": {"x": 11, "y": 22}, "state": "on_stage"},
            "bulk2": {"position": {"x": 33, "y": 44}, "state": "on_stage"},
        }
    }
    resp = _post(f"{aria_server}/api/aria/objects", payload)
    assert resp.get("status") == "ok"
    assert "bulk1" in resp["objects"]
    assert "bulk2" in resp["objects"]


@pytest.mark.integration
def test_bulk_update_reflects_in_get(aria_server):
    _post(
        f"{aria_server}/api/aria/objects",
        {"objects": {"merged": {"position": {"x": 55, "y": 66}, "state": "on_stage"}}},
    )
    resp = _get(f"{aria_server}/api/aria/objects")
    assert "merged" in resp["objects"]
    assert resp["objects"]["merged"]["position"] == {"x": 55, "y": 66}


# ---------------------------------------------------------------------------
# Tests — Error cases
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_missing_id_returns_error(aria_server):
    payload = {"action": "add", "object": {"position": {"x": 1, "y": 1}}}
    req = urllib.request.Request(
        f"{aria_server}/api/aria/object",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            # Some implementations return 200 with error key
            assert "error" in body or resp.status >= 400
    except urllib.error.HTTPError as e:
        assert e.code in (400, 500)


@pytest.mark.integration
def test_unknown_action_returns_error(aria_server):
    payload = {"action": "fly", "object": {"id": "x"}}
    req = urllib.request.Request(
        f"{aria_server}/api/aria/object",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            assert "error" in body
    except urllib.error.HTTPError as e:
        assert e.code in (400, 500)
