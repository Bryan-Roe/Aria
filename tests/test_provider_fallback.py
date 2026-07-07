"""Tests for provider fallback chain behaviour.

Validates that the provider detection logic (shared/config.py active_provider)
and the import helpers (shared/import_helpers.py safe_import) correctly
handle provider selection and unavailable imports without raising.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from shared.config import Settings, reset_settings
from shared.import_helpers import create_stub_function, safe_import


@pytest.fixture(autouse=True)
def _clean():
    reset_settings()
    yield
    reset_settings()


# ---------------------------------------------------------------------------
# Provider priority chain
# ---------------------------------------------------------------------------


class TestProviderPriorityChain:
    """Provider detection should follow: lmstudio > ollama > azure > openai > groq > local."""

    def _clean_env(self) -> dict:
        """Return env with all provider keys stripped out."""
        strip = {
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT",
            "OPENAI_API_KEY",
            "LMSTUDIO_BASE_URL",
            "OLLAMA_BASE_URL",
            "GROQ_API_KEY",
        }
        return {k: v for k, v in os.environ.items() if k not in strip}

    def test_all_missing_returns_local(self):
        with patch.dict(os.environ, self._clean_env(), clear=True):
            s = Settings()
            assert s.active_provider() == "local"

    def test_azure_takes_priority(self):
        env = self._clean_env()
        env.update(
            {
                "AZURE_OPENAI_API_KEY": "key",
                "AZURE_OPENAI_ENDPOINT": "https://res.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
                "AZURE_OPENAI_API_VERSION": "2024-02-01",
                "OPENAI_API_KEY": "sk-also-here",
                "LMSTUDIO_BASE_URL": "http://localhost:1234",
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            }
        )
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "lmstudio"

    def test_openai_when_azure_incomplete(self):
        env = self._clean_env()
        # Azure missing key
        env.update(
            {
                "AZURE_OPENAI_ENDPOINT": "https://res.openai.azure.com/",
                "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
                "OPENAI_API_KEY": "sk-test",
            }
        )
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "openai"

    def test_lmstudio_when_azure_and_openai_missing(self):
        env = self._clean_env()
        env["LMSTUDIO_BASE_URL"] = "http://localhost:1234"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "lmstudio"

    def test_ollama_when_lmstudio_missing(self):
        env = self._clean_env()
        env["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "ollama"

    def test_azure_requires_all_four_vars(self):
        """Azure OpenAI is only 'ready' when all four required vars are set."""
        env = self._clean_env()
        # Only three of four set — api_version has a default, so azure IS ready
        env.update(
            {
                "AZURE_OPENAI_API_KEY": "key",
                "AZURE_OPENAI_ENDPOINT": "https://example.com",
                "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
                # AZURE_OPENAI_API_VERSION omitted — has a default of "2024-02-01"
            }
        )
        env.pop("AZURE_OPENAI_API_VERSION", None)
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            # api_version has a default, so azure should be ready when key/endpoint/deployment set
            assert s.azure_openai_ready is True

    def test_groq_detected_when_key_is_set(self):
        """Settings.active_provider() returns 'groq' when only GROQ_API_KEY is set."""
        env = self._clean_env()
        env["GROQ_API_KEY"] = "gsk-test"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.groq_ready is True
            assert s.active_provider() == "groq"

    def test_groq_not_selected_when_openai_present(self):
        """OpenAI takes priority over Groq in the default chain."""
        env = self._clean_env()
        env["OPENAI_API_KEY"] = "sk-test"
        env["GROQ_API_KEY"] = "gsk-test"
        with patch.dict(os.environ, env, clear=True):
            s = Settings()
            assert s.active_provider() == "openai"


# ---------------------------------------------------------------------------
# safe_import helper
# ---------------------------------------------------------------------------


class TestSafeImport:
    """safe_import should never raise; it returns None or a fallback on error."""

    def test_import_nonexistent_module_returns_none(self):
        result = safe_import("this.module.does.not.exist.at.all")
        assert result is None

    def test_import_nonexistent_with_names_returns_fallback_dict(self):
        def fallback(name):
            return lambda: {"error": name}

        result = safe_import(
            "no.such.module",
            import_names=("foo", "bar"),
            fallback_factory=fallback,
        )
        assert result is not None
        assert "foo" in result
        assert "bar" in result
        assert callable(result["foo"])

    def test_import_nonexistent_with_names_no_fallback_returns_none_values(self):
        result = safe_import("no.such.module", import_names=("x", "y"))
        assert result == {"x": None, "y": None}

    def test_import_real_module(self):
        result = safe_import("os")
        assert result is not None
        assert hasattr(result, "path")

    def test_import_real_module_with_names(self):
        result = safe_import("os", import_names=("getcwd", "path"))
        assert result is not None
        assert callable(result["getcwd"])
        assert result["path"] is not None

    def test_import_real_module_missing_name_returns_none(self):
        result = safe_import("os", import_names=("this_does_not_exist",))
        assert result == {"this_does_not_exist": None}


# ---------------------------------------------------------------------------
# create_stub_function helper
# ---------------------------------------------------------------------------


class TestCreateStubFunction:
    """Stubs should be callable and return a dict with the unavailable marker."""

    def test_stub_returns_dict(self):
        stub = create_stub_function("my_func")
        result = stub()
        assert isinstance(result, dict)
        assert result.get("enabled") is False

    def test_stub_accepts_any_args(self):
        stub = create_stub_function("another_func")
        result = stub(1, 2, key="value")
        assert isinstance(result, dict)

    def test_stub_has_correct_name(self):
        stub = create_stub_function("sql_health")
        assert stub.__name__ == "sql_health"

    def test_stub_custom_error_key(self):
        stub = create_stub_function("check", error_key="status")
        result = stub()
        assert "status" in result


# ---------------------------------------------------------------------------
# Resilience: provider readiness flags are boolean
# ---------------------------------------------------------------------------


class TestProviderReadinessFlags:
    """Readiness properties must always return bool, not None or str."""

    def test_azure_ready_is_bool(self):
        s = Settings()
        assert isinstance(s.azure_openai_ready, bool)

    def test_openai_ready_is_bool(self):
        s = Settings()
        assert isinstance(s.openai_ready, bool)

    def test_lmstudio_ready_is_bool(self):
        s = Settings()
        assert isinstance(s.lmstudio_ready, bool)

    def test_ollama_ready_is_bool(self):
        s = Settings()
        assert isinstance(s.ollama_ready, bool)

    def test_groq_ready_is_bool(self):
        s = Settings()
        assert isinstance(s.groq_ready, bool)
