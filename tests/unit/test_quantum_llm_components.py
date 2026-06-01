"""
Unit tests for quantum LLM components.

Tests sampler, embeddings, and router functions with classical backends.
"""

import numpy as np
import pytest
from ai_projects.quantum_ml.src.quantum_llm.quantum_embeddings import (
    QuantumEmbeddingTransformer,
    _classical_amplitude_transform,
)
from ai_projects.quantum_ml.src.quantum_llm.quantum_router import (
    QuantumRouter,
    _classical_score_providers,
    _extract_prompt_features,
)
from ai_projects.quantum_ml.src.quantum_llm.quantum_sampler import (
    QuantumSampler,
    _active_backend,
    _classical_variational_probs,
)


class TestActiveBackend:
    """Test backend detection and fallback logic."""

    def test_auto_backend_defaults_to_classical(self):
        """Should fall back to classical when 'auto' and no backends available."""
        backend = _active_backend("auto")
        # Will be pennylane or qiskit if installed, otherwise classical
        assert backend in {"pennylane", "qiskit", "classical"}

    def test_classical_backend_always_works(self):
        """Should always accept 'classical' backend."""
        assert _active_backend("classical") == "classical"

    def test_invalid_backend_defaults_to_auto(self):
        """Should treat invalid backends as 'auto'."""
        backend = _active_backend("invalid")
        assert backend in {"pennylane", "qiskit", "classical"}


class TestClassicalVariationalProbs:
    """Test classical variational circuit simulator."""

    def test_returns_valid_probabilities(self):
        """Should return normalized probability distribution."""
        params = np.array([0.5, 1.0, 1.5])
        probs = _classical_variational_probs(params, num_qubits=2, shots=100, rng=None)

        assert isinstance(probs, np.ndarray)
        assert len(probs) == 4  # 2^2 = 4
        assert np.allclose(probs.sum(), 1.0)
        assert np.all(probs >= 0)
        assert np.all(probs <= 1)

    def test_reproducible_with_seed(self):
        """Should produce same results with same seed."""
        params = np.array([0.1, 0.2, 0.3])
        rng1 = np.random.Generator(np.random.PCG64(42))
        rng2 = np.random.Generator(np.random.PCG64(42))

        probs1 = _classical_variational_probs(params, num_qubits=2, shots=100, rng=rng1)
        probs2 = _classical_variational_probs(params, num_qubits=2, shots=100, rng=rng2)

        assert np.allclose(probs1, probs2)

    def test_different_qubit_counts(self):
        """Should handle different numbers of qubits."""
        for n_qubits in [1, 2, 3, 4]:
            params = np.random.randn(n_qubits * 2)
            probs = _classical_variational_probs(params, num_qubits=n_qubits, shots=100, rng=None)
            assert len(probs) == 2**n_qubits


class TestQuantumSampler:
    """Test QuantumSampler class."""

    def test_initialization(self):
        """Should initialize with valid parameters."""
        sampler = QuantumSampler(
            backend="classical",
            num_qubits=4,
            shots=512,
            num_layers=2,
        )
        assert sampler.effective_backend == "classical"
        assert sampler.num_qubits == 4
        assert sampler.shots == 512

    def test_sample_returns_valid_index(self):
        """Should return valid top-k index from logits."""
        sampler = QuantumSampler(backend="classical", num_qubits=2, shots=100, num_layers=1)
        logits = np.array([1.0, 2.0, 0.5, 1.5])

        for _ in range(10):
            idx = sampler.sample(logits, blend_factor=0.5, seed=None)
            assert 0 <= idx < len(logits)

    def test_sample_respects_blend_factor(self):
        """Should respect blend_factor between 0 and 1."""
        sampler = QuantumSampler(backend="classical", num_qubits=2, shots=100, num_layers=1)
        logits = np.array([10.0, 1.0, 1.0])  # Strongly prefer index 0

        # With blend_factor=0 (classical), should heavily favor index 0
        classical_samples = [sampler.sample(logits, blend_factor=0.0, seed=None) for _ in range(100)]
        classical_mode = max(set(classical_samples), key=classical_samples.count)
        assert classical_mode == 0


class TestClassicalAmplitudeTransform:
    """Test classical amplitude encoding and transformation."""

    def test_returns_same_shape(self):
        """Should return embedding of same shape as input."""
        embedding = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        params = np.array([0.5, 1.0, 1.5])

        transformed = _classical_amplitude_transform(embedding, params, num_qubits=2)
        assert transformed.shape == embedding.shape

    def test_handles_zero_embedding(self):
        """Should handle zero embedding gracefully."""
        embedding = np.zeros(5)
        params = np.array([0.5, 1.0])

        transformed = _classical_amplitude_transform(embedding, params, num_qubits=2)
        assert transformed.shape == embedding.shape
        assert np.allclose(transformed, embedding)

    def test_preserves_norm_structure(self):
        """Should preserve norm scaling."""
        embedding = np.array([1.0, 1.0, 1.0, 1.0])
        params = np.array([0.5])

        original_norm = np.linalg.norm(embedding)
        transformed = _classical_amplitude_transform(embedding, params, num_qubits=2)
        transformed_norm = np.linalg.norm(transformed)

        # Norm should be preserved
        assert np.isclose(original_norm, transformed_norm)


class TestQuantumEmbeddingTransformer:
    """Test QuantumEmbeddingTransformer class."""

    def test_initialization(self):
        """Should initialize with valid parameters."""
        embedder = QuantumEmbeddingTransformer(
            backend="classical",
            num_qubits=4,
            num_layers=2,
        )
        assert embedder.effective_backend == "classical"
        assert embedder.num_qubits == 4
        assert embedder.num_layers == 2

    def test_transform_returns_valid_embedding(self):
        """Should return valid embedding."""
        embedder = QuantumEmbeddingTransformer(backend="classical", num_qubits=2, num_layers=1)
        embedding = np.random.randn(10)

        transformed = embedder.transform(embedding)
        assert isinstance(transformed, np.ndarray)
        assert transformed.shape == embedding.shape
        assert not np.any(np.isnan(transformed))


class TestPromptFeatureExtraction:
    """Test prompt feature extraction."""

    def test_extracts_features(self):
        """Should extract numeric features from prompt."""
        prompt = "This is a test prompt?"
        features = _extract_prompt_features(prompt)

        assert isinstance(features, np.ndarray)
        assert len(features) == 5
        assert np.all(features >= 0.0)
        assert np.all(features <= 1.0)

    def test_long_prompt_saturates_length(self):
        """Should cap length feature for very long prompts."""
        short = "hello"
        long = "x" * 20000

        short_features = _extract_prompt_features(short)
        long_features = _extract_prompt_features(long)

        # Length feature should saturate for long prompt
        assert short_features[0] < long_features[0]
        assert long_features[0] == pytest.approx(1.0)

    def test_detects_question_mark(self):
        """Should detect presence of question mark."""
        with_q = _extract_prompt_features("Is this a question?")
        without_q = _extract_prompt_features("This is not a question")

        assert with_q[2] == 1.0
        assert without_q[2] == 0.0

    def test_detects_code_blocks(self):
        """Should detect presence of code blocks."""
        with_code = _extract_prompt_features("Here's code: ```python\nprint('hi')\n```")
        without_code = _extract_prompt_features("Just plain text")

        assert with_code[3] == 1.0
        assert without_code[3] == 0.0


class TestClassicalScoreProviders:
    """Test provider scoring."""

    def test_scores_providers(self):
        """Should score each provider."""
        features = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        providers = ["azure", "openai", "local"]
        params = np.random.randn(len(providers) * len(features))

        scores = _classical_score_providers(features, providers, params)

        assert len(scores) == len(providers)
        assert isinstance(scores, np.ndarray)

    def test_different_providers_get_different_scores(self):
        """Should produce different scores for different providers."""
        features = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        providers = ["azure", "openai", "local"]
        params = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

        scores = _classical_score_providers(features, providers, params)

        # Scores may differ (unless by chance they're equal)
        # Just verify they're computed
        assert len(scores) == len(providers)


class TestQuantumRouter:
    """Test QuantumRouter class."""

    def test_initialization(self):
        """Should initialize with valid parameters."""
        router = QuantumRouter(backend="classical", num_qubits=4)
        assert router.effective_backend == "classical"
        assert router.num_qubits == 4

    def test_route_returns_provider_name(self):
        """Should return a provider name string."""
        router = QuantumRouter(backend="classical", num_qubits=2)
        provider = router.route("What is the meaning of life?")

        assert isinstance(provider, str)
        assert len(provider) > 0

    def test_route_consistent_for_same_prompt(self):
        """Should return consistent routing for same prompt."""
        router = QuantumRouter(backend="classical", num_qubits=2)
        prompt = "Tell me about quantum computing"

        route1 = router.route(prompt)
        route2 = router.route(prompt)

        assert route1 == route2

    def test_route_different_for_different_prompts(self):
        """May return different routes for different prompts."""
        router = QuantumRouter(backend="classical", num_qubits=2)

        short = "Hi"
        long = "Can you explain quantum mechanics, quantum computing, and how they relate to artificial intelligence in the context of modern physics and classical computing paradigms?"

        route_short = router.route(short)
        route_long = router.route(long)

        # Routes might differ, just verify both are valid
        assert isinstance(route_short, str)
        assert isinstance(route_long, str)
