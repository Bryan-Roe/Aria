"""Comprehensive tests for shared/cosmos_client.py."""

from __future__ import annotations

import logging
import os
from unittest.mock import MagicMock, patch

import pytest

import shared.cosmos_client as cosmos


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_module_state():
    """Reset module-level singletons between tests."""
    cosmos._CLIENT = None
    cosmos._CONTAINER = None
    cosmos._WORLDS_CONTAINER = None


# ---------------------------------------------------------------------------
# _enabled / _settings_present
# ---------------------------------------------------------------------------


class TestEnabled:
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            assert cosmos._enabled() is False

    def test_enabled_when_flag_true(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "true"}):
            assert cosmos._enabled() is True

    def test_case_insensitive(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "TRUE"}):
            assert cosmos._enabled() is True


class TestSettingsPresent:
    def test_false_when_missing_endpoint(self):
        env = {"COSMOS_KEY": "key123"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("COSMOS_ENDPOINT", None)
            assert cosmos._settings_present() is False

    def test_false_when_missing_key(self):
        env = {"COSMOS_ENDPOINT": "https://example.documents.azure.com"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("COSMOS_KEY", None)
            assert cosmos._settings_present() is False

    def test_true_when_both_present(self):
        env = {
            "COSMOS_ENDPOINT": "https://example.documents.azure.com",
            "COSMOS_KEY": "key123",
        }
        with patch.dict(os.environ, env):
            assert cosmos._settings_present() is True


# ---------------------------------------------------------------------------
# init()
# ---------------------------------------------------------------------------


class TestInit:
    def setup_method(self):
        _reset_module_state()

    def test_returns_false_when_disabled(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            assert cosmos.init() is False

    def test_returns_false_when_sdk_unavailable(self):
        env = {
            "QAI_ENABLE_COSMOS": "true",
            "COSMOS_ENDPOINT": "https://example.documents.azure.com",
            "COSMOS_KEY": "k",
        }
        with patch.dict(os.environ, env):
            with patch.object(cosmos, "CosmosClient", None):
                assert cosmos.init() is False

    def test_returns_false_when_settings_missing(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "true"}, clear=False):
            os.environ.pop("COSMOS_ENDPOINT", None)
            os.environ.pop("COSMOS_KEY", None)
            assert cosmos.init() is False

    def test_returns_true_when_already_initialized(self):
        cosmos._CLIENT = MagicMock()
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "true"}):
            assert cosmos.init() is True

    def test_successful_init(self):
        env = {
            "QAI_ENABLE_COSMOS": "true",
            "COSMOS_ENDPOINT": "https://example.documents.azure.com",
            "COSMOS_KEY": "k",
            "COSMOS_DATABASE": "qai",
            "COSMOS_CONTAINER": "chat_sessions",
        }
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_container = MagicMock()
        mock_client.create_database_if_not_exists.return_value = mock_db
        mock_db.create_container_if_not_exists.return_value = mock_container
        mock_partition_key = MagicMock()

        with patch.dict(os.environ, env):
            with patch.object(cosmos, "CosmosClient", return_value=mock_client):
                with patch("shared.cosmos_client.PartitionKey", mock_partition_key, create=True):
                    result = cosmos.init()

        assert result is True
        assert cosmos._CLIENT is mock_client
        assert cosmos._CONTAINER is mock_container

    def test_init_failure_on_db_creation_error(self):
        env = {
            "QAI_ENABLE_COSMOS": "true",
            "COSMOS_ENDPOINT": "https://example.documents.azure.com",
            "COSMOS_KEY": "k",
        }
        mock_client = MagicMock()
        mock_client.create_database_if_not_exists.side_effect = Exception("DB error")

        with patch.dict(os.environ, env):
            with patch.object(cosmos, "CosmosClient", return_value=mock_client):
                result = cosmos.init()

        assert result is False

    def test_init_failure_on_container_creation_error(self):
        env = {
            "QAI_ENABLE_COSMOS": "true",
            "COSMOS_ENDPOINT": "https://example.documents.azure.com",
            "COSMOS_KEY": "k",
        }
        mock_client = MagicMock()
        mock_db = MagicMock()
        mock_client.create_database_if_not_exists.return_value = mock_db
        mock_db.create_container_if_not_exists.side_effect = Exception("Container error")

        with patch.dict(os.environ, env):
            with patch.object(cosmos, "CosmosClient", return_value=mock_client):
                result = cosmos.init()

        assert result is False


# ---------------------------------------------------------------------------
# container()
# ---------------------------------------------------------------------------


class TestContainer:
    def setup_method(self):
        _reset_module_state()

    def test_returns_none_when_not_initialized(self):
        assert cosmos.container() is None

    def test_returns_container_when_initialized(self):
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = MagicMock()
        assert cosmos.container() is cosmos._CONTAINER


# ---------------------------------------------------------------------------
# health()
# ---------------------------------------------------------------------------


class TestHealth:
    def setup_method(self):
        _reset_module_state()

    def test_health_when_disabled(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            h = cosmos.health()
        assert h["enabled"] is False
        assert h["initialized"] is False

    def test_health_structure(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            h = cosmos.health()
        required_keys = ["enabled", "settings_present", "initialized", "container_id", "database", "container", "error"]
        for key in required_keys:
            assert key in h

    def test_health_when_enabled_but_sdk_missing(self):
        env = {"QAI_ENABLE_COSMOS": "true", "COSMOS_ENDPOINT": "https://x.com", "COSMOS_KEY": "k"}
        with patch.dict(os.environ, env):
            with patch.object(cosmos, "CosmosClient", None):
                h = cosmos.health()
        assert h["enabled"] is True
        assert h["initialized"] is False


# ---------------------------------------------------------------------------
# record_chat_message()
# ---------------------------------------------------------------------------


class TestRecordChatMessage:
    def setup_method(self):
        _reset_module_state()

    def test_returns_false_when_cosmos_disabled(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            result = cosmos.record_chat_message("user1", {"content": "hello"}, "local", "model")
        assert result is False

    def test_returns_false_with_empty_content(self):
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = MagicMock()

        with patch.object(cosmos, "init", return_value=True):
            result = cosmos.record_chat_message(
                "user1", {"content": ""}, "local", "model"
            )
        assert result is False

    def test_returns_false_with_whitespace_only_content(self):
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = MagicMock()

        with patch.object(cosmos, "init", return_value=True):
            result = cosmos.record_chat_message(
                "user1", {"content": "   "}, "local", "model"
            )
        assert result is False

    def test_returns_true_on_success(self):
        mock_container = MagicMock()
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = mock_container

        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "container", return_value=mock_container):
                result = cosmos.record_chat_message(
                    "user1",
                    {"content": "Hello world", "role": "user"},
                    "openai",
                    "gpt-4",
                )
        assert result is True
        mock_container.upsert_item.assert_called_once()
        # Verify doc structure
        call_args = mock_container.upsert_item.call_args[0][0]
        assert call_args["userId"] == "user1"
        assert call_args["content"] == "Hello world"
        assert call_args["provider"] == "openai"

    def test_handles_upsert_exception(self):
        mock_container = MagicMock()
        mock_container.upsert_item.side_effect = Exception("Network error")
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = mock_container

        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "container", return_value=mock_container):
                result = cosmos.record_chat_message(
                    "user1", {"content": "hello"}, "local", "model"
                )
        assert result is False

    def test_doc_id_is_unique_per_call(self):
        mock_container = MagicMock()
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = mock_container

        ids = []
        def capture_upsert(doc):
            ids.append(doc["id"])

        mock_container.upsert_item.side_effect = capture_upsert

        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "container", return_value=mock_container):
                cosmos.record_chat_message("u1", {"content": "a"}, "p", "m")
                cosmos.record_chat_message("u1", {"content": "b"}, "p", "m")

        assert ids[0] != ids[1]


# ---------------------------------------------------------------------------
# record_chat_session()
# ---------------------------------------------------------------------------


class TestRecordChatSession:
    def setup_method(self):
        _reset_module_state()

    def test_returns_false_when_disabled(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            result = cosmos.record_chat_session("user1", [], "local", "m")
        assert result is False

    def test_returns_true_on_success(self):
        mock_container = MagicMock()
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = mock_container

        messages = [{"role": "user", "content": "hi"}]
        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "container", return_value=mock_container):
                result = cosmos.record_chat_session("user1", messages, "openai", "gpt-4")

        assert result is True
        call_args = mock_container.upsert_item.call_args[0][0]
        assert call_args["userId"] == "user1"
        assert call_args["messageCount"] == 1

    def test_handles_upsert_exception(self):
        mock_container = MagicMock()
        mock_container.upsert_item.side_effect = Exception("error")
        cosmos._CLIENT = MagicMock()
        cosmos._CONTAINER = mock_container

        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "container", return_value=mock_container):
                result = cosmos.record_chat_session("u1", [], "local", "m")
        assert result is False


# ---------------------------------------------------------------------------
# worlds_container() / record_world() / get_world() / list_worlds()
# ---------------------------------------------------------------------------


class TestWorldsContainer:
    def setup_method(self):
        _reset_module_state()

    def test_returns_none_when_cosmos_disabled(self):
        with patch.dict(os.environ, {"QAI_ENABLE_COSMOS": "false"}):
            assert cosmos.worlds_container() is None

    def test_returns_none_when_sdk_missing(self):
        with patch.object(cosmos, "CosmosClient", None):
            with patch.object(cosmos, "init", return_value=True):
                assert cosmos.worlds_container() is None

    def test_returns_cached_container(self):
        mock_wc = MagicMock()
        cosmos._WORLDS_CONTAINER = mock_wc
        cosmos._CLIENT = MagicMock()

        with patch.object(cosmos, "init", return_value=True):
            with patch.object(cosmos, "CosmosClient", MagicMock()):
                result = cosmos.worlds_container()
        assert result is mock_wc


class TestRecordWorld:
    def setup_method(self):
        _reset_module_state()

    def test_returns_false_when_container_unavailable(self):
        with patch.object(cosmos, "worlds_container", return_value=None):
            assert cosmos.record_world({"id": "w1"}) is False

    def test_returns_true_on_success(self):
        mock_wc = MagicMock()
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.record_world({"id": "w1", "theme_seed": "forest_1"})
        assert result is True
        mock_wc.upsert_item.assert_called_once()

    def test_handles_upsert_exception(self):
        mock_wc = MagicMock()
        mock_wc.upsert_item.side_effect = Exception("error")
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.record_world({"id": "w1"})
        assert result is False


class TestGetWorld:
    def setup_method(self):
        _reset_module_state()

    def test_returns_none_when_container_unavailable(self):
        with patch.object(cosmos, "worlds_container", return_value=None):
            assert cosmos.get_world("forest", 1) is None

    def test_returns_none_when_not_found(self):
        mock_wc = MagicMock()
        mock_wc.query_items.return_value = []
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            assert cosmos.get_world("forest", 1) is None

    def test_returns_first_item_when_found(self):
        mock_wc = MagicMock()
        world_doc = {"id": "world-forest-1", "theme": "forest"}
        mock_wc.query_items.return_value = [world_doc]
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.get_world("forest", 1)
        assert result == world_doc

    def test_handles_query_exception(self):
        mock_wc = MagicMock()
        mock_wc.query_items.side_effect = Exception("query error")
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.get_world("forest", 1)
        assert result is None


class TestListWorlds:
    def setup_method(self):
        _reset_module_state()

    def test_returns_empty_when_container_unavailable(self):
        with patch.object(cosmos, "worlds_container", return_value=None):
            assert cosmos.list_worlds() == []

    def test_returns_items(self):
        mock_wc = MagicMock()
        worlds = [{"id": f"w{i}"} for i in range(5)]
        mock_wc.query_items.return_value = iter(worlds)
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.list_worlds()
        assert len(result) == 5

    def test_respects_limit(self):
        mock_wc = MagicMock()
        worlds = [{"id": f"w{i}"} for i in range(10)]
        mock_wc.query_items.return_value = iter(worlds)
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.list_worlds(limit=3)
        assert len(result) == 3

    def test_handles_query_exception(self):
        mock_wc = MagicMock()
        mock_wc.query_items.side_effect = Exception("error")
        with patch.object(cosmos, "worlds_container", return_value=mock_wc):
            result = cosmos.list_worlds()
        assert result == []
