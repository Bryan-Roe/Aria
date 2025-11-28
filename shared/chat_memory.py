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

import os
import math
import struct
from typing import Any, Dict, List, Optional, Sequence

try:
    import pyodbc  # type: ignore
except Exception:  # pragma: no cover
    pyodbc = None  # type: ignore

try:  # OpenAI unified SDK
    from openai import OpenAI, AzureOpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore

# Optional NumPy for faster cosine similarity
try:
    import numpy as np  # type: ignore
    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

# ------------------------- Cached Embedding Clients -------------------------
# Cache embedding clients to avoid repeated instantiation overhead

_embedding_clients: Dict[str, Any] = {}


def _get_embedding_client(provider: str) -> Any:
    """Get or create a cached embedding client for the given provider."""
    if provider in _embedding_clients:
        return _embedding_clients[provider]
    
    client = None
    if provider == "azure":
        az_key = os.getenv("AZURE_OPENAI_API_KEY")
        az_ep = os.getenv("AZURE_OPENAI_ENDPOINT")
        if az_key and az_ep and AzureOpenAI is not None:
            try:
                client = AzureOpenAI(api_key=az_key, azure_endpoint=az_ep)
            except Exception:
                # Client initialization failed (e.g., invalid credentials, network error)
                # Fall through to return None, allowing caller to use fallback
                pass
    elif provider == "openai":
        oi_key = os.getenv("OPENAI_API_KEY")
        if oi_key and OpenAI is not None:
            try:
                client = OpenAI(api_key=oi_key)
            except Exception:
                # Client initialization failed (e.g., invalid API key, network error)
                # Fall through to return None, allowing caller to use fallback
                pass
    
    if client is not None:
        _embedding_clients[provider] = client
    return client


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
    """
    import hashlib
    tokens = [t for t in text.lower().split() if t]
    vec = [0.0] * dim
    if not tokens:
        return vec
    for tok in tokens:
        h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def generate_embedding(text: str) -> List[float]:  # noqa: ANN001
    """Generate an embedding for text using Azure OpenAI > OpenAI > local hash.

    Returns a list[float]; errors fall back to hash embedding.
    Uses cached clients for performance (see _get_embedding_client).
    """
    text = text or ""
    # Azure first (using cached client)
    az_emb = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    if az_emb:
        client = _get_embedding_client("azure")
        if client is not None:
            try:
                resp = client.embeddings.create(model=az_emb, input=[text])
                return resp.data[0].embedding  # type: ignore[attr-defined]
            except Exception:
                pass
    # Public OpenAI (using cached client)
    client = _get_embedding_client("openai")
    if client is not None:
        try:
            resp = client.embeddings.create(model="text-embedding-3-small", input=[text])
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
            chunk = blob[i * 4 : (i + 1) * 4]
            if len(chunk) == 4:
                out.append(struct.unpack("<f", chunk)[0])
            else:
                out.append(0.0)
        return out


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Uses NumPy for faster computation when available, falling back
    to pure Python for environments without NumPy.
    
    Note: float32 is used intentionally for memory efficiency. The precision
    loss is negligible for cosine similarity comparisons (< 1e-6 difference).
    """
    if not a or not b or len(a) != len(b):
        return 0.0
    
    if _HAS_NUMPY:
        # NumPy path: ~8x faster for typical embedding dimensions (256-1536)
        # Using float32 for memory efficiency; precision loss is negligible
        a_arr = np.asarray(a, dtype=np.float32)
        b_arr = np.asarray(b, dtype=np.float32)
        dot = np.dot(a_arr, b_arr)
        na = np.linalg.norm(a_arr)
        nb = np.linalg.norm(b_arr)
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(dot / (na * nb))
    
    # Pure Python fallback
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def fetch_similar_messages(query_embedding: Sequence[float], top_k: int = 5, session_id: Optional[str] = None) -> List[dict]:  # noqa: ANN001
    """Return top_k similar past messages using Python-side cosine similarity.

    If session_id is provided, restrict search to that session's conversation(s).
    For performance we limit to the most recent 500 embeddings.
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
        scored = []
        for r in rows:
            dim = r.EmbeddingDim
            emb = _deserialize_f32(r.EmbeddingVector, dim)
            sim = _cosine(query_embedding, emb)
            if sim <= 0:
                continue
            scored.append({
                "message_id": r.MessageId,
                "content": r.Content,
                "similarity": sim,
                "embedding_model": r.EmbeddingModel,
            })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
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
