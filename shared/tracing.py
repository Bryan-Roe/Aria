"""Central tracing helper for QAI — optional OpenTelemetry initialization.

This module provides a safe, low-friction entrypoint to enable tracing across
the repository. It intentionally keeps a very small runtime footprint and
falls back to a no-op when OpenTelemetry packages are not available in the
runtime environment (useful for CI and developer machines where tracing may
not be configured).

Usage:
    from shared.tracing import init_tracing, get_tracer, is_tracing_enabled
    init_tracing(service_name="my-service")

Design goals:
- Safe no-op when dependencies are missing
- Prefer Application Insights via shared.telemetry when APPLICATIONINSIGHTS_CONNECTION_STRING
  is present (consistent with existing codebase pattern)
- Auto-instrument common libraries when possible (requests, logging)
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager, nullcontext
from typing import Optional

_INITIALIZED = False
_TRACER = None


def init_tracing(service_name: Optional[str] = None, enable_auto_instrumentation: bool = True) -> bool:
    """Initialize tracing for the current process.

    The function is idempotent and safe to call multiple times. It will try
    to configure Application Insights (via shared.telemetry) when
    APPLICATIONINSIGHTS_CONNECTION_STRING is present. Otherwise it attempts a
    lightweight OpenTelemetry SDK setup and best-effort auto-instrumentation.

    Returns True when tracing has been successfully enabled (or Azure
    Application Insights was configured), False if tracing is unavailable or
    dependencies are missing.
    """
    global _INITIALIZED, _TRACER
    if _INITIALIZED:
        return True

    svc = service_name or os.environ.get(
        "OTEL_SERVICE_NAME") or os.environ.get("OTEL_SERVICE") or "qai"

    # Prefer Azure Monitor OpenTelemetry if Application Insights string present
    if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        try:
            # Keep import local so missing package doesn't break the app
            from shared.telemetry import init_telemetry  # type: ignore

            ok = init_telemetry()
            if ok:
                try:
                    from opentelemetry import trace  # type: ignore

                    _TRACER = trace.get_tracer(svc)
                except Exception:
                    # If opentelemetry lib isn't present we still consider
                    # tracing enabled because Azure SDK configured.
                    pass
                _INITIALIZED = True
                logging.info(
                    "[tracing] Azure Application Insights configured via shared.telemetry")
                return True
        except Exception as e:  # pragma: no cover - defensive
            logging.warning(
                f"[tracing] Failed to initialize azure telemetry: {e}")

    # Try to enable OpenTelemetry SDK + OTLP exporter (best-effort)
    try:
        # Import SDK pieces locally to avoid hard dependency at import time
        from opentelemetry import trace  # type: ignore
        from opentelemetry.sdk.resources import Resource  # type: ignore
        from opentelemetry.sdk.trace import TracerProvider  # type: ignore
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore

        exporter = None
        # Try OTLP exporter (gRPC proto exporter recommended)
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT")

        # Avoid attempting to connect to a local OTLP collector in CI/test
        # environments when no explicit endpoint is provided. This prevents
        # noisy connection-refused warnings during automated test runs. To
        # force the default local exporter behavior, set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
        # (or OTEL_EXPORTER_OTLP_ENDPOINT) or set QAI_ALLOW_DEFAULT_OTLP=true.
        if not otlp_endpoint and (os.getenv("CI") or os.getenv("PYTEST_CURRENT_TEST") or os.getenv("GITHUB_ACTIONS")) and not os.getenv("QAI_ALLOW_DEFAULT_OTLP"):
            logging.info(
                "[tracing] Skipping OTLP exporter default in CI/test environment; set OTEL_EXPORTER_OTLP_TRACES_ENDPOINT to enable.")
            exporter = None
        else:
            try:
                # Prefer modern gRPC exporter module
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore

                exporter = OTLPSpanExporter(
                    endpoint=otlp_endpoint) if otlp_endpoint else OTLPSpanExporter()
            except Exception:
                try:
                    # Fallback to HTTP exporter (older package layout)
                    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # type: ignore

                    exporter = OTLPSpanExporter(
                        endpoint=otlp_endpoint) if otlp_endpoint else OTLPSpanExporter()
                except Exception:
                    exporter = None

        # Initialize tracer provider and attach exporter (if found)
        resource = Resource.create({"service.name": svc})
        provider = TracerProvider(resource=resource)
        if exporter is not None:
            try:
                provider.add_span_processor(BatchSpanProcessor(exporter))
            except Exception as e:  # pragma: no cover - defensive
                logging.warning(
                    f"[tracing] Failed to attach OTLP exporter: {e}")

        trace.set_tracer_provider(provider)
        _TRACER = trace.get_tracer(svc)

        # Auto-instrumentation (best effort) — wrap in try/except to avoid hard fails
        if enable_auto_instrumentation:
            try:
                # Requests instrumentation is lightweight and very helpful
                from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore

                RequestsInstrumentor().instrument()
            except Exception:
                logging.debug(
                    "[tracing] RequestsInstrumentor unavailable or failed")

            try:
                from opentelemetry.instrumentation.logging import LoggingInstrumentor  # type: ignore

                LoggingInstrumentor().instrument(set_logging_format=True)
            except Exception:
                logging.debug(
                    "[tracing] LoggingInstrumentor unavailable or failed")

        _INITIALIZED = True
        logging.info(
            f"[tracing] OpenTelemetry tracing initialized (service_name={svc})")
        return True
    except Exception as e:  # pragma: no cover - safe fallback
        logging.debug(
            f"[tracing] OpenTelemetry not available or failed to initialize: {e}")
        _INITIALIZED = False
        _TRACER = None
        return False


def is_tracing_enabled() -> bool:
    return bool(_INITIALIZED)


def get_tracer(name: Optional[str] = None):
    """Return the active tracer or None when tracing isn't enabled.

    Prefer returning a tracer created from the shared tracer provider. If
    tracing isn't initialized this will return None. This helper keeps the
    rest of the codebase compact and tolerant to missing tracing libs.
    """
    global _TRACER
    if _TRACER is not None:
        return _TRACER
    try:
        from opentelemetry import trace  # type: ignore

        return trace.get_tracer(name or "qai")
    except Exception:
        return None


@contextmanager
def start_span(name: str):
    """Context manager that starts a span when tracing is available.

    When tracing is disabled this yields a nullcontext so callers do not
    need to guard their span usage with try/except. Example:

        with start_span("my.op"):
            do_work()

    """
    tracer = get_tracer()
    if not tracer:
        yield nullcontext()
        return
    try:
        with tracer.start_as_current_span(name):
            yield
    except Exception:
        # If the tracer interface changes or fails, we swallow errors to
        # preserve the main application logic.
        yield


__all__ = ["init_tracing", "is_tracing_enabled", "get_tracer", "start_span"]
