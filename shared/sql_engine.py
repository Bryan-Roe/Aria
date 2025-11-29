"""Unified SQL engine helper for QAI.

Purpose:
  - Provide a lazy, pooled SQLAlchemy Engine built from either QAI_SQL_URL
    or (fallback) QAI_DB_CONN ODBC connection string.
  - Support multiple RDBMS vendors (SQL Server, PostgreSQL, MySQL, SQLite).
  - Offer a simple health probe used by /api/ai/status.
  - Provide lightweight pool statistics for diagnostics.
  - Slow query logging with configurable threshold.
  - Gracefully degrade when no URL or driver is available.

Environment variables:
  QAI_SQL_URL        -> Preferred full SQLAlchemy URL (e.g. postgresql+psycopg://user:pass@host/db)
  QAI_DB_CONN        -> Legacy ODBC string for SQL Server (used with pyodbc fallback)
  QAI_SQL_SLOW_MS    -> (optional) slow query threshold in milliseconds (default: 500)

Usage:
  from shared.sql_engine import sql_health, engine_stats, quick_query

Design notes:
  - Engine cached globally; pool_pre_ping=True to evict dead connections.
  - For SQL Server ODBC fallback we URL-encode the entire connection string.
  - Deliberately lightweight (no ORM Session dependency) but future-ready.
  - Stats function is defensive; returns None values if pool does not expose metrics.
"""
from __future__ import annotations

import os
import logging
import time
import urllib.parse
import hashlib
from typing import Optional, Any, Dict

# Attempt to import SQLAlchemy; provide graceful fallback if unavailable
_SQLALCHEMY_AVAILABLE = True
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError  # type: ignore
except Exception:  # pragma: no cover
    _SQLALCHEMY_AVAILABLE = False
    create_engine = None  # type: ignore
    text = None  # type: ignore

_ENGINE = None  # cached engine instance
_LAST_URL = None

# Slow query frequency tracking (in-memory, last 60 seconds)
# Use collections.deque for O(1) append and efficient pruning from left
from collections import deque
_SLOW_QUERY_LOG: deque[tuple[float, float]] = deque()  # (timestamp, duration_ms)
_SLOW_QUERY_CACHE_SIZE = 1000  # Maximum entries to prevent unbounded growth

def _prune_slow_query_log() -> None:
    """Remove slow query entries older than 60 seconds.
    
    Uses efficient deque operations - pops from left since entries are 
    chronologically ordered.
    """
    now = time.time()
    cutoff = now - 60
    # Pop old entries from the left (oldest first)
    while _SLOW_QUERY_LOG and _SLOW_QUERY_LOG[0][0] < cutoff:
        _SLOW_QUERY_LOG.popleft()
    
    # Also enforce max size to prevent memory growth
    while len(_SLOW_QUERY_LOG) > _SLOW_QUERY_CACHE_SIZE:
        _SLOW_QUERY_LOG.popleft()

def _compute_query_hash(sql: str) -> str:
    """Compute SHA256 hash of normalized SQL for tracking."""
    # Use faster string operations - avoid multiple replace calls
    normalized = ' '.join(sql.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

def _track_query_metrics(sql: str, duration_ms: float, vendor: str) -> None:
    """Persist query metrics to QAI_QueryMetrics table if tracking enabled."""
    if os.getenv("QAI_ENABLE_QUERY_TRACKING", "false").lower() != "true":
        return
    
    engine = get_engine()
    if not engine:
        return
    
    try:
        query_hash = _compute_query_hash(sql)
        sql_snippet = sql[:500]
        
        insert_sql = text(
            "INSERT INTO QAI_QueryMetrics (query_hash, sql_snippet, vendor, execution_time_ms, executed_at) "
            "VALUES (:hash, :snippet, :vendor, :duration, :ts)"
        )
        
        with engine.begin() as conn:
            conn.execute(insert_sql, {
                "hash": query_hash,
                "snippet": sql_snippet,
                "vendor": vendor,
                "duration": duration_ms,
                "ts": time.time(),
            })
    except Exception as e:  # noqa: BLE001
        # Silent degradation - don't fail queries due to tracking issues
        logging.debug(f"[sql_engine] Query tracking failed: {e}")

# ----------------------------------------------------------------------------
# URL Resolution
# ----------------------------------------------------------------------------

def _build_url_from_odbc(conn_str: str) -> str:
    """Convert raw ODBC connection string into SQLAlchemy pyodbc URL.

    Example input:
      Driver={ODBC Driver 18 for SQL Server};Server=tcp:host.database.windows.net,1433;Database=db;Uid=user;Pwd=pw;Encrypt=yes;TrustServerCertificate=no;

    Returns:
      mssql+pyodbc:///?odbc_connect=<percent-encoded>
    """
    return f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"


def resolve_sql_url() -> Optional[str]:
    url = os.getenv("QAI_SQL_URL")
    if url:
        return url.strip() or None
    odbc = os.getenv("QAI_DB_CONN")
    if odbc:
        return _build_url_from_odbc(odbc)
    return None

def resolve_slow_query_threshold() -> float:
    """Determine slow query threshold in milliseconds with environment awareness.
    
    Priority: QAI_SQL_SLOW_MS env var > environment profile > default 500ms
    Profiles: dev=100ms, staging=300ms, production=500ms
    """
    explicit = os.getenv("QAI_SQL_SLOW_MS")
    if explicit:
        try:
            return float(explicit)
        except ValueError:
            pass
    
    env_profile = os.getenv("AZURE_FUNCTIONS_ENVIRONMENT", "development").lower()
    if "dev" in env_profile or "local" in env_profile:
        return 100.0
    elif "stag" in env_profile or "test" in env_profile:
        return 300.0
    else:  # production or unknown
        return 500.0

# ----------------------------------------------------------------------------
# Engine Accessors
# ----------------------------------------------------------------------------

def get_engine():  # noqa: ANN001
    global _ENGINE, _LAST_URL
    url = resolve_sql_url()
    if not url:
        return None
    if not _SQLALCHEMY_AVAILABLE:
        # Fallback: no SQLAlchemy installed
        # Return None to allow sqlite3 fallback in calling code
        # Only SQLite URLs are supported in fallback mode
        if str(url).startswith("sqlite"):
            _ENGINE = None
            _LAST_URL = url
            return None
        # Unsupported vendor without SQLAlchemy
        return None
        # Unsupported vendor without SQLAlchemy
        return None
    if _ENGINE is None or _LAST_URL != url:
        try:
            _ENGINE = create_engine(
                url,
                pool_pre_ping=True,
                pool_recycle=1800,  # refresh idle conns every 30m
                future=True,
            )
            _LAST_URL = url
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_engine] Engine creation failed: {e}")
            _ENGINE = None
            return None
    return _ENGINE

# ----------------------------------------------------------------------------
# Health Probe
# ----------------------------------------------------------------------------

def sql_health() -> dict:
    engine = get_engine()
    if not engine:
        return {"enabled": False, "url": None}
    info = {
        "enabled": True,
        "url": str(getattr(engine, "url", "")),
        "vendor": getattr(engine.dialect, "name", "unknown"),
        "connectivity": False,
        "error": None,
    }
    try:
        if _SQLALCHEMY_AVAILABLE:
            with engine.connect() as conn:
                val = conn.execute(text("SELECT 1")).scalar()
                info["connectivity"] = bool(val == 1)
        else:
            # Fallback: direct sqlite3 connectivity check
            import sqlite3
            # Use in-memory DB for health probe
            with sqlite3.connect(":memory:") as conn:
                cur = conn.execute("SELECT 1")
                row = cur.fetchone()
                info["connectivity"] = bool(row and row[0] == 1)
    except Exception as e:  # noqa: BLE001
        info["error"] = str(e)
    return info

# ----------------------------------------------------------------------------
# Pool Statistics (best effort)
# ----------------------------------------------------------------------------

def _safe_call(obj: Any, name: str) -> Any:
    try:
        attr = getattr(obj, name, None)
        if callable(attr):
            return attr()
        return attr
    except Exception:
        return None

def engine_stats() -> Dict[str, Any]:
    engine = get_engine()
    if not engine:
        return {"enabled": False}
    pool = getattr(engine, "pool", None)
    stats: Dict[str, Any] = {
        "enabled": True,
        "type": pool.__class__.__name__ if pool else None,
        "vendor": getattr(engine.dialect, "name", "unknown"),
        "size": None,
        "checkedout": None,
        "overflow": None,
        "recycle": None,
        "timeout": None,
        "status": None,
        "saturation_alert": None,
        "saturation_pct": None,
        "slow_queries_1min": 0,
        "slow_query_threshold_ms": resolve_slow_query_threshold(),
    }
    if not _SQLALCHEMY_AVAILABLE:
        # Minimal stats for fallback
        stats.update({
            "type": "DirectSQLite",
            "vendor": "sqlite",
            "status": "ok",
        })
        _prune_slow_query_log()
        stats["slow_queries_1min"] = len(_SLOW_QUERY_LOG)
        return stats
    if pool:
        for attr in ["size", "checkedout", "overflow"]:
            stats[attr] = _safe_call(pool, attr)
        # Internal attributes (QueuePool only)
        stats["recycle"] = getattr(pool, "_recycle", None)
        stats["timeout"] = getattr(pool, "_timeout", None)
        stats["status"] = _safe_call(pool, "status")
        
        # Saturation detection
        pool_size = stats["size"]
        checked_out = stats["checkedout"]
        if pool_size and checked_out is not None:
            saturation_pct = (checked_out / pool_size) * 100
            stats["saturation_pct"] = round(saturation_pct, 1)
            if saturation_pct > 80:
                stats["saturation_alert"] = f"Pool {saturation_pct:.1f}% saturated ({checked_out}/{pool_size})"
                logging.warning(f"[sql_engine] {stats['saturation_alert']} vendor={stats['vendor']}")
    
    # Slow query frequency
    _prune_slow_query_log()
    stats["slow_queries_1min"] = len(_SLOW_QUERY_LOG)
    
    return stats

# ----------------------------------------------------------------------------
# Convenience Exec (read-only quick queries) with slow query logging
# ----------------------------------------------------------------------------

def quick_query(sql: str, **kwargs) -> list[dict]:  # noqa: ANN001
    """Execute a read-only query and return list of row dicts.

    Optional kwargs:
      simulate_delay (float) -> seconds to sleep before executing (test hook)
    """
    engine = get_engine()
    if not engine:
        return []
    simulate_delay = float(kwargs.get("simulate_delay", 0) or 0)
    if simulate_delay > 0:
        time.sleep(simulate_delay)
    start = time.perf_counter()
    rows: list[dict] = []
    if _SQLALCHEMY_AVAILABLE:
        try:
            with engine.connect() as conn:
                res = conn.execute(text(sql))
                cols = res.keys()
                rows = [dict(zip(cols, row)) for row in res.fetchall()]
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_engine] quick_query failed: {e}")
            return []
    else:
        # Fallback: execute via sqlite3
        import sqlite3
        try:
            with sqlite3.connect(":memory:") as conn:
                cur = conn.execute(sql)
                # SQLite cursor.description provides columns
                cols = [d[0] for d in (cur.description or [])]
                data = cur.fetchall()
                if cols:
                    rows = [dict(zip(cols, row)) for row in data]
                else:
                    rows = []
        except Exception as e:  # noqa: BLE001
            logging.warning(f"[sql_engine] quick_query fallback failed: {e}")
            return []
    duration_ms = (time.perf_counter() - start) * 1000.0
    slow_ms = resolve_slow_query_threshold()
    vendor = getattr(engine.dialect, "name", "unknown")
    
    # Track all queries if enabled (not just slow ones)
    _track_query_metrics(sql, duration_ms, vendor)
    
    if duration_ms > slow_ms:
        truncated_sql = sql[:120].replace("\n", " ")
        logging.warning(
            f"[sql_engine] slow query ({duration_ms:.1f} ms > {slow_ms} ms) vendor={vendor} sql={truncated_sql}"
        )
        # Track slow query frequency
        global _SLOW_QUERY_LOG
        _SLOW_QUERY_LOG.append((time.time(), duration_ms))
    return rows

__all__ = ["resolve_sql_url", "get_engine", "sql_health", "quick_query", "engine_stats", "resolve_slow_query_threshold"]
