"""
Unit tests for the Quantum-Powered LLM module.

All tests use the classical (numpy) fallback — no quantum SDK required.
Tests are discoverable by ``python scripts/test_runner.py --unit``.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure the quantum_llm package is importable
_QUANTUM_LLM_SRC = Path(__file__).resolve().parents[1] / "ai-projects" / "quantum-ml" / "src"
if str(_QUANTUM_LLM_SRC) not in sys.path:
    sys.path.insert(0, str(_QUANTUM_LLM_SRC))

from quantum_llm import (  # noqa: E402
    QuantumEmbeddingTransformer,
    QuantumLLMConfig,
    QuantumLLMPipeline,
    QuantumRouter,
    QuantumSampler,
)

# ===========================================================================
# Config tests
# ===========================================================================


class TestQuantumLLMConfig:
    def test_defaults(self):
        cfg = QuantumLLMConfig()
        assert cfg.backend == "auto"
        assert cfg.num_qubits == 4
        assert cfg.shots == 512
        assert cfg.top_k == 10
        assert cfg.max_tokens == 512
        assert cfg.max_prompt_chars == 8000

    def test_to_dict(self):
        cfg = QuantumLLMConfig(backend="classical", num_qubits=2)
        d = cfg.to_dict()
        assert d["backend"] == "classical"
        assert d["num_qubits"] == 2

    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("QUANTUM_LLM_BACKEND", "classical")
        monkeypatch.setenv("QUANTUM_LLM_QUBITS", "2")
        monkeypatch.setenv("QUANTUM_LLM_SHOTS", "128")
        cfg = QuantumLLMConfig.from_env()
        assert cfg.backend == "classical"
        assert cfg.num_qubits == 2
        assert cfg.shots == 128

    def test_from_env_preserves_valid_backend(self, monkeypatch):
        monkeypatch.setenv("QUANTUM_LLM_BACKEND", "qiskit")
        cfg = QuantumLLMConfig.from_env()
        assert cfg.backend == "qiskit"

    def test_from_env_invalid_backend_falls_back_to_auto(self, monkeypatch):
        monkeypatch.setenv("QUANTUM_LLM_BACKEND", "invalid-backend")
        cfg = QuantumLLMConfig.from_env()
        assert cfg.backend == "auto"

    def test_from_env_invalid_numeric_values_fallback(self, monkeypatch):
        monkeypatch.setenv("QUANTUM_LLM_QUBITS", "abc")
        monkeypatch.setenv("QUANTUM_LLM_SHOTS", "NaN")
        monkeypatch.setenv("QUANTUM_LLM_LAYERS", "bad")
        monkeypatch.setenv("QUANTUM_LLM_TEMPERATURE", "oops")

        cfg = QuantumLLMConfig.from_env()

        assert cfg.num_qubits == 4
        assert cfg.shots == 512
        assert cfg.num_layers == 2
        assert cfg.temperature == 0.7

    def test_from_env_clamps_numeric_values_to_valid_ranges(self, monkeypatch):
        monkeypatch.setenv("QUANTUM_LLM_QUBITS", "0")
        monkeypatch.setenv("QUANTUM_LLM_SHOTS", "-1")
        monkeypatch.setenv("QUANTUM_LLM_LAYERS", "0")
        monkeypatch.setenv("QUANTUM_LLM_TOP_K", "0")
        monkeypatch.setenv("QUANTUM_LLM_TEMP_BLEND", "2.5")
        monkeypatch.setenv("QUANTUM_LLM_TEMPERATURE", "-9")
        monkeypatch.setenv("QUANTUM_LLM_MAX_TOKENS", "9999")
        monkeypatch.setenv("QUANTUM_LLM_MAX_TOKENS_CAP", "128")

        cfg = QuantumLLMConfig.from_env()

        assert cfg.num_qubits == 1
        assert cfg.shots == 1
        assert cfg.num_layers == 1
        assert cfg.top_k == 1
        assert cfg.temperature_blend == 1.0
        assert cfg.temperature == 0.0
        assert cfg.max_tokens == 128

    def test_direct_constructor_coerces_invalid_types(self):
        cfg = QuantumLLMConfig(
            backend="invalid",
            num_qubits="bad",  # type: ignore[arg-type]
            shots="oops",  # type: ignore[arg-type]
            num_layers="bad",  # type: ignore[arg-type]
            top_k="bad",  # type: ignore[arg-type]
            temperature_blend="bad",  # type: ignore[arg-type]
            temperature="bad",  # type: ignore[arg-type]
            max_tokens="bad",  # type: ignore[arg-type]
            max_tokens_cap="bad",  # type: ignore[arg-type]
            max_prompt_chars="bad",  # type: ignore[arg-type]
        )
        assert cfg.backend == "auto"
        assert cfg.num_qubits == 4
        assert cfg.shots == 512
        assert cfg.num_layers == 2
        assert cfg.top_k == 10
        assert cfg.temperature_blend == 0.3
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 512
        assert cfg.max_tokens_cap == 2048
        assert cfg.max_prompt_chars == 8000


# ===========================================================================
# QuantumSampler tests
# ===========================================================================


class TestQuantumSampler:
    def _make_sampler(self, **kwargs) -> QuantumSampler:
        return QuantumSampler(backend="classical", num_qubits=4, shots=128, seed=42, **kwargs)

    def test_init_classical(self):
        s = self._make_sampler()
        assert s.effective_backend == "classical"

    def test_sample_returns_valid_index(self):
        s = self._make_sampler()
        logits = [1.0, 2.0, 0.5, 0.1]
        idx = s.sample(logits, blend_factor=0.3)
        assert 0 <= idx < len(logits)

    def test_sample_single_logit(self):
        s = self._make_sampler()
        idx = s.sample([3.0], blend_factor=0.5)
        assert idx == 0

    def test_sample_empty_logits(self):
        s = self._make_sampler()
        idx = s.sample([], blend_factor=0.3)
        assert idx == 0

    def test_sample_deterministic_with_seed(self):
        s1 = QuantumSampler(backend="classical", num_qubits=4, shots=128, seed=99)
        s2 = QuantumSampler(backend="classical", num_qubits=4, shots=128, seed=99)
        logits = [1.0, 2.0, 0.5, 1.5, 0.8]
        assert s1.sample(logits, seed=7) == s2.sample(logits, seed=7)

    def test_blend_factor_zero_is_classical(self):
        """With blend_factor=0, result should be drawn from pure classical softmax."""
        s = self._make_sampler()
        logits = [5.0, 0.0, 0.0, 0.0]  # strongly favours index 0
        # With a fixed seed and strongly biased logits, index 0 must always win
        results = [s.sample(logits, blend_factor=0.0, seed=i) for i in range(20)]
        # With logit[0] = 5.0 vs rest = 0.0, softmax gives P(0) ≈ 0.9994
        # Index 0 must win at least 90% of the time
        assert results.count(0) >= 18

    def test_blend_factor_above_one_is_clamped(self):
        """blend_factor > 1 must be clamped, not raise on negative probabilities."""
        s = self._make_sampler()
        logits = [3.0, 1.0, 0.5, 0.2]
        # Without clamping this raised ValueError("Probabilities are not non-negative").
        idx = s.sample(logits, blend_factor=1.5, seed=1)
        assert 0 <= idx < len(logits)

    def test_blend_factor_below_zero_is_clamped(self):
        """blend_factor < 0 must be clamped to a pure-classical blend."""
        s = self._make_sampler()
        logits = [5.0, 0.0, 0.0, 0.0]
        # Clamped to 0.0 => pure classical, so the strongly favoured index 0 wins.
        results = [s.sample(logits, blend_factor=-0.5, seed=i) for i in range(20)]
        assert results.count(0) >= 18

    def test_blend_factor_above_one_matches_pure_quantum(self):
        """Clamping blend_factor=1.5 yields the same draw as blend_factor=1.0."""
        s = self._make_sampler()
        logits = [3.0, 1.0, 0.5, 0.2]
        assert s.sample(logits, blend_factor=1.5, seed=11) == s.sample(
            logits, blend_factor=1.0, seed=11
        )


# ===========================================================================
# QuantumEmbeddingTransformer tests
# ===========================================================================


class TestQuantumEmbeddingTransformer:
    def _make_transformer(self, **kwargs) -> QuantumEmbeddingTransformer:
        return QuantumEmbeddingTransformer(backend="classical", num_qubits=4, num_layers=1, seed=42, **kwargs)

    def test_transform_preserves_shape(self):
        t = self._make_transformer()
        emb = np.random.default_rng(0).random(16)
        out = t.transform(emb)
        assert out.shape == emb.shape

    def test_transform_zero_embedding(self):
        t = self._make_transformer()
        emb = np.zeros(8, dtype=float)
        out = t.transform(emb)
        assert out.shape == emb.shape
        assert np.allclose(out, 0.0)

    def test_transform_rejects_2d(self):
        t = self._make_transformer()
        with pytest.raises(ValueError, match="1-D"):
            t.transform(np.ones((4, 4)))

    def test_update_params(self):
        t = self._make_transformer()
        new_params = np.zeros(t._params.shape)
        t.update_params(new_params)
        assert np.allclose(t._params, 0.0)

    def test_transform_different_dims(self):
        t = self._make_transformer()
        for dim in [4, 8, 16, 32, 64]:
            emb = np.ones(dim)
            out = t.transform(emb)
            assert out.shape == (dim,)


# ===========================================================================
# QuantumRouter tests
# ===========================================================================


class TestQuantumRouter:
    def _make_router(self, providers=None, **kwargs) -> QuantumRouter:
        return QuantumRouter(
            providers=providers or ["azure", "openai", "local"],
            backend="classical",
            num_qubits=4,
            seed=42,
            **kwargs,
        )

    def test_route_returns_valid_provider(self):
        r = self._make_router()
        chosen = r.route("Hello, world!")
        assert chosen in ["azure", "openai", "local"]

    def test_route_single_provider(self):
        r = self._make_router(providers=["local"])
        assert r.route("test") == "local"

    def test_route_excludes_providers(self):
        r = self._make_router(providers=["azure", "openai", "local"])
        chosen = r.route("Hello", exclude=["azure", "openai"])
        assert chosen == "local"

    def test_route_all_excluded_falls_back(self):
        r = self._make_router(providers=["azure"])
        # Even if all excluded, falls back to first provider
        result = r.route("Hello", exclude=["azure"])
        assert result == "azure"

    def test_route_with_scores_returns_dict(self):
        r = self._make_router()
        chosen, scores = r.route_with_scores("What is quantum?")
        assert chosen in r.providers
        assert set(scores.keys()) == set(r.providers)

    def test_route_empty_providers(self):
        r = QuantumRouter(providers=[], backend="classical")
        result = r.route("test")
        # Empty providers list falls back to default providers list
        assert result in ["azure", "openai", "lmstudio", "local"]

    def test_route_exclusion_is_identity_stable(self):
        """Excluding a non-winning provider must not change which provider wins.

        Regression: scores were previously computed over the filtered candidate
        list, so a provider's weight slice depended on its position after
        exclusion rather than its identity. Excluding any non-winner reshuffled
        the params and could flip the chosen provider.
        """
        r = self._make_router(providers=["azure", "openai", "lmstudio", "local"])
        prompt = "Hello world, please route me."
        winner = r.route(prompt)
        # Pick any provider that is not the winner and exclude it.
        non_winner = next(p for p in r.providers if p != winner)
        assert r.route(prompt, exclude=[non_winner]) == winner

    def test_route_matches_score_ranking(self):
        """route() must return the highest-scoring non-excluded provider."""
        r = self._make_router(providers=["azure", "openai", "lmstudio", "local"])
        prompt = "What is the best provider for this query?"
        _, scores = r.route_with_scores(prompt)
        # No exclusion: route() should equal the global argmax provider.
        expected = max(scores, key=lambda k: scores[k])
        assert r.route(prompt) == expected
        # Excluding the winner: route() should equal the best of the rest.
        rest = {p: s for p, s in scores.items() if p != expected}
        expected_runner_up = max(rest, key=lambda k: rest[k])
        assert r.route(prompt, exclude=[expected]) == expected_runner_up


# ===========================================================================
# QuantumLLMPipeline tests (integration with classical fallback + mock provider)
# ===========================================================================


class _MockProvider:
    """Minimal mock LLM provider for pipeline integration tests."""

    name = "mock-provider"

    def __init__(self, response: str = "mock response"):
        self._response = response

    def complete(self, messages, stream=False):
        if stream:
            return iter(self._response.split())
        return self._response


class TestQuantumLLMPipeline:
    def _make_pipeline(self, response="Hello from mock", **cfg_kwargs) -> QuantumLLMPipeline:
        cfg = QuantumLLMConfig(
            backend="classical",
            num_qubits=2,
            shots=64,
            use_thread=False,
            **cfg_kwargs,
        )
        pipeline = QuantumLLMPipeline(config=cfg)
        # Inject mock provider
        pipeline._get_provider = lambda prompt, provider=None: _MockProvider(response)
        return pipeline

    def test_generate_returns_dict(self):
        pipeline = self._make_pipeline()
        result = asyncio.run(pipeline.generate("Test prompt"))
        assert isinstance(result, dict)
        assert "response" in result
        assert "backend" in result
        assert "latency_ms" in result
        assert result["quantum_augmented"] is True

    def test_generate_response_content(self):
        pipeline = self._make_pipeline(response="Quantum rocks!")
        result = asyncio.run(pipeline.generate("Hello"))
        assert result["response"] == "Quantum rocks!"

    def test_generate_deterministic_with_seed(self):
        pipeline1 = self._make_pipeline(response="deterministic output")
        pipeline2 = self._make_pipeline(response="deterministic output")
        r1 = asyncio.run(pipeline1.generate("Test", seed=42))
        r2 = asyncio.run(pipeline2.generate("Test", seed=42))
        assert r1["response"] == r2["response"]

    def test_generate_rejects_long_prompt(self):
        pipeline = self._make_pipeline(max_prompt_chars=10)
        with pytest.raises(ValueError, match="too long"):
            asyncio.run(pipeline.generate("A" * 11))

    def test_stream_yields_sse_chunks(self):
        pipeline = self._make_pipeline(response="Hello world from quantum")

        async def collect():
            chunks = []
            async for chunk in pipeline.stream("Test"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect())
        assert any("[DONE]" in c for c in chunks)
        assert any("delta" in c for c in chunks)
        assert any("meta" in c for c in chunks)

    def test_stream_ends_with_done(self):
        pipeline = self._make_pipeline()

        async def collect():
            chunks = []
            async for chunk in pipeline.stream("Ping"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect())
        assert chunks[-1].strip() == "data: [DONE]"

    def test_stream_rejects_long_prompt(self):
        pipeline = self._make_pipeline(max_prompt_chars=5)

        async def collect():
            chunks = []
            async for chunk in pipeline.stream("TOOLONG"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect())
        assert any("error" in c for c in chunks)
        assert any("[DONE]" in c for c in chunks)

    def test_status_dict(self):
        pipeline = self._make_pipeline()
        s = pipeline.status()
        assert s["backend"] == "classical"
        assert s["fallback"] is True
        assert s["num_qubits"] == 2
        assert "router_providers" in s

    def test_generate_backend_in_response(self):
        pipeline = self._make_pipeline()
        result = asyncio.run(pipeline.generate("Hi"))
        assert result["backend"] == "classical"
        assert result["qubits"] == 2


# ===========================================================================
# Integration test: mock provider, fixed seed, deterministic output
# ===========================================================================


class TestPipelineIntegration:
    """Integration test with mocked LLM provider and fixed random seed."""

    def test_end_to_end_deterministic(self):
        """Full pipeline with classical backend + fixed seed → deterministic."""
        cfg = QuantumLLMConfig(
            backend="classical",
            num_qubits=2,
            shots=64,
            temperature_blend=0.5,
            use_thread=False,
        )
        pipeline = QuantumLLMPipeline(config=cfg)
        pipeline._get_provider = lambda prompt, provider=None: _MockProvider("The answer to everything is quantum.")

        r1 = asyncio.run(pipeline.generate("What is the answer?", seed=42))
        r2 = asyncio.run(pipeline.generate("What is the answer?", seed=42))

        assert r1["response"] == r2["response"]
        assert r1["backend"] == "classical"
        assert r1["quantum_augmented"] is True

    def test_stream_meta_event_contains_backend(self):
        """SSE meta event must contain backend info."""
        import json

        cfg = QuantumLLMConfig(backend="classical", use_thread=False)
        pipeline = QuantumLLMPipeline(config=cfg)
        pipeline._get_provider = lambda prompt, provider=None: _MockProvider("hi")

        async def collect():
            chunks = []
            async for chunk in pipeline.stream("hello"):
                chunks.append(chunk)
            return chunks

        chunks = asyncio.run(collect())
        # Find meta event
        meta_chunks = [c for c in chunks if "event: meta" in c]
        assert meta_chunks, "No meta event emitted"
        meta_data = meta_chunks[0].split("data:", 1)[1].strip()
        meta = json.loads(meta_data)
        assert "backend" in meta
        assert "qubits" in meta
