import asyncio
import os
import sys
import time
import json
import requests
import socket
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARIA_WEB = REPO_ROOT / 'aria_web'
SERVER_URL = 'http://127.0.0.1:8080'


def is_port_open(port=8080, host='127.0.0.1'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.4)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


def _find_free_port(host='127.0.0.1'):
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
    global SERVER_URL

    # Re-use only when 8080 is an actual Aria API instance.
    if is_port_open(8080) and is_aria_api_healthy(SERVER_URL):
        return None

    # If 8080 is occupied by something else, run Aria on a free port.
    target_port = 8080 if not is_port_open(8080) else _find_free_port()
    target_url = f"http://127.0.0.1:{target_port}"

    env = os.environ.copy()
    env['ARIA_PORT'] = str(target_port)

    proc = subprocess.Popen(["python3", "server.py"], cwd=str(
        ARIA_WEB), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # wait for server to be available
    for _ in range(30):
        if is_aria_api_healthy(target_url):
            SERVER_URL = target_url
            return proc
        time.sleep(0.2)

    proc.kill()
    raise RuntimeError('Failed to start aria server')


def wait_for_object(name, timeout=4.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0)
            if r.ok and 'objects' in r.json() and name in r.json()['objects']:
                return r.json()['objects'][name]
        except Exception:
            pass
        time.sleep(0.12)
    return None


@pytest.mark.pyppeteer
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_pyppeteer_add_pickup_drop():
    if sys.version_info >= (3, 12):
        pytest.skip(
            "pyppeteer is not reliable on Python >= 3.12 in this environment")

    try:
        from pyppeteer import launch
    except Exception:
        pytest.skip('pyppeteer not available')

    proc = ensure_server_running()
    started_proc = proc is not None

    name = f"e2e_pypp_{int(time.time()*1000)}"

    try:
        chrome_path = os.getenv('CHROME_PATH') or os.getenv(
            'PUPPETEER_EXECUTABLE_PATH')
        launch_kwargs = {
            'headless': True,
            'args': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--disable-setuid-sandbox']
        }
        if chrome_path:
            # Use system-installed Chrome/Chromium for better CI compatibility
            launch_kwargs['executablePath'] = chrome_path

        browser = await launch(**launch_kwargs)
    except Exception as e:
        # In many headless CI/dev containers Chromium fails to launch due missing system deps.
        pytest.skip(f"pyppeteer/Chromium couldn't start: {e}")
    page = await browser.newPage()
    await page.goto(SERVER_URL)

    # Add object via client code
    await page.evaluate("(n, e) => addObject(n, e)", name, '🧸')

    obj = wait_for_object(name, timeout=6.0)
    assert obj is not None, f"Server didn't report newly added object {name}"

    # Pick it up
    await page.evaluate("(n) => pickUpObject(n)", name)

    # Wait for server state 'held'
    deadline = time.time() + 4.0
    held = False
    while time.time() < deadline:
        j = requests.get(f"{SERVER_URL}/api/aria/state", timeout=1.0).json()
        if j.get('objects', {}).get(name, {}).get('state') == 'held':
            held = True
            break
        await asyncio.sleep(0.1)
    assert held, 'Object not marked held on server after pickUpObject'

    # Drop
    await page.evaluate('() => dropObject()')
    dropped = wait_for_object(name, timeout=5.0)
    assert dropped is not None and dropped.get(
        'state') in ['on_stage', 'on_table']

    # Cleanup
    r = requests.post(f"{SERVER_URL}/api/aria/object",
                      json={'action': 'remove', 'object': {'id': name}})
    assert r.ok

    await browser.close()

    if started_proc and proc:
        proc.kill()
        proc.wait(timeout=2)
