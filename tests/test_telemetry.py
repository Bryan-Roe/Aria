"""Tests for shared/telemetry.py — Azure Monitor OpenTelemetry initialization."""

from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch


def _reload_telemetry():
    """Re-import telemetry with a fresh module state (resets _INITIALIZED)."""
    if "shared.telemetry" in sys.modules:
        del sys.modules["shared.telemetry"]
    import shared.telemetry as tel

    return tel


class TestInitTelemetry:
    def test_no_connection_string_returns_false(self):
        tel = _reload_telemetry()
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
            result = tel.init_telemetry()
        assert result is False

    def test_no_connection_string_stays_disabled(self):
        tel = _reload_telemetry()
        os.environ.pop("APPLICATIONINSIGHTS_CONNECTION_STRING", None)
        tel.init_telemetry()
        assert tel.is_enabled() is False

    def test_idempotent_already_initialized(self):
        tel = _reload_telemetry()
        # Force _INITIALIZED to True without actually calling configure
        tel._INITIALIZED = True
        result = tel.init_telemetry()
        assert result is True  # short-circuit returns True

    def test_azure_monitor_configured_when_conn_string_set(self):
        tel = _reload_telemetry()
        mock_configure = MagicMock()
        fake_azure = MagicMock()
        fake_azure.configure_azure_monitor = mock_configure

        with patch.dict(
            os.environ,
            {"APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=fake-key"},
        ):
            with patch.dict(sys.modules, {"azure.monitor.opentelemetry": fake_azure}):
                result = tel.init_telemetry()

        assert result is True
        mock_configure.assert_called_once_with(
            connection_string="InstrumentationKey=fake-key"
        )

    def test_is_enabled_reflects_state(self):
        tel = _reload_telemetry()
        assert tel.is_enabled() is False
        tel._INITIALIZED = True
        assert tel.is_enabled() is True


class TestIsEnabled:
    def test_false_by_default(self):
        tel = _reload_telemetry()
        assert tel.is_enabled() is False

    def test_true_after_successful_init(self):
        tel = _reload_telemetry()
        mock_configure = MagicMock()
        fake_azure = MagicMock()
        fake_azure.configure_azure_monitor = mock_configure

        with patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": "fake"}):
            with patch.dict(sys.modules, {"azure.monitor.opentelemetry": fake_azure}):
                tel.init_telemetry()

        assert tel.is_enabled() is True
