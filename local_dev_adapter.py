"""Local Developer Adapter for Azure Functions endpoints.

This tiny adapter lets you run selected Azure Functions handlers
locally without needing the Azure Functions Core Tools host.
It exposes the status, routes, AGI, and chat-web static endpoints
used by local health checks.

Usage:
  python local_dev_adapter.py
  python local_dev_adapter.py --port 7072
  python local_dev_adapter.py --check

Design notes:
- Imports the `function_app` module and calls `ai_status()` directly.
- Uses Flask when available, but falls back to a stdlib HTTP server so strict
    integration smoke checks can run in minimal Python environments.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import types
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from shared.local_settings import apply_local_settings

try:
    _load_env_loader = import_module("dotenv").load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    _load_env_loader = None

flask_app_cls: Any | None = None
flask_make_response: Callable[..., Any] | None = None
flask_request: Any | None = None
_flask_cors: Any | None = None
has_flask = False

try:
    from flask import Flask as _flask_app_cls  # type: ignore
    from flask import make_response as _flask_make_response  # type: ignore
    from flask import request as _flask_request  # type: ignore
    from flask_cors import CORS as _flask_cors  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal envs
    pass
else:
    flask_app_cls = _flask_app_cls
    flask_make_response = _flask_make_response
    flask_request = _flask_request
    has_flask = True

logger = logging.getLogger(__name__)

JsonValue = dict[str, Any] | list[Any] | str | int | float | bool | None


def _apply_cors_headers(
    handler: BaseHTTPRequestHandler,
) -> None:
    """Apply CORS headers for local development."""
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")


def _safe_log_label(value: str) -> str:
    """Strip control chars from user-influenced values before logging."""
    return str(value).split("?", 1)[0].replace("\n", "").replace("\r", "")[:120]


def _coerce_bytes(value: Any) -> bytes:
    """Convert arbitrary local adapter payloads into bytes."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8")
    if value is None:
        return b""
    try:
        return json.dumps(value).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return str(value).encode("utf-8")


# Ensure repo modules are importable when running from the repo root.
repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "ai-projects" / "chat-cli" / "src"))
sys.path.insert(0, str(repo_root / "ai-projects" / "quantum-ml" / "src"))
sys.path.insert(0, str(repo_root / "scripts"))
sys.path.insert(0, str(repo_root))


def _load_env_file() -> None:
    """Load local dev settings early so provider selection sees them."""
    apply_local_settings()

    env_file = repo_root / ".env"
    if not env_file.exists():
        return

    if _load_env_loader is not None:
        _load_env_loader(env_file, override=False)
        return

    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = val


def _install_azure_functions_shim() -> Any:  # pylint: disable=too-many-statements
    """Install a lightweight azure.functions shim for local development."""
    logger.debug("azure.functions not found; installing lightweight shim for local dev adapter")
    fake_mod: Any = types.ModuleType("azure.functions")

    class AuthLevel:
        ANONYMOUS = "ANONYMOUS"

    class HttpRequest:  # pylint: disable=too-few-public-methods
        """Minimal request placeholder with helpful helpers."""

        def __init__(self, **kwargs: Any):
            """Build a request-like object from keyword arguments."""
            self.method = kwargs.get("method", "GET")
            self.url = kwargs.get("url", "/")
            self.params = dict(kwargs.get("params") or {})
            self.route_params = dict(kwargs.get("route_params") or {})
            self.headers = {k.lower(): v for k, v in dict(kwargs.get("headers") or {}).items()}
            self._body = _coerce_bytes(kwargs.get("body"))
            self._json_cache: JsonValue | None = None

        def get_body(self) -> bytes:
            """Return the request body bytes."""
            return self._body

        def get_json(self, force: bool = False) -> JsonValue:
            """Parse and cache the body as JSON."""
            if self._json_cache is not None and not force:
                return self._json_cache
            try:
                text = self._body.decode("utf-8")
                parsed = cast(JsonValue, json.loads(text) if text else {})
                self._json_cache = parsed
                return parsed
            except (
                AttributeError,
                TypeError,
                UnicodeDecodeError,
                json.JSONDecodeError,
            ) as e:
                logger.debug("HttpRequest.get_json failed: %s", e)
                raise ValueError("Failed to parse JSON body") from e

    class HttpResponse:  # pylint: disable=too-few-public-methods
        """Minimal response placeholder with body and headers."""

        def __init__(self, **kwargs: Any):
            """Build a response-like object from keyword arguments."""
            self._body = _coerce_bytes(kwargs.get("body", b""))
            self.status_code = int(kwargs.get("status_code", 200))
            self.mimetype = kwargs.get("mimetype")
            self.headers = dict(kwargs.get("headers") or {})

        def get_body(self):
            """Return the response body bytes."""
            return self._body

    class FunctionApp:  # pylint: disable=too-few-public-methods
        """Minimal app container that preserves route metadata."""

        def __init__(self):
            self._routes = []

        def route(
            self,
            *args: Any,
            **kwargs: Any,
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            """Decorator placeholder that records route metadata."""

            def decorator(
                fn: Callable[..., Any],
            ) -> Callable[..., Any]:
                try:
                    fn.__qai_route__ = {"args": args, "kwargs": kwargs}
                except AttributeError as exc:
                    logger.debug("Failed setting __qai_route__: %s", exc)
                return fn

            return decorator

    fake_mod.AuthLevel = AuthLevel
    fake_mod.HttpRequest = HttpRequest
    fake_mod.HttpResponse = HttpResponse
    fake_mod.FunctionApp = FunctionApp

    azure_pkg: Any = sys.modules.setdefault("azure", types.ModuleType("azure"))
    if not hasattr(azure_pkg, "__path__"):
        azure_pkg.__path__ = []  # type: ignore[attr-defined]
    azure_pkg.functions = fake_mod
    sys.modules["azure.functions"] = fake_mod
    return HttpResponse


_load_env_file()

try:
    import_module("azure.functions")
except ModuleNotFoundError:
    _install_azure_functions_shim()

# Import function_app only after sys.path, env, and shim setup.


def _get_function_app() -> Any:
    """Import function_app after sys.path, env, and azure shim setup."""
    try:
        return import_module("function_app")
    except (ModuleNotFoundError, SyntaxError) as exc:
        raise RuntimeError("Failed to import function_app") from exc


def _azure_response_parts(
    resp: Any,
) -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Extract body/status/mimetype/headers from an Azure HTTP response."""
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


def _azure_to_flask(resp: Any) -> Any:
    """Convert an azure.functions.HttpResponse to a Flask Response."""
    body_bytes, status_code, mimetype, headers = _azure_response_parts(resp)

    assert flask_make_response is not None
    flask_resp = flask_make_response(body_bytes, status_code)
    if mimetype:
        flask_resp.mimetype = mimetype

    # Copy headers
    try:
        for k, v in headers.items():
            flask_resp.headers[k] = v
    except Exception:
        # best-effort fallback for unexpected header shapes
        logger.debug("Unexpected header shape when converting azure HttpResponse to Flask Response")

    return flask_resp


def _build_local_http_request(
    *,
    method: str,
    url: str,
    body_bytes: bytes,
    headers: dict[str, str],
) -> Any:
    """Create a local shim HttpRequest for handlers that need one."""
    # pylint: disable=import-outside-toplevel
    try:
        from azure.functions import HttpRequest as ShimHttpRequest  # type: ignore
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("No HttpRequest implementation available for local dev adapter") from exc

    req_factory = cast(Callable[..., Any], ShimHttpRequest)
    try:
        return req_factory(
            method=method,
            url=url,
            headers=headers,
            params={},
            route_params={},
            body=body_bytes,
        )
    except TypeError:
        return req_factory(method=method, url=url, body=body_bytes)


def _call_function_handler(
    handler_name: str,
    method: str,
    url: str,
    *,
    body: Any = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Invoke a function_app HTTP handler with a minimal HttpRequest."""
    function_app = _get_function_app()
    handler = getattr(function_app, handler_name, None)
    if handler is None:
        raise RuntimeError(f"function_app.{handler_name} is not available")

    req_cls = getattr(function_app, "HttpRequest", None)
    body_bytes = _coerce_bytes(body)

    request_headers = dict(headers or {})
    if body is not None and not any(k.lower() == "content-type" for k in request_headers):
        request_headers["Content-Type"] = "application/json"

    if isinstance(req_cls, type) or callable(req_cls):
        req_factory = cast(Callable[..., Any], req_cls)
        try:
            fake_req = req_factory(
                method=method,
                url=url,
                headers=request_headers,
                params={},
                route_params={},
                body=body_bytes,
            )
        except TypeError:
            fake_req = req_factory(method=method, url=url, body=body_bytes)
    else:
        fake_req = _build_local_http_request(
            method=method,
            url=url,
            body_bytes=body_bytes,
            headers=request_headers,
        )

    return handler(fake_req)


def _json_body(payload: dict[str, Any]) -> bytes:
    """Encode a small JSON payload for local handler probes."""
    return json.dumps(payload).encode("utf-8")


def _call_function_parts(
    handler_name: str,
    method: str,
    url: str,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
) -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Call a function handler and return response components."""
    azure_resp = _call_function_handler(
        handler_name,
        method,
        url,
        body=body,
        headers=headers,
    )
    return _azure_response_parts(azure_resp)


def get_ai_status_response() -> Any:
    """Call the function_app.ai_status handler and return a Flask response."""
    azure_resp = _call_function_handler("ai_status", "GET", "/api/ai/status")
    return _azure_to_flask(azure_resp)


def get_agi_status_response() -> Any:
    """Call function_app.agi_status and return a Flask response."""
    azure_resp = _call_function_handler("agi_status", "GET", "/api/agi/status")
    return _azure_to_flask(azure_resp)


def get_ai_routes_response() -> Any:
    """Call function_app.ai_routes and return a Flask response."""
    azure_resp = _call_function_handler("ai_routes", "GET", "/api/ai/routes")
    return _azure_to_flask(azure_resp)


def get_agi_analyze_response(
    payload: dict[str, Any],
) -> Any:
    """Call function_app.agi_analyze and return a Flask response."""
    azure_resp = _call_function_handler(
        "agi_analyze",
        "POST",
        "/api/agi/analyze",
        body=payload,
    )
    return _azure_to_flask(azure_resp)


def get_agi_reason_response(
    payload: dict[str, Any],
) -> Any:
    """Call function_app.agi_reason and return a Flask response."""
    azure_resp = _call_function_handler(
        "agi_reason",
        "POST",
        "/api/agi/reason",
        body=payload,
    )
    return _azure_to_flask(azure_resp)


def get_agi_stream_response(
    payload: dict[str, Any],
) -> Any:
    """Call function_app.agi_stream and return a Flask response."""
    azure_resp = _call_function_handler(
        "agi_stream",
        "POST",
        "/api/agi/stream",
        body=payload,
    )
    return _azure_to_flask(azure_resp)


def get_agi_stream_utils_response() -> Any:
    """Call function_app.serve_agi_stream_utils and return a Flask response."""
    azure_resp = _call_function_handler(
        "serve_agi_stream_utils",
        "GET",
        "/api/chat-web/static/agi_stream_utils.js",
    )
    return _azure_to_flask(azure_resp)


def _agi_json_response(handler_name: str, url: str) -> Any:
    """Call a JSON AGI POST handler with the active Flask request body."""
    assert flask_request is not None
    azure_resp = _call_function_handler(
        handler_name,
        "POST",
        url,
        body=flask_request.get_data() or b"{}",
        headers={
            "Content-Type": flask_request.headers.get(
                "Content-Type",
                "application/json",
            )
        },
    )
    return _azure_to_flask(azure_resp)


def get_ai_status_parts() -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return endpoint response components for non-Flask fallback servers."""
    return _call_function_parts("ai_status", "GET", "/api/ai/status")


def get_agi_status_parts() -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return /api/agi/status response components for non-Flask servers."""
    return _call_function_parts("agi_status", "GET", "/api/agi/status")


def get_ai_routes_parts() -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return /api/ai/routes response components for non-Flask servers."""
    return _call_function_parts("ai_routes", "GET", "/api/ai/routes")


def get_agi_stream_utils_parts() -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return AGI stream utility asset parts for non-Flask servers."""
    return _call_function_parts(
        "serve_agi_stream_utils",
        "GET",
        "/api/chat-web/static/agi_stream_utils.js",
    )


def get_agi_analyze_parts(
    body: bytes,
) -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return /api/agi/analyze response components for non-Flask servers."""
    return _call_function_parts(
        "agi_analyze",
        "POST",
        "/api/agi/analyze",
        body=body,
        headers={"Content-Type": "application/json"},
    )


def get_agi_reason_parts(
    body: bytes,
) -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return /api/agi/reason response components for non-Flask servers."""
    return _call_function_parts(
        "agi_reason",
        "POST",
        "/api/agi/reason",
        body=body,
        headers={"Content-Type": "application/json"},
    )


def get_agi_stream_parts(
    body: bytes,
) -> tuple[bytes, int, str | None, dict[str, Any]]:
    """Return /api/agi/stream response components for non-Flask servers."""
    return _call_function_parts(
        "agi_stream",
        "POST",
        "/api/agi/stream",
        body=body,
        headers={"Content-Type": "application/json"},
    )


def create_app() -> Any:
    """Create the Flask app when Flask is available."""
    if not has_flask:
        raise RuntimeError("Flask is not installed")
    assert flask_app_cls is not None

    app = flask_app_cls(__name__)

    # Enable CORS for local development
    try:
        _flask_cors(app, resources={r"/api/*": {"origins": "*"}})
    except Exception:  # pragma: no cover
        logger.debug("CORS setup failed; continuing without CORS")

    @app.get("/api/ai/status")
    def ai_status_route():  # pyright: ignore[reportUnusedFunction]
        return get_ai_status_response()

    @app.get("/api/agi/status")
    def agi_status_route():  # pyright: ignore[reportUnusedFunction]
        return get_agi_status_response()

    @app.get("/api/ai/routes")
    def ai_routes_route():  # pyright: ignore[reportUnusedFunction]
        return get_ai_routes_response()

    @app.post("/api/agi/analyze")
    def agi_analyze_route():  # pyright: ignore[reportUnusedFunction]
        return _agi_json_response("agi_analyze", "/api/agi/analyze")

    @app.post("/api/agi/reason")
    def agi_reason_route():  # pyright: ignore[reportUnusedFunction]
        return _agi_json_response("agi_reason", "/api/agi/reason")

    @app.post("/api/agi/stream")
    def agi_stream_route():  # pyright: ignore[reportUnusedFunction]
        return _agi_json_response("agi_stream", "/api/agi/stream")

    @app.get("/api/chat-web/static/agi_stream_utils.js")
    def agi_stream_utils_route():  # pyright: ignore[reportUnusedFunction]
        return get_agi_stream_utils_response()

    # Aria character endpoints (if available)
    try:

        @app.get("/api/aria/state")
        def aria_state_route():  # pyright: ignore[reportUnusedFunction]
            azure_resp = _call_function_handler("aria_get_state", "GET", "/api/aria/state")
            return _azure_to_flask(azure_resp)

        @app.post("/api/aria/command")
        def aria_command_route():  # pyright: ignore[reportUnusedFunction]
            return _agi_json_response("aria_process_command", "/api/aria/command")

        @app.post("/api/aria/execute")
        def aria_execute_route():  # pyright: ignore[reportUnusedFunction]
            return _agi_json_response("aria_execute_actions", "/api/aria/execute")

        @app.post("/api/aria/object")
        def aria_object_route():  # pyright: ignore[reportUnusedFunction]
            return _agi_json_response("aria_manage_object", "/api/aria/object")

        @app.post("/api/aria/world")
        def aria_world_route():  # pyright: ignore[reportUnusedFunction]
            return _agi_json_response("aria_generate_world", "/api/aria/world")
    except Exception:  # pragma: no cover
        logger.debug("Aria endpoints not available; skipping registration")

    return app


def run_stdlib_server(
    host: str = "0.0.0.0",
    port: int = 7071,
) -> None:  # pylint: disable=too-many-statements
    """Serve selected local Functions endpoints using stdlib HTTP server."""

    class _Handler(BaseHTTPRequestHandler):
        """Request handler for the stdlib fallback server."""

        def _serve_parts(
            self,
            parts_fn: Callable[
                ...,
                tuple[bytes, int, str | None, dict[str, Any]],
            ],
            *,
            request_body: bytes | None = None,
        ) -> None:
            path = self.path.split("?", 1)[0]
            try:
                if request_body is None:
                    resp_body, status_code, mimetype, headers = parts_fn()
                else:
                    resp_body, status_code, mimetype, headers = parts_fn(request_body)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Failed to build %s response: %s",
                    _safe_log_label(path),
                    exc,
                )
                resp_body = json.dumps({"error": str(exc)}).encode("utf-8")
                status_code = 500
                mimetype = "application/json"
                headers = {}

            self.send_response(status_code)
            _apply_cors_headers(self)
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
            self.wfile.write(resp_body)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            route_map = {
                "/api/ai/status": get_ai_status_parts,
                "/api/agi/status": get_agi_status_parts,
                "/api/ai/routes": get_ai_routes_parts,
                "/api/chat-web/static/agi_stream_utils.js": get_agi_stream_utils_parts,
            }

            if path not in route_map:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not found"}')
                return

            self._serve_parts(route_map[path])

        def do_OPTIONS(self) -> None:  # noqa: N802
            """Handle CORS preflight requests."""
            self.send_response(204)
            _apply_cors_headers(self)
            self.end_headers()

        # pylint: disable=invalid-name
        def do_POST(self) -> None:  # noqa: N802
            """Handle POST requests for the supported AGI endpoints."""
            path = self.path.split("?", 1)[0]
            route_map = {
                "/api/agi/analyze": get_agi_analyze_parts,
                "/api/agi/reason": get_agi_reason_parts,
                "/api/agi/stream": get_agi_stream_parts,
            }

            if path not in route_map:
                self.send_response(404)
                _apply_cors_headers(self)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"not found"}')
                return

            length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(length) if length else _json_body({"query": "local dev adapter smoke"})
            self._serve_parts(route_map[path], request_body=body)

        # pylint: disable=arguments-differ
        def log_message(self, fmt: str, *args: Any) -> None:
            """Silence the default HTTP server access log."""
            del fmt, args

    server = ThreadingHTTPServer((host, port), _Handler)
    logger.info(
        "Starting stdlib local dev adapter on http://%s:%s",
        host,
        port,
    )
    try:
        server.serve_forever()
    finally:
        server.server_close()


def check_status_endpoints() -> int:  # pylint: disable=broad-exception-caught
    """Probe adapter handlers without starting an HTTP server."""
    probes = (
        ("GET /api/ai/status", get_ai_status_parts),
        ("GET /api/agi/status", get_agi_status_parts),
        ("GET /api/ai/routes", get_ai_routes_parts),
        (
            "GET /api/chat-web/static/agi_stream_utils.js",
            get_agi_stream_utils_parts,
        ),
        (
            "POST /api/agi/analyze",
            lambda: get_agi_analyze_parts(_json_body({"query": "adapter analyze check"})),
        ),
        (
            "POST /api/agi/reason",
            lambda: get_agi_reason_parts(_json_body({"query": "adapter reason check"})),
        ),
        (
            "POST /api/agi/stream",
            lambda: get_agi_stream_parts(_json_body({"query": "adapter stream check"})),
        ),
    )
    errors: list[str] = []
    for label, parts_fn in probes:
        try:
            resp_body, status_code, mimetype, headers = parts_fn()
            if status_code != 200:
                errors.append(f"{label}: http {status_code}")
                logger.warning("%s returned %d", label, status_code)
            else:
                logger.debug("%s: ok (%d bytes, %s)", label, len(resp_body), mimetype or "no mimetype")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{label}: {exc}")
            logger.error("%s failed: %s", label, exc, exc_info=True)

    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1

    print("ok: local adapter strict smoke endpoints")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse local adapter CLI arguments."""

    default_host = os.getenv("LOCAL_DEV_ADAPTER_HOST", "0.0.0.0")
    default_port = int(os.getenv("LOCAL_DEV_ADAPTER_PORT", "7071"))

    parser = argparse.ArgumentParser(
        description=(
            "Run the local dev adapter for GET /api/ai/status "
            "and GET /api/agi/status "
            "without Azure Functions Core Tools."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python local_dev_adapter.py\n"
            "  python local_dev_adapter.py --port 7072\n"
            "  python local_dev_adapter.py --check\n"
            "  curl -s http://localhost:7071/api/agi/status | jq .backends\n"
        ),
    )
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Bind host for the local adapter (default: {default_host}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Bind port for the local adapter (default: {default_port}).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Probe local adapter handlers and exit (no server).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Run the local dev adapter CLI."""
    args = parse_args(argv)
    if args.check:
        raise SystemExit(check_status_endpoints())

    print(f"Starting local dev adapter for /api/ai/status and /api/agi/status on http://{args.host}:{args.port}")

    if has_flask:
        app = create_app()
        app.run(host=args.host, port=args.port, debug=False)
    else:
        run_stdlib_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
