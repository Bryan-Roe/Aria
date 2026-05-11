"""
Semantic chat memory backed by SQL embeddings.

This module implements a robust, thread-safe connection pool for database
operations and provides batch insertion for embeddings to reduce connection
churn and per-row transaction overhead.

Design highlights:
  - ConnectionPool: LIFO queue with thread-local fast path and configurable max size.
  - store_embeddings_batch: Bulk insert using executemany() in a single transaction.
  - store_embedding: Backward-compatible single-insert wrapper that delegates to batch API.
  - close_all_connections: Clean shutdown helper to close pooled and cached connections.

Environment variables:
  QAI_DB_CONN: SQL connection string (ODBC Driver 18 for SQL Server recommended)
  QAI_DB_POOL_SIZE: Optional override for maximum pooled connections (default: 5)
  AZURE_OPENAI_API_KEY / AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_EMBEDDING_DEPLOYMENT
  OPENAI_API_KEY (for public OpenAI embedding fallback)
"""

from __future__ import annotations

import hashlib
import heapq
import logging
import math
import os
import queue
import struct
import logging
import queue
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple

# Third-party optional imports
try:
    import pyodbc  # type: ignore
except Exception:  # pragma: no cover
    pyodbc = None  # type: ignore

try:  # OpenAI unified SDK
    from openai import AzureOpenAI, OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore

# Optional helpers fallback
try:
    from shared.azure_utils import format_quota_message, is_quota_error
except Exception:  # pragma: no cover - best effort import
    def is_quota_error(e: Exception) -> bool:  # noqa: D401
        if e is None:
            return False
        txt = str(e).lower()
        return any(
            k in txt
            for k in (
                "quota",
                "premium",
                "exceed",
                "allowance",
                "insufficient",
                "billing",
            )
        )

    def format_quota_message(e: Exception, service_name: str = "Azure OpenAI") -> str:  # noqa: D401
        return f"{service_name} quota/premium limit reached. Details: {str(e)}"

# Configure logger for the module
_logger = logging.getLogger(__name__)

# Default pooling parameters; override via QAI_DB_POOL_SIZE env var
_DEFAULT_MAX_POOL_SIZE = 5
_MAX_POOL_SIZE = int(os.getenv("QAI_DB_POOL_SIZE", str(_DEFAULT_MAX_POOL_SIZE)))

# Thread-local storage for fast-path cached connection
_thread_local = threading.local()

# Keep a mapping of thread_id -> conn for compatibility and inspection
_thread_connections: Dict[int, Any] = {}
_conn_lock = threading.RLock()

_conn_lock = threading.RLock()
_thread_local = threading.local()
_thread_connections: Dict[int, Any] = {}

class ConnectionPool:
    """Simple LIFO connection pool with thread-local fast-path.

    Behavior:
      - Threads first attempt to reuse a thread-local cached connection.
      - If none, a pooled connection is popped (LIFO) and validated.
      - If pool empty and under max size, a new connection is created.
      - Returned connections go back to the pool unless the pool is full,
        in which case they are closed.
    """

    def __init__(self, max_size: int = _MAX_POOL_SIZE):
        self._max_size = max_size
        self._pool: "queue.LifoQueue[Any]" = queue.LifoQueue(maxsize=max_size)
        # Count of total connections created and not closed (approximate)
        self._total_created = 0
        self._lock = threading.RLock()

    def _create_connection(self):
        conn_str = os.getenv("QAI_DB_CONN")
        if not conn_str or not pyodbc:
            return None
        try:
            conn = pyodbc.connect(conn_str, timeout=4)
            with self._lock:
                self._total_created += 1
            return conn
        except Exception as e:
            _logger.debug("Failed to create DB connection: %s", str(e))
            return None

    def _is_alive(self, conn: Any) -> bool:
        try:
            # Lightweight probe
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            # Some drivers require fetchone()
            try:
                cursor.fetchone()
            except Exception:
                pass
            cursor.close()
            return True
        except Exception:
            return False

    def acquire(self, timeout: float = 0.0) -> Optional[Any]:
        """Acquire a live connection (thread-local -> pool -> new)."""
        thread_id = threading.get_ident()

        # 1) Thread-local fast-path
        cached = getattr(_thread_local, "conn", None)
        if cached is not None:
            if self._is_alive(cached):
                _thread_connections[thread_id] = cached
                return cached
            # stale cached; close and remove
            try:
                cached.close()
            except Exception:
                pass
            _thread_local.conn = None
            with _conn_lock:
                _thread_connections.pop(thread_id, None)

        # 2) Try pool
        try:
            conn = self._pool.get(block=(timeout > 0.0), timeout=timeout if timeout > 0 else 0)
        except Exception:
            conn = None

        if conn is not None:
            if self._is_alive(conn):
                # Cache in thread-local for fast reuse
                _thread_local.conn = conn
                _thread_connections[thread_id] = conn
                return conn
            # Dead connection: close and continue to create
            try:
                conn.close()
            except Exception:
                pass

        # 3) Create new connection (if allowed)
        conn = self._create_connection()
        if conn is not None:
            _thread_local.conn = conn
            _thread_connections[thread_id] = conn
        return conn

    def release(self, conn: Any) -> None:
        """Return a connection to pool or close it if pool is full."""
        if not conn:
            return
        thread_id = threading.get_ident()
        # If this is the same as thread-local, keep it cached (fast-path)
        if getattr(_thread_local, "conn", None) is conn:
            # keep cached for thread reuse; do not put back into shared pool
            _thread_connections[thread_id] = conn
            return

        # Otherwise, try to put back into pool
        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            # Pool full: close the connection
            try:
                conn.close()
            except Exception:
                pass

    def close_all(self) -> None:
        """Close and clear all pooled connections and thread-local caches."""
        # Clear pool
        while True:
            try:
                conn = self._pool.get_nowait()
            except Exception:
                break
            try:
                conn.close()
            except Exception:
                pass
        # Clear thread-local mapping entries (best-effort)
        with _conn_lock:
            for tid, conn in list(_thread_connections.items()):
                try:
                    conn.close()
                except Exception:
                    pass
                _thread_connections.pop(tid, None)
        # Clear any thread-local conn in current thread
        try:
            if getattr(_thread_local, "conn", None) is not None:
                try:
                    _thread_local.conn.close()
                except Exception:
                    pass
                _thread_local.conn = None
        except Exception:
            pass

    def current_pool_items(self) -> List[Any]:
        """Return a snapshot list of connections currently in the pool (debug view)."""
        # queue doesn't provide a safe way to peek; build snapshot by draining/reloading
        items: List[Any] = []
        tmp: List[Any] = []
        while True:
            try:
                item = self._pool.get_nowait()
                items.append(item)
                tmp.append(item)
            except Exception:
                break
        # put them back
        for item in tmp:
            try:
                self._pool.put_nowait(item)
            except Exception:
                try:
                    item.close()
                except Exception:
                    pass
        return items


# Instantiate module-level pool
_POOL = ConnectionPool(max_size=_MAX_POOL_SIZE)

# Backwards-compatible exported names (views into new pool)
_connection_pool = _POOL.current_pool_items  # callable to snapshot pool contents
_conn_cache = _thread_connections
# Keep lock object for external code that may import it
_conn_lock = _conn_lock


def _get_conn() -> Optional[Any]:
    """Get a live database connection (module-level wrapper)."""
    return _POOL.acquire(timeout=0.0)


def _return_conn(conn: Any) -> None:
    """Return a connection to the pool (module-level wrapper)."""
    _POOL.release(conn)


def close_all_connections() -> None:
    """Close all connections in pool and thread-local caches."""
    _POOL.close_all()


# ------------------------- Embedding Generation -------------------------

_LOCAL_DIM = 256  # dimension for lightweight local fallback


def _hash_embedding(text: str, dim: int = _LOCAL_DIM) -> List[float]:
    """Very lightweight deterministic hashing embedding.

    Not semantically rich but provides some signal for similarity when no
    embedding API is configured.
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


def generate_embedding(text: str) -> List[float]:
    """Generate an embedding for text using Azure OpenAI > OpenAI > local hash.

    Returns:
        list[float]: embedding vector (fallback to _hash_embedding on errors).
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
            if is_quota_error(e):
                _logger.warning("Azure embedding quota/premium error: %s", str(e))
                return _hash_embedding(text)
            _logger.debug("Azure embedding error, falling back: %s", str(e))
    # Public OpenAI
    oi_key = os.getenv("OPENAI_API_KEY")
    if oi_key and OpenAI is not None:
        try:
            client = OpenAI(api_key=oi_key)
            resp = client.embeddings.create(model="text-embedding-3-small", input=[text])
            return resp.data[0].embedding  # type: ignore[attr-defined]
        except Exception as e:
            _logger.debug("OpenAI embedding error, falling back: %s", str(e))
    # Fallback
    return _hash_embedding(text)


# ------------------------- Embedding Persistence -------------------------


def _serialize_f32(vec: Sequence[float]) -> bytes:
    """Serialize a sequence of floats to little-endian float32 bytes."""
    return struct.pack(f"<{len(vec)}f", *[float(v) for v in vec])


def store_embeddings_batch(embeddings: List[Tuple[str, Sequence[float], str]]) -> int:
    """Store multiple embeddings in a single transaction (bulk insert).

    Args:
        embeddings: List of tuples (message_id, embedding, model)

    Returns:
        Number of embeddings successfully stored (0 on failure).
    """
    if not embeddings:
        return 0

    conn = _get_conn()
    if not conn:
        _logger.debug("No DB connection available to store embeddings batch.")
        return 0

    try:
        values: List[Tuple[str, str, int, bytes]] = []
        for message_id, embedding, model in embeddings:
            if not message_id or not embedding:
                continue
            values.append(
                (
                    message_id,
                    model or "unknown-model",
                    len(embedding),
                    _serialize_f32(embedding),
                )
            )
        if not values:
            return 0
        cursor = conn.cursor()
        values = []
        for message_id, embedding, model in embeddings:
            if not message_id or not embedding:
                continue
            blob = _serialize_f32(embedding)
            values.append((message_id, model or "unknown-model", len(embedding), blob))

        if not values:
            return 0

        try:
            cursor.executemany(
                "INSERT INTO dbo.ChatMessageEmbeddings "
                "(MessageId, EmbeddingModel, EmbeddingDim, EmbeddingVector) VALUES (?,?,?,?)",
                values,
            )
            conn.commit()
            return len(values)
        except Exception as e:
            _logger.exception("Failed to execute batch insert for embeddings: %s", str(e))
            try:
                conn.rollback()
            except Exception:
                pass
            return 0
    finally:
        _return_conn(conn)


def store_embedding(message_id: Optional[str], embedding: Sequence[float], model: str) -> bool:
    """Backward-compatible single-insert wrapper that delegates to batch insert."""
    if not message_id or not embedding:
        return False
    inserted = store_embeddings_batch([(message_id, embedding, model)])
    return inserted == 1


# ------------------------- Similarity Search -------------------------


def _deserialize_f32(blob: bytes, dim: int) -> List[float]:
    """Deserialize float32 little-endian bytes to list[float]."""
    if not blob:
        return [0.0] * dim
    try:
        return list(struct.unpack(f"<{dim}f", blob[: dim * 4]))
    except Exception:
        out = []
        for i in range(dim):
            chunk = blob[i * 4 : (i + 1) * 4]
            if len(chunk) == 4:
                out.append(struct.unpack("<f", chunk)[0])
            else:
                out.append(0.0)
        return out


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def fetch_similar_messages(
    query_embedding: Sequence[float], top_k: int = 5, session_id: Optional[str] = None
) -> List[dict]:
    """Return top_k similar past messages using Python-side cosine similarity.

    If session_id is provided, restrict search to that session's conversation(s).
    For performance we limit to the most recent 500 embeddings.

    Returns:
        List[dict]: each dict contains message_id, content, similarity, embedding_model
    """
    if not query_embedding:
        return []

    conn = _get_conn()
    if not conn:
        _logger.debug("No DB connection available for similarity fetch.")
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

        scored: List[dict] = []
        for r in rows:
            dim = getattr(r, "EmbeddingDim", None) or 0
            emb = _deserialize_f32(getattr(r, "EmbeddingVector", b""), dim)
            sim = _cosine(query_embedding, emb)
            if sim > 0:
                scored.append(
                    {
                        "message_id": getattr(r, "MessageId", None),
                        "content": getattr(r, "Content", None),
                        "similarity": sim,
                        "embedding_model": getattr(r, "EmbeddingModel", None),
                    }
                )

        # Efficient top-k selection
        return heapq.nlargest(top_k, scored, key=lambda x: x["similarity"])
    except Exception as e:
        _logger.exception("Failed to fetch similar messages: %s", str(e))
        return []
    finally:
        _return_conn(conn)


# Public API exports
__all__ = [
    "generate_embedding",
    "store_embedding",
    "store_embeddings_batch",
    "fetch_similar_messages",
    "close_all_connections",
    "_get_conn",
    "_return_conn",
    "_conn_cache",
    "_conn_lock",
    "_connection_pool",
]
