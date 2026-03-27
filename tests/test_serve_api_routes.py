"""
Unit/integration tests for apps/dashboard/serve.py HTTP routes.

Uses a threading.Thread to start the server on an ephemeral port, then
sends real HTTP requests (no mocking of the HTTP layer).  Mocks only the
heavy I/O dependencies (vram_calculator, file I/O, subprocess) to keep
tests fast and free of GPU/torch requirements.
"""

import importlib.util
import json
import socket
import sys
import threading
import time
import urllib.request
import urllib.parse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SERVE_PATH = Path(__file__).parent.parent / "apps" / "dashboard" / "serve.py"


def _free_port() -> int:
    """Find a free TCP port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url: str, timeout: float = 5.0):
    """Return (status, response_body_bytes)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


# ---------------------------------------------------------------------------
# Fixture: running dashboard server
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dashboard_server():
    """Start serve.py on an ephemeral port; yield base URL; stop after tests."""
    port = _free_port()

    # We load the module to access DashboardHandler; patch expensive stuff.
    spec = importlib.util.spec_from_file_location("dash_serve", SERVE_PATH)
    assert spec and spec.loader, f"Cannot load {SERVE_PATH}"
    serve_mod = importlib.util.module_from_spec(spec)

    # Patch vram_calculator import inside serve.py before exec_module
    gpu_mock = MagicMock()
    gpu_mock.get_gpu_info.return_value = {
        "gpu_name": "TestGPU", "total_gb": 8.0, "free_gb": 6.0}
    gpu_mock.get_gpu_processes.return_value = []
    gpu_mock.get_system_resources.return_value = {
        "cpu_percent": 10.0, "ram_percent": 40.0}
    vram_mock = MagicMock()
    vram_mock.calculate_safe_batch_size.return_value = {
        "available": True,
        "gpu_name": "TestGPU",
        "total_gb": 8.0,
        "free_gb": 6.0,
        "safe_batch_size": 4,
        "total_estimated_gb": 2.5,
    }
    patcher = patch.dict("sys.modules", {
        "vram_calculator": vram_mock,
        "gpu_monitor": gpu_mock,
    })
    patcher.start()

    spec.loader.exec_module(serve_mod)
    sys.modules["dash_serve"] = serve_mod

    import http.server

    handler = serve_mod.MyHTTPRequestHandler
    httpd = http.server.HTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    # Wait up to 2 s for server to accept connections
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.05)

    yield base, serve_mod

    httpd.shutdown()
    httpd.server_close()
    patcher.stop()
    sys.modules.pop("dash_serve", None)


# ---------------------------------------------------------------------------
# /api/vram-info
# ---------------------------------------------------------------------------

class TestVramInfoEndpoint:
    def test_returns_200(self, dashboard_server):
        base, _ = dashboard_server
        status, _ = _get(f"{base}/api/vram-info?model=test&lora_rank=16")
        assert status == 200

    def test_returns_json(self, dashboard_server):
        base, _ = dashboard_server
        _, body = _get(f"{base}/api/vram-info?model=test&lora_rank=16")
        data = json.loads(body)
        assert isinstance(data, dict)

    def test_contains_expected_keys(self, dashboard_server):
        base, _ = dashboard_server
        _, body = _get(f"{base}/api/vram-info?model=test&lora_rank=16")
        data = json.loads(body)
        for key in ("available", "safe_batch_size"):
            assert key in data, f"Missing key: {key}"

    def test_default_lora_rank(self, dashboard_server):
        """Endpoint should not 500 when lora_rank is omitted."""
        base, _ = dashboard_server
        status, _ = _get(f"{base}/api/vram-info?model=llama-7b")
        assert status == 200

    def test_no_gpu_path(self, dashboard_server):
        """When vram_calculator returns available=False, endpoint still returns 200 JSON."""
        base, serve_mod = dashboard_server
        no_gpu = {
            "available": False,
            "error": "No GPU detected",
            "safe_batch_size": 1,
            "recommendation": "Use CPU training.",
        }
        with patch.object(
            serve_mod, "calculate_safe_batch_size", return_value=no_gpu
        ):
            status, body = _get(f"{base}/api/vram-info?model=test&lora_rank=8")
        assert status == 200
        data = json.loads(body)
        assert data["available"] is False
        assert data["safe_batch_size"] == 1


# ---------------------------------------------------------------------------
# /api/status
# ---------------------------------------------------------------------------

class TestStatusEndpoint:
    def test_returns_200_or_404(self, dashboard_server):
        """Either a real status is served, or the route 404s — never 5xx."""
        base, _ = dashboard_server
        status, _ = _get(f"{base}/api/status")
        assert status in (200, 404)

    def test_json_on_200(self, dashboard_server):
        base, _ = dashboard_server
        status, body = _get(f"{base}/api/status")
        if status == 200:
            data = json.loads(body)
            assert isinstance(data, (dict, list))


# ---------------------------------------------------------------------------
# Static file serving
# ---------------------------------------------------------------------------

class TestStaticServing:
    def test_root_returns_html(self, dashboard_server):
        """GET / should return HTML (consolidated.html)."""
        base, _ = dashboard_server
        status, body = _get(f"{base}/")
        assert status == 200
        assert b"<!DOCTYPE html>" in body or b"<html" in body

    def test_nonexistent_path_returns_404(self, dashboard_server):
        base, _ = dashboard_server
        status, _ = _get(f"{base}/no-such-route-xyz")
        assert status == 404
