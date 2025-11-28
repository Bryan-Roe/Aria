from __future__ import annotations

import os
import math
import sys
from pathlib import Path

# Ensure repository root is on path for 'shared'
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import shared.chat_memory as chat_memory  # noqa: E402


def test_generate_embedding_hash_fallback(monkeypatch):
    # Ensure no API keys -> fallback path
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    emb = chat_memory.generate_embedding("Hello world this is a test message for embedding")
    assert isinstance(emb, list)
    assert len(emb) == 256  # local hash fallback dimension
    # Normalized
    norm = math.sqrt(sum(x * x for x in emb))
    assert abs(norm - 1.0) < 1e-6


def test_serialize_deserialize_cycle():
    vec = [0.1, 0.2, -0.3, 0.4]
    blob = chat_memory._serialize_f32(vec)  # type: ignore[attr-defined]
    out = chat_memory._deserialize_f32(blob, len(vec))  # type: ignore[attr-defined]
    assert len(out) == len(vec)
    for a, b in zip(vec, out):
        assert abs(a - b) < 1e-6


def test_cosine_similarity_internal():
    a = [1.0, 0.0, 0.0]
    b = [1.0, 0.0, 0.0]
    c = [0.0, 1.0, 0.0]
    sim_ab = chat_memory._cosine(a, b)  # type: ignore[attr-defined]
    sim_ac = chat_memory._cosine(a, c)  # type: ignore[attr-defined]
    assert sim_ab > 0.999
    assert sim_ac < 0.01
