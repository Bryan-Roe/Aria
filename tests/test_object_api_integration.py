import requests
import time
import subprocess
import socket
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


def ensure_server_running():
    if is_port_open(8080):
        return None
    proc = subprocess.Popen(["python3", "server.py"], cwd=str(ARIA_WEB), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        if is_port_open(8080):
            return proc
        time.sleep(0.2)
    proc.kill()
    raise RuntimeError('Failed to start aria_server')


def test_add_update_remove_object_integration():
    proc = ensure_server_running()
    started_proc = proc is not None

    try:
        name = f'integ_obj_{int(time.time()*1000)}'

        # Add
        payload = {'action': 'add', 'object': {'id': name, 'position': {'x': 42, 'y': 42}, 'state': 'on_table', 'emoji': '🧸'}}
        r = requests.post(SERVER_URL + '/api/aria/object', json=payload, timeout=3.0)
        assert r.ok and r.json().get('status') in ('added','ok')

        # Read back
        r2 = requests.get(SERVER_URL + '/api/aria/state', timeout=2.0)
        assert r2.ok
        j = r2.json()
        assert name in j.get('objects', {}), f"object {name} not present: {j.get('objects')}"

        # Update
        payload2 = {'action': 'update', 'object': {'id': name, 'position': {'x': 12, 'y': 26}, 'state': 'on_stage'}}
        r3 = requests.post(SERVER_URL + '/api/aria/object', json=payload2, timeout=3.0)
        assert r3.ok and r3.json().get('status') == 'updated'

        # Verify update
        r4 = requests.get(SERVER_URL + '/api/aria/state', timeout=2.0)
        assert r4.ok
        obj = r4.json()['objects'].get(name)
        assert obj and obj.get('position', {}).get('x') == 12

        # Remove
        r5 = requests.post(SERVER_URL + '/api/aria/object', json={'action': 'remove', 'object': {'id': name}}, timeout=3.0)
        assert r5.ok and r5.json().get('status') == 'removed'

    finally:
        if started_proc and proc:
            proc.kill()
            proc.wait(timeout=2)
