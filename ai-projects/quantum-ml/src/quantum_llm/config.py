"""
Configuration settings for the Quantum-Powered LLM module.

Supports dataclass-based config (no pydantic dependency required).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Optional


def _read_int_env(name: str, default: int) -> int:
    """Return integer env var value or fallback to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _read_float_env(name: str, default: float) -> float:
    """Return float env var value or fallback to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@dataclass
class QuantumLLMConfig:
    """Settings for QuantumLLMPipeline and its sub-components."""

    # Quantum backend selection
    backend: Literal["auto", "qiskit", "pennylane", "classical"] = "auto"

    # Circuit parameters
    num_qubits: int = 4
    shots: int = 512
    num_layers: int = 2  # variational circuit depth

    # Sampling parameters
    top_k: int = 10
    temperature_blend: float = 0.3  # blend factor between quantum and classical distributions (0=classical, 1=quantum)

    # LLM provider settings
    provider: str = "auto"  # forwarded to detect_provider
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 512

    # Security / validation
    max_prompt_chars: int = 8000
    max_tokens_cap: int = 2048

    # Performance
    use_thread: bool = True  # asyncio.to_thread for blocking quantum calls

    def __post_init__(self) -> None:
        """Normalize and clamp config values to safe, valid ranges."""
        valid_backends = {"auto", "qiskit", "pennylane", "classical"}
        if self.backend not in valid_backends:
            self.backend = "auto"

        self.num_qubits = max(1, int(self.num_qubits))
        self.shots = max(1, int(self.shots))
        self.num_layers = max(1, int(self.num_layers))
        self.top_k = max(1, int(self.top_k))

        self.temperature_blend = min(1.0, max(0.0, float(self.temperature_blend)))
        self.temperature = max(0.0, float(self.temperature))

        self.max_prompt_chars = max(1, int(self.max_prompt_chars))
        self.max_tokens_cap = max(1, int(self.max_tokens_cap))
        self.max_tokens = max(1, int(self.max_tokens))
        if self.max_tokens > self.max_tokens_cap:
            self.max_tokens = self.max_tokens_cap

        provider = (self.provider or "auto").strip()
        self.provider = provider or "auto"

    @classmethod
    def from_env(cls) -> "QuantumLLMConfig":
        """Build config from environment variables."""
        return cls(
            backend=os.getenv("QUANTUM_LLM_BACKEND", "auto"),
            num_qubits=_read_int_env("QUANTUM_LLM_QUBITS", 4),
            shots=_read_int_env("QUANTUM_LLM_SHOTS", 512),
            num_layers=_read_int_env("QUANTUM_LLM_LAYERS", 2),
            top_k=_read_int_env("QUANTUM_LLM_TOP_K", 10),
            temperature_blend=_read_float_env("QUANTUM_LLM_TEMP_BLEND", 0.3),
            provider=os.getenv("QUANTUM_LLM_PROVIDER", "auto"),
            model=os.getenv("QUANTUM_LLM_MODEL"),
            temperature=_read_float_env("QUANTUM_LLM_TEMPERATURE", 0.7),
            max_tokens=_read_int_env("QUANTUM_LLM_MAX_TOKENS", 512),
            max_prompt_chars=_read_int_env("QUANTUM_LLM_MAX_PROMPT_CHARS", 8000),
            max_tokens_cap=_read_int_env("QUANTUM_LLM_MAX_TOKENS_CAP", 2048),
        )

    def to_dict(self) -> dict:
        """Serialize to dict for status/health endpoints."""
        return {
            "backend": self.backend,
            "num_qubits": self.num_qubits,
            "shots": self.shots,
            "num_layers": self.num_layers,
            "top_k": self.top_k,
            "temperature_blend": self.temperature_blend,
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
