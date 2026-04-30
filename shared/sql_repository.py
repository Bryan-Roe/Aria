"""Generic lightweight SQL repository utilities.

Provides a key-value store abstraction for multi-database support using
SQLAlchemy core when available, and a sqlite3-based fallback when SQLAlchemy
is not installed. Table auto-creation is vendor-aware and idempotent.

Table name: QAI_KeyValue
Columns:
  key_name (primary key), value_data (text/blob), updated_at (timestamp)

Graceful degradation: If an engine or driver is unavailable, operations return
fallback values instead of raising.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

# Conditional SQLAlchemy import
_SQLALCHEMY_AVAILABLE = True
try:
    from sqlalchemy import text  # type: ignore
except Exception:  # pragma: no cover
    _SQLALCHEMY_AVAILABLE = False
    text = None  # type: ignore

from .sql_engine import get_engine, resolve_sql_url

_TABLE_CREATED = False
_SQLITE_CONN: Optional[sqlite3.Connection] = None

# ----------------------------------------------------------------------------
# Helpers (fallback)
# ----------------------------------------------------------------------------


def _sqlite_path_from_url(url: str) -> str:
    """Resolve sqlite database path from SQLAlchemy-style URL.
    Supports file paths (sqlite:///path/to.db) and in-memory (:memory:).
    """
    if url.endswith(":memory:"):
        return ":memory:"
    if url.startswith("sqlite:///"):
        path = url[len("sqlite:///") :]
        return os.path.normpath(path)
    # Default to in-memory if unrecognized format
    return ":memory:"


def _get_sqlite_conn() -> sqlite3.Connection:
    global _SQLITE_CONN
    if _SQLITE_CONN is not None:
        return _SQLITE_CONN
    url = resolve_sql_url() or "sqlite:///:memory:"
    db_path = _sqlite_path_from_url(url)
    # Ensure directory exists for file-based DBs
    if db_path != ":memory:":
        try:
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        except Exception:  # pragma: no cover
            pass
    _SQLITE_CONN = sqlite3.connect(db_path, check_same_thread=False)
    return _SQLITE_CONN


# ----------------------------------------------------------------------------
# Table Creation (idempotent)
# ----------------------------------------------------------------------------


def _ensure_table():
    global _TABLE_CREATED
    if _TABLE_CREATED:
        return True

    engine = get_engine()
    if not engine and not _SQLALCHEMY_AVAILABLE:
        # Fallback path: sqlite3 direct
        try:
            conn = _get_sqlite_conn()
            conn.execute(
                "CREATE TABLE IF NOT EXISTS QAI_KeyValue ("
                "key_name TEXT PRIMARY KEY, value_data TEXT, updated_at TEXT)"
            )
            conn.commit()
            _TABLE_CREATED = True
            return True
        except Exception as e:  # noqa: BLE001
            logging.warning(
                f"[sql_repository] sqlite fallback table create failed: {e}"
            )
            return False

    if not engine:
        return False

    vendor = getattr(engine.dialect, "name", "unknown")
    try:
        if vendor == "sqlite":
            ddl = "CREATE TABLE IF NOT EXISTS QAI_KeyValue (key_name TEXT PRIMARY KEY, value_data TEXT, updated_at TEXT)"
        elif vendor in {"postgresql", "postgres"}:
            ddl = (
                "CREATE TABLE IF NOT EXISTS QAI_KeyValue ("
                "key_name VARCHAR(200) PRIMARY KEY, "
                "value_data TEXT, "
                "updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)"
            )
        elif vendor in {"mysql"}:
            ddl = (
                "CREATE TABLE IF NOT EXISTS QAI_KeyValue ("
                "key_name VARCHAR(200) PRIMARY KEY, "
                "value_data TEXT, "
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"
            )
        else:  # mssql & fallback
            # SQL Server: need IF NOT EXISTS pattern
            ddl = (
                "IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='QAI_KeyValue') "
                "BEGIN CREATE TABLE dbo.QAI_KeyValue ("
                "key_name NVARCHAR(200) NOT NULL PRIMARY KEY, "
                "value_data NVARCHAR(MAX) NULL, "
                "updated_at DATETIME2 DEFAULT SYSUTCDATETIME()) END"
            )
        with engine.begin() as conn:
            conn.execute(text(ddl))
        _TABLE_CREATED = True
        return True
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sql_repository] table create failed: {e}")
        return False


# ----------------------------------------------------------------------------
# CRUD Operations
# ----------------------------------------------------------------------------


def put_value(key: str, value: str) -> bool:
    if not _ensure_table():
        return False

    engine = get_engine()
    if not engine and not _SQLALCHEMY_AVAILABLE:
        # Fallback: sqlite3 direct
        try:
            conn = _get_sqlite_conn()
            conn.execute(
                "INSERT OR REPLACE INTO QAI_KeyValue (key_name, value_data, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
            return True
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_repository] sqlite fallback put_value failed: {e}")
            return False

    if not engine:
        return False

    vendor = getattr(engine.dialect, "name", "unknown")
    try:
        with engine.begin() as conn:
            if vendor == "sqlite":
                conn.execute(
                    text(
                        "REPLACE INTO QAI_KeyValue (key_name,value_data,updated_at) VALUES (:key_name,:value_data,:ts)"
                    ),
                    {
                        "key_name": key,
                        "value_data": value,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    },
                )
            elif vendor in {"postgresql", "postgres"}:
                conn.execute(
                    text(
                        "INSERT INTO QAI_KeyValue (key_name,value_data) VALUES (:key_name,:value_data) ON CONFLICT (key_name) DO UPDATE SET value_data=EXCLUDED.value_data, updated_at=CURRENT_TIMESTAMP"
                    ),
                    {"key_name": key, "value_data": value},
                )
            elif vendor == "mysql":
                conn.execute(
                    text(
                        "INSERT INTO QAI_KeyValue (key_name,value_data) VALUES (:key_name,:value_data) ON DUPLICATE KEY UPDATE value_data=VALUES(value_data)"
                    ),
                    {"key_name": key, "value_data": value},
                )
            else:  # SQL Server
                conn.execute(
                    text(
                        "MERGE dbo.QAI_KeyValue AS tgt USING (SELECT :key_name AS key_name, :value_data AS value_data) AS src ON tgt.key_name=src.key_name WHEN MATCHED THEN UPDATE SET value_data=src.value_data, updated_at=SYSUTCDATETIME() WHEN NOT MATCHED THEN INSERT (key_name,value_data,updated_at) VALUES (src.key_name, src.value_data, SYSUTCDATETIME());"
                    ),
                    {"key_name": key, "value_data": value},
                )
        return True
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sql_repository] put_value failed: {e}")
        return False


def get_value(key: str) -> Optional[str]:
    if not _ensure_table():
        return None

    engine = get_engine()
    if not engine and not _SQLALCHEMY_AVAILABLE:
        try:
            conn = _get_sqlite_conn()
            cur = conn.execute(
                "SELECT value_data FROM QAI_KeyValue WHERE key_name=?", (key,)
            )
            row = cur.fetchone()
            return None if not row else row[0]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_repository] sqlite fallback get_value failed: {e}")
            return None

    if not engine:
        return None

    try:
        with engine.connect() as conn:
            res = conn.execute(
                text("SELECT value_data FROM QAI_KeyValue WHERE key_name=:key_name"),
                {"key_name": key},
            ).fetchone()
            return None if not res else res[0]
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sql_repository] get_value failed: {e}")
        return None


def delete_value(key: str) -> bool:
    if not _ensure_table():
        return False

    engine = get_engine()
    if not engine and not _SQLALCHEMY_AVAILABLE:
        try:
            conn = _get_sqlite_conn()
            conn.execute("DELETE FROM QAI_KeyValue WHERE key_name=?", (key,))
            conn.commit()
            return True
        except Exception as e:  # noqa: BLE001
            logging.warning(
                f"[sql_repository] sqlite fallback delete_value failed: {e}"
            )
            return False

    if not engine:
        return False

    try:
        with engine.begin() as conn:
            conn.execute(
                text("DELETE FROM QAI_KeyValue WHERE key_name=:key_name"),
                {"key_name": key},
            )
        return True
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sql_repository] delete_value failed: {e}")
        return False


def list_values(limit: int = 100) -> list[dict]:  # noqa: ANN001
    if not _ensure_table():
        return []

    engine = get_engine()
    if not engine and not _SQLALCHEMY_AVAILABLE:
        try:
            conn = _get_sqlite_conn()
            cur = conn.execute(
                "SELECT key_name, value_data, updated_at FROM QAI_KeyValue ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            )
            return [
                {"key_name": row[0], "value_data": row[1], "updated_at": row[2]}
                for row in cur.fetchall()
            ]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_repository] sqlite fallback list_values failed: {e}")
            return []

    if not engine:
        return []

    try:
        with engine.connect() as conn:
            res = conn.execute(
                text(
                    "SELECT key_name, value_data, updated_at FROM QAI_KeyValue ORDER BY updated_at DESC LIMIT :limit"
                ),
                {"limit": limit},
            )
            return [
                {"key_name": row[0], "value_data": row[1], "updated_at": row[2]}
                for row in res.fetchall()
            ]
    except Exception as e:  # noqa: BLE001
        logging.warning(f"[sql_repository] list_values failed: {e}")
        return []


__all__ = ["put_value", "get_value", "delete_value", "list_values"]
