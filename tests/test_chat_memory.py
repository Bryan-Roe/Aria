"""Tests for shared/chat_memory.py — semantic memory with embedding fallback."""

from __future__ import annotations

import math
import os
from unittest.mock import patch

# We import the private helpers directly for unit-testing pure functions.
import shared.chat_memory as cm

# ---------------------------------------------------------------------------
# _hash_embedding
# ---------------------------------------------------------------------------


class TestHashEmbedding:
    def test_returns_correct_dimension(self):
        vec = cm._hash_embedding("hello world")
        assert len(vec) == cm._LOCAL_DIM  # 256

    def test_all_floats(self):
        vec = cm._hash_embedding("test")
        assert all(isinstance(v, float) for v in vec)

    def test_empty_string_returns_zeros(self):
        vec = cm._hash_embedding("")
        assert all(v == 0.0 for v in vec)

    def test_whitespace_returns_zeros(self):
        vec = cm._hash_embedding("   ")
        assert all(v == 0.0 for v in vec)

    def test_deterministic(self):
        v1 = cm._hash_embedding("quantum computing")
        v2 = cm._hash_embedding("quantum computing")
        assert v1 == v2

    def test_different_inputs_different_vectors(self):
        v1 = cm._hash_embedding("hello")
        v2 = cm._hash_embedding("goodbye")
        assert v1 != v2

    def test_unit_norm(self):
        vec = cm._hash_embedding("normalize this text")
        norm = math.sqrt(sum(v * v for v in vec))
        # Allow floating point tolerance; should be ~1.0
        assert abs(norm - 1.0) < 1e-5

    def test_custom_dim(self):
        vec = cm._hash_embedding("text", dim=64)
        assert len(vec) == 64


# ---------------------------------------------------------------------------
# generate_embedding (tests the fallback path — no API configured)
# ---------------------------------------------------------------------------


class TestGenerateEmbedding:
    def test_falls_back_to_hash_without_api_keys(self):
        # Remove relevant env vars to force hash fallback
        with patch.dict(os.environ, {}, clear=False):
            for k in (
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
                "OPENAI_API_KEY",
            ):
                os.environ.pop(k, None)
            vec = cm.generate_embedding("test text")
        assert isinstance(vec, list)
        assert len(vec) == cm._LOCAL_DIM

    def test_empty_text_returns_list(self):
        with patch.dict(os.environ, {}, clear=False):
            for k in ("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"):
                os.environ.pop(k, None)
            vec = cm.generate_embedding("")
        assert isinstance(vec, list)

    def test_returns_floats(self):
        with patch.dict(os.environ, {}, clear=False):
            for k in ("AZURE_OPENAI_API_KEY", "OPENAI_API_KEY"):
                os.environ.pop(k, None)
            vec = cm.generate_embedding("some content")
        assert all(isinstance(v, float) for v in vec)


# ---------------------------------------------------------------------------
# _serialize_f32 / _deserialize_f32
# ---------------------------------------------------------------------------


class TestSerializeDeserialize:
    def test_round_trip(self):
        original = [0.1, 0.5, -0.3, 1.0, 0.0]
        blob = cm._serialize_f32(original)
        recovered = cm._deserialize_f32(blob, len(original))
        for orig, rec in zip(original, recovered):
            assert abs(orig - rec) < 1e-5

    def test_empty_blob_returns_zeros(self):
        result = cm._deserialize_f32(b"", 4)
        assert result == [0.0, 0.0, 0.0, 0.0]

    def test_pack_size(self):
        vec = [1.0, 2.0, 3.0]
        blob = cm._serialize_f32(vec)
        assert len(blob) == 3 * 4  # 4 bytes per float32

    def test_zero_vector_round_trip(self):
        original = [0.0] * 256
        blob = cm._serialize_f32(original)
        recovered = cm._deserialize_f32(blob, 256)
        assert recovered == original

    def test_truncated_blob(self):
        vec = [1.0, 2.0, 3.0, 4.0]
        blob = cm._serialize_f32(vec)
        # Pass truncated blob — should handle gracefully
        partial = blob[:8]  # only 2 floats
        recovered = cm._deserialize_f32(partial, 4)
        assert len(recovered) == 4


# ---------------------------------------------------------------------------
# _cosine
# ---------------------------------------------------------------------------


class TestCosine:
    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert abs(cm._cosine(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(cm._cosine(a, b)) < 1e-6

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert abs(cm._cosine(a, b) + 1.0) < 1e-6

    def test_empty_vectors(self):
        assert cm._cosine([], []) == 0.0

    def test_mismatched_lengths(self):
        assert cm._cosine([1.0, 2.0], [1.0]) == 0.0

    def test_range_minus_one_to_one(self):
        import random

        random.seed(42)
        for _ in range(20):
            a = [random.gauss(0, 1) for _ in range(10)]
            b = [random.gauss(0, 1) for _ in range(10)]
            sim = cm._cosine(a, b)
            assert -1.0 - 1e-6 <= sim <= 1.0 + 1e-6

    def test_unit_normalized_hash_similarity(self):
        v1 = cm._hash_embedding("quantum")
        v2 = cm._hash_embedding("quantum")
        sim = cm._cosine(v1, v2)
        assert abs(sim - 1.0) < 1e-5  # same text → cosine ≈ 1.0


# ---------------------------------------------------------------------------
# store_embedding (no DB path)
# ---------------------------------------------------------------------------


class TestStoreEmbedding:
    def test_returns_false_without_db(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            result = cm.store_embedding("some-id", [0.1, 0.2], "test-model")
        assert result is False

    def test_returns_false_without_message_id(self):
        result = cm.store_embedding(None, [0.1, 0.2], "test-model")
        assert result is False

    def test_returns_false_without_embedding(self):
        result = cm.store_embedding("id", [], "model")
        assert result is False


# ---------------------------------------------------------------------------
# fetch_similar_messages (no DB path)
# ---------------------------------------------------------------------------


class TestFetchSimilarMessages:
    def test_returns_empty_without_db(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            result = cm.fetch_similar_messages([0.1] * 256)
        assert result == []

    def test_returns_empty_empty_query(self):
        result = cm.fetch_similar_messages([])
        assert result == []
