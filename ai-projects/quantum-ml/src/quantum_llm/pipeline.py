"""
QuantumLLMPipeline — wires sampler + embeddings + router together.

Exposes:
- ``async generate(prompt, **kwargs)`` → JSON-serialisable dict
- ``async stream(prompt, **kwargs)``   → async generator of SSE-compatible chunks

The SSE format mirrors ``/api/chat/stream``:
  ``data: {"delta": "..."}\n\n``
  final: ``data: [DONE]\n\n``
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator
from typing import Any

import numpy as np

from .config import QuantumLLMConfig
from .quantum_embeddings import QuantumEmbeddingTransformer
from .quantum_router import QuantumRouter
from .quantum_sampler import QuantumSampler, _active_backend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_detect_provider():
    """Try to import detect_provider from the existing chat-cli stack."""
    try:
        import sys
        from pathlib import Path

        # Walk up to find the repo root (sentinel: pyproject.toml or .git)
        current = Path(__file__).resolve()
        repo_root = None
        for parent in current.parents:
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                repo_root = parent
                break
        if repo_root is None:
            return None

        chat_src = repo_root / "ai-projects" / "chat-cli" / "src"
        if not chat_src.exists():
            return None
        if str(chat_src) not in sys.path:
            sys.path.insert(0, str(chat_src))

        from chat_providers import detect_provider  # type: ignore

        return detect_provider
    except ImportError:
        return None


def _make_local_provider():
    """Return a minimal no-dependency provider that echoes the prompt."""

    class _EchoProvider:
        name = "local-echo"

        def complete(self, messages, stream=False):
            text = messages[-1].get("content", "") if messages else ""
            return f"[quantum-llm echo] {text}"

    return _EchoProvider()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class QuantumLLMPipeline:
    """
    End-to-end Quantum-Powered LLM pipeline.

    Combines:
    1. QuantumRouter  — picks the best downstream LLM provider
    2. QuantumEmbeddingTransformer — transforms the prompt embedding
    3. QuantumSampler — re-weights token sampling probabilities
    4. Downstream LLM provider — generates actual text

    Parameters
    ----------
    config : QuantumLLMConfig, optional
        Pipeline configuration.  Defaults to ``QuantumLLMConfig.from_env()``.
    """

    def __init__(self, config: QuantumLLMConfig | None = None) -> None:
        self.config = config or QuantumLLMConfig.from_env()
        cfg = self.config

        self.sampler = QuantumSampler(
            backend=cfg.backend,
            num_qubits=cfg.num_qubits,
            shots=cfg.shots,
            num_layers=cfg.num_layers,
            cache_enabled=cfg.cache_enabled,
            cache_max_size=cfg.cache_max_size,
            cache_ttl_seconds=cfg.cache_ttl_seconds,
        )
        self.embedder = QuantumEmbeddingTransformer(
            backend=cfg.backend,
            num_qubits=cfg.num_qubits,
            num_layers=cfg.num_layers,
        )
        self.router = QuantumRouter(
            backend=cfg.backend,
            num_qubits=cfg.num_qubits,
        )

        # Effective (resolved) backend
        self.effective_backend = _active_backend(cfg.backend)
        self._detect_provider = _resolve_detect_provider()
        logger.info(
            "QuantumLLMPipeline ready: backend=%s, provider=%s",
            self.effective_backend,
            cfg.provider,
        )

    # ------------------------------------------------------------------
    # Provider resolution
    # ------------------------------------------------------------------

    def _get_provider(self, prompt: str, explicit_provider: str | None = None):
        """Resolve and return a chat provider instance."""
        provider_name = explicit_provider or self.config.provider

        # Let the quantum router pick if "auto"
        if provider_name == "auto" and self._detect_provider is None:
            provider_name = self.router.route(prompt)

        if self._detect_provider is not None:
            try:
                provider, _ = self._detect_provider(
                    explicit=provider_name if provider_name != "auto" else None,
                    model_override=self.config.model,
                    temperature=self.config.temperature,
                    max_output_tokens=min(
                        self.config.max_tokens, self.config.max_tokens_cap
                    ),
                )
                return provider
            except Exception as exc:  # noqa: BLE001
                logger.warning("detect_provider failed (%s), using echo fallback", exc)

        return _make_local_provider()

    # ------------------------------------------------------------------
    # Quantum augmentation of a text embedding
    # ------------------------------------------------------------------

    def _augment_embedding(self, text: str) -> np.ndarray:
        """Return quantum-transformed byte embedding for ``text``."""
        raw = np.frombuffer(text[:256].encode("utf-8", errors="replace"), dtype=np.uint8).astype(float)
        raw = raw / 255.0  # normalize to [0, 1]
        return self.embedder.transform(raw)

    # ------------------------------------------------------------------
    # Token re-sampling
    # ------------------------------------------------------------------

    def _resample_response(self, text: str, seed: int | None = None) -> str:
        """
        Apply quantum token re-sampling to a generated text.

        Uses word-level logit simulation: assigns synthetic logits based on
        character frequencies, then re-samples word order.  In a real system
        this hook would receive the raw top-k logits from the LLM.
        """
        words = text.split()
        if len(words) <= 1:
            return text

        # Synthetic logits: prefer shorter words (simulate token probability)
        logits = [-len(w) * 0.1 for w in words]
        k = min(len(words), self.config.top_k)
        top_logits = sorted(logits, reverse=True)[:k]

        _ = self.sampler.sample(
            top_logits,
            blend_factor=self.config.temperature_blend,
            seed=seed,
        )
        # Keep original text but note sampling happened (in production you'd
        # use the sampled index to select a continuation token)
        return text

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def generate(
        self,
        prompt: str,
        provider: str | None = None,
        seed: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Generate a completion for ``prompt`` (non-streaming).

        Parameters
        ----------
        prompt : str
            User prompt.
        provider : str, optional
            Override provider selection.
        seed : int, optional
            Random seed for reproducibility.

        Returns
        -------
        dict with keys: response, provider, backend, qubits, shots, latency_ms
        """
        # Validate
        if len(prompt) > self.config.max_prompt_chars:
            raise ValueError(
                f"Prompt too long: {len(prompt)} chars (max {self.config.max_prompt_chars})"
            )

        t0 = time.monotonic()

        # Empty / whitespace-only prompts are handled gracefully without calling
        # the LLM provider, which rejects empty message content.
        if not prompt.strip():
            latency_ms = round((time.monotonic() - t0) * 1000, 1)
            return {
                "response": "",
                "provider": "none",
                "backend": self.effective_backend,
                "qubits": self.config.num_qubits,
                "shots": self.config.shots,
                "embedding_dim": 0,
                "embedding_norm": 0.0,
                "latency_ms": latency_ms,
                "quantum_augmented": False,
            }

        # Quantum embedding augmentation (run in thread to avoid blocking)
        if self.config.use_thread:
            embedding = await asyncio.to_thread(self._augment_embedding, prompt)
        else:
            embedding = self._augment_embedding(prompt)

        # Provider selection
        llm_provider = self._get_provider(prompt, provider)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # LLM call (blocking — run in thread)
        def _call():
            result = llm_provider.complete(messages, stream=False)
            if isinstance(result, str):
                return result
            if isinstance(result, bytes):
                return result.decode("utf-8", errors="replace")
            try:
                return "".join(str(chunk) for chunk in result)
            except Exception:
                return str(result)

        if self.config.use_thread:
            raw_response = await asyncio.to_thread(_call)
        else:
            raw_response = _call()

        # Quantum re-sampling
        response = self._resample_response(raw_response, seed=seed)

        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        provider_name = getattr(llm_provider, "name", str(type(llm_provider).__name__))

        return {
            "response": response,
            "provider": provider_name,
            "backend": self.effective_backend,
            "qubits": self.config.num_qubits,
            "shots": self.config.shots,
            "embedding_dim": int(embedding.size),
            "embedding_norm": float(np.linalg.norm(embedding)),
            "latency_ms": latency_ms,
            "quantum_augmented": True,
        }

    async def stream(
        self,
        prompt: str,
        provider: str | None = None,
        seed: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream SSE chunks for ``prompt``.

        Yields strings in SSE format:
        ``"data: {"delta": "..."}\n\n"``
        Final chunk: ``"data: [DONE]\n\n"``

        Parameters
        ----------
        prompt : str
        provider : str, optional
        seed : int, optional
        """
        if len(prompt) > self.config.max_prompt_chars:
            yield f'data: {json.dumps({"error": "Prompt too long"})}\n\n'
            yield "data: [DONE]\n\n"
            return

        t0 = time.monotonic()
        llm_provider = self._get_provider(prompt, provider)
        provider_name = getattr(llm_provider, "name", str(type(llm_provider).__name__))

        # Meta event
        meta = {
            "provider": provider_name,
            "backend": self.effective_backend,
            "qubits": self.config.num_qubits,
            "shots": self.config.shots,
        }
        yield f"event: meta\ndata: {json.dumps(meta)}\n\n"

        messages = [{"role": "user", "content": prompt}]

        def _stream_call():
            try:
                result = llm_provider.complete(messages, stream=True)
                if isinstance(result, str):
                    return [result]
                return result
            except Exception as exc:  # noqa: BLE001
                return [f"[error: {exc}]"]

        if self.config.use_thread:
            chunks = await asyncio.to_thread(_stream_call)
        else:
            chunks = _stream_call()

        full_text = ""
        for chunk in chunks:
            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8", errors="replace")
            full_text += chunk
            yield f'data: {json.dumps({"delta": chunk})}\n\n'

        # Apply quantum re-sampling metadata (just signals to client that it happened)
        _ = self._resample_response(full_text, seed=seed)

        latency_ms = round((time.monotonic() - t0) * 1000, 1)
        done_meta = {"latency_ms": latency_ms, "quantum_augmented": True}
        yield f'data: {json.dumps(done_meta)}\n\n'
        yield "data: [DONE]\n\n"

    def status(self) -> dict[str, Any]:
        """Return a health/status dict for the ``/api/quantum-llm/status`` endpoint."""
        cache_stats = self.sampler.cache_stats()
        return {
            "backend": self.effective_backend,
            "fallback": self.effective_backend == "classical",
            "num_qubits": self.config.num_qubits,
            "shots": self.config.shots,
            "num_layers": self.config.num_layers,
            "top_k": self.config.top_k,
            "temperature_blend": self.config.temperature_blend,
            "provider": self.config.provider,
            "model": self.config.model,
            "router_providers": self.router.providers,
            "router_backend": self.router.effective_backend,
            "embedder_backend": self.embedder.effective_backend,
            "sampler_backend": self.sampler.effective_backend,
            "cache": {
                "enabled": self.config.cache_enabled,
                "stats": cache_stats,
            },
        }
