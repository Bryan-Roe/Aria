"""Trainer callback that emits lightweight OpenTelemetry spans for HF Trainer.

This module optionally integrates OpenTelemetry into Hugging Face Trainer
callbacks. It is intentionally tolerant of missing OpenTelemetry dependencies
so training can still run without telemetry (dry-run / CI environments).

To use, simply add the callback to your Trainer:

    from otel_callback import OpenTelemetryTrainerCallback
    trainer.add_callback(OpenTelemetryTrainerCallback())

The callback will create a training-level span and brief spans for prediction
steps when possible.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
import sys
import os

import logging
from typing import Any

# Transformers' TrainerCallback is optional at import time.
try:  # pragma: no cover - optional dependency in some environments
    from transformers import TrainerCallback  # type: ignore
except Exception:  # pragma: no cover - fallback type
    class TrainerCallback:  # type: ignore
        pass


try:
    from opentelemetry import trace  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    trace = None  # type: ignore


class OpenTelemetryTrainerCallback(TrainerCallback):
    """A robust, best-effort TrainerCallback that emits spans.

    This callback intentionally swallows exceptions so it never interferes
    with training if OpenTelemetry or the Trainer API is not available.
    """

    def __init__(self, tracer_name: str = "qai.hf.trainer") -> None:
        self._tracer_name = tracer_name
        self._tracer = None
        self._train_span = None
        self._train_scope = None
        if trace is not None:
            try:
                self._tracer = trace.get_tracer(self._tracer_name)
            except Exception as e:
                logging.debug(f"[otel_callback] Could not get tracer: {e}")

    def on_train_begin(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:  # type: ignore
        try:
            if not self._tracer:
                return
            # Create a persistent span for the whole training session
            self._train_span = self._tracer.start_span("hf.train_session")
            # Make it the current span for subsequent events
            self._train_scope = trace.use_span(
                self._train_span, end_on_exit=False)
            self._train_scope.__enter__()
        except Exception:
            # Never allow tracing errors to disrupt training
            pass

    def on_train_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:  # type: ignore
        try:
            if not self._tracer or not self._train_span:
                return
            # Close the session span
            try:
                if self._train_scope is not None:
                    self._train_scope.__exit__(None, None, None)
            finally:
                try:
                    self._train_span.end()
                except Exception:
                    pass
        except Exception:
            pass

    def on_prediction_step(self, args: Any, state: Any, control: Any, **kwargs: Any) -> None:  # type: ignore
        # Called for prediction-related steps (if supported). We create a
        # short-lived span around prediction work so that prediction latencies
        # are visible in the tracing backend.
        try:
            if not self._tracer:
                return
            with self._tracer.start_as_current_span("hf.prediction_step"):
                # No-op inside span — HF will continue its normal workflow
                pass
        except Exception:
            pass


__all__ = ["OpenTelemetryTrainerCallback"]

# Optional OpenTelemetry imports
try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
except Exception:
    trace = None  # type: ignore
    TracerProvider = OTLPSpanExporter = BatchSpanProcessor = None  # type: ignore


class OpenTelemetryTrainerCallback:
    """
    Hugging Face Trainer callback that emits OpenTelemetry spans for training lifecycle events.

    Env vars:
      - OTEL_EXPORTER_OTLP_ENDPOINT (e.g., http://localhost:4317)
      - OTEL_SERVICE_NAME (optional, default: lora-training)
    """

    def __init__(self):
        self.tracer: Optional[Any] = None
        self.training_span: Optional[Any] = None

        otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otel_endpoint and trace and TracerProvider and OTLPSpanExporter and BatchSpanProcessor:
            try:
                provider = TracerProvider()
                exporter = OTLPSpanExporter(
                    endpoint=otel_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                trace.set_tracer_provider(provider)
                service_name = os.environ.get(
                    "OTEL_SERVICE_NAME", "lora-training")
                self.tracer = trace.get_tracer(service_name)
            except Exception as e:
                print(
                    f"[otel] Failed to init OpenTelemetry tracer: {e}", file=sys.stderr)

    # type: ignore[no-untyped-def]
    def on_train_begin(self, args, state, control, **kwargs):
        if self.tracer:
            self.training_span = self.tracer.start_span(
                "training_run")  # type: ignore[union-attr]
            self.training_span.set_attribute(
                "num_train_epochs", int(getattr(args, "num_train_epochs", 0)))
            self.training_span.set_attribute("per_device_train_batch_size", int(
                getattr(args, "per_device_train_batch_size", 0)))
            self.training_span.set_attribute(
                "learning_rate", float(getattr(args, "learning_rate", 0.0)))

    # type: ignore[no-untyped-def]
    def on_train_end(self, args, state, control, **kwargs):
        if self.training_span:
            self.training_span.set_attribute(
                "final_global_step", int(getattr(state, "global_step", 0)))
            self.training_span.end()
            self.training_span = None

    # type: ignore[no-untyped-def]
    def on_step_end(self, args, state, control, **kwargs):
        if self.tracer and self.training_span:
            # Emit periodic step events (every 100 steps to avoid overhead)
            step = int(getattr(state, "global_step", 0))
            if step % 100 == 0:
                # type: ignore[union-attr]
                with self.tracer.start_as_current_span("training_step") as span:
                    span.set_attribute("global_step", step)
                    span.set_attribute("epoch", float(
                        getattr(state, "epoch", 0.0)))

    # type: ignore[no-untyped-def]
    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if self.tracer:
            # type: ignore[union-attr]
            with self.tracer.start_as_current_span("evaluation") as span:
                span.set_attribute("global_step", int(
                    getattr(state, "global_step", 0)))
                if metrics:
                    for k, v in metrics.items():
                        try:
                            if isinstance(v, (int, float)):
                                span.set_attribute(f"metric.{k}", float(v))
                        except Exception:
                            pass

    # type: ignore[no-untyped-def]
    def on_log(self, args, state, control, logs=None, **kwargs):
        # Log training loss if available
        if self.tracer and logs and "loss" in logs:
            # type: ignore[union-attr]
            with self.tracer.start_as_current_span("log_event") as span:
                span.set_attribute("global_step", int(
                    getattr(state, "global_step", 0)))
                span.set_attribute("metric.loss", float(logs["loss"]))

    # type: ignore[no-untyped-def]
    def on_prediction_step(self, args, state, control, **kwargs):
        """Emit a brief span for prediction/prediction-step events.

        Hugging Face Trainer may not call this method in all versions; presence
        is checked by callers before adding the callback to the trainer.
        """
        if self.tracer:
            try:
                with self.tracer.start_as_current_span("prediction_step") as span:
                    span.set_attribute("global_step", int(
                        getattr(state, "global_step", 0)))
            except Exception:
                pass
