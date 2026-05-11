"""
Database connection caching and embedding storage utilities.

This module maintains a per-thread cached pyodbc connection to avoid repeatedly
creating expensive DB connections. Functions use os.getenv to obtain the
connection string so unit tests can patch os.getenv("...") easily.

Design goals:
- Use import pyodbc (not from pyodbc import connect) so tests can patch shared.chat_memory.pyodbc.
- Cache connections per thread id under _conn_cache protected by _conn_lock.
- Keep cached connections open (do not close them in store_embedding).
- Perform lightweight health-check before reusing a cached connection and
  reconnect if needed.
- Use parameterized queries to avoid SQL injection.
"""

from __future__ import annotations

import os
import threading
import time
import logging
from typing import Any, Dict, Optional

import pyodbc

logger = logging.getLogger(__name__)

# Connection cache keyed by thread identity
# Keep legacy shape: mapping tid -> pyodbc.Connection so external tests that
# inspect _conn_cache still see connection objects.
_conn_cache: Dict[int, pyodbc.Connection] = {}
_conn_timestamps: Dict[int, float] = {}
_conn_lock = threading.Lock()

# Tunables
_CONN_HEALTH_CHECK_SQL = "SELECT 1"
_CONN_HEALTH_CHECK_TIMEOUT = 2.0  # seconds
_MAX_CONN_AGE_SECONDS = int(os.getenv("QAI_DB_CONN_MAX_AGE", str(300)))


def _create_connection() -> pyodbc.Connection:
    """
    Create a new pyodbc connection using the connection string from env.

    Uses os.getenv to allow tests to patch shared.chat_memory.os.getenv.
    Supports multiple env var names for backwards compatibility.
    """
    # Prefer application-specific env var but fall back to commonly-used names
    conn_str = os.getenv("QAI_DB_CONN") or os.getenv("DB_CONN_STRING") or os.getenv("CONN_STRING")

    if not conn_str:
        raise RuntimeError("Database connection string not set in environment variables")

    # Use a conservative timeout; autocommit disabled to allow explicit commits
    conn = pyodbc.connect(conn_str, autocommit=False, timeout=4)  # type: ignore[arg-type]
    return conn


def _is_connection_usable(conn: pyodbc.Connection) -> bool:
    """
    Perform a lightweight health check on the connection.

    Returns True if the connection appears usable, False otherwise.
    """
    try:
        start = time.time()
        cur = conn.cursor()
        cur.execute(_CONN_HEALTH_CHECK_SQL)
        # fetching results often unnecessary for SELECT 1, but fetchone to be safe
        try:
            _ = cur.fetchone()
        except Exception:
            # Some drivers don't require fetchone; ignore fetch errors here
            pass
        cur.close()
        elapsed = time.time() - start
        if elapsed > _CONN_HEALTH_CHECK_TIMEOUT:
            logger.debug("Connection health check too slow (%.3fs)", elapsed)
            return False
        return True
    except Exception:
        logger.debug("Connection health check failed", exc_info=True)
        return False


def _get_conn() -> pyodbc.Connection:
    """
    Get a cached connection for the current thread or create a new one.

    This function is thread-safe and ensures the cached connection is still
    healthy and not older than _MAX_CONN_AGE_SECONDS.
    """
    tid = threading.get_ident()
    now = time.time()

    with _conn_lock:
        conn = _conn_cache.get(tid)
        if conn is not None:
            ts = _conn_timestamps.get(tid, 0)
            age = now - ts
            if age < _MAX_CONN_AGE_SECONDS and _is_connection_usable(conn):
                return conn
            # stale or unhealthy connection: try to close and remove
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing stale connection", exc_info=True)
            _conn_cache.pop(tid, None)
            _conn_timestamps.pop(tid, None)

        # Create new connection and cache it
        new_conn = _create_connection()
        _conn_cache[tid] = new_conn
        _conn_timestamps[tid] = time.time()
        return new_conn


def store_embedding(message_id: str, embedding: list[float], model: str) -> bool:
    """
    Store an embedding for a message_id into the database.

    - Uses _get_conn() to obtain a cached connection (so tests that patch pyodbc.connect
      will see one call when creating the connection).
    - Does NOT close the connection (it remains cached).
    - Uses parameterized SQL to avoid injection.
    - Commits the transaction after insert.

    Returns True on success, False on failure.
    """
    conn: Optional[pyodbc.Connection] = None
    cur = None
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Example schema: embeddings(message_id VARCHAR PRIMARY KEY, model VARCHAR, vector VARBINARY or similar)
        insert_sql = """
            INSERT INTO embeddings (message_id, model, embedding_vector)
            VALUES (?, ?, ?)
        """

        # Serialize embedding to a bytes representation if required by DB. If DB expects
        # a JSON/text column, adapt accordingly. Here we'll try a compact binary
        # representation and fall back to comma-separated text.
        embedding_value: Any
        try:
            embedding_value = bytes(bytearray(int(x * 255) & 0xFF for x in embedding))
        except Exception:
            embedding_value = ",".join(str(x) for x in embedding)

        cur.execute(insert_sql, (message_id, model, embedding_value))

        # Commit after successful insert
        conn.commit()
        return True
    except Exception:
        # Do not close the cached connection here; let _get_conn handle reconnection on next use.
        logger.exception("Failed to store embedding for message_id=%s", message_id)
        try:
            if conn is not None:
                conn.rollback()
        except Exception:
            logger.debug("Rollback failed or not applicable", exc_info=True)
        return False
    finally:
        # Close the cursor (driver resources), but keep connection cached for reuse
        try:
            if cur is not None:
                cur.close()
        except Exception:
            logger.debug("Failed to close cursor", exc_info=True)


def clear_cached_connections() -> None:
    """
    Close and clear all cached connections. Use in shutdown or tests teardown if needed.
    """
    with _conn_lock:
        for conn in list(_conn_cache.values()):
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing connection during clear", exc_info=True)
        _conn_cache.clear()
        _conn_timestamps.clear()
