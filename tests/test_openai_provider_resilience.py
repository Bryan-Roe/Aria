"""Unit tests for OpenAIProvider quota/rate-limit resilience in chat_providers."""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any
import unittest.mock

import pytest

chat_providers: Any = importlib.import_module("chat_providers")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_openai_provider(monkeypatch: pytest.MonkeyPatch, fake_client):
    """Return an OpenAIProvider with a mocked SDK client."""
    provider = object.__new__(chat_providers.OpenAIProvider)
    provider.client = fake_client
    provider.model = "gpt-test"
    provider.temperature = 0.7
    provider.max_output_tokens = None
    return provider


class _FakeQuotaError(Exception):
    """Simulates an OpenAI quota/billing error."""


class _FakeRateLimitError(Exception):
    """Simulates an OpenAI transient rate-limit (429) error."""


def _patch_quota_helpers(monkeypatch: pytest.MonkeyPatch, *, quota_exc_type, rate_exc_type):
    """Patch is_quota_error and is_transient_rate_error in chat_providers module."""
    monkeypatch.setattr(chat_providers, "is_quota_error",
                        lambda e: isinstance(e, quota_exc_type))
    monkeypatch.setattr(chat_providers, "is_transient_rate_error",
                        lambda e: isinstance(e, rate_exc_type))
    monkeypatch.setattr(
        chat_providers, "format_quota_message",
        lambda exc, service_name="OpenAI": f"QUOTA:{service_name}",
    )


# ---------------------------------------------------------------------------
# Non-streaming quota tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_openai_quota_error_non_stream_returns_friendly_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-streaming call: quota error → friendly string, no exception raised."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.side_effect = _FakeQuotaError(
        "over quota")

    provider = _make_openai_provider(monkeypatch, fake_client)
    result = provider.complete(
        [{"role": "user", "content": "hi"}], stream=False)

    assert isinstance(result, str)
    assert "QUOTA:OpenAI" in result


@pytest.mark.unit
def test_openai_quota_error_stream_returns_friendly_generator(monkeypatch: pytest.MonkeyPatch) -> None:
    """Streaming call: quota error → iterable yielding friendly message."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.side_effect = _FakeQuotaError(
        "billing exceeded")

    provider = _make_openai_provider(monkeypatch, fake_client)
    result = provider.complete(
        [{"role": "user", "content": "hi"}], stream=True)

    chunks = list(result)
    assert len(chunks) == 1
    assert "QUOTA:OpenAI" in chunks[0]


# ---------------------------------------------------------------------------
# Transient rate-limit retry tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_openai_transient_rate_limit_retries_and_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Transient rate-limit errors should be retried; success on 2nd attempt."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)
    monkeypatch.setattr(chat_providers.time, "sleep", lambda _: None)

    call_count = {"n": 0}

    def _side_effect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise _FakeRateLimitError("429 Too Many Requests")
        # Second attempt: return a successful mock response
        mock_resp = unittest.mock.MagicMock()
        mock_resp.choices[0].message.content = "hello"
        return mock_resp

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.side_effect = _side_effect

    provider = _make_openai_provider(monkeypatch, fake_client)
    result = provider.complete(
        [{"role": "user", "content": "hi"}], stream=False)

    assert result == "hello"
    assert call_count["n"] == 2


@pytest.mark.unit
def test_openai_non_transient_error_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-quota, non-transient errors must still propagate as exceptions."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.side_effect = ConnectionError(
        "network down")

    provider = _make_openai_provider(monkeypatch, fake_client)

    with pytest.raises(ConnectionError, match="network down"):
        provider.complete([{"role": "user", "content": "hi"}], stream=False)


# ---------------------------------------------------------------------------
# Mid-stream error handling
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_openai_mid_stream_quota_error_yields_friendly_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quota error raised mid-stream must be converted to a friendly yielded message."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)

    def _bad_iter():
        yield unittest.mock.MagicMock(choices=[unittest.mock.MagicMock(delta=unittest.mock.MagicMock(content="tok1"))])
        raise _FakeQuotaError("quota mid-stream")

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.return_value = _bad_iter()

    provider = _make_openai_provider(monkeypatch, fake_client)
    result = provider.complete(
        [{"role": "user", "content": "hi"}], stream=True)

    chunks = list(result)
    # First valid chunk, then friendly quota message
    assert chunks[0] == "tok1"
    assert any("QUOTA:OpenAI" in c for c in chunks)


@pytest.mark.unit
def test_openai_mid_stream_generic_error_yields_error_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-quota mid-stream error must yield an error token rather than raising."""
    _patch_quota_helpers(
        monkeypatch, quota_exc_type=_FakeQuotaError, rate_exc_type=_FakeRateLimitError)

    def _bad_iter():
        yield unittest.mock.MagicMock(choices=[unittest.mock.MagicMock(delta=unittest.mock.MagicMock(content="tok1"))])
        raise RuntimeError("unexpected stream failure")

    fake_client = unittest.mock.MagicMock()
    fake_client.chat.completions.create.return_value = _bad_iter()

    provider = _make_openai_provider(monkeypatch, fake_client)
    result = provider.complete(
        [{"role": "user", "content": "hi"}], stream=True)

    chunks = list(result)
    assert chunks[0] == "tok1"
    assert any("[OpenAI error:" in c for c in chunks)
