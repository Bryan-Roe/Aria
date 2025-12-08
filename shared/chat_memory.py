"""Semantic chat memory backed by SQL embeddings.

Functions are fault-tolerant and degrade gracefully when the database
or embedding APIs are unavailable.

Design:
  - generate_embedding(text): attempts Azure OpenAI embeddings, then OpenAI,
    then falls back to a lightweight local hashing embedding (fixed dim=256).
  - store_embedding(message_id, embedding, model): persists embedding bytes
    to [dbo].[ChatMessageEmbeddings]. Float32 little-endian layout.
  - fetch_similar_messages(query_embedding, top_k=5, session_id=None): loads
    recent embeddings (optionally scoped to a session) and computes cosine
    similarity in Python, returning the top-k matches with message content.

Environment variables:
  QAI_DB_CONN: SQL connection string (ODBC Driver 18 for SQL Server recommended)
  AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_EMBEDDING_DEPLOYMENT
  OPENAI_API_KEY (for public OpenAI embedding fallback)

Table schema created in database/Tables/ChatMessageEmbeddings.sql
"""
from __future__ import annotations

import hashlib
import heapq
import os
import math
import struct
from typing import Iterable, List, Optional, Sequence

try:
    import pyodbc  # type: ignore
except Exception:  # pragma: no cover
    pyodbc = None  # type: ignore

try:  # OpenAI unified SDK
    from openai import OpenAI, AzureOpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore

try:
    from shared.azure_utils import is_quota_error, format_quota_message
except Exception:  # pragma: no cover - best effort import
    # Provide simple fallbacks if helper isn't available
    def is_quota_error(e: Exception) -> bool:  # noqa: D401
        if e is None:
            return False
        txt = str(e).lower()
        return any(k in txt for k in ("quota", "premium", "exceed", "allowance", "insufficient", "billing"))

    def format_quota_message(e: Exception, service_name: str = "Azure OpenAI") -> str:  # noqa: D401
        return f"{service_name} quota/premium limit reached. Details: {str(e)}"

# ------------------------- DB Helpers -------------------------


def _get_conn():  # noqa: ANN001
    conn_str = os.getenv("QAI_DB_CONN")
    if not conn_str or not pyodbc:
        return None
    try:
        return pyodbc.connect(conn_str, timeout=4)
    except Exception:
        return None

# ------------------------- Embedding Generation -------------------------


_LOCAL_DIM = 256  # dimension for lightweight local fallback


def _hash_embedding(text: str, dim: int = _LOCAL_DIM) -> List[float]:
    """Very lightweight deterministic hashing embedding.

    Not semantically rich but provides some signal for similarity
    within the same workspace when no embedding API is configured.

    Optimized: Uses module-level hashlib import and single-pass norm calculation.
    """
    tokens = [t for t in text.lower().split() if t]
    vec = [0.0] * dim
    if not tokens:
        return vec

    # Build vector with hash-based indices
    for tok in tokens:
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0

    # L2 normalize in single pass
    sum_sq = sum(v * v for v in vec)
    if sum_sq > 0:
        norm = math.sqrt(sum_sq)
        return [v / norm for v in vec]
    return vec


def generate_embedding(text: str) -> List[float]:  # noqa: ANN001
    """Generate an embedding for text using Azure OpenAI > OpenAI > local hash.

    Returns a list[float]; errors fall back to hash embedding.
    """
    text = text or ""
    # Azure first
    az_key = os.getenv("AZURE_OPENAI_API_KEY")
    az_ep = os.getenv("AZURE_OPENAI_ENDPOINT")
    az_emb = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    if az_key and az_ep and az_emb and AzureOpenAI is not None:
        try:
            client = AzureOpenAI(api_key=az_key, azure_endpoint=az_ep)
            resp = client.embeddings.create(model=az_emb, input=[text])
            return resp.data[0].embedding  # type: ignore[attr-defined]
        except Exception as e:
            # If this looks like a quota/premium issue, log and fall back to
            # the lightweight local hash embedding so the app remains usable.
            if is_quota_error(e):
                try:
                    import logging

                    logging.getLogger(__name__).warning(
                        "Azure embedding call detected quota/premium error: %s", str(
                            e)
                    )
                except Exception:
                    pass
                return _hash_embedding(text)
            # Otherwise continue to try public OpenAI or local fallback
            pass
    # Public OpenAI
    oi_key = os.getenv("OPENAI_API_KEY")
    if oi_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=oi_key)
            resp = client.embeddings.create(
                model="text-embedding-3-small", input=[text])
            return resp.data[0].embedding  # type: ignore[attr-defined]
        except Exception:
            pass
    # Fallback
    return _hash_embedding(text)

# ------------------------- Embedding Persistence -------------------------


def _serialize_f32(vec: Sequence[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *[float(v) for v in vec])


def store_embedding(message_id: Optional[str], embedding: Sequence[float], model: str) -> bool:  # noqa: ANN001
    if not message_id or not embedding:
        return False
    conn = _get_conn()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        blob = _serialize_f32(embedding)
        cursor.execute(
            "INSERT INTO dbo.ChatMessageEmbeddings (MessageId, EmbeddingModel, EmbeddingDim, EmbeddingVector) VALUES (?,?,?,?)",
            message_id,
            model or "unknown-model",
            len(embedding),
            blob,
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ------------------------- Similarity Search -------------------------


def _deserialize_f32(blob: bytes, dim: int) -> List[float]:
    if not blob:
        return [0.0] * dim
    # Expect exact length = dim * 4
    try:
        return list(struct.unpack(f"<{dim}f", blob[: dim * 4]))
    except Exception:
        # Fallback slice-based
        out = []
        for i in range(dim):
            chunk = blob[i * 4: (i + 1) * 4]
            if len(chunk) == 4:
                out.append(struct.unpack("<f", chunk)[0])
            else:
                out.append(0.0)
        return out


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def fetch_similar_messages(query_embedding: Sequence[float], top_k: int = 5, session_id: Optional[str] = None) -> List[dict]:  # noqa: ANN001
    """Return top_k similar past messages using Python-side cosine similarity.

    If session_id is provided, restrict search to that session's conversation(s).
    For performance we limit to the most recent 500 embeddings.

    Optimization: Uses heapq.nlargest for O(n log k) top-k selection instead of
    O(n log n) full sort when top_k is small relative to result set.
    """
    if not query_embedding:
        return []
    conn = _get_conn()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        if session_id:
            cursor.execute(
                "SELECT TOP 500 e.MessageId, e.EmbeddingModel, e.EmbeddingDim, e.EmbeddingVector, m.Content "
                "FROM dbo.ChatMessageEmbeddings e JOIN dbo.ChatMessages m ON e.MessageId=m.MessageId "
                "JOIN dbo.ChatConversations c ON m.ConversationId=c.ConversationId "
                "WHERE c.SessionId=? ORDER BY e.CreatedAt DESC",
                session_id,
            )
        else:
            cursor.execute(
                "SELECT TOP 500 e.MessageId, e.EmbeddingModel, e.EmbeddingDim, e.EmbeddingVector, m.Content "
                "FROM dbo.ChatMessageEmbeddings e JOIN dbo.ChatMessages m ON e.MessageId=m.MessageId "
                "ORDER BY e.CreatedAt DESC",
            )
        rows = cursor.fetchall()

        # Build scored list with only positive similarities
        scored = []
        for r in rows:
            dim = r.EmbeddingDim
            emb = _deserialize_f32(r.EmbeddingVector, dim)
            sim = _cosine(query_embedding, emb)
            if sim > 0:
                scored.append({
                    "message_id": r.MessageId,
                    "content": r.Content,
                    "similarity": sim,
                    "embedding_model": r.EmbeddingModel,
                })

        # Use heapq.nlargest for efficient top-k selection (O(n log k) vs O(n log n))
        # This is more efficient when top_k << len(scored)
        return heapq.nlargest(top_k, scored, key=lambda x: x["similarity"])
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


__all__ = [
    "generate_embedding",
    "store_embedding",
    "fetch_similar_messages",
]
