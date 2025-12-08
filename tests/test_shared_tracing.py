import importlib
import os
import sys


def test_init_tracing_safe_no_otel(monkeypatch):
    """init_tracing must not raise when OpenTelemetry is missing.

    The runtime environment for CI may or may not have OTEL packages; this
    test ensures the helper is tolerant and always returns a boolean without
    blowing up.
    """
    # Ensure we don't accidentally initialize Azure telemetry during test
    monkeypatch.delenv("APPLICATIONINSIGHTS_CONNECTION_STRING", raising=False)

    # Reload the module to ensure a clean start (previous import may have
    # initialized tracing depending on the dev environment)
    import shared.tracing as st
    importlib.reload(st)

    # Call init_tracing - should return a boolean and not raise
    result = st.init_tracing(service_name="test_shared_tracing")
    assert isinstance(result, bool)


def test_start_span_context_manager(monkeypatch):
    import shared.tracing as st
    importlib.reload(st)

    # Should work whether tracing is enabled or not
    with st.start_span("smoke_test"):
        # inside the span context. No exception means success.
        pass
