"""Unit tests for quantum provider selection behavior in chat_providers."""

from __future__ import annotations

import importlib
import sys
import types
from typing import Any

import pytest

chat_providers: Any = importlib.import_module("chat_providers")
ProviderChoice = chat_providers.ProviderChoice


def _install_fake_quantum_provider(
    monkeypatch: pytest.MonkeyPatch, captured: dict
) -> None:
    """Install a lightweight fake quantum_provider module for deterministic tests."""
    fake_module = types.ModuleType("quantum_provider")

    def _fake_factory(
        model_path: str,
        temperature: float = 0.8,
        max_output_tokens: int = 200,
        **kwargs,
    ):
        captured["model_path"] = model_path
        captured["temperature"] = temperature
        captured["max_output_tokens"] = max_output_tokens
        captured["kwargs"] = kwargs
        return object(), ProviderChoice(
            name="quantum-llm", model=f"quantum-llm ({model_path})"
        )

    fake_module.create_quantum_llm_provider = _fake_factory
    monkeypatch.setitem(sys.modules, "quantum_provider", fake_module)


@pytest.mark.unit
def test_detect_provider_quantum_uses_model_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    _install_fake_quantum_provider(monkeypatch, captured)

    provider, info = chat_providers.detect_provider(
        explicit="quantum",
        model_override="data_out/quantum_llm_training",
        temperature=0.42,
        max_output_tokens=64,
    )

    assert provider is not None
    assert info.name == "quantum-llm"
    assert captured["model_path"] == "data_out/quantum_llm_training"
    assert captured["temperature"] == 0.42
    assert captured["max_output_tokens"] == 64


@pytest.mark.unit
def test_detect_provider_quantum_uses_env_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    _install_fake_quantum_provider(monkeypatch, captured)
    monkeypatch.setenv("QAI_QUANTUM_MODEL_PATH", "data_out/quantum_llm_api")

    provider, info = chat_providers.detect_provider(
        explicit="quantum",
        model_override=None,
    )

    assert provider is not None
    assert info.name == "quantum-llm"
    assert captured["model_path"] == "data_out/quantum_llm_api"


@pytest.mark.unit
def test_detect_provider_quantum_requires_model_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    _install_fake_quantum_provider(monkeypatch, captured)
    monkeypatch.delenv("QAI_QUANTUM_MODEL_PATH", raising=False)
    monkeypatch.delenv("QAI_QUANTUM_MODEL", raising=False)

    with pytest.raises(RuntimeError, match="QAI_QUANTUM_MODEL_PATH"):
        chat_providers.detect_provider(explicit="quantum", model_override=None)
