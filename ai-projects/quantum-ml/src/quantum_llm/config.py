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


def _read_backend_env(name: str, default: str = "auto") -> str:
    """Return validated backend env var value or fallback."""
    raw = (os.getenv(name, default) or default).strip()
    valid_backends = {"auto", "qiskit", "pennylane", "classical"}
    return raw if raw in valid_backends else default


def _coerce_int(value: object, default: int, minimum: int = 1) -> int:
    """Convert value to int with safe default and lower bound."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _coerce_float(value: object, default: float) -> float:
    """Convert value to float with safe default."""
    try:
        return float(value)
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

        self.num_qubits = _coerce_int(self.num_qubits, default=4, minimum=1)
        self.shots = _coerce_int(self.shots, default=512, minimum=1)
        self.num_layers = _coerce_int(self.num_layers, default=2, minimum=1)
        self.top_k = _coerce_int(self.top_k, default=10, minimum=1)

        self.temperature_blend = min(
            1.0, max(0.0, _coerce_float(self.temperature_blend, default=0.3))
        )
        self.temperature = max(0.0, _coerce_float(self.temperature, default=0.7))

        self.max_prompt_chars = _coerce_int(
            self.max_prompt_chars, default=8000, minimum=1
        )
        self.max_tokens_cap = _coerce_int(self.max_tokens_cap, default=2048, minimum=1)
        self.max_tokens = _coerce_int(self.max_tokens, default=512, minimum=1)
        self.max_tokens = min(self.max_tokens, self.max_tokens_cap)

        self.provider = (self.provider or "auto").strip()

    @classmethod
    def from_env(cls) -> "QuantumLLMConfig":
        """Build config from environment variables."""
        return cls(
            backend=_read_backend_env("QUANTUM_LLM_BACKEND", "auto"),
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
