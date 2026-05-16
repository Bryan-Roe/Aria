"""
Database connection caching and embedding storage utilities.

This module maintains a per-thread cached ODBC connection to avoid repeatedly
creating expensive DB connections.

Key changes:
- Lazy-import pyodbc inside _create_connection so importing this module doesn't
  immediately fail in environments missing the unixODBC shared libraries.
- Use typing.Any for connection types to avoid import-time references.
- Provide a clear, actionable RuntimeError when pyodbc (or system ODBC libs)
  are missing.
- Preserve previous caching, health-check, and commit/rollback semantics.
"""

from __future__ import annotations

import os
import threading
import time
import logging
from typing import Any, Dict, Optional, Sequence

logger = logging.getLogger(__name__)

# Connection cache keyed by thread identity
# Keep legacy shape: mapping tid -> connection object so external tests that
# inspect _conn_cache still see connection objects.
_conn_cache: Dict[int, Any] = {}
_conn_timestamps: Dict[int, float] = {}
_conn_lock = threading.Lock()

# Tunables
_CONN_HEALTH_CHECK_SQL = "SELECT 1"
_CONN_HEALTH_CHECK_TIMEOUT = 2.0  # seconds
_MAX_CONN_AGE_SECONDS = int(os.getenv("QAI_DB_CONN_MAX_AGE", str(300)))


def _create_connection() -> Any:
    """
    Create a new pyodbc connection using the connection string from env.

    Lazy-imports pyodbc so importing this module won't fail on systems missing
    the unixODBC shared libraries. Raises a RuntimeError with an actionable
    message if pyodbc cannot be imported.
    """
    try:
        import pyodbc  # local import so module import doesn't fail when libodbc is missing
    except Exception as e:  # ImportError or OSError from underlying lib load
        raise RuntimeError(
            "pyodbc import failed. Ensure the unixODBC system libraries are installed "
            "(e.g. on Debian/Ubuntu: `apt-get update && apt-get install -y unixodbc unixodbc-dev libodbc1`). "
            "Also ensure the Python package `pyodbc` is installed in your environment."
        ) from e

    # Prefer application-specific env var but fall back to commonly-used names
    conn_str = os.getenv("QAI_DB_CONN") or os.getenv("DB_CONN_STRING") or os.getenv("CONN_STRING")

    if not conn_str:
        raise RuntimeError("Database connection string not set in environment variables")

    # Use a conservative timeout; autocommit disabled to allow explicit commits
    # Some pyodbc drivers don't accept a 'timeout' keyword depending on version; keep type-ignore
    conn = pyodbc.connect(conn_str, autocommit=False, timeout=4)  # type: ignore[arg-type]
    return conn


def _is_connection_usable(conn: Any) -> bool:
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


def _get_conn() -> Any:
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
            # Dead or stale connection: close and continue to create a new one
            try:
                conn.close()
            except Exception:
                logger.debug("Failed closing stale connection", exc_info=True)

        # Create new connection and cache it
        conn = _create_connection()
        _conn_cache[tid] = conn
        _conn_timestamps[tid] = now
        return conn


def store_embedding(message_id: str, embedding: Sequence[float], model: str) -> bool:
    """
    Store an embedding for a message_id into the database.

    - Uses _get_conn() to obtain a cached connection (so tests that patch pyodbc.connect
      will see one call when creating the connection).
    - Does NOT close the connection (it remains cached).
    - Uses parameterized SQL to avoid injection.
    - Commits the transaction after insert.

    Returns True on success, False on failure.
    """
    conn: Optional[Any] = None
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
        try:
            # Clamp to 0-255 per element and convert to bytes. This is lossy; callers should
            # adapt to the DB schema they use (e.g., store JSON/text or use proper binary encoding).
            embedding_value = bytes(bytearray(int(max(0, min(1, float(x))) * 255) & 0xFF for x in embedding))
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
        for tid, conn in list(_conn_cache.items()):
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing connection during clear", exc_info=True)
        _conn_cache.clear()
        _conn_timestamps.clear()
