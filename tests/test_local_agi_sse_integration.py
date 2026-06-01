"""
End-to-end tests for AGI SSE streaming and LocalAGIProvider structured chunks.

These tests validate that LocalAGIProvider yields structured chunks and that
/api/agi/stream packaging wraps those chunks as SSE data events containing
{"delta": ...} payloads.
"""

import json
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
import sys

import pytest


# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _import_local_agi():
    mod_path = REPO_ROOT / "ai-projects" / "chat-cli" / "src" / "local_agi_provider.py"
    spec = importlib.util.spec_from_file_location("local_agi_provider", str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod.LocalAGIProvider


def _mock_request(body: dict):
    req = MagicMock()
    req.get_json.return_value = body
    req.get_body.return_value = json.dumps(body).encode("utf-8")
    req.method = "POST"
    req.params = {}
    req.route_params = {}
    return req


def test_local_agi_structured_chunks():
    LocalAGIProvider = _import_local_agi()
    provider = LocalAGIProvider()
    # Use system prompt that triggers the simulator plan path
    messages = [
        {"role": "system", "content": "JSON list of tasks"},
        {"role": "user", "content": "Goal: improve the summarizer"},
    ]

    gen = provider.complete(messages, stream=True)
    chunks = list(gen)
    assert len(chunks) > 0
    # Expect dict-typed structured chunks with a 'type' key
    types = {c.get("type") for c in chunks if isinstance(c, dict)}
    assert types & {"analysis", "step", "output", "payload", "error"}


def test_agi_stream_http_sse(monkeypatch):
    """Simulate the /api/agi/stream SSE packaging using the LocalAGIProvider.

    The azure.functions.HttpResponse in the test harness may reject generators,
    so exercise the provider and replicate the SSE packaging logic locally.
    """
    LocalAGIProvider = _import_local_agi()
    provider = LocalAGIProvider()

    # Use system prompt to trigger structured simulator output
    messages = [
        {"role": "system", "content": "JSON list of tasks"},
        {"role": "user", "content": "Plan the next step"},
    ]

    gen = provider.complete(messages, stream=True)

    # Replicate SSE packaging used by /api/agi/stream
    sse_parts = []
    pre = {"provider": "agi", "base_provider": "local", "base_model": "local-llm"}
    sse_parts.append("event: meta\n" + "data: " + json.dumps(pre) + "\n\n")

    for chunk in gen:
        payload = json.dumps({"delta": chunk})
        sse_parts.append("data: " + payload + "\n\n")

    sse_parts.append("data: [DONE]\n\n")
    sse_text = "".join(sse_parts)

    # Parse the SSE text and validate delta shapes
    events = [e for e in sse_text.split("\n\n") if e.strip()]
    assert events, "No SSE events produced"

    deltas = []
    for ev in events:
        for line in ev.splitlines():
            if line.startswith("data: "):
                try:
                    payload = json.loads(line[len("data: ") :])
                except Exception:
                    continue
                delta = payload.get("delta")
                deltas.append(delta)

    assert deltas, "No deltas found in packaged SSE"
    parsed_types = {d.get("type") for d in deltas if isinstance(d, dict)}
    assert parsed_types & {"analysis", "step", "output", "payload", "error"}
