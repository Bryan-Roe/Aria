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
- Converts the returned `azure.functions.HttpResponse` into a Flask response.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from flask import Flask, make_response, Response
import types

# Ensure repo modules are importable when running from the repo root
repo_root = Path(__file__).resolve().parent
# Make sure common src paths are on sys.path BEFORE importing function_app
# function_app imports modules like token_utils at module-import time, so we
# must ensure those directories are available.
sys.path.insert(0, str(repo_root / "talk-to-ai" / "src"))
sys.path.insert(0, str(repo_root / "quantum-ai" / "src"))
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
    import function_app
    from azure.functions import HttpResponse as AzureHttpResponse
except ModuleNotFoundError as e:
    # Provide a lightweight shim for azure.functions when it's not installed.
    if "azure.functions" in str(e):
        logger.debug(
            "azure.functions not found; installing lightweight shim for local dev adapter")
        fake_mod = types.ModuleType("azure.functions")

        class AuthLevel:
            ANONYMOUS = "ANONYMOUS"

        class HttpRequest:  # minimal request placeholder with helpful helpers
            def __init__(self, method: str = "GET", url: str = "/", params: dict | None = None, headers: dict | None = None, body: Any = None, route_params: dict | None = None):
                self.method = method
                self.url = url
                self.params = params or {}
                self.route_params = route_params or {}
                # Normalize headers to lowercase keys for convenience
                self.headers = {k.lower(): v for k, v in (
                    headers or {}).items()}
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
            def __init__(self, body=b"", status_code: int = 200, mimetype: str | None = None, headers: dict | None = None):
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


def _azure_to_flask(resp: AzureHttpResponse) -> Response:
    """Convert an azure.functions.HttpResponse to a Flask Response.

    We assert resp is an instance of AzureHttpResponse and extract body, status
    code, mimetype and headers.
    """
    body_bytes = resp.get_body()
    # Ensure bytes
    if not isinstance(body_bytes, (bytes, bytearray)):
        try:
            body_bytes = str(body_bytes).encode("utf-8")
        except Exception:
            body_bytes = b""

    # Try to detect JSON content-type if not provided
    mimetype = getattr(resp, "mimetype", None)
    headers = getattr(resp, "headers", None) or {}
    if not mimetype:
        content_type = headers.get(
            "Content-Type") or headers.get("content-type")
        if content_type:
            mimetype = content_type
        else:
            # Heuristic: if body decodes to JSON, set application/json
            try:
                json.loads(body_bytes.decode("utf-8"))
                mimetype = "application/json"
            except Exception:
                mimetype = None

    flask_resp = make_response(body_bytes, getattr(resp, "status_code", 200))
    if mimetype:
        flask_resp.mimetype = mimetype

    # Copy headers
    try:
        for k, v in headers.items():
            flask_resp.headers[k] = v
    except Exception:
        # best-effort fallback for unexpected header shapes
        logger.debug(
            "Unexpected header shape when converting azure HttpResponse to Flask Response")

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
            from azure.functions import HttpRequest as ShimHttpRequest  # type: ignore
            fake_req = ShimHttpRequest(method="GET", url="/api/ai/status")
        except Exception:
            fake_req = None
    else:
        fake_req = req(method="GET", url="/api/ai/status")

    azure_resp = function_app.ai_status(fake_req)
    flask_resp = _azure_to_flask(azure_resp)
    return flask_resp


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/api/ai/status")
    def ai_status_route():
        return get_ai_status_response()

    return app


if __name__ == "__main__":
    app = create_app()
    print("Starting local dev adapter for /api/ai/status on http://0.0.0.0:7071")
    # Use port 7071 to match Functions local host default
    app.run(host="0.0.0.0", port=7071, debug=False)
