"""
Selenium E2E test for Aria object sync using containerized Chrome.

This test uses Selenium with a remote Chrome instance (from Docker container).
It's ideal for CI/CD environments where you want isolated browser instances.

Requirements:
- selenium installed: pip install selenium
- Chrome container running: docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-chrome:latest
- Or use SELENIUM_REMOTE_URL env var for custom Selenium Grid

Docker setup:
  docker run -d -p 4444:4444 -p 5900:5900 --shm-size=2g selenium/standalone-chrome:latest
  
  VNC viewer (optional): Connect to localhost:5900 to watch tests run (password: secret)
"""

import time
import json
import requests
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse
import pytest
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conditionally import selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.warning("Selenium not installed")

REPO_ROOT = Path(__file__).resolve().parents[1]
ARIA_WEB = REPO_ROOT / 'aria_web'
ARIA_APPS = REPO_ROOT / 'apps' / 'aria'
SERVER_URL = os.environ.get('ARIA_SERVER_URL', 'http://localhost:8080')
SELENIUM_REMOTE_URL = os.environ.get(
    'SELENIUM_REMOTE_URL', 'http://localhost:4444/wd/hub')


def _is_local_host(hostname: str | None) -> bool:
    """Return True for localhost-style hostnames/IPs."""
    return hostname in {'127.0.0.1', 'localhost', '::1'}


def _resolve_server_cwd() -> Path:
    """Resolve the best directory containing server.py for Aria UI tests."""
    if (ARIA_WEB / 'server.py').exists():
        return ARIA_WEB
    if (ARIA_APPS / 'server.py').exists():
        return ARIA_APPS
    # Keep a clear failure mode if project layout changes unexpectedly.
    raise RuntimeError(
        f"Could not find Aria server.py under {ARIA_WEB} or {ARIA_APPS}")


def _selenium_status_url(remote_url: str) -> str:
    """Build a Selenium status URL from a WebDriver endpoint URL.

    Supports standard endpoints like:
    - http://host:4444/wd/hub
    - http://host:4444/wd/hub/
    - http://host:4444/session (fallback)
    """
    parsed = urlparse(remote_url)
    base = f"{parsed.scheme or 'http'}://{parsed.netloc}"
    path = (parsed.path or '').rstrip('/')

    if path.endswith('/wd/hub'):
        return f"{base}/wd/hub/status"

    # Default modern Selenium path.
    return f"{base}/status"


def _selenium_status_urls(remote_url: str) -> list[str]:
    """Return candidate status endpoints to probe in priority order."""
    primary = _selenium_status_url(remote_url)
    parsed = urlparse(remote_url)
    base = f"{parsed.scheme or 'http'}://{parsed.netloc}"
    secondary = f"{base}/wd/hub/status" if primary != f"{base}/wd/hub/status" else f"{base}/status"
    return [primary, secondary]


def _selenium_ready_from_payload(status: dict) -> bool:
    """Interpret Selenium status payloads across Grid versions."""
    if not isinstance(status, dict):
        return False

    value = status.get('value')
    if isinstance(value, dict) and 'ready' in value:
        return bool(value.get('ready'))

    # Fallback for alternate payloads that expose top-level ready.
    if 'ready' in status:
        return bool(status.get('ready'))

    return False


def test_is_local_host_variants():
    assert _is_local_host('localhost')
    assert _is_local_host('127.0.0.1')
    assert _is_local_host('::1')
    assert not _is_local_host('example.com')


def test_resolve_server_cwd_contains_server_script():
    cwd = _resolve_server_cwd()
    assert (cwd / 'server.py').exists()


def test_ensure_server_running_rejects_unhealthy_non_local(monkeypatch):
    module = sys.modules[__name__]
    monkeypatch.setattr(module, 'SERVER_URL', 'http://example.com:8080')
    monkeypatch.setattr(module, 'is_aria_api_healthy', lambda _url: False)

    with pytest.raises(RuntimeError, match='Configured ARIA_SERVER_URL is not healthy'):
        ensure_server_running()


def test_selenium_status_url_with_wd_hub_path():
    assert _selenium_status_url(
        'http://localhost:4444/wd/hub') == 'http://localhost:4444/wd/hub/status'
    assert _selenium_status_url(
        'http://localhost:4444/wd/hub/') == 'http://localhost:4444/wd/hub/status'


def test_selenium_status_url_with_non_standard_path_uses_status_root():
    assert _selenium_status_url(
        'http://localhost:4444/session') == 'http://localhost:4444/status'


def test_selenium_status_urls_returns_primary_and_fallback():
    urls = _selenium_status_urls('http://localhost:4444/session')
    assert urls == ['http://localhost:4444/status',
                    'http://localhost:4444/wd/hub/status']


def test_selenium_ready_from_payload_variants():
    assert _selenium_ready_from_payload({'value': {'ready': True}})
    assert _selenium_ready_from_payload({'ready': True})
    assert not _selenium_ready_from_payload({'value': {'ready': False}})
    assert not _selenium_ready_from_payload({'foo': 'bar'})


def is_port_open(port=8080, host='127.0.0.1'):
    """Check if a port is open."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.4)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def _find_free_port(host='127.0.0.1'):
    """Find a free TCP port on localhost."""
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
        return isinstance(payload, dict) and 'aria' in payload and 'objects' in payload
    except (requests.RequestException, ValueError, json.JSONDecodeError):
        return False


def ensure_server_running():
    """Start the Aria server if not already running."""
    global SERVER_URL

    parsed = urlparse(SERVER_URL)
    configured_host = parsed.hostname or '127.0.0.1'
    configured_port = parsed.port or 8080

    # Re-use configured URL whenever it is healthy.
    if is_aria_api_healthy(SERVER_URL):
        logger.info("Aria API server already running")
        return None

    # If user points to a non-local endpoint and it's unhealthy, do not silently
    # start a local server on a different URL.
    if not _is_local_host(configured_host):
        raise RuntimeError(
            f"Configured ARIA_SERVER_URL is not healthy: {SERVER_URL}")

    # If configured local port is occupied by another service, launch Aria on a free port.
    target_port = configured_port if not is_port_open(
        configured_port, configured_host) else _find_free_port()
    target_url = f"http://127.0.0.1:{target_port}"
    server_cwd = _resolve_server_cwd()

    logger.info("Starting Aria server...")
    env = os.environ.copy()
    env['ARIA_PORT'] = str(target_port)
    proc = subprocess.Popen(
        ["python3", "server.py"],
        cwd=str(server_cwd),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for server to be available
    for i in range(30):
        if is_aria_api_healthy(target_url):
            SERVER_URL = target_url
            logger.info(f"Server started successfully after {i+1} attempts")
            return proc
        time.sleep(0.2)

    proc.kill()
    raise RuntimeError('Failed to start Aria server')


def wait_for_object(name, timeout=4.0):
    """Wait for an object to appear in server state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
            if r.ok and 'objects' in r.json() and name in r.json()['objects']:
                return r.json()['objects'][name]
        except Exception as e:
            logger.debug(f"Waiting for object {name}: {e}")
        time.sleep(0.12)
    return None


def is_selenium_hub_ready():
    """Check if Selenium hub is accessible."""
    for status_url in _selenium_status_urls(SELENIUM_REMOTE_URL):
        try:
            response = requests.get(status_url, timeout=2)
            if response.ok:
                status = response.json()
                if _selenium_ready_from_payload(status):
                    logger.info(f"Selenium hub is ready via {status_url}")
                    return True
                logger.warning(
                    f"Selenium hub not ready via {status_url}: {status}")
        except Exception as e:
            logger.warning(
                f"Selenium hub not accessible via {status_url}: {e}")
    return False


def create_remote_driver(max_retries=3):
    """Create a remote WebDriver with retry logic."""
    # Check if Selenium hub is ready
    if not is_selenium_hub_ready():
        raise Exception("Selenium hub is not ready or not accessible")

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(
                f"Connecting to Selenium hub at {SELENIUM_REMOTE_URL} (attempt {attempt + 1}/{max_retries})...")
            driver = webdriver.Remote(
                command_executor=SELENIUM_REMOTE_URL,
                options=chrome_options
            )
            logger.info(
                f"Connected successfully. Session ID: {driver.session_id}")
            return driver
        except Exception as e:
            last_error = e
            logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)

    # All retries failed
    error_msg = f"Failed to connect to Selenium hub after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


@pytest.mark.selenium
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not installed")
def test_selenium_add_pickup_drop():
    """Test object sync using containerized Chrome via Selenium."""
    # Ensure server is running
    try:
        proc = ensure_server_running()
    except RuntimeError as e:
        pytest.skip(f"Aria server unavailable for Selenium E2E: {e}")
    started_proc = proc is not None

    # Generate unique object name
    name = f"e2e_sel_{int(time.time()*1000)}"

    driver = None
    try:
        # Create remote WebDriver
        try:
            driver = create_remote_driver()
        except Exception as e:
            pytest.skip(f"Selenium hub not available: {e}")
            return

        # Navigate to Aria web interface
        logger.info(f"Navigating to {SERVER_URL}")
        driver.get(SERVER_URL)

        # Wait for page to load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return document.readyState") == "complete"
        )
        logger.info(f"Page loaded: {driver.title}")

        # Add object via JavaScript
        logger.info(f"Adding object '{name}' with emoji 🧸")
        driver.execute_script(f"addObject('{name}', '🧸')")

        # Wait for object to appear on server
        obj = wait_for_object(name, timeout=6.0)
        assert obj is not None, f"Server didn't report newly added object {name}"
        logger.info(f"Object added successfully: {obj}")

        # Pick it up
        logger.info(f"Picking up object '{name}'")
        driver.execute_script(f"pickUpObject('{name}')")

        # Wait for server state 'held'
        deadline = time.time() + 4.0
        held = False
        while time.time() < deadline:
            try:
                r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
                state = r.json().get('objects', {}).get(name, {}).get('state')
                if state == 'held':
                    held = True
                    logger.info(f"Object '{name}' is now held")
                    break
                logger.debug(f"Waiting for held state, current: {state}")
            except Exception as e:
                logger.debug(f"Error checking state: {e}")
            time.sleep(0.1)

        assert held, f'Object {name} not marked held on server after pickUpObject'

        # Drop
        logger.info(f"Dropping object '{name}'")
        driver.execute_script('dropObject()')
        dropped = wait_for_object(name, timeout=5.0)
        assert dropped is not None, f"Object {name} disappeared after drop"
        assert dropped.get('state') in [
            'on_stage', 'on_table'], f"Unexpected state after drop: {dropped.get('state')}"
        logger.info(f"Object dropped successfully: {dropped}")

        # Cleanup: remove object
        logger.info(f"Removing object '{name}'")
        r = requests.post(
            f"{SERVER_URL}/api/aria/object",
            json={'action': 'remove', 'object': {'id': name}}
        )
        assert r.ok, f"Failed to remove object: {r.status_code} {r.text}"
        logger.info("Object removed successfully")

    finally:
        # Close browser
        if driver:
            logger.info("Closing browser session")
            driver.quit()

        # Stop server if we started it
        if started_proc and proc:
            logger.info("Stopping Aria server...")
            proc.kill()
            proc.wait(timeout=2)


if __name__ == "__main__":
    # Allow running this test directly
    pytest.main([__file__, "-v", "-s"])
