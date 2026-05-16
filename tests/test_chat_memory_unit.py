import os
import threading
from unittest.mock import MagicMock, patch

import pytest

from shared import chat_memory as cm


@pytest.fixture(autouse=True)
def ensure_env_and_clear(monkeypatch):
    # Ensure a connection string is present so _create_connection() doesn't raise
    monkeypatch.setenv("QAI_DB_CONN", "DRIVER={dummy};SERVER=;DATABASE=;UID=;PWD=")
    # Clear any cached connections before each test
    try:
        cm.clear_cached_connections()
    except Exception:
        # If clearing fails, reset internal caches (defensive)
        cm._conn_cache.clear()
        cm._conn_timestamps.clear()
    yield
    # Teardown: clear caches again
    try:
        cm.clear_cached_connections()
    except Exception:
        cm._conn_cache.clear()
        cm._conn_timestamps.clear()


def make_mock_conn():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


def test_get_conn_creates_and_caches():
    mock_conn, _ = make_mock_conn()
    with patch("shared.chat_memory.pyodbc.connect", return_value=mock_conn) as mock_connect:
        conn1 = cm._get_conn()
        conn2 = cm._get_conn()

        assert conn1 is conn2
        mock_connect.assert_called_once()


def test_store_embedding_success_calls_execute_and_commit():
    mock_conn, mock_cursor = make_mock_conn()
    with patch("shared.chat_memory.pyodbc.connect", return_value=mock_conn):
        ok = cm.store_embedding("msg-1", [0.0, 0.5, 1.0], "test-model")

        assert ok is True
        # Ensure a cursor was acquired and execute called
        mock_conn.cursor.assert_called()
        # Execute should be called at least once
        assert mock_cursor.execute.called
        # Commit should be called
        mock_conn.commit.assert_called_once()


def test_clear_cached_connections_closes_connection():
    mock_conn, _ = make_mock_conn()
    with patch("shared.chat_memory.pyodbc.connect", return_value=mock_conn):
        conn = cm._get_conn()
        # Ensure it's cached
        assert cm._conn_cache.get(threading.get_ident()) is conn

        cm.clear_cached_connections()

        # After clearing, the previously created connection should have been closed
        mock_conn.close.assert_called()
        assert cm._conn_cache == {}
        assert cm._conn_timestamps == {}
