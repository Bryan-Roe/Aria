"""
Semantic chat memory: embedding generation (with hash fallback), serialization,
cosine similarity, and DB-backed storage/retrieval.

- Lazy-imports pyodbc so the module loads even on systems without unixODBC.
- If no API keys or DB connection string are present, functions degrade
  gracefully (hash fallback for embeddings, no-op False/[] for DB ops).
"""

from __future__ import annotations

import hashlib
import logging
import math
import os
import struct
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LOCAL_DIM = 256  # dimension of the local hash-based embedding fallback

# ---------------------------------------------------------------------------
# Connection cache (unchanged behavior)
# ---------------------------------------------------------------------------

_conn_cache: Dict[int, Any] = {}
_conn_timestamps: Dict[int, float] = {}
_conn_lock = threading.Lock()

_CONN_HEALTH_CHECK_SQL = "SELECT 1"
_CONN_HEALTH_CHECK_TIMEOUT = 2.0
_MAX_CONN_AGE_SECONDS = int(os.getenv("QAI_DB_CONN_MAX_AGE", "300"))


def _conn_str() -> Optional[str]:
    return (
        os.getenv("QAI_DB_CONN")
        or os.getenv("DB_CONN_STRING")
        or os.getenv("CONN_STRING")
    )


def _create_connection() -> Any:
    try:
        import pyodbc  # local import
    except Exception as e:
        raise RuntimeError(
            "pyodbc import failed. Install unixODBC system libs and the `pyodbc` package."
        ) from e

    conn_str = _conn_str()
    if not conn_str:
        raise RuntimeError("Database connection string not set in environment variables")

    return pyodbc.connect(conn_str, autocommit=False, timeout=4)  # type: ignore[arg-type]


def _is_connection_usable(conn: Any) -> bool:
    try:
        start = time.time()
        cur = conn.cursor()
        cur.execute(_CONN_HEALTH_CHECK_SQL)
        try:
            cur.fetchone()
        except Exception:
            pass
        cur.close()
        return (time.time() - start) <= _CONN_HEALTH_CHECK_TIMEOUT
    except Exception:
        logger.debug("Connection health check failed", exc_info=True)
        return False


def _get_conn() -> Any:
    tid = threading.get_ident()
    now = time.time()
    with _conn_lock:
        conn = _conn_cache.get(tid)
        if conn is not None:
            age = now - _conn_timestamps.get(tid, 0)
            if age < _MAX_CONN_AGE_SECONDS and _is_connection_usable(conn):
                return conn
            try:
                conn.close()
            except Exception:
                logger.debug("Failed closing stale connection", exc_info=True)
        conn = _create_connection()
        _conn_cache[tid] = conn
        _conn_timestamps[tid] = now
        return conn


# ---------------------------------------------------------------------------
# Hash-based embedding fallback
# ---------------------------------------------------------------------------

def _hash_embedding(text: str, dim: int = _LOCAL_DIM) -> List[float]:
    """
    Deterministic, unit-normalized hash embedding used when no embedding API
    is configured. Returns a zero vector for empty/whitespace input.
    """
    if not text or not text.strip():
        return [0.0] * dim

    vec = [0.0] * dim
    # Token-level hashing with signed contribution per byte
    for token in text.split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        for i, b in enumerate(digest):
            idx = (i * 131 + b) % dim
            # Map byte to [-1, 1)
            vec[idx] += (b - 127.5) / 127.5

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return [0.0] * dim
    return [v / norm for v in vec]


def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding using Azure OpenAI / OpenAI if configured; otherwise
    fall back to the local hash embedding. Never raises — returns a list.
    """
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_deploy = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    openai_key = os.getenv("OPENAI_API_KEY")

    try:
        if azure_key and azure_endpoint and azure_deploy:
            from openai import AzureOpenAI  # type: ignore
            client = AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=azure_endpoint,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            )
            resp = client.embeddings.create(model=azure_deploy, input=text)
            return [float(x) for x in resp.data[0].embedding]

        if openai_key:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=openai_key)
            resp = client.embeddings.create(
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
                input=text,
            )
            return [float(x) for x in resp.data[0].embedding]
    except Exception:
        logger.exception("Embedding API call failed; falling back to hash embedding")

    return _hash_embedding(text)


# ---------------------------------------------------------------------------
# Binary (de)serialization for float32 vectors
# ---------------------------------------------------------------------------

def _serialize_f32(vec: Sequence[float]) -> bytes:
    """Pack a sequence of floats as little-endian float32 bytes."""
    return struct.pack(f"<{len(vec)}f", *(float(v) for v in vec))


def _deserialize_f32(blob: bytes, dim: int) -> List[float]:
    """
    Unpack little-endian float32 bytes back into a list of length `dim`.
    Tolerates empty or truncated blobs by zero-padding.
    """
    if not blob:
        return [0.0] * dim
    count = min(dim, len(blob) // 4)
    if count <= 0:
        return [0.0] * dim
    values = list(struct.unpack(f"<{count}f", blob[: count * 4]))
    if count < dim:
        values.extend([0.0] * (dim - count))
    return values


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Return cosine similarity in [-1, 1]; 0.0 if inputs are empty or mismatched."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


# ---------------------------------------------------------------------------
# DB-backed storage and retrieval (graceful no-op when no DB)
# ---------------------------------------------------------------------------

def store_embedding(
    message_id: Optional[str],
    embedding: Sequence[float],
    model: str,
) -> bool:
    """
    Store an embedding row. Returns False (no raise) if inputs are invalid or
    if no DB connection string is configured.
    """
    if not message_id or not embedding:
        return False
    if not _conn_str():
        return False

    conn: Optional[Any] = None
    cur = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO embeddings (message_id, model, embedding_vector, dim)
            VALUES (?, ?, ?, ?)
            """,
            (message_id, model, _serialize_f32(embedding), len(embedding)),
        )
        conn.commit()
        return True
    except Exception:
        logger.exception("Failed to store embedding for message_id=%s", message_id)
        try:
            if conn is not None:
                conn.rollback()
        except Exception:
            logger.debug("Rollback failed", exc_info=True)
        return False
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            logger.debug("Failed to close cursor", exc_info=True)


def fetch_similar_messages(
    query_embedding: Sequence[float],
    limit: int = 5,
    min_similarity: float = 0.0,
) -> List[Tuple[str, float]]:
    """
    Return list of (message_id, similarity) sorted by descending similarity.
    Returns [] if query is empty or no DB connection is configured.
    """
    if not query_embedding:
        return []
    if not _conn_str():
        return []

    conn: Optional[Any] = None
    cur = None
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT message_id, embedding_vector, dim FROM embeddings")
        rows = cur.fetchall()

        scored: List[Tuple[str, float]] = []
        for row in rows:
            mid, blob, dim = row[0], row[1], int(row[2])
            vec = _deserialize_f32(bytes(blob), dim)
            sim = _cosine(query_embedding, vec)
            if sim >= min_similarity:
                scored.append((mid, sim))

        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:limit]
    except Exception:
        logger.exception("Failed to fetch similar messages")
        return []
    finally:
        try:
            if cur is not None:
                cur.close()
        except Exception:
            logger.debug("Failed to close cursor", exc_info=True)


def clear_cached_connections() -> None:
    with _conn_lock:
        for _, conn in list(_conn_cache.items()):
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing connection", exc_info=True)
        _conn_cache.clear()
        _conn_timestamps.clear()
