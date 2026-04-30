"""Telemetry initialization for QAI Functions.

Sets up Azure Monitor OpenTelemetry if APPLICATIONINSIGHTS_CONNECTION_STRING is present.
Falls back gracefully if dependencies are missing.

Usage:
    from shared.telemetry import init_telemetry
    init_telemetry()
"""

from __future__ import annotations

import logging
import os

_INITIALIZED = False


def init_telemetry() -> bool:
    global _INITIALIZED
    if _INITIALIZED:
        return True

    conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not conn:
        logging.info(
            "[telemetry] No Application Insights connection string; telemetry disabled."
        )
        return False

    try:
        # Azure Monitor OpenTelemetry configuration.
        from azure.monitor.opentelemetry import \
            configure_azure_monitor  # type: ignore

        configure_azure_monitor(connection_string=conn)
        _INITIALIZED = True
        logging.info("[telemetry] Azure Monitor OpenTelemetry configured.")
        return True
    except Exception as e:  # pragma: no cover - defensive
        logging.warning(
            f"[telemetry] Failed to initialize Azure Monitor instrumentation: {e}"
        )
        return False


def is_enabled() -> bool:
    return _INITIALIZED


__all__ = ["init_telemetry", "is_enabled"]
