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
_conn_cache: Dict[int, pyodbc.Connection] = {}
_conn_lock = threading.Lock()

# Tunables
_CONN_HEALTH_CHECK_SQL = "SELECT 1"
_CONN_HEALTH_CHECK_TIMEOUT = 2.0  # seconds


def _create_connection() -> pyodbc.Connection:
    """
    Create a new pyodbc connection using the connection string from env.

    Uses os.getenv to allow tests to patch shared.chat_memory.os.getenv.
    """
    conn_str = os.getenv("DB_CONN_STRING")
    if not conn_str:
        # Fall back to a generic name if the env var isn't present; tests patch os.getenv
        conn_str = os.getenv("CONN_STRING", None)

    if not conn_str:
        raise RuntimeError("Database connection string not set in environment variables")

    # Use default timeout and any recommended options here
    conn = pyodbc.connect(conn_str, autocommit=False)
    return conn


def _is_connection_usable(conn: pyodbc.Connection) -> bool:
    """
    Perform a lightweight health check on the connection.

    Returns True if the connection appears usable, False otherwise.
    """
    try:
        # Try a fast query and enforce a timeout by measuring elapsed time
        start = time.time()
        cur = conn.cursor()
        cur.execute(_CONN_HEALTH_CHECK_SQL)
        # fetching results often unnecessary for SELECT 1, but fetchone to be safe
        _ = cur.fetchone()
        elapsed = time.time() - start
        if elapsed > _CONN_HEALTH_CHECK_TIMEOUT:
            logger.debug("Connection health check too slow (%.3fs)", elapsed)
            return False
        return True
    except Exception:
        logger.exception("Connection health check failed")
        return False


def _get_conn() -> pyodbc.Connection:
    """
    Get a cached connection for the current thread or create a new one.

    This function is thread-safe.
    """
    tid = threading.get_ident()

    with _conn_lock:
        conn = _conn_cache.get(tid)
        if conn:
            if _is_connection_usable(conn):
                return conn
            else:
                # Try to close and drop the cached connection; create a fresh one
                try:
                    conn.close()
                except Exception:
                    logger.debug("Error closing unhealthy cached connection", exc_info=True)
                _conn_cache.pop(tid, None)

        # Create new connection and cache it
        conn = _create_connection()
        _conn_cache[tid] = conn
        return conn


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
    try:
        conn = _get_conn()
        cur = conn.cursor()

        # Example schema: embeddings(message_id VARCHAR PRIMARY KEY, model VARCHAR, vector VARBINARY or similar)
        # The actual schema may differ; adapt the SQL accordingly.
        # Use a simple upsert pattern supported by the DB or emulate with try/except.
        # Here we try an insert then an update on duplicate key pattern — adjust for your DB.
        insert_sql = """
            INSERT INTO embeddings (message_id, model, embedding_vector)
            VALUES (?, ?, ?)
        """

        # Serialize embedding to a bytes representation if required by DB. If DB expects
        # a JSON/text column, adapt accordingly. Here we'll use comma-joined text as a safe fallback.
        # If your DB supports storing arrays or binary, replace this serialization.
        embedding_value: Any
        try:
            # Prefer compact binary when DB supports it; otherwise fallback to text
            embedding_value = bytes(bytearray(int(x * 255) & 0xFF for x in embedding))
        except Exception:
            # Fallback: store as comma-separated string
            embedding_value = ",".join(str(x) for x in embedding)

        cur.execute(insert_sql, (message_id, model, embedding_value))

        # Commit after successful insert
        conn.commit()
        return True
    except Exception:
        # Do not close the cached connection here; let _get_conn handle reconnection on next use.
        logger.exception("Failed to store embedding for message_id=%s", message_id)
        try:
            # If a transaction is open, attempt to rollback to leave connection usable.
            conn.rollback()
        except Exception:
            logger.debug("Rollback failed or not applicable", exc_info=True)
        return False


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
