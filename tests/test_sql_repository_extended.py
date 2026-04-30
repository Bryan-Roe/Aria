"""Extended tests for shared/sql_repository.py.

Covers: _sqlite_path_from_url, _get_sqlite_conn (caching), _ensure_table
idempotency, CRUD error handling, and no-engine fallback paths.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("QAI_SQL_URL", "sqlite:///:memory:")

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_repo_state():
    """Reset cached state between tests."""
    import shared.sql_engine as eng
    import shared.sql_repository as repo

    eng._ENGINE = None
    eng._LAST_URL = None
    repo._TABLE_CREATED = False
    if repo._SQLITE_CONN is not None:
        try:
            repo._SQLITE_CONN.close()
        except Exception:
            pass
    repo._SQLITE_CONN = None

    old_url = os.environ.get("QAI_SQL_URL")
    old_db_conn = os.environ.get("QAI_DB_CONN")
    yield

    eng._ENGINE = None
    eng._LAST_URL = None
    repo._TABLE_CREATED = False
    if repo._SQLITE_CONN is not None:
        try:
            repo._SQLITE_CONN.close()
        except Exception:
            pass
    repo._SQLITE_CONN = None

    for key, val in [("QAI_SQL_URL", old_url), ("QAI_DB_CONN", old_db_conn)]:
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val


# ---------------------------------------------------------------------------
# _sqlite_path_from_url
# ---------------------------------------------------------------------------


def test_sqlite_path_from_url_memory():
    from shared.sql_repository import _sqlite_path_from_url

    assert _sqlite_path_from_url("sqlite:///:memory:") == ":memory:"


def test_sqlite_path_from_url_file():
    from shared.sql_repository import _sqlite_path_from_url

    result = _sqlite_path_from_url("sqlite:///path/to/db.sqlite")
    assert "db.sqlite" in result


def test_sqlite_path_from_url_unknown_format_returns_memory():
    from shared.sql_repository import _sqlite_path_from_url

    result = _sqlite_path_from_url("some-weird-url")
    assert result == ":memory:"


# ---------------------------------------------------------------------------
# _get_sqlite_conn (caching)
# ---------------------------------------------------------------------------


def test_get_sqlite_conn_returns_connection():
    import shared.sql_repository as repo

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    conn = repo._get_sqlite_conn()
    assert conn is not None


def test_get_sqlite_conn_is_cached():
    import shared.sql_repository as repo

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    conn1 = repo._get_sqlite_conn()
    conn2 = repo._get_sqlite_conn()
    assert conn1 is conn2


# ---------------------------------------------------------------------------
# _ensure_table — idempotency
# ---------------------------------------------------------------------------


def test_ensure_table_returns_true_when_already_created():
    import shared.sql_repository as repo

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    assert repo._ensure_table() is True
    # Calling again should return True (cached flag)
    assert repo._ensure_table() is True


def test_ensure_table_returns_false_when_no_engine_and_sqlalchemy():
    """When engine unavailable and SQLAlchemy present, returns False."""
    import shared.sql_repository as repo

    with patch("shared.sql_repository.get_engine", return_value=None), \
         patch("shared.sql_repository._SQLALCHEMY_AVAILABLE", True):
        repo._TABLE_CREATED = False
        result = repo._ensure_table()
        assert result is False


# ---------------------------------------------------------------------------
# CRUD with SQLAlchemy (SQLite engine)
# ---------------------------------------------------------------------------


def test_put_and_get_value():
    from shared.sql_repository import get_value, put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    assert put_value("test_key", "test_val") is True
    assert get_value("test_key") == "test_val"


def test_put_value_update_existing():
    from shared.sql_repository import get_value, put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    put_value("k", "v1")
    put_value("k", "v2")
    assert get_value("k") == "v2"


def test_get_value_returns_none_for_missing_key():
    from shared.sql_repository import get_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    assert get_value("nonexistent_key_xyz") is None


def test_delete_value_removes_key():
    from shared.sql_repository import delete_value, get_value, put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    put_value("del_key", "del_val")
    assert delete_value("del_key") is True
    assert get_value("del_key") is None


def test_delete_value_nonexistent_key_returns_true():
    """Delete of missing key should still succeed (no error)."""
    from shared.sql_repository import delete_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    # Table must exist first
    from shared.sql_repository import _ensure_table
    _ensure_table()
    result = delete_value("absolutely_not_there")
    assert result is True


def test_list_values_returns_inserted_items():
    from shared.sql_repository import list_values, put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    put_value("a", "1")
    put_value("b", "2")
    items = list_values()
    keys = [item["key_name"] for item in items]
    assert "a" in keys
    assert "b" in keys


def test_list_values_respects_limit():
    from shared.sql_repository import list_values, put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    for i in range(10):
        put_value(f"key_{i}", str(i))
    result = list_values(limit=3)
    assert len(result) <= 3


# ---------------------------------------------------------------------------
# No-engine paths (table_created=False, no URL)
# ---------------------------------------------------------------------------


def test_put_value_returns_false_when_no_engine():
    from shared.sql_repository import put_value

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    import shared.sql_repository as repo
    repo._TABLE_CREATED = False

    with patch("shared.sql_repository.get_engine", return_value=None), \
         patch("shared.sql_repository._SQLALCHEMY_AVAILABLE", True):
        result = put_value("k", "v")
        assert result is False


def test_get_value_returns_none_when_no_engine():
    from shared.sql_repository import get_value

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    import shared.sql_repository as repo
    repo._TABLE_CREATED = False

    with patch("shared.sql_repository.get_engine", return_value=None), \
         patch("shared.sql_repository._SQLALCHEMY_AVAILABLE", True):
        assert get_value("k") is None


def test_delete_value_returns_false_when_no_engine():
    from shared.sql_repository import delete_value

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    import shared.sql_repository as repo
    repo._TABLE_CREATED = False

    with patch("shared.sql_repository.get_engine", return_value=None), \
         patch("shared.sql_repository._SQLALCHEMY_AVAILABLE", True):
        assert delete_value("k") is False


def test_list_values_returns_empty_when_no_engine():
    from shared.sql_repository import list_values

    os.environ.pop("QAI_SQL_URL", None)
    os.environ.pop("QAI_DB_CONN", None)
    import shared.sql_repository as repo
    repo._TABLE_CREATED = False

    with patch("shared.sql_repository.get_engine", return_value=None), \
         patch("shared.sql_repository._SQLALCHEMY_AVAILABLE", True):
        assert list_values() == []


# ---------------------------------------------------------------------------
# Exception handling in CRUD
# ---------------------------------------------------------------------------


def test_put_value_handles_db_error_gracefully():
    """put_value returns False when DB raises."""
    from shared.sql_repository import put_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    import shared.sql_repository as repo
    repo._TABLE_CREATED = True  # skip _ensure_table

    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"
    mock_engine.begin.side_effect = Exception("DB error")

    with patch("shared.sql_repository.get_engine", return_value=mock_engine):
        result = put_value("k", "v")
        assert result is False


def test_get_value_handles_db_error_gracefully():
    """get_value returns None when DB raises."""
    from shared.sql_repository import get_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    import shared.sql_repository as repo
    repo._TABLE_CREATED = True

    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"
    mock_engine.connect.side_effect = Exception("DB error")

    with patch("shared.sql_repository.get_engine", return_value=mock_engine):
        result = get_value("k")
        assert result is None


def test_delete_value_handles_db_error_gracefully():
    """delete_value returns False when DB raises."""
    from shared.sql_repository import delete_value

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    import shared.sql_repository as repo
    repo._TABLE_CREATED = True

    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"
    mock_engine.begin.side_effect = Exception("DB error")

    with patch("shared.sql_repository.get_engine", return_value=mock_engine):
        result = delete_value("k")
        assert result is False


def test_list_values_handles_db_error_gracefully():
    """list_values returns [] when DB raises."""
    from shared.sql_repository import list_values

    os.environ["QAI_SQL_URL"] = "sqlite:///:memory:"
    import shared.sql_repository as repo
    repo._TABLE_CREATED = True

    mock_engine = MagicMock()
    mock_engine.dialect.name = "sqlite"
    mock_engine.connect.side_effect = Exception("DB error")

    with patch("shared.sql_repository.get_engine", return_value=mock_engine):
        result = list_values()
        assert result == []
