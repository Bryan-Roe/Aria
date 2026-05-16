"""Tests for the OllamaProvider and Ollama-related detection logic.

Covers:
  - OllamaProvider instantiation and contract
  - Streaming and non-streaming complete() paths
  - Friendly connection-error messages
  - Friendly model-not-found messages
  - _check_ollama_available caching behaviour
  - detect_provider with explicit 'ollama' selection
  - detect_provider auto-detection when Ollama is reachable
  - OLLAMA_BASE_URL / OLLAMA_MODEL env-var wiring
"""

from __future__ import annotations
from chat_providers import (
    OllamaProvider,
    _check_ollama_available,
    _ollama_availability_cache,
    _ollama_cache_lock,
    detect_provider,
)

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure chat_providers is importable from the source tree
_CHAT_SRC = Path(__file__).parent.parent / "ai-projects" / "chat-cli" / "src"
if str(_CHAT_SRC) not in sys.path:
    sys.path.insert(0, str(_CHAT_SRC))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_ollama_cache() -> None:
    """Reset the Ollama availability cache between tests."""
    with _ollama_cache_lock:
        _ollama_availability_cache["available"] = None
        _ollama_availability_cache["checked_at"] = 0.0
        _ollama_availability_cache["url"] = None


# ---------------------------------------------------------------------------
# OllamaProvider — basic construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ollama_provider_requires_openai_package(monkeypatch):
    """OllamaProvider raises RuntimeError when openai is not installed."""
    import chat_providers as cp

    original = cp.OpenAI
    try:
        cp.OpenAI = None  # simulate missing package
        with pytest.raises(RuntimeError, match="openai package not installed"):
            OllamaProvider()
    finally:
        cp.OpenAI = original


@pytest.mark.unit
def test_ollama_provider_defaults():
    """OllamaProvider picks up default URL, model, and temperature."""
    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        p = OllamaProvider()
    assert p.base_url == "http://127.0.0.1:11434/v1"
    assert p.model == "llama3.2"
    assert p.temperature == 0.7


@pytest.mark.unit
def test_ollama_provider_custom_params():
    """OllamaProvider accepts custom URL, model, temperature."""
    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        p = OllamaProvider(
            base_url="http://10.0.0.1:11434/v1",
            model="mistral",
            temperature=0.3,
            max_output_tokens=512,
        )
    assert p.base_url == "http://10.0.0.1:11434/v1"
    assert p.model == "mistral"
    assert p.temperature == 0.3
    assert p.max_output_tokens == 512


# ---------------------------------------------------------------------------
# OllamaProvider — complete() non-streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ollama_provider_complete_non_stream():
    """complete(stream=False) returns the full response string."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello from Ollama!"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider(model="llama3.2")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert result == "Hello from Ollama!"
    mock_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["stream"] is False
    assert call_kwargs["model"] == "llama3.2"


# ---------------------------------------------------------------------------
# OllamaProvider — complete() streaming
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ollama_provider_complete_stream():
    """complete(stream=True) yields text chunks from streaming response."""

    def _mock_chunks():
        for word in ["Hello", " from", " Ollama"]:
            chunk = MagicMock()
            chunk.choices[0].delta.content = word
            yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_chunks()

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider(model="llama3.2")
    p.client = mock_client

    chunks = list(p.complete([{"role": "user", "content": "hi"}], stream=True))
    assert chunks == ["Hello", " from", " Ollama"]


# ---------------------------------------------------------------------------
# OllamaProvider — friendly error messages
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_ollama_provider_connection_error_stream():
    """Friendly message yielded when Ollama server is unreachable (stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ConnectionRefusedError(
        "Connection refused")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider()
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=True)
    text = "".join(result)
    assert "Cannot connect to Ollama" in text
    assert "ollama serve" in text.lower() or "ollama.ai" in text


@pytest.mark.unit
def test_ollama_provider_connection_error_non_stream():
    """Friendly message returned when Ollama server is unreachable (non-stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ConnectionRefusedError(
        "Connection refused")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider()
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert isinstance(result, str)
    assert "Cannot connect to Ollama" in result


@pytest.mark.unit
def test_ollama_provider_model_not_found_stream():
    """Friendly message yielded when requested model is not pulled (stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception(
        "model 'nomodel' not found")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider(model="nomodel")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=True)
    text = "".join(result)
    assert "not found in Ollama" in text
    assert "ollama pull" in text.lower()


@pytest.mark.unit
def test_ollama_provider_model_not_found_non_stream():
    """Friendly message returned when requested model is not pulled (non-stream)."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception(
        "model 'nomodel' not found")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider(model="nomodel")
    p.client = mock_client

    result = p.complete([{"role": "user", "content": "hi"}], stream=False)
    assert isinstance(result, str)
    assert "not found in Ollama" in result


@pytest.mark.unit
def test_ollama_provider_unexpected_error_raises():
    """Unexpected exceptions (not connection/model errors) are re-raised."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ValueError(
        "unexpected error")

    with patch("chat_providers.OpenAI", return_value=mock_client):
        p = OllamaProvider()
    p.client = mock_client

    with pytest.raises(ValueError, match="unexpected error"):
        p.complete([{"role": "user", "content": "hi"}], stream=False)


# ---------------------------------------------------------------------------
# _check_ollama_available — caching behaviour
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_check_ollama_available_returns_true_when_reachable():
    """Returns True when Ollama tags endpoint responds."""
    _reset_ollama_cache()

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MagicMock()
        result = _check_ollama_available("http://127.0.0.1:11434/v1")

    assert result is True


@pytest.mark.unit
def test_check_ollama_available_returns_false_when_unreachable():
    """Returns False when both Ollama endpoints are unreachable."""
    _reset_ollama_cache()
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no route")):
        result = _check_ollama_available("http://127.0.0.1:11434/v1")

    assert result is False


@pytest.mark.unit
def test_check_ollama_available_uses_cache():
    """Second call within TTL does not make a new HTTP request."""
    _reset_ollama_cache()

    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.return_value = MagicMock()
        first = _check_ollama_available("http://127.0.0.1:11434/v1")
        second = _check_ollama_available("http://127.0.0.1:11434/v1")

    # urlopen called only once; second call used cache
    assert mock_urlopen.call_count == 1
    assert first is True
    assert second is True


@pytest.mark.unit
def test_check_ollama_available_cache_different_url():
    """Different URL invalidates cache and triggers new HTTP check."""
    _reset_ollama_cache()

    import urllib.error

    call_count = 0

    def urlopen_side_effect(req, timeout=None):
        nonlocal call_count
        call_count += 1
        if "11434" in req.full_url:
            return MagicMock()
        raise urllib.error.URLError("refused")

    with patch("urllib.request.urlopen", side_effect=urlopen_side_effect):
        r1 = _check_ollama_available("http://127.0.0.1:11434/v1")
        _reset_ollama_cache()
        r2 = _check_ollama_available("http://127.0.0.1:9999/v1")

    assert r1 is True
    assert r2 is False


# ---------------------------------------------------------------------------
# detect_provider — explicit 'ollama' selection
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_detect_provider_explicit_ollama(monkeypatch):
    """detect_provider('ollama') returns OllamaProvider with OLLAMA_MODEL."""
    monkeypatch.setenv("OLLAMA_MODEL", "mistral")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="ollama")

    assert choice.name == "ollama"
    assert choice.model == "mistral"
    assert isinstance(provider, OllamaProvider)


@pytest.mark.unit
def test_detect_provider_explicit_ollama_model_override(monkeypatch):
    """detect_provider('ollama', model_override=...) uses override model."""
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(
            explicit="ollama", model_override="phi3")

    assert choice.name == "ollama"
    assert choice.model == "phi3"
    assert provider.model == "phi3"


@pytest.mark.unit
def test_detect_provider_explicit_ollama_default_model(monkeypatch):
    """detect_provider('ollama') falls back to default model when env var unset."""
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)

    with patch("chat_providers.OpenAI") as mock_openai_cls:
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="ollama")

    assert choice.name == "ollama"
    # Default model from the provider definition
    assert choice.model == "llama3.2"


@pytest.mark.unit
def test_detect_provider_explicit_invalid_provider_raises_value_error():
    """Explicit unknown providers should fail fast with a clear error."""
    with pytest.raises(ValueError, match="Unknown provider"):
        detect_provider(explicit="definitely-not-a-provider")


# ---------------------------------------------------------------------------
# detect_provider — auto-detection picks Ollama when reachable
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_detect_provider_auto_picks_ollama_when_reachable(monkeypatch):
    """Auto-detect selects Ollama when it is reachable and LMStudio is not."""
    _reset_ollama_cache()
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2")

    def fake_check_lm(url):
        return False

    def fake_check_ollama(url):
        return True

    with (
        patch("chat_providers._check_lm_studio_available",
              side_effect=fake_check_lm),
        patch("chat_providers._check_ollama_available",
              side_effect=fake_check_ollama),
        patch("chat_providers.OpenAI") as mock_openai_cls,
    ):
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="auto")

    assert choice.name == "ollama"
    assert isinstance(provider, OllamaProvider)


@pytest.mark.unit
def test_detect_provider_auto_prefers_lmstudio_over_ollama(monkeypatch):
    """LMStudio takes priority over Ollama in auto-detection."""
    _reset_ollama_cache()
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    def fake_check_lm(url):
        return True

    def fake_check_ollama(url):
        return True

    with (
        patch("chat_providers._check_lm_studio_available",
              side_effect=fake_check_lm),
        patch("chat_providers._check_ollama_available",
              side_effect=fake_check_ollama),
        patch("chat_providers.OpenAI") as mock_openai_cls,
    ):
        mock_openai_cls.return_value = MagicMock()
        provider, choice = detect_provider(explicit="auto")

    # LMStudio should win when both are available
    assert choice.name == "lmstudio"


@pytest.mark.unit
def test_detect_provider_ollama_not_picked_when_unreachable(monkeypatch):
    """Auto-detect falls through to local echo when Ollama is unreachable."""
    _reset_ollama_cache()
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with (
        patch("chat_providers._check_lm_studio_available", return_value=False),
        patch("chat_providers._check_ollama_available", return_value=False),
    ):
        provider, choice = detect_provider(explicit="auto")

    assert choice.name == "local"
