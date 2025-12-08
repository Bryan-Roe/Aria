import importlib
from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path


def test_otel_callback_import_and_methods(monkeypatch):
    """OpenTelemetry Trainer callback must import and expose expected methods.

    Behavior should be safe even when opentelemetry is unavailable.
    """
    # Load the file directly to avoid package name issues
    script_path = Path(__file__).resolve(
    ).parents[1] / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "otel_callback.py"
    spec = spec_from_file_location("otel_callback_test_mod", str(script_path))
    assert spec is not None
    mod = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)  # type: ignore

    # Ensure the symbol exists
    assert hasattr(mod, "OpenTelemetryTrainerCallback")

    cb_cls = mod.OpenTelemetryTrainerCallback
    # Instantiation should not raise
    cb = cb_cls()

    # Methods should be callable (no-op if tracing is disabled)
    for name in ("on_train_begin", "on_prediction_step", "on_train_end"):
        assert hasattr(cb, name)
        meth = getattr(cb, name)
        # Call with empty args to ensure no exceptions
        meth(None, None, None)
