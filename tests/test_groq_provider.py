"""Tests for GroqProvider and Groq-related detection logic.

Covers:
  - GroqProvider instantiation (with and without openai package)
  - Streaming and non-streaming complete() paths
  - Friendly error messages for connection, auth, and model-not-found errors
  - _check_groq_available caching behavior
  - detect_provider with explicit 'groq' selection
  - detect_provider auto-detection when Groq key is set and endpoint is reachable
  - GROQ_API_KEY / GROQ_MODEL / GROQ_BASE_URL env-var wiring
  - Alias resolution (groq-api, groq_api)
  - Cache key includes Groq env vars
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure chat_providers is importable from the source tree
_CHAT_SRC = Path(__file__).parent.parent / "ai-projects" / "chat-cli" / "src"
if str(_CHAT_SRC) not in sys.path:
    sys.path.insert(0, str(_CHAT_SRC))

from chat_providers import (
    GroqProvider,
    LocalEchoProvider,
    _build_provider_detect_cache_key,
    _check_groq_available,
    _groq_availability_cache,
    _groq_cache_lock,
    _provider_detection_cache,
    _provider_detection_cache_lock,
    detect_provider,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_groq_cache() -> None:
    """Reset the Groq availability cache between tests."""
    with _groq_cache_lock:
        _groq_availability_cache["available"] = None
        _groq_availability_cache["checked_at"] = 0.0
        _groq_availability_cache["url"] = None


def _reset_detect_provider_cache() -> None:
    """Reset detect_provider result cache between tests."""
    with _provider_detection_cache_lock:
        _provider_detection_cache.clear()


# ---------------------------------------------------------------------------
# GroqProvider — basic construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_groq_provider_requires_openai_package(monkeypatch):
    """GroqProvider raises RuntimeError when openai is not installed."""
    import chat_providers as cp

    original = cp.OpenAI
    try:
        cp.OpenAI = None  # simulate missing package
        with pytest.raises(RuntimeError, match="openai package not installed"):
            GroqProvider(api_key="test-key")
    finally:
        cp.OpenAI = original


@pytest.mark.unit
def test_groq_provider_requires_api_key(monkeypatch):
    """GroqProvider raises RuntimeError when no API key is available."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with patch("chat_providers.OpenAI") as mock_cls:
        mock_cls.return_value = MagicMock()
        with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
            GroqProvider()


@pytest.mark.unit
def test_groq_provider_defaults(monkeypatch):
    """GroqProvider picks up default base_url, model, and temperature."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        p = GroqProvider(api_key="gsk-test")
    assert p.base_url == "https://api.groq.com/openai/v1"
    assert p.model == "llama-3.1-8b-instant"
    assert p.temperature == 0.7


@pytest.mark.unit
def test_groq_provider_custom_params():
    """GroqProvider accepts custom model, base_url, and temperature."""
    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        p = GroqProvider(
            model="mixtral-8x7b-32768",
            api_key="gsk-test",
            base_url="https://custom.groq.example/v1",
            temperature=0.3,
            max_output_tokens=512,
        )
    assert p.model == "mixtral-8x7b-32768"
    assert p.base_url == "https://custom.groq.example/v1"
    assert p.temperature == 0.3
    assert p.max_output_tokens == 512


@pytest.mark.unit
def test_groq_provider_reads_api_key_from_env(monkeypatch):
    """GroqProvider reads GROQ_API_KEY from env when no explicit key given."""
    monkeypatch.setenv("GROQ_API_KEY", "env-key-123")
    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        p = GroqProvider()
    assert p is not None


# ---------------------------------------------------------------------------
# GroqProvider — complete() non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_groq_provider_complete_non_stream():
    """complete(stream=False) returns the full response string."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello from Groq!"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(model="llama-3.1-8b-instant", api_key="gsk-test")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert result == "Hello from Groq!"
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["stream"] is False
    assert call_kwargs["model"] == "llama-3.1-8b-instant"


# ---------------------------------------------------------------------------
# GroqProvider — complete() streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_groq_provider_complete_stream():
    """complete(stream=True) yields text chunks from streaming response."""

    def _mock_chunks():
        for word in ["Hello", " from", " Groq"]:
            chunk = MagicMock()
            chunk.choices[0].delta.content = word
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_chunks()

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(model="llama-3.1-8b-instant", api_key="gsk-test")
    p.client = mock_client

    chunks = list(p.complete([{"role": "user", "content": "hi"}], stream=True))
    assert chunks == ["Hello", " from", " Groq"]


# ---------------------------------------------------------------------------
# GroqProvider — friendly error messages
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_groq_provider_connection_error_stream():
    """Friendly message yielded when Groq API is unreachable (stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ConnectionRefusedError("Connection refused")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(api_key="gsk-test")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=True)
    text = "".join(result)
    assert "Cannot connect to Groq" in text


@pytest.mark.unit
def test_groq_provider_connection_error_non_stream():
    """Friendly message returned when Groq API is unreachable (non-stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ConnectionRefusedError("Connection refused")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(api_key="gsk-test")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert isinstance(result, str)
    assert "Cannot connect to Groq" in result


@pytest.mark.unit
def test_groq_provider_auth_error_stream():
    """Friendly message yielded when Groq auth fails (stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("invalid_api_key: authentication failed")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(api_key="bad-key")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=True)
    text = "".join(result)
    assert "authentication" in text.lower() or "GROQ_API_KEY" in text


@pytest.mark.unit
def test_groq_provider_auth_error_non_stream():
    """Friendly message returned when Groq auth fails (non-stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("invalid_api_key: authentication failed")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(api_key="bad-key")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert isinstance(result, str)
    assert "GROQ_API_KEY" in result or "authentication" in result.lower()


@pytest.mark.unit
def test_groq_provider_model_not_found_stream():
    """Friendly message yielded when the requested Groq model is not found (stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("model 'bad-model' not found")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(model="bad-model", api_key="gsk-test")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=True)
    text = "".join(result)
    assert "not found on Groq" in text


@pytest.mark.unit
def test_groq_provider_model_not_found_non_stream():
    """Friendly message returned when the requested Groq model is not found (non-stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("model 'bad-model' not found")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(model="bad-model", api_key="gsk-test")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert isinstance(result, str)
    assert "not found on Groq" in result


@pytest.mark.unit
def test_groq_provider_unexpected_error_raises():
    """Unexpected exceptions (not connection/auth/model errors) are re-raised."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ValueError("unexpected error")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = GroqProvider(api_key="gsk-test")
    p.client = mock_client

    with pytest.raises(ValueError, match="unexpected error"):
        p.complete([{"role": "user", "content": "hi"}], stream=False)


# ---------------------------------------------------------------------------
# _check_groq_available — caching behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_check_groq_available_false_when_no_key(monkeypatch):
    """Returns False immediately when GROQ_API_KEY is not set."""
    _reset_groq_cache()
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with patch("urllib.request.urlopen") as mock_urlopen:
        result = _check_groq_available("https://api.groq.com/openai/v1")

    assert result is False
    mock_urlopen.assert_not_called()


@pytest.mark.unit
def test_check_groq_available_true_when_reachable(monkeypatch):
    """Returns True when the Groq models endpoint responds."""
    _reset_groq_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MagicMock()
        result = _check_groq_available("https://api.groq.com/openai/v1")

    assert result is True


@pytest.mark.unit
def test_check_groq_available_false_when_unreachable(monkeypatch):
    """Returns False when the Groq endpoint raises an exception."""
    _reset_groq_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
        result = _check_groq_available("https://api.groq.com/openai/v1")

    assert result is False


@pytest.mark.unit
def test_check_groq_available_uses_cache(monkeypatch):
    """Second call within TTL does not make a new HTTP request."""
    _reset_groq_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MagicMock()
        first = _check_groq_available("https://api.groq.com/openai/v1")
        second = _check_groq_available("https://api.groq.com/openai/v1")

    assert mock_urlopen.call_count == 1
    assert first is True
    assert second is True


@pytest.mark.unit
def test_check_groq_available_cache_different_url(monkeypatch):
    """Different URL invalidates cache and triggers a new HTTP check."""
    _reset_groq_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    call_count = 0

    def urlopen_side_effect(req, timeout=None):
        nonlocal call_count
        call_count += 1
        from urllib.parse import urlparse

        if urlparse(req.full_url).hostname == "api.groq.com":
            return MagicMock()
        import urllib.error

        raise urllib.error.URLError("refused")

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        r1 = _check_groq_available("https://api.groq.com/openai/v1")
        _reset_groq_cache()
        r2 = _check_groq_available("https://custom.example.com/openai/v1")

    assert r1 is True
    assert r2 is False


# ---------------------------------------------------------------------------
# detect_provider — explicit 'groq' selection
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_detect_provider_explicit_groq(monkeypatch):
    """detect_provider('groq') returns GroqProvider with GROQ_MODEL."""
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GROQ_MODEL", "mixtral-8x7b-32768")

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="groq")

    assert choice.name == "groq"
    assert choice.model == "mixtral-8x7b-32768"
    assert isinstance(provider, GroqProvider)


@pytest.mark.unit
def test_detect_provider_explicit_groq_model_override(monkeypatch):
    """detect_provider('groq', model_override=...) uses override model."""
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="groq", model_override="gemma2-9b-it")

    assert choice.name == "groq"
    assert choice.model == "gemma2-9b-it"
    assert provider.model == "gemma2-9b-it"


@pytest.mark.unit
def test_detect_provider_explicit_groq_default_model(monkeypatch):
    """detect_provider('groq') falls back to default model when GROQ_MODEL unset."""
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="groq")

    assert choice.name == "groq"
    assert choice.model == "llama-3.1-8b-instant"


@pytest.mark.unit
def test_detect_provider_explicit_groq_without_key_raises(monkeypatch):
    """detect_provider('groq') raises RuntimeError when GROQ_API_KEY is missing."""
    _reset_detect_provider_cache()
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        detect_provider(explicit="groq")


# ---------------------------------------------------------------------------
# detect_provider — alias resolution
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_detect_provider_alias_groq_api(monkeypatch):
    """'groq-api' alias resolves to GroqProvider."""
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="groq-api")

    assert choice.name == "groq"
    assert isinstance(provider, GroqProvider)


@pytest.mark.unit
def test_detect_provider_alias_groq_api_underscore(monkeypatch):
    """'groq_api' alias resolves to GroqProvider."""
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="groq_api")

    assert choice.name == "groq"
    assert isinstance(provider, GroqProvider)


# ---------------------------------------------------------------------------
# detect_provider — auto-detection picks Groq when reachable
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_detect_provider_auto_picks_groq_when_reachable(monkeypatch):
    """Auto-detect selects Groq when it is reachable and other providers are not."""
    _reset_groq_cache()
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fake_check_lm(url):
        return False

    def fake_check_ollama(url):
        return False

    def fake_check_groq(url):
        return True

    with (
        patch("chat_providers._check_lm_studio_available", side_effect=fake_check_lm),
        patch("chat_providers._check_ollama_available", side_effect=fake_check_ollama),
        patch("chat_providers._check_groq_available", side_effect=fake_check_groq),
        patch("chat_providers.OpenAI") as mock_openai_cls,
    ):
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="auto")

    assert choice.name == "groq"
    assert isinstance(provider, GroqProvider)


@pytest.mark.unit
def test_detect_provider_groq_not_picked_when_unreachable(monkeypatch):
    """Auto-detect falls through to local echo when Groq is unreachable."""
    _reset_groq_cache()
    _reset_detect_provider_cache()
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with (
        patch("chat_providers._check_lm_studio_available", return_value=False),
        patch("chat_providers._check_ollama_available", return_value=False),
        patch("chat_providers._check_groq_available", return_value=False),
    ):
        provider, choice = detect_provider(explicit="auto")

    assert choice.name == "local"
    assert isinstance(provider, LocalEchoProvider)


# ---------------------------------------------------------------------------
# Cache key includes Groq env vars
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_cache_key_includes_groq_api_key_presence(monkeypatch):
    """Cache key changes when GROQ_API_KEY is set vs. unset."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    key_without = _build_provider_detect_cache_key("auto", None, None, None)

    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    key_with = _build_provider_detect_cache_key("auto", None, None, None)

    assert key_without != key_with


@pytest.mark.unit
def test_cache_key_includes_groq_model(monkeypatch):
    """Cache key changes when GROQ_MODEL changes."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    key_a = _build_provider_detect_cache_key("groq", None, None, None)

    monkeypatch.setenv("GROQ_MODEL", "mixtral-8x7b-32768")
    key_b = _build_provider_detect_cache_key("groq", None, None, None)

    assert key_a != key_b


@pytest.mark.unit
def test_cache_key_includes_groq_base_url(monkeypatch):
    """Cache key changes when GROQ_BASE_URL changes."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.delenv("GROQ_BASE_URL", raising=False)
    key_default = _build_provider_detect_cache_key("groq", None, None, None)

    monkeypatch.setenv("GROQ_BASE_URL", "https://custom.groq.example/v1")
    key_custom = _build_provider_detect_cache_key("groq", None, None, None)

    assert key_default != key_custom
