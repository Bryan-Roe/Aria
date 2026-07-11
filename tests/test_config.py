"""Tests for shared/config.py — central configuration layer.

These tests verify that:
- Settings loads with defaults (no env vars required)
- Environment variables are correctly picked up
- The ``active_provider()`` helper returns the correct provider
- ``summary()`` never includes secret values
- ``reset_settings()`` clears the cache
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from shared.config import Settings, get_settings, reset_settings

# Ensure shared/ is importable when running from the repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(autouse=True)
def _clean_settings():
    """Reset the settings singleton before and after each test."""
    reset_settings()
    yield
    reset_settings()


class TestDefaultSettings:
    """Settings should have safe defaults without any env vars."""

    def test_loads_without_env_vars(self):
        s = Settings()
        assert s.log_level in ("INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL")

    def test_default_log_level_is_info(self):
        with patch.dict(os.environ, {}, clear=False):
            # Remove QAI_LOG_LEVEL if set
            env = {k: v for k, v in os.environ.items() if k != "QAI_LOG_LEVEL"}
            with patch.dict(os.environ, env, clear=True):
                s = Settings()
                assert s.log_level == "INFO"

    def test_azure_openai_not_ready_by_default(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
            }
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert not s.azure_openai_ready

    def test_openai_not_ready_by_default(self):
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert not s.openai_ready

    def test_active_provider_defaults_to_local(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "OPENAI_API_KEY",
                "LMSTUDIO_BASE_URL",
                "OLLAMA_BASE_URL",
            }
        }
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "local"


class TestEnvVarPropagation:
    """Environment variables should override defaults."""

    def test_openai_key_sets_openai_ready(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            s = Settings()
            assert s.openai_ready

    def test_lmstudio_url_sets_lmstudio_ready(self):
        with patch.dict(os.environ, {"LMSTUDIO_BASE_URL": "http://localhost:1234"}):
            s = Settings()
            assert s.lmstudio_ready

    def test_azure_openai_fully_set(self):
        azure_env = {
            "AZURE_OPENAI_API_KEY": "key",
            "AZURE_OPENAI_ENDPOINT": "https://myresource.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
        }
        with patch.dict(os.environ, azure_env):
            s = Settings()
            assert s.azure_openai_ready

    def test_sql_pool_size_from_env(self):
        with patch.dict(os.environ, {"QAI_SQL_POOL_SIZE": "25"}):
            s = Settings()
            assert s.sql_pool_size == 25

    def test_log_level_from_env(self):
        with patch.dict(os.environ, {"QAI_LOG_LEVEL": "DEBUG"}):
            s = Settings()
            assert s.log_level == "DEBUG"

    def test_invalid_log_level_falls_back_to_info(self):
        with patch.dict(os.environ, {"QAI_LOG_LEVEL": "INVALID"}):
            s = Settings()
            assert s.log_level == "INFO"

    def test_blank_provider_priority_falls_back_to_default_chain(self):
        with patch.dict(os.environ, {"QAI_PROVIDER_PRIORITY": ""}):
            s = Settings()
            assert s.provider_chain() == ["lmstudio", "ollama", "azure", "openai", "groq", "local"]

    def test_whitespace_provider_priority_falls_back_to_default_chain(self):
        with patch.dict(os.environ, {"QAI_PROVIDER_PRIORITY": " ,  ,   "}):
            s = Settings()
            assert s.provider_chain() == ["lmstudio", "ollama", "azure", "openai", "groq", "local"]


class TestActiveProvider:
    """active_provider() should follow the priority chain."""

    def test_azure_preferred_over_openai(self):
        env = {
            "AZURE_OPENAI_API_KEY": "key",
            "AZURE_OPENAI_ENDPOINT": "https://res.openai.azure.com/",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
            "AZURE_OPENAI_API_VERSION": "2024-02-01",
            "OPENAI_API_KEY": "sk-also-set",
            "LMSTUDIO_BASE_URL": "",
            "OLLAMA_BASE_URL": "",
        }
        with patch.dict(os.environ, env, clear=False):
            s = Settings()
            assert s.active_provider() == "azure"

    def test_openai_when_azure_missing(self):
        env = {k: v for k, v in os.environ.items() if "AZURE_OPENAI" not in k}
        env["OPENAI_API_KEY"] = "sk-test"
        env["LMSTUDIO_BASE_URL"] = ""
        env["OLLAMA_BASE_URL"] = ""
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "openai"

    def test_lmstudio_fallback(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "OPENAI_API_KEY",
                "LMSTUDIO_BASE_URL",
                "OLLAMA_BASE_URL",
            }
        }
        env["LMSTUDIO_BASE_URL"] = "http://localhost:1234"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "lmstudio"

    def test_ollama_fallback_when_lmstudio_missing(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "OPENAI_API_KEY",
                "LMSTUDIO_BASE_URL",
                "OLLAMA_BASE_URL",
            }
        }
        env["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "ollama"

    def test_lmstudio_whitespace_url_is_not_ready(self):
        env = {
            k: v
            for k, v in os.environ.items()
            if k
            not in {
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_DEPLOYMENT",
                "OPENAI_API_KEY",
                "LMSTUDIO_BASE_URL",
                "OLLAMA_BASE_URL",
            }
        }
        env["LMSTUDIO_BASE_URL"] = "   "
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.lmstudio_ready is False
            assert s.active_provider() == "local"


class TestSummary:
    """summary() must not expose secret values."""

    def test_summary_contains_no_secrets(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "sk-top-secret",
                "AZURE_OPENAI_API_KEY": "azure-secret-key",
            },
        ):
            s = Settings()
            doc = s.summary()
            dumped = str(doc)
            assert "sk-top-secret" not in dumped
            assert "azure-secret-key" not in dumped

    def test_summary_has_expected_keys(self):
        s = Settings()
        doc = s.summary()
        assert "active_provider" in doc
        assert "azure_openai_ready" in doc
        assert "openai_ready" in doc
        assert "db_enabled" in doc


class TestGetSettings:
    """get_settings() returns a singleton; reset_settings() clears it."""

    def test_get_settings_returns_same_object(self):
        a = get_settings()
        b = get_settings()
        assert a is b

    def test_reset_settings_clears_cache(self):
        a = get_settings()
        reset_settings()
        b = get_settings()
        # After reset, a new instance is returned
        assert a is not b
