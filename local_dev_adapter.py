"""
Local Developer Adapter for Azure Functions endpoints

This tiny adapter lets you run selected Azure Functions handlers locally without
needing the Azure Functions Core Tools host. It's intentionally small and only
exposes the `/api/ai/status` endpoint used by the repo for health checks.

Usage:
  # Run server on port 7071 (default)
  python local_dev_adapter.py

Design notes:
- Imports the `function_app` module and calls `ai_status()` directly.
- Uses Flask when available, but falls back to a stdlib HTTP server so strict
    integration smoke checks can run in minimal Python environments.
"""

from __future__ import annotations

import json
import logging
import sys
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from flask import Flask, Response, make_response

    HAS_FLASK = True
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal envs
    Flask = None  # type: ignore[assignment]
    Response = Any  # type: ignore[assignment]
    make_response = None  # type: ignore[assignment]
    HAS_FLASK = False

# Ensure repo modules are importable when running from the repo root
repo_root = Path(__file__).resolve().parent
# Make sure common src paths are on sys.path BEFORE importing function_app
# function_app imports modules like token_utils at module-import time, so we
# must ensure those directories are available.
sys.path.insert(0, str(repo_root / "ai-projects" / "chat-cli" / "src"))
sys.path.insert(0, str(repo_root / "ai-projects" / "quantum-ml" / "src"))
sys.path.insert(0, str(repo_root / "scripts"))
sys.path.insert(0, str(repo_root))

logger = logging.getLogger(__name__)

# Attempt to import the real function_app and the azure.functions HttpResponse
# type. If azure.functions isn't available in the current dev/test environment
# (common in lightweight test containers), create a minimal local shim so that
# function_app can import and its ai_status handler can be invoked. The shim
# implements only what the local adapter needs: FunctionApp decorator, simple
# HttpRequest/HttpResponse types and an AuthLevel constant.
try:
    from azure.functions import HttpResponse as AzureHttpResponse

    import function_app
except ModuleNotFoundError as e:
    # Provide a lightweight shim for azure.functions when it's not installed.
    if "azure.functions" in str(e):
        logger.debug(
            "azure.functions not found; installing lightweight shim for local dev adapter"
        )
        fake_mod = types.ModuleType("azure.functions")

        class AuthLevel:
            ANONYMOUS = "ANONYMOUS"

        class HttpRequest:  # minimal request placeholder with helpful helpers
            def __init__(
                self,
                method: str = "GET",
                url: str = "/",
                params: dict | None = None,
                headers: dict | None = None,
                body: Any = None,
                route_params: dict | None = None,
            ):
                self.method = method
                self.url = url
                self.params = params or {}
                self.route_params = route_params or {}
                # Normalize headers to lowercase keys for convenience
                self.headers = {k.lower(): v for k, v in (headers or {}).items()}
                # Normalize body to bytes internally
                if isinstance(body, bytes):
                    self._body = body
                elif isinstance(body, str):
                    self._body = body.encode("utf-8")
                elif body is None:
                    self._body = b""
                else:
                    try:
                        self._body = json.dumps(body).encode("utf-8")
                    except Exception:
                        self._body = str(body).encode("utf-8")
                self._json_cache = None

            def get_body(self) -> bytes:
                return self._body

            def get_json(self, force: bool = False):
                """Parse and return JSON body. Raises ValueError on parse failure.

                Args:
                    force: If True, re-parse even if cached.
                """
                if self._json_cache is not None and not force:
                    return self._json_cache
                try:
                    text = self._body.decode("utf-8")
                    parsed = json.loads(text) if text else {}
                    self._json_cache = parsed
                    return parsed
                except Exception as e:
                    logger.debug("HttpRequest.get_json failed: %s", e)
                    raise ValueError("Failed to parse JSON body") from e

        class HttpResponse:
            def __init__(
                self,
                body=b"",
                status_code: int = 200,
                mimetype: str | None = None,
                headers: dict | None = None,
            ):
                # Normalize to bytes to match real azure HttpResponse.get_body()
                if isinstance(body, str):
                    self._body = body.encode("utf-8")
                elif isinstance(body, bytes):
                    self._body = body
                else:
                    try:
                        self._body = json.dumps(body).encode("utf-8")
                    except Exception:
                        self._body = str(body).encode("utf-8")
                self.status_code = status_code
                self.mimetype = mimetype
                self.headers = headers or {}

            def get_body(self):
                return self._body

        class FunctionApp:
            def __init__(self):
                self._routes = []

            def route(self, *args, **kwargs):
                def decorator(fn):
                    # attach route metadata but otherwise return the original function
                    try:
                        fn.__qai_route__ = {"args": args, "kwargs": kwargs}
                    except Exception:
                        pass
                    return fn

                return decorator

        fake_mod.AuthLevel = AuthLevel
        fake_mod.HttpRequest = HttpRequest
        fake_mod.HttpResponse = HttpResponse
        fake_mod.FunctionApp = FunctionApp

        # Insert into sys.modules so import statements in function_app succeed
        sys.modules.setdefault("azure.functions", fake_mod)

        # Now import function_app and reference the shim's HttpResponse
        import function_app

        AzureHttpResponse = fake_mod.HttpResponse
    else:
        raise


def _azure_response_parts(
    resp: AzureHttpResponse,
) -> Tuple[bytes, int, Optional[str], Dict[str, Any]]:
    """Extract body/status/mimetype/headers from azure.functions.HttpResponse."""
    body_bytes = resp.get_body()
    # Ensure bytes
    if not isinstance(body_bytes, (bytes, bytearray)):
        try:
            body_bytes = str(body_bytes).encode("utf-8")
        except Exception:
            body_bytes = b""

    mimetype = getattr(resp, "mimetype", None)
    headers = dict(getattr(resp, "headers", None) or {})
    if not mimetype:
        content_type = headers.get("Content-Type") or headers.get("content-type")
        if content_type:
            mimetype = content_type
        else:
            # Heuristic: if body decodes to JSON, set application/json
            try:
                json.loads(body_bytes.decode("utf-8"))
                mimetype = "application/json"
            except Exception:
                mimetype = None

    status_code = int(getattr(resp, "status_code", 200))
    return bytes(body_bytes), status_code, mimetype, headers


def _azure_to_flask(resp: AzureHttpResponse) -> Response:
    """Convert an azure.functions.HttpResponse to a Flask Response."""
    body_bytes, status_code, mimetype, headers = _azure_response_parts(resp)

    flask_resp = make_response(body_bytes, status_code)
    if mimetype:
        flask_resp.mimetype = mimetype

    # Copy headers
    try:
        for k, v in headers.items():
            flask_resp.headers[k] = v
    except Exception:
        # best-effort fallback for unexpected header shapes
        logger.debug(
            "Unexpected header shape when converting azure HttpResponse to Flask Response"
        )

    return flask_resp


def get_ai_status_response() -> Tuple[Response, int]:
    """Call the function_app.ai_status handler and return a Flask response.

    ai_status() does not depend on incoming request data so we just call it
    with a lightweight HttpRequest and adapt the returned azure.functions.HttpResponse.
    """
    # Provide a minimal HttpRequest instance for greater compatibility with
    # handlers that expect `req` to be an azure.functions.HttpRequest.
    try:
        req = getattr(function_app, "HttpRequest", None)
    except Exception:
        req = None

    if req is None or not hasattr(req, "get_body"):
        # Use shim's HttpRequest if available in sys.modules
        try:
            from azure.functions import \
                HttpRequest as ShimHttpRequest  # type: ignore

            fake_req = ShimHttpRequest(method="GET", url="/api/ai/status")
        except Exception:
            fake_req = None
    else:
        fake_req = req(method="GET", url="/api/ai/status")

    azure_resp = function_app.ai_status(fake_req)
    flask_resp = _azure_to_flask(azure_resp)
    return flask_resp


def get_ai_status_parts() -> Tuple[bytes, int, Optional[str], Dict[str, Any]]:
    """Return endpoint response components for non-Flask fallback servers."""
    try:
        req = getattr(function_app, "HttpRequest", None)
    except Exception:
        req = None

    if req is None or not hasattr(req, "get_body"):
        try:
            from azure.functions import \
                HttpRequest as ShimHttpRequest  # type: ignore

            fake_req = ShimHttpRequest(method="GET", url="/api/ai/status")
        except Exception:
            fake_req = None
    else:
        fake_req = req(method="GET", url="/api/ai/status")

    azure_resp = function_app.ai_status(fake_req)
    return _azure_response_parts(azure_resp)


def create_app() -> Flask:
    if not HAS_FLASK:
        raise RuntimeError("Flask is not installed")

    app = Flask(__name__)

    @app.get("/api/ai/status")
    def ai_status_route():
        return get_ai_status_response()

    return app


def run_stdlib_server(host: str = "0.0.0.0", port: int = 7071) -> None:
    """Serve /api/ai/status using stdlib HTTP server (no Flask dependency)."""

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path.split("?", 1)[0] != "/api/ai/status":
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not found"}')
                return

            try:
                body, status_code, mimetype, headers = get_ai_status_parts()
            except Exception as exc:  # noqa: BLE001
                logger.exception("Failed to build /api/ai/status response: %s", exc)
                body = json.dumps({"error": str(exc)}).encode("utf-8")
                status_code = 500
                mimetype = "application/json"
                headers = {}

            self.send_response(status_code)
            sent_content_type = False
            if mimetype:
                self.send_header("Content-Type", str(mimetype))
                sent_content_type = True

            for key, value in headers.items():
                key_str = str(key)
                if key_str.lower() == "content-type":
                    if sent_content_type:
                        continue
                    sent_content_type = True
                self.send_header(key_str, str(value))

            if not sent_content_type:
                self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, _fmt: str, *_args: Any) -> None:
            return

    server = ThreadingHTTPServer((host, port), _Handler)
    logger.info("Starting stdlib local dev adapter on http://%s:%s", host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    print("Starting local dev adapter for /api/ai/status on http://0.0.0.0:7071")
    # Use port 7071 to match Functions local host default
    if HAS_FLASK:
        app = create_app()
        app.run(host="0.0.0.0", port=7071, debug=False)
    else:
        run_stdlib_server(host="0.0.0.0", port=7071)
