"""
Smoke tests for function_app.py API endpoints.

Uses unittest.mock to mock Azure Functions HttpRequest objects
and validates response shapes, status codes, and error handling
without running a live server.
"""

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure project root on path
REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helper: build a mock Azure Functions HttpRequest
# ---------------------------------------------------------------------------
def _mock_request(
    method: str = "GET",
    body: dict | None = None,
    params: dict | None = None,
    route_params: dict | None = None,
) -> MagicMock:
    """Create a lightweight mock of azure.functions.HttpRequest."""
    req = MagicMock()
    req.method = method
    req.params = params or {}
    req.route_params = route_params or {}

    if body is not None:
        raw = json.dumps(body).encode("utf-8")
        req.get_json.return_value = body
        req.get_body.return_value = raw
    else:
        req.get_json.side_effect = ValueError("No JSON body")
        req.get_body.return_value = b""

    return req


def _install_fake_quantum_trainer_module(
    monkeypatch: pytest.MonkeyPatch,
    capture: dict | None = None,
    generate_tokens: list[int] | None = None,
):
    """Install a fake quantum_llm_trainer module for endpoint tests.

    This keeps endpoint tests fast and deterministic without loading heavyweight
    model dependencies.
    """
    module = types.ModuleType("quantum_llm_trainer")
    module.QUANTUM_AVAILABLE = True

    try:
        import torch
    except Exception:
        torch = None

    class _FakeModel:
        def __init__(self, tokens: list[int]):
            self._tokens = tokens

        def generate(self, prompt_ids, max_new_tokens: int, temperature: float, top_k: int):
            if capture is not None:
                capture["generate_kwargs"] = {
                    "max_new_tokens": max_new_tokens,
                    "temperature": temperature,
                    "top_k": top_k,
                }
                if hasattr(prompt_ids, "shape"):
                    capture["prompt_shape"] = tuple(prompt_ids.shape)
                else:
                    capture["prompt_shape"] = (
                        len(prompt_ids),
                        len(prompt_ids[0]) if prompt_ids else 0,
                    )

            if torch is not None:
                return torch.tensor([self._tokens], dtype=torch.long)
            return [self._tokens]

    class QuantumEnhancedLLMTrainer:
        def __init__(self, config):
            if capture is not None:
                capture["init_config"] = dict(config)
            self.model_config = {"vocab_size": 256}
            self.model = _FakeModel(generate_tokens or [72, 105, 33])  # "Hi!"

        def train_with_quantum_enhancement(self, dataset_path, output_dir, epochs, model=None):
            if capture is not None:
                capture["train_args"] = {
                    "dataset_path": dataset_path,
                    "output_dir": output_dir,
                    "epochs": epochs,
                    "model": model,
                }
            return {
                "status": "success",
                "epochs_completed": epochs,
                "final_loss": 0.123,
                "quantum_metrics": {"circuit_executions": 7},
                "checkpoint_path": "data_out/quantum_llm_api/best_quantum_llm.pt",
            }

    def get_quantum_llm_status(*, status_file=None, output_dir=None):
        if capture is not None:
            capture["status_call"] = {
                "status_file": status_file,
                "output_dir": output_dir,
            }
        return {
            "available": True,
            "status": "completed",
            "checkpoint_exists": True,
            "checkpoint_path": "data_out/quantum_llm_training/best_quantum_llm.pt",
            "status_file": "data_out/quantum_llm_training/status.json",
            "inference_ready": True,
        }

    module.QuantumEnhancedLLMTrainer = QuantumEnhancedLLMTrainer
    module.get_quantum_llm_status = get_quantum_llm_status
    monkeypatch.setitem(sys.modules, "quantum_llm_trainer", module)


# ---------------------------------------------------------------------------
# Import the function_app module (best-effort; skip suite if unavailable)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def app_module():
    """Import function_app once; skip tests if it can't load."""
    try:
        import function_app

        return function_app
    except Exception as exc:
        pytest.skip(f"Cannot import function_app: {exc}")


# ===========================================================================
# GET endpoint tests — should return 200 with expected content types
# ===========================================================================
class TestGetEndpoints:
    """GET endpoints should return valid responses without a request body."""

    def test_ai_status(self, app_module):
        """GET /api/ai/status returns JSON with provider info."""
        req = _mock_request("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert "provider" in data or "status" in data

    def test_health(self, app_module):
        """GET /api/health returns a compact status payload."""
        req = _mock_request("GET")
        resp = app_module.health(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["status"] == "ok"
        assert "settings" in data

    def test_ai_status_uses_shared_status_loader_without_leaking_metadata(
        self, app_module, monkeypatch
    ):
        """GET /api/ai/status should strip shared loader metadata from payloads."""

        def _fake_status(path, *_, **__):
            path = Path(path)
            base = {
                "_status_file_exists": True,
                "_status_file_age_seconds": 1.0,
                "_status_file_stale": False,
                "_status_file_error": None,
            }
            if path.name == "autonomous_training_status.json":
                return {
                    **base,
                    "cycles_completed": 4,
                    "best_accuracy": 0.91,
                    "last_updated": "2026-03-28T00:00:00Z",
                    "performance_history": [
                        {"accuracy": 0.5},
                        {"accuracy": 0.9},
                    ],
                }
            if path.name == "autonomous_training_heartbeat.json":
                return {**base, "state": "completed", "pid": 1234}
            if path.name == "status.json" and path.parent.name == "autotrain":
                return {
                    **base,
                    "total_jobs": 5,
                    "succeeded": 5,
                    "failed": 0,
                    "running": 0,
                    "last_updated": "2026-03-28T00:00:00Z",
                }
            return {
                "_status_file_exists": False,
                "_status_file_age_seconds": None,
                "_status_file_stale": None,
                "_status_file_error": "File not found",
            }

        monkeypatch.setattr(app_module, "load_status_json", _fake_status)

        req = _mock_request("GET")
        resp = app_module.ai_status(req)
        assert resp.status_code == 200

        data = json.loads(resp.get_body())
        orch = data["orchestrator_health"]["orchestrators"]

        assert orch["autonomous_training"]["cycles_completed"] == 4
        assert orch["autonomous_training"]["heartbeat_running"] is False
        assert orch["autotrain"]["status"] == "ok"
        assert not any(key.startswith("_status_file_")
                       for key in orch["autonomous_training"])

    def test_chat_options(self, app_module):
        """OPTIONS /api/chat returns CORS headers."""
        req = _mock_request("OPTIONS")
        resp = app_module.chat_options(req)
        assert resp.status_code == 200

    def test_chat_stream_options(self, app_module):
        """OPTIONS /api/chat/stream returns CORS headers."""
        req = _mock_request("OPTIONS")
        resp = app_module.chat_stream_options(req)
        assert resp.status_code == 200

    def test_subscription_pricing(self, app_module):
        """GET /api/subscription/pricing returns tier data."""
        req = _mock_request("GET")
        resp = app_module.subscription_pricing(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        # Should contain at least one tier
        assert isinstance(data, (dict, list))

    def test_quantum_info(self, app_module):
        """GET /api/quantum/info returns backend/version data."""
        req = _mock_request("GET")
        resp = app_module.quantum_info(req)
        assert resp.status_code == 200


# ===========================================================================
# POST endpoint validation tests — bad input ➜ 400
# ===========================================================================
class TestPostValidation:
    """POST endpoints should reject malformed payloads."""

    def test_chat_empty_messages(self, app_module):
        """POST /api/chat with empty messages → 400."""
        req = _mock_request("POST", body={"messages": []})
        resp = app_module.chat(req)
        assert resp.status_code == 400

    def test_chat_no_body(self, app_module):
        """POST /api/chat with no JSON body → 400 or 500."""
        req = _mock_request("POST")
        resp = app_module.chat(req)
        assert resp.status_code in (400, 500)

    def test_chat_invalid_json_body_returns_400(self, app_module):
        """POST /api/chat with malformed JSON should return 400."""
        req = MagicMock()
        req.method = "POST"
        req.params = {}
        req.route_params = {}
        req.get_json.side_effect = ValueError("bad json")
        req.get_body.return_value = b"{bad-json"

        resp = app_module.chat(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "invalid json body" in data["error"].lower()

    def test_chat_whitespace_only_message(self, app_module):
        """POST /api/chat with whitespace-only content should return 400."""
        req = _mock_request(
            "POST",
            body={"messages": [{"role": "user", "content": "   \n\t  "}]},
        )
        resp = app_module.chat(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_whitespace_only_text_block_message(self, app_module):
        """POST /api/chat with whitespace-only text block content should return 400."""
        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "   "},
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.com/img.png"},
                            },
                        ],
                    }
                ]
            },
        )
        resp = app_module.chat(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_whitespace_only_input_text_block_message(self, app_module):
        """POST /api/chat with whitespace-only input_text block content should return 400."""
        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "   \n\t  "},
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.com/img.png"},
                            },
                        ],
                    }
                ]
            },
        )
        resp = app_module.chat(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_drops_compaction_placeholder_before_provider_call(self, app_module, monkeypatch):
        """Synthetic compaction placeholders should not be forwarded to providers."""

        captured: dict = {}

        class _FakeProvider:
            def complete(self, messages, stream=False):
                captured["messages"] = messages
                return "Recovered reply"

        monkeypatch.setattr(
            app_module,
            "detect_provider",
            lambda **kwargs: (
                _FakeProvider(),
                types.SimpleNamespace(name="local", model="test-model"),
            ),
        )
        monkeypatch.setattr(app_module, "generate_embedding", lambda text: [])
        monkeypatch.setattr(
            app_module,
            "fetch_similar_messages",
            lambda query_emb, top_k=5, session_id=None: [],
        )
        monkeypatch.setattr(app_module, "log_chat_message_safe", None)
        monkeypatch.setattr(app_module, "cosmos_client", None)

        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {"role": "assistant", "content": "Compacted conversation"},
                    {"role": "user", "content": "Continue with the fix"},
                ]
            },
        )

        resp = app_module.chat(req)

        assert resp.status_code == 200
        assert captured["messages"] == [
            {"role": "user", "content": "Continue with the fix"}]

    def test_chat_only_compaction_placeholder_messages_return_validation_error(self, app_module):
        """Placeholder-only histories should be rejected like other empty input."""

        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {"role": "assistant", "content": "Compacted conversation"},
                    {"role": "assistant", "content": "\nCompacted conversation\n"},
                ]
            },
        )

        resp = app_module.chat(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_stream_empty_messages(self, app_module):
        """POST /api/chat/stream with empty messages → 400."""
        req = _mock_request("POST", body={"messages": []})
        resp = app_module.chat_stream(req)
        assert resp.status_code == 400

    def test_chat_stream_invalid_json_body_returns_400(self, app_module):
        """POST /api/chat/stream with malformed JSON should return 400."""
        req = MagicMock()
        req.method = "POST"
        req.params = {}
        req.route_params = {}
        req.get_json.side_effect = ValueError("bad json")
        req.get_body.return_value = b"{bad-json"

        resp = app_module.chat_stream(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "invalid json body" in data["error"].lower()

    def test_chat_stream_whitespace_only_message(self, app_module):
        """POST /api/chat/stream with whitespace-only content should return 400."""
        req = _mock_request(
            "POST",
            body={"messages": [{"role": "user", "content": "   "}]},
        )
        resp = app_module.chat_stream(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_stream_whitespace_only_text_block_message(self, app_module):
        """POST /api/chat/stream with whitespace-only text block content should return 400."""
        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "\n\t  "},
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.com/img.png"},
                            },
                        ],
                    }
                ]
            },
        )
        resp = app_module.chat_stream(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_stream_whitespace_only_input_text_block_message(self, app_module):
        """POST /api/chat/stream with whitespace-only input_text blocks should return 400."""
        req = _mock_request(
            "POST",
            body={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "  \n  "},
                            {
                                "type": "image_url",
                                "image_url": {"url": "https://example.com/img.png"},
                            },
                        ],
                    }
                ]
            },
        )
        resp = app_module.chat_stream(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "validation error" in data["error"].lower()

    def test_chat_stream_memory_injection(self, app_module, monkeypatch):
        """POST /api/chat/stream should call memory helpers and include count in meta SSE event."""
        import inspect

        import azure.functions as _af

        captured: dict = {"embedding": None,
                          "session_id": None, "sse_body": b""}

        def _fake_embedding(text: str):
            captured["embedding"] = text
            return [0.1, 0.2, 0.3]

        def _fake_similar(query_emb, top_k=5, session_id=None):
            captured["session_id"] = session_id
            return [{"content": "Previous answer about widgets", "similarity": 0.88}]

        # Patch func.HttpResponse inside function_app so streaming body (generator) is consumed
        _real_HttpResponse = _af.HttpResponse

        def _capturing_HttpResponse(body=None, **kwargs):
            if body is not None and inspect.isgenerator(body):
                consumed = b"".join(body)
                captured["sse_body"] = consumed
                return _real_HttpResponse(consumed, **kwargs)
            return _real_HttpResponse(body, **kwargs)

        monkeypatch.setattr(app_module.func, "HttpResponse",
                            _capturing_HttpResponse)
        monkeypatch.setattr(app_module, "generate_embedding", _fake_embedding)
        monkeypatch.setattr(
            app_module, "fetch_similar_messages", _fake_similar)

        req = _mock_request(
            "POST",
            body={
                "messages": [{"role": "user", "content": "How do I use widgets?"}],
                "session_id": "test-session-789",
            },
        )
        resp = app_module.chat_stream(req)
        assert resp.status_code == 200

        # Parse SSE body for the meta event
        body_text = captured["sse_body"].decode("utf-8")
        meta_data: dict | None = None
        for line in body_text.splitlines():
            if line.startswith("data:"):
                try:
                    obj = json.loads(line[5:].strip())
                    if "memory_messages" in obj:
                        meta_data = obj
                        break
                except json.JSONDecodeError:
                    pass

        assert meta_data is not None, "No meta event with memory_messages in SSE body"
        assert meta_data["memory_messages"] == 1
        assert captured["embedding"] == "How do I use widgets?"
        assert captured["session_id"] == "test-session-789"

    def test_chat_stream_emits_done_sentinel(self, app_module, monkeypatch):
        """POST /api/chat/stream should terminate SSE with data: [DONE]."""
        import inspect

        import azure.functions as _af

        captured: dict = {"sse_body": b""}

        class _FakeProvider:
            def complete(self, messages, stream=False):
                assert stream is True
                yield "Hello"
                yield " world"

        monkeypatch.setattr(
            app_module,
            "_detect_provider_with_runtime_fallback",
            lambda **kwargs: (
                _FakeProvider(),
                types.SimpleNamespace(name="local", model="local-echo"),
            ),
        )
        monkeypatch.setattr(app_module, "generate_embedding", lambda text: [])
        monkeypatch.setattr(
            app_module,
            "fetch_similar_messages",
            lambda query_emb, top_k=5, session_id=None: [],
        )

        _real_HttpResponse = _af.HttpResponse

        def _capturing_HttpResponse(body=None, **kwargs):
            if body is not None and inspect.isgenerator(body):
                consumed = b"".join(body)
                captured["sse_body"] = consumed
                return _real_HttpResponse(consumed, **kwargs)
            return _real_HttpResponse(body, **kwargs)

        monkeypatch.setattr(app_module.func, "HttpResponse",
                            _capturing_HttpResponse)

        req = _mock_request(
            "POST",
            body={"messages": [{"role": "user", "content": "say hi"}]},
        )
        resp = app_module.chat_stream(req)

        assert resp.status_code == 200
        body_text = captured["sse_body"].decode("utf-8")
        assert '"delta": "Hello"' in body_text or '"delta": " world"' in body_text
        assert "data: [DONE]" in body_text

    def test_tts_no_text(self, app_module):
        """POST /api/tts with no text field → 400."""
        req = _mock_request("POST", body={})
        resp = app_module.tts(req)
        assert resp.status_code in (400, 500)


# ===========================================================================
# AGI endpoint tests — /api/agi/analyze and /api/agi/status
# ===========================================================================
class TestAgiEndpoints:
    def test_agi_analyze_uses_query_and_returns_routing(self, app_module, monkeypatch):
        class _FakeAgiProvider:
            def _analyze_query(self, query: str):
                assert query == "implement a safer routing layer"
                return {
                    "complexity": "complex",
                    "intent": "coding",
                    "domain": "ai",
                    "confidence": 0.92,
                }

            def _select_agent(self, analysis):
                assert analysis["intent"] == "coding"
                return "code-specialist", 0.88

        monkeypatch.setattr(
            app_module,
            "create_agi_provider",
            lambda **kwargs: (
                _FakeAgiProvider(),
                types.SimpleNamespace(name="local", model="local-echo"),
            ),
        )

        req = _mock_request(
            "POST",
            body={"query": "implement a safer routing layer"},
        )
        resp = app_module.agi_analyze(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["status"] == "ok"
        assert data["analysis"]["intent"] == "coding"
        assert data["routing"]["selected_agent"] == "code-specialist"
        assert data["provider"]["name"] == "agi"

    def test_agi_analyze_validation_error_when_missing_query(self, app_module):
        req = _mock_request("POST", body={})
        resp = app_module.agi_analyze(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert data["status"] == "error"
        assert "validation error" in data["error"].lower()

    def test_agi_status_returns_reasoning_summary(self, app_module, monkeypatch):
        class _FakeAgiProvider:
            def get_reasoning_summary(self):
                return {
                    "total_reasoning_chains": 3,
                    "active_goals": ["improve reliability"],
                    "learned_patterns_count": 2,
                    "top_learned_patterns": [],
                    "conversation_length": 12,
                    "last_agent_used": "code-specialist",
                    "last_agent_score": 0.81,
                    "available_agents": ["general", "code-specialist"],
                }

        monkeypatch.setattr(
            app_module,
            "create_agi_provider",
            lambda **kwargs: (
                _FakeAgiProvider(),
                types.SimpleNamespace(name="azure", model="gpt-4o"),
            ),
        )

        req = _mock_request("GET")
        resp = app_module.agi_status(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["status"] == "ok"
        assert data["available"] is True
        assert data["provider"]["name"] == "agi"
        assert data["reasoning"]["total_reasoning_chains"] == 3

    def test_agi_reason_returns_response_and_summary(self, app_module, monkeypatch):
        class _FakeAgiProvider:
            def __init__(self):
                self.goals = []

            def set_goal(self, goal: str):
                self.goals.append(goal)

            def complete(self, messages, stream=False):
                assert stream is False
                assert messages[-1]["content"] == "reason through this architecture"
                return "Here is a reasoned response"

            def get_reasoning_summary(self):
                return {
                    "total_reasoning_chains": 1,
                    "active_goals": self.goals,
                    "learned_patterns_count": 0,
                    "top_learned_patterns": [],
                    "conversation_length": 2,
                    "last_agent_used": "reasoning-specialist",
                    "last_agent_score": 0.77,
                    "available_agents": ["general", "reasoning-specialist"],
                }

        monkeypatch.setattr(
            app_module,
            "create_agi_provider",
            lambda **kwargs: (
                _FakeAgiProvider(),
                types.SimpleNamespace(name="openai", model="gpt-test"),
            ),
        )

        req = _mock_request(
            "POST",
            body={
                "query": "reason through this architecture",
                "goals": ["be concise"],
            },
        )
        resp = app_module.agi_reason(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["status"] == "ok"
        assert data["response"] == "Here is a reasoned response"
        assert data["reasoning"]["active_goals"] == ["be concise"]

    def test_agi_reason_validation_error_when_missing_input(self, app_module):
        req = _mock_request("POST", body={})
        resp = app_module.agi_reason(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert data["status"] == "error"
        assert "validation error" in data["error"].lower()

    def test_agi_stream_emits_done_sentinel(self, app_module, monkeypatch):
        import inspect

        import azure.functions as _af

        captured: dict = {"sse_body": b""}

        class _FakeAgiProvider:
            def complete(self, messages, stream=False):
                assert stream is True
                yield "Hello"
                yield " world"

            def set_goal(self, _goal: str):
                return None

        monkeypatch.setattr(
            app_module,
            "create_agi_provider",
            lambda **kwargs: (
                _FakeAgiProvider(),
                types.SimpleNamespace(name="local", model="local-echo"),
            ),
        )

        _real_HttpResponse = _af.HttpResponse

        def _capturing_HttpResponse(body=None, **kwargs):
            if body is not None and inspect.isgenerator(body):
                consumed = b"".join(body)
                captured["sse_body"] = consumed
                return _real_HttpResponse(consumed, **kwargs)
            return _real_HttpResponse(body, **kwargs)

        monkeypatch.setattr(app_module.func, "HttpResponse",
                            _capturing_HttpResponse)

        req = _mock_request(
            "POST",
            body={"query": "stream a short response", "goals": ["be concise"]},
        )
        resp = app_module.agi_stream(req)

        assert resp.status_code == 200
        body_text = captured["sse_body"].decode("utf-8")
        assert "event: meta" in body_text
        assert '"delta": "Hello"' in body_text or '"delta": " world"' in body_text
        assert "data: [DONE]" in body_text

    def test_agi_stream_validation_error_when_missing_input(self, app_module):
        req = _mock_request("POST", body={})
        resp = app_module.agi_stream(req)

        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert data["status"] == "error"
        assert "validation error" in data["error"].lower()


# ===========================================================================
# Quantum LLM endpoint tests — /api/quantum/llm
# ===========================================================================
class TestQuantumLlmEndpoint:
    """Coverage for GET/POST branches of the quantum LLM endpoint."""

    def test_quantum_llm_get(self, app_module):
        req = _mock_request("GET")
        resp = app_module.quantum_llm(req)
        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert "available" in data
        assert "capabilities" in data

    def test_quantum_llm_get_includes_readiness(self, app_module, monkeypatch):
        capture: dict = {}
        _install_fake_quantum_trainer_module(monkeypatch, capture=capture)

        req = _mock_request("GET")
        resp = app_module.quantum_llm(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["readiness"]["inference_ready"] is True
        assert data["readiness"]["checkpoint_exists"] is True

    def test_quantum_llm_post_invalid_json(self, app_module, monkeypatch):
        _install_fake_quantum_trainer_module(monkeypatch)

        req = MagicMock()
        req.method = "POST"
        req.params = {}
        req.route_params = {}
        req.get_body.return_value = b"{bad-json"
        req.get_json.side_effect = ValueError("bad json")

        resp = app_module.quantum_llm(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert data["error"] == "Invalid JSON body"

    def test_quantum_llm_post_generate(self, app_module, monkeypatch):
        capture: dict = {}
        _install_fake_quantum_trainer_module(
            monkeypatch,
            capture=capture,
            generate_tokens=[72, 105, 33],  # "Hi!"
        )

        req = _mock_request(
            "POST",
            body={
                "action": "generate",
                "prompt": "Hi",
                "max_tokens": 3,
            },
        )
        resp = app_module.quantum_llm(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["action"] == "generate"
        assert data["tokens"] == 3
        assert "generated" in data
        assert data["readiness"]["inference_ready"] is True
        assert capture["generate_kwargs"]["max_new_tokens"] == 3

    def test_quantum_llm_post_train_rejects_external_path(self, app_module, monkeypatch):
        _install_fake_quantum_trainer_module(monkeypatch)
        req = _mock_request(
            "POST",
            body={
                "action": "train",
                "dataset_path": "/tmp/not-in-repo",
                "epochs": 1,
            },
        )

        resp = app_module.quantum_llm(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "dataset_path" in data["error"]

    def test_quantum_llm_post_train_success_caps_epochs(self, app_module, monkeypatch):
        capture: dict = {}
        _install_fake_quantum_trainer_module(monkeypatch, capture=capture)

        req = _mock_request(
            "POST",
            body={
                "action": "train",
                "dataset_path": "datasets/chat",
                "epochs": 999,
            },
        )
        resp = app_module.quantum_llm(req)

        assert resp.status_code == 200
        data = json.loads(resp.get_body())
        assert data["action"] == "train"
        assert data["status"] == "success"
        assert data["epochs_completed"] == 5
        assert data["checkpoint_path"].endswith("best_quantum_llm.pt")
        assert data["readiness"]["inference_ready"] is True

        train_args = capture["train_args"]
        assert train_args["epochs"] == 5
        assert train_args["dataset_path"].is_absolute()
        assert str(train_args["output_dir"]).endswith(
            "data_out/quantum_llm_api")

    def test_quantum_llm_post_unknown_action(self, app_module, monkeypatch):
        _install_fake_quantum_trainer_module(monkeypatch)
        req = _mock_request("POST", body={"action": "mystery"})

        resp = app_module.quantum_llm(req)
        assert resp.status_code == 400
        data = json.loads(resp.get_body())
        assert "Unknown action" in data["error"]


# ===========================================================================
# Request validator unit tests (shared/request_validator.py)
# ===========================================================================
class TestRequestValidator:
    """Unit tests for the shared request validation module."""

    def test_parse_valid_json(self):
        from shared.request_validator import parse_json_body

        req = _mock_request("POST", body={"key": "value"})
        body, err = parse_json_body(req)
        assert err is None
        assert body == {"key": "value"}

    def test_parse_invalid_json(self):
        from shared.request_validator import parse_json_body

        req = MagicMock()
        req.get_json.side_effect = ValueError("bad json")
        req.get_body.return_value = b"not-json"
        body, err = parse_json_body(req)
        assert err is not None
        assert body is None

    def test_validate_required_field(self):
        from shared.request_validator import validate_fields

        err = validate_fields({}, {"name": {"type": str, "required": True}})
        assert err is not None
        assert "required" in err.lower() or "missing" in err.lower()

    def test_validate_type_mismatch(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"count": "not-a-number"},
            {"count": {"type": int}},
        )
        assert err is not None

    def test_validate_range(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"temperature": 3.0},
            {"temperature": {"type": (int, float), "min": 0, "max": 2}},
        )
        assert err is not None

    def test_validate_allowlist(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"tier": "MEGA"},
            {"tier": {"type": str, "allowed": ["FREE", "PRO", "ENTERPRISE"]}},
        )
        assert err is not None

    def test_chat_schema_accepts_quantum_provider(self):
        from shared.request_validator import CHAT_SCHEMA, validate_fields

        err = validate_fields(
            {
                "messages": [{"role": "user", "content": "hello"}],
                "provider": "quantum",
            },
            CHAT_SCHEMA,
        )
        assert err is None

    def test_agi_reason_schema_accepts_query_and_goals(self):
        from shared.request_validator import AGI_REASON_SCHEMA, validate_fields

        err = validate_fields(
            {
                "query": "Reason through this architecture",
                "goals": ["be concise"],
                "temperature": 0.3,
                "include_reasoning_summary": True,
            },
            AGI_REASON_SCHEMA,
        )
        assert err is None

    def test_agi_stream_schema_rejects_invalid_temperature(self):
        from shared.request_validator import AGI_STREAM_SCHEMA, validate_fields

        err = validate_fields(
            {
                "query": "Stream",
                "temperature": 3.5,
            },
            AGI_STREAM_SCHEMA,
        )
        assert err is not None

    def test_validate_min_length(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"messages": []},
            {"messages": {"type": list, "required": True, "min_length": 1}},
        )
        assert err is not None

    def test_validate_happy_path(self):
        from shared.request_validator import validate_fields

        err = validate_fields(
            {"messages": [{"role": "user", "content": "hi"}],
                "temperature": 0.7},
            {
                "messages": {"type": list, "required": True, "min_length": 1},
                "temperature": {"type": (int, float), "min": 0, "max": 2},
            },
        )
        assert err is None

    def test_full_validate_request(self):
        from shared.request_validator import CHAT_SCHEMA, validate_request

        req = _mock_request(
            "POST",
            body={
                "messages": [{"role": "user", "content": "hello"}],
                "temperature": 0.5,
            },
        )
        body, err = validate_request(req, CHAT_SCHEMA)
        assert err is None
        assert body is not None
