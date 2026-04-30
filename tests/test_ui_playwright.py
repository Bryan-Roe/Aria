import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests

pytest.importorskip("playwright", reason="playwright is not installed")

REPO_ROOT = Path(__file__).resolve().parents[1]
ARIA_WEB = REPO_ROOT / "aria_web"
SERVER_URL = "http://127.0.0.1:8080"


def is_port_open(port=8080, host="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.4)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def _find_free_port(host="127.0.0.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        return s.getsockname()[1]
    finally:
        s.close()


def is_aria_api_healthy(base_url: str) -> bool:
    """Return True only when /api/aria/state responds with expected JSON."""
    try:
        r = requests.get(f"{base_url}/api/aria/state", timeout=1.0)
        if not r.ok:
            return False
        payload = r.json()
        return isinstance(payload, dict) and "aria" in payload and "objects" in payload
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return False


def ensure_server_running():
    """Start aria_web server when it's not running and return process (if started).
    If another server is already running, return None (re-use).
    """
    global SERVER_URL

    # Re-use only if the existing listener is the actual Aria API server.
    if is_port_open(8080) and is_aria_api_healthy(SERVER_URL):
        return None

    # If 8080 is occupied by a non-Aria server, run Aria on a free port.
    target_port = 8080 if not is_port_open(8080) else _find_free_port()
    target_url = f"http://127.0.0.1:{target_port}"

    # start server using python in aria_web
    env = os.environ.copy()
    env["ARIA_PORT"] = str(target_port)
    proc = subprocess.Popen(
        ["python3", "server.py"],
        cwd=str(ARIA_WEB),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # wait a short while for server to come up
    for _ in range(30):
        if is_aria_api_healthy(target_url):
            SERVER_URL = target_url
            return proc
        time.sleep(0.2)

    # didn't start
    proc.kill()
    raise RuntimeError("Failed to start aria_server on 8080")


def wait_for_object(name, timeout=4.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
            if r.ok:
                j = r.json()
                if "objects" in j and name in j["objects"]:
                    return j["objects"][name]
        except Exception:
            pass
        time.sleep(0.12)
    return None


@pytest.mark.playwright
@pytest.mark.e2e
@pytest.mark.skipif(
    not os.getenv("CI")
    and not (
        shutil.which("chromium-browser")
        or shutil.which("chrome")
        or shutil.which("google-chrome")
    ),
    reason="Chromium/Chrome not available",
)
def test_client_add_pickup_and_drag_updates_server():
    """E2E: Launch browser, add object in-page, pick up and drop, and ensure server stage_state is updated."""
    # Ensure server running
    proc = ensure_server_running()
    started_proc = proc is not None

    # Use playwright for browser automation
    try:
        from playwright.sync_api import sync_playwright

        unique_name = f"e2e_toy_{int(time.time()*1000)}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(SERVER_URL)

            # make sure main page loads
            assert "Aria" in page.content()

            # Add object via client API
            page.evaluate(
                "([name, emoji]) => addObject(name, emoji)", [unique_name, "🧸"]
            )

            # wait for server to report it
            obj = wait_for_object(unique_name, timeout=5.0)
            assert (
                obj is not None
            ), f"Server didn't report new object {unique_name}: {requests.get(SERVER_URL + '/api/aria/state').text}"

            # Now pick the object up using client function
            page.evaluate("(name) => pickUpObject(name)", unique_name)

            # verify server state becomes 'held'
            deadline = time.time() + 4.0
            held_ok = False
            while time.time() < deadline:
                resp = requests.get(SERVER_URL + "/api/aria/state", timeout=1.0)
                if resp.ok and unique_name in resp.json().get("objects", {}):
                    st = resp.json()["objects"][unique_name].get("state")
                    if st == "held":
                        held_ok = True
                        break
                time.sleep(0.15)
            assert held_ok, f"Object {unique_name} was not marked 'held' on server"

            # Drop object and see where it lands
            page.evaluate("() => dropObject()")
            dropped = wait_for_object(unique_name, timeout=4.0)
            assert dropped is not None and dropped.get("state") in [
                "on_stage",
                "on_table",
            ], "Dropped state not persisted on server"

            # Clean up: remove object via server API
            r = requests.post(
                SERVER_URL + "/api/aria/object",
                json={"action": "remove", "object": {"id": unique_name}},
            )
            assert r.ok

            browser.close()

    finally:
        # If we started the server for this test, kill it
        if started_proc and proc:
            proc.kill()
            proc.wait(timeout=2)
