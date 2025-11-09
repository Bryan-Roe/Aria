import os
import sys
from typing import Any, Dict, Optional

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
                exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                trace.set_tracer_provider(provider)
                service_name = os.environ.get("OTEL_SERVICE_NAME", "lora-training")
                self.tracer = trace.get_tracer(service_name)
            except Exception as e:
                print(f"[otel] Failed to init OpenTelemetry tracer: {e}", file=sys.stderr)

    def on_train_begin(self, args, state, control, **kwargs):  # type: ignore[no-untyped-def]
        if self.tracer:
            self.training_span = self.tracer.start_span("training_run")  # type: ignore[union-attr]
            self.training_span.set_attribute("num_train_epochs", int(getattr(args, "num_train_epochs", 0)))
            self.training_span.set_attribute("per_device_train_batch_size", int(getattr(args, "per_device_train_batch_size", 0)))
            self.training_span.set_attribute("learning_rate", float(getattr(args, "learning_rate", 0.0)))

    def on_train_end(self, args, state, control, **kwargs):  # type: ignore[no-untyped-def]
        if self.training_span:
            self.training_span.set_attribute("final_global_step", int(getattr(state, "global_step", 0)))
            self.training_span.end()
            self.training_span = None

    def on_step_end(self, args, state, control, **kwargs):  # type: ignore[no-untyped-def]
        if self.tracer and self.training_span:
            # Emit periodic step events (every 100 steps to avoid overhead)
            step = int(getattr(state, "global_step", 0))
            if step % 100 == 0:
                with self.tracer.start_as_current_span("training_step") as span:  # type: ignore[union-attr]
                    span.set_attribute("global_step", step)
                    span.set_attribute("epoch", float(getattr(state, "epoch", 0.0)))

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):  # type: ignore[no-untyped-def]
        if self.tracer:
            with self.tracer.start_as_current_span("evaluation") as span:  # type: ignore[union-attr]
                span.set_attribute("global_step", int(getattr(state, "global_step", 0)))
                if metrics:
                    for k, v in metrics.items():
                        try:
                            if isinstance(v, (int, float)):
                                span.set_attribute(f"metric.{k}", float(v))
                        except Exception:
                            pass

    def on_log(self, args, state, control, logs=None, **kwargs):  # type: ignore[no-untyped-def]
        # Log training loss if available
        if self.tracer and logs and "loss" in logs:
            with self.tracer.start_as_current_span("log_event") as span:  # type: ignore[union-attr]
                span.set_attribute("global_step", int(getattr(state, "global_step", 0)))
                span.set_attribute("metric.loss", float(logs["loss"]))
