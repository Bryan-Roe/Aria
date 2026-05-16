"""End-to-end UI test for the Aria web server using pyppeteer.

This test:
  1. Ensures an Aria web server is running (reusing an existing healthy
     instance on :8080 or starting a fresh one on a free port).
  2. Drives the page with pyppeteer to add, pick up, and drop an object.
  3. Verifies server-side state at each step via the /api/aria/state endpoint.
  4. Cleans up the created object and any process it started.

The test is skipped gracefully on environments where pyppeteer / Chromium
cannot run (Python >= 3.12, missing system dependencies, etc.).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest
import requests

logger = logging.getLogger(__name__)

# --- Paths and constants ---------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]

# The Aria web app has lived under a couple of different paths historically.
# Prefer the modern layout (apps/aria) and fall back to legacy (aria_web).
_CANDIDATE_ARIA_DIRS = (
    REPO_ROOT / "apps" / "aria",
    REPO_ROOT / "aria_web",
)
ARIA_WEB: Optional[Path] = next(
    (p for p in _CANDIDATE_ARIA_DIRS if (p / "server.py").is_file()),
    None,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
DEFAULT_SERVER_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

# Tunable timeouts (seconds). Override in CI by setting env vars.
HTTP_TIMEOUT = float(os.getenv("ARIA_TEST_HTTP_TIMEOUT", "1.0"))
SERVER_BOOT_TIMEOUT = float(os.getenv("ARIA_TEST_BOOT_TIMEOUT", "10.0"))
SERVER_BOOT_POLL_INTERVAL = 0.2
STATE_POLL_INTERVAL = 0.12

# Mutable state for the test session.
SERVER_URL = DEFAULT_SERVER_URL


# --- Networking helpers ----------------------------------------------------


def is_port_open(port: int = DEFAULT_PORT, host: str = DEFAULT_HOST) -> bool:
    """Return True if a TCP connection to (host, port) succeeds quickly."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False


def _find_free_port(host: str = DEFAULT_HOST) -> int:
    """Return an OS-assigned free TCP port on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def is_aria_api_healthy(base_url: str) -> bool:
    """Return True only when /api/aria/state responds with the expected JSON."""
    try:
        r = requests.get(f"{base_url}/api/aria/state", timeout=HTTP_TIMEOUT)
        if not r.ok:
            return False
        payload = r.json()
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return False
    return isinstance(payload, dict) and "aria" in payload and "objects" in payload


# --- Server lifecycle ------------------------------------------------------


def ensure_server_running() -> Optional[subprocess.Popen]:
    """Make sure an Aria server is reachable, starting one if necessary.

    Returns the spawned ``subprocess.Popen`` if this function started a server
    (so the caller is responsible for terminating it), or ``None`` if an
    existing healthy instance was reused.
    """
    global SERVER_URL

    # Re-use only when :8080 is an actual Aria API instance.
    if is_port_open(DEFAULT_PORT) and is_aria_api_healthy(DEFAULT_SERVER_URL):
        SERVER_URL = DEFAULT_SERVER_URL
        return None

    if ARIA_WEB is None:
        pytest.skip(
            "Aria web app not found in any known location: "
            + ", ".join(str(p) for p in _CANDIDATE_ARIA_DIRS)
        )

    # If :8080 is occupied by something else, run Aria on a free port.
    target_port = DEFAULT_PORT if not is_port_open(DEFAULT_PORT) else _find_free_port()
    target_url = f"http://{DEFAULT_HOST}:{target_port}"

    env = os.environ.copy()
    env["ARIA_PORT"] = str(target_port)

    proc = subprocess.Popen(
        [sys.executable, "server.py"],
        cwd=str(ARIA_WEB),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + SERVER_BOOT_TIMEOUT
    try:
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(
                    f"Aria server exited prematurely with code {proc.returncode}"
                )
            if is_aria_api_healthy(target_url):
                SERVER_URL = target_url
                return proc
            time.sleep(SERVER_BOOT_POLL_INTERVAL)
    except BaseException:
        _terminate_process(proc)
        raise

    _terminate_process(proc)
    raise RuntimeError(
        f"Failed to start Aria server on {target_url} within {SERVER_BOOT_TIMEOUT:.1f}s"
    )


def _terminate_process(proc: subprocess.Popen, timeout: float = 2.0) -> None:
    """Best-effort termination of a child process."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            proc.wait(timeout=timeout)


# --- State polling helpers -------------------------------------------------


def _get_state() -> Optional[dict]:
    try:
        r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=HTTP_TIMEOUT)
        if not r.ok:
            return None
        return r.json()
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return None


def wait_for_object(name: str, timeout: float = 4.0) -> Optional[dict]:
    """Poll the server state until an object with ``name`` exists or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = _get_state()
        if state:
            obj = state.get("objects", {}).get(name)
            if obj is not None:
                return obj
        time.sleep(STATE_POLL_INTERVAL)
    return None


async def wait_for_object_state(
    name: str, expected_states: tuple[str, ...], timeout: float = 4.0
) -> Optional[dict]:
    """Async variant: poll until the named object reaches one of ``expected_states``."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Run blocking HTTP off the event loop so we don't stall page traffic.
        state = await asyncio.to_thread(_get_state)
        if state:
            obj = state.get("objects", {}).get(name)
            if obj is not None and obj.get("state") in expected_states:
                return obj
        await asyncio.sleep(STATE_POLL_INTERVAL)
    return None


# --- The actual test -------------------------------------------------------


@pytest.mark.pyppeteer
@pytest.mark.e2e
def test_pyppeteer_add_pickup_drop() -> None:
    """Add an object, pick it up, drop it, and clean up — verifying server state."""
    if sys.version_info >= (3, 12):
        pytest.skip("pyppeteer is not reliable on Python >= 3.12 in this environment")

    try:
        from pyppeteer import launch  # noqa: F401  (import-time check)
    except ImportError:
        pytest.skip("pyppeteer not available")

    asyncio.run(_run_pyppeteer_scenario())


async def _run_pyppeteer_scenario() -> None:
    from pyppeteer import launch

    proc = ensure_server_running()
    started_proc = proc is not None

    name = f"e2e_pypp_{int(time.time() * 1000)}"
    browser = None
    try:
        chrome_path = os.getenv("CHROME_PATH") or os.getenv("PUPPETEER_EXECUTABLE_PATH")
        launch_kwargs: dict = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
            ],
        }
        if chrome_path:
            # Use system-installed Chrome/Chromium for better CI compatibility.
            launch_kwargs["executablePath"] = chrome_path

        try:
            browser = await launch(**launch_kwargs)
        except Exception as e:  # noqa: BLE001
            # In many headless CI/dev containers Chromium fails to launch
            # due to missing system deps; treat as skip rather than failure.
            pytest.skip(f"pyppeteer/Chromium couldn't start: {e}")

        page = await browser.newPage()
        await page.goto(SERVER_URL)

        # Add object via client code.
        await page.evaluate("(n, e) => addObject(n, e)", name, "🧸")
        obj = await asyncio.to_thread(wait_for_object, name, 6.0)
        assert obj is not None, f"Server didn't report newly added object {name}"

        # Pick it up.
        await page.evaluate("(n) => pickUpObject(n)", name)
        held = await wait_for_object_state(name, ("held",), timeout=4.0)
        assert held is not None, "Object not marked 'held' on server after pickUpObject"

        # Drop.
        await page.evaluate("() => dropObject()")
        dropped = await wait_for_object_state(
            name, ("on_stage", "on_table"), timeout=5.0
        )
        assert dropped is not None, (
            f"Object {name} did not return to a resting state after dropObject"
        )

        # Cleanup the test object.
        cleanup = await asyncio.to_thread(
            requests.post,
            f"{SERVER_URL}/api/aria/object",
            None,  # data
        )
        # The above call signature is awkward; do it explicitly with json kwarg:
        cleanup = await asyncio.to_thread(
            lambda: requests.post(
                f"{SERVER_URL}/api/aria/object",
                json={"action": "remove", "object": {"id": name}},
                timeout=HTTP_TIMEOUT,
            )
        )
        assert cleanup.ok, f"Failed to remove test object: HTTP {cleanup.status_code}"
    finally:
        if browser is not None:
            with contextlib.suppress(Exception):
                await browser.close()

        if started_proc and proc is not None:
            _terminate_process(proc)
