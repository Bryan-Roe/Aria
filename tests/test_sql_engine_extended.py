"""Extended tests for shared/sql_engine.py.

Covers: _prune_recent_slow_queries, _compute_query_hash, _build_url_from_odbc,
resolve_sql_url with ODBC path, get_engine URL change detection,
quick_query error/slow-query paths, _track_query_metrics toggle,
and engine_stats saturation detection.
"""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock, patch

import pytest

# Ensure SQLite in-memory DB for isolation
os.environ.setdefault("QAI_SQL_URL", "sqlite:///:memory:")

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_engine_state():
    """Reset cached engine and slow-query deque between tests."""
    import shared.sql_engine as eng

    eng._ENGINE = None
    eng._LAST_URL = None
    eng._recent_slow_queries.clear()
    old_url = os.environ.get("QAI_SQL_URL")
    old_db_conn = os.environ.get("QAI_DB_CONN")
    old_slow_ms = os.environ.get("QAI_SQL_SLOW_MS")
    old_tracking = os.environ.get("QAI_ENABLE_QUERY_TRACKING")
    yield
    eng._ENGINE = None
    eng._LAST_URL = None
    eng._recent_slow_queries.clear()
    # Restore env vars
    for key, val in [
        ("QAI_SQL_URL", old_url),
        ("QAI_DB_CONN", old_db_conn),
        ("QAI_SQL_SLOW_MS", old_slow_ms),
        ("QAI_ENABLE_QUERY_TRACKING", old_tracking),
    ]:
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


# ---------------------------------------------------------------------------
# _prune_recent_slow_queries
# ---------------------------------------------------------------------------


def test_prune_removes_old_entries():
    import shared.sql_engine as eng

    now = time.time()
    # Add one old entry (> 60 s ago) and one recent
    eng._recent_slow_queries.append((now - 120, 600.0))  # old
    eng._recent_slow_queries.append((now - 10, 700.0))  # recent
    eng._prune_recent_slow_queries()
    assert len(eng._recent_slow_queries) == 1
    assert eng._recent_slow_queries[0][1] == 700.0


def test_prune_enforces_max_size():
    import shared.sql_engine as eng

    now = time.time()
    # Exceed _SLOW_QUERY_CACHE_MAX_SIZE
    max_size = eng._SLOW_QUERY_CACHE_MAX_SIZE
    for i in range(max_size + 10):
        eng._recent_slow_queries.append((now - 5, float(i)))
    eng._prune_recent_slow_queries()
    assert len(eng._recent_slow_queries) <= max_size


def test_prune_empty_deque_is_noop():
    import shared.sql_engine as eng

    eng._recent_slow_queries.clear()
    eng._prune_recent_slow_queries()  # must not raise
    assert len(eng._recent_slow_queries) == 0


# ---------------------------------------------------------------------------
# _compute_query_hash
# ---------------------------------------------------------------------------


def test_compute_query_hash_is_16_chars():
    from shared.sql_engine import _compute_query_hash

    h = _compute_query_hash("SELECT 1")
    assert isinstance(h, str)
    assert len(h) == 16


def test_compute_query_hash_normalises_whitespace():
    from shared.sql_engine import _compute_query_hash

    h1 = _compute_query_hash("SELECT   1")
    h2 = _compute_query_hash("SELECT 1")
    assert h1 == h2


def test_compute_query_hash_differs_for_different_sql():
    from shared.sql_engine import _compute_query_hash

    assert _compute_query_hash("SELECT 1") != _compute_query_hash("SELECT 2")


# ---------------------------------------------------------------------------
# _build_url_from_odbc
# ---------------------------------------------------------------------------


def test_build_url_from_odbc_encodes_connection_string():
    from shared.sql_engine import _build_url_from_odbc

    odbc = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:host.db.windows.net,1433;Database=mydb;"
    url = _build_url_from_odbc(odbc)
    assert url.startswith("mssql+pyodbc:///?odbc_connect=")
    # Spaces/braces should be percent-encoded
    assert " " not in url[url.index("odbc_connect=") + len("odbc_connect=") :]


# ---------------------------------------------------------------------------
# resolve_sql_url
# ---------------------------------------------------------------------------


def test_resolve_sql_url_returns_qai_sql_url():
    from shared.sql_engine import resolve_sql_url

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    assert resolve_sql_url() == "sqlite:///:memory:"


def test_resolve_sql_url_uses_odbc_fallback():
    from shared.sql_engine import resolve_sql_url

    os.environ.pop("QAI_SQL_URL", None)
    os.environ["QAI_DB_CONN"] = "Driver={SQL Server};Server=localhost;"
    url = resolve_sql_url()
    assert url is not None
    assert "mssql+pyodbc" in url


def test_resolve_sql_url_returns_none_when_neither_set():
    from shared.sql_engine import resolve_sql_url

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    assert resolve_sql_url() is None


def test_resolve_sql_url_strips_whitespace():
    from shared.sql_engine import resolve_sql_url

    os.environ["QAI_SQL_URL"] = "  sqlite:///:memory:  "
    result = resolve_sql_url()
    assert result == "sqlite:///:memory:"


def test_resolve_sql_url_empty_string_returns_none():
    from shared.sql_engine import resolve_sql_url

    os.environ["QAI_SQL_URL"] = "   "
    assert resolve_sql_url() is None


# ---------------------------------------------------------------------------
# get_engine — URL change detection
# ---------------------------------------------------------------------------


def test_get_engine_creates_new_engine_on_url_change():
    from shared.sql_engine import get_engine

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    engine1 = get_engine()
    assert engine1 is not None

    # Change the URL — should create a new engine
    os.environ["QAI_SQL_URL"] = "sqlite:///file::memory:?cache=shared"
    engine2 = get_engine()
    assert engine2 is not None
    assert engine1 is not engine2


def test_get_engine_returns_none_when_no_url():
    import shared.sql_engine as eng
    from shared.sql_engine import get_engine

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    eng._ENGINE = None
    eng._LAST_URL = None
    assert get_engine() is None


def test_get_engine_caches_instance():
    from shared.sql_engine import get_engine

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    e1 = get_engine()
    e2 = get_engine()
    assert e1 is e2


# ---------------------------------------------------------------------------
# quick_query — error and slow-query tracking
# ---------------------------------------------------------------------------


def test_quick_query_returns_empty_on_bad_sql():
    from shared.sql_engine import quick_query

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    rows = quick_query("INVALID SQL ###")
    assert rows == []


def test_quick_query_appends_slow_entry():
    import shared.sql_engine as eng
    from shared.sql_engine import quick_query

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    os.environ["QAI_SQL_SLOW_MS"] = "1"  # 1 ms threshold
    eng._recent_slow_queries.clear()
    # Patch perf_counter to make the query appear to take 100 ms
    _counter = [0.0]

    def _fake_perf_counter():
        _counter[0] += 0.05  # each call advances by 50 ms
        return _counter[0]

    with patch("shared.sql_engine.time.perf_counter", side_effect=_fake_perf_counter):
        quick_query("SELECT 1 AS x")

    assert len(eng._recent_slow_queries) >= 1


def test_quick_query_no_slow_entry_when_fast():
    import shared.sql_engine as eng
    from shared.sql_engine import quick_query

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    os.environ["QAI_SQL_SLOW_MS"] = "9999"  # high threshold — nothing qualifies
    eng._recent_slow_queries.clear()
    quick_query("SELECT 1 AS x")
    assert len(eng._recent_slow_queries) == 0


# ---------------------------------------------------------------------------
# _track_query_metrics
# ---------------------------------------------------------------------------


def test_track_query_metrics_disabled_by_default():
    """Should return immediately without touching DB when tracking is off."""
    import shared.sql_engine as eng

    os.environ.pop("QAI_ENABLE_QUERY_TRACKING", None)
    # No exception expected even if engine is None
    eng._track_query_metrics("SELECT 1", 10.0, "sqlite")


def test_track_query_metrics_enabled_but_no_engine():
    """Should silently skip when tracking enabled but no engine."""
    import shared.sql_engine as eng

    os.environ["QAI_ENABLE_QUERY_TRACKING"] = "true"
    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    eng._ENGINE = None
    eng._LAST_URL = None
    eng._track_query_metrics("SELECT 1", 10.0, "sqlite")  # must not raise


# ---------------------------------------------------------------------------
# engine_stats — saturation detection
# ---------------------------------------------------------------------------


def test_engine_stats_saturation_alert_triggered():
    """Saturation alert should appear when checkedout/size > 80%."""
    from shared.sql_engine import engine_stats

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"

    mock_pool = MagicMock()
    mock_pool.size.return_value = 10
    mock_pool.checkedout.return_value = 9  # 90% saturation
    mock_pool.overflow.return_value = 0
    mock_pool.status.return_value = "9 out of 10"
    mock_pool._recycle = 1800
    mock_pool._timeout = 30

    with patch("shared.sql_engine.get_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.pool = mock_pool
        mock_engine.dialect.name = "sqlite"
        mock_get_engine.return_value = mock_engine

        stats = engine_stats()

    assert stats["saturation_alert"] is not None
    assert stats["saturation_pct"] > 80


def test_engine_stats_no_alert_below_threshold():
    """No saturation alert when pool is below 80%."""
    from shared.sql_engine import engine_stats

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"

    mock_pool = MagicMock()
    mock_pool.size.return_value = 10
    mock_pool.checkedout.return_value = 5  # 50%
    mock_pool.overflow.return_value = 0
    mock_pool.status.return_value = "5 out of 10"
    mock_pool._recycle = 1800
    mock_pool._timeout = 30

    with patch("shared.sql_engine.get_engine") as mock_get_engine:
        mock_engine = MagicMock()
        mock_engine.pool = mock_pool
        mock_engine.dialect.name = "sqlite"
        mock_get_engine.return_value = mock_engine

        stats = engine_stats()

    assert stats["saturation_alert"] is None
    assert stats["saturation_pct"] == 50.0


def test_engine_stats_returns_disabled_when_no_engine():
    import shared.sql_engine as eng
    from shared.sql_engine import engine_stats

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    eng._ENGINE = None
    eng._LAST_URL = None
    stats = engine_stats()
    assert stats == {"enabled": False}


def test_engine_stats_includes_slow_query_count():
    import shared.sql_engine as eng
    from shared.sql_engine import engine_stats

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    now = time.time()
    eng._recent_slow_queries.append((now - 5, 800.0))  # recent slow query

    stats = engine_stats()
    assert stats["slow_queries_1min"] >= 1
