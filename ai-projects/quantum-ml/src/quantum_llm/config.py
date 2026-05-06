"""
Configuration settings for the Quantum-Powered LLM module.

Supports dataclass-based config (no pydantic dependency required).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal, Optional


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

    @classmethod
    def from_env(cls) -> "QuantumLLMConfig":
        """Build config from environment variables."""
        # The `type: ignore[arg-type]` is suppressed because `os.getenv` returns
        # `str | None`; we validate and fall back to "auto" if the value is invalid.
        raw_backend = os.getenv("QUANTUM_LLM_BACKEND", "auto")
        valid_backends = {"auto", "qiskit", "pennylane", "classical"}
        backend_val = raw_backend if raw_backend in valid_backends else "auto"
        return cls(
            backend=backend_val,  # type: ignore[arg-type]
            num_qubits=int(os.getenv("QUANTUM_LLM_QUBITS", "4")),
            shots=int(os.getenv("QUANTUM_LLM_SHOTS", "512")),
            num_layers=int(os.getenv("QUANTUM_LLM_LAYERS", "2")),
            top_k=int(os.getenv("QUANTUM_LLM_TOP_K", "10")),
            temperature_blend=float(os.getenv("QUANTUM_LLM_TEMP_BLEND", "0.3")),
            provider=os.getenv("QUANTUM_LLM_PROVIDER", "auto"),
            model=os.getenv("QUANTUM_LLM_MODEL"),
            temperature=float(os.getenv("QUANTUM_LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("QUANTUM_LLM_MAX_TOKENS", "512")),
            max_prompt_chars=int(os.getenv("QUANTUM_LLM_MAX_PROMPT_CHARS", "8000")),
            max_tokens_cap=int(os.getenv("QUANTUM_LLM_MAX_TOKENS_CAP", "2048")),
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
