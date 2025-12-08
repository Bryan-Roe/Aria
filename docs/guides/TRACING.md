## Tracing & Observability (OpenTelemetry)

This workspace includes an optional, developer-friendly tracing setup using
OpenTelemetry. Tracing is intentionally opt-in and safe to leave disabled in
CI or environments that don't have the OpenTelemetry SDK installed.

Quick points:

- A central helper lives at `shared/tracing.py`. It implements `init_tracing()`
  which will:
  - Use Application Insights if `APPLICATIONINSIGHTS_CONNECTION_STRING` is set
    (via existing `shared.telemetry` helper).
  - Otherwise attempt to configure a local OpenTelemetry SDK + OTLP exporter
    (if the SDK package is installed).
  - Enable lightweight auto-instrumentation for `requests` and `logging` if
    available.
  - Fall back to a safe no-op when OpenTelemetry packages are not installed.

- Scripts that run long-lived work (e.g., `scripts/autotrain.py`,
  `scripts/evaluation_autorun.py`, `scripts/train_and_evaluate.py`) call
  `shared.tracing.init_tracing()` on startup. The call never fails when OTEL
  packages are missing.

- Training-specific integration for Hugging Face Trainer is available in
  `AI/microsoft_phi-silica-3.6_v1/scripts/otel_callback.py`. It exposes
  `OpenTelemetryTrainerCallback` that can be added to `trainer.add_callback(...)`.

Enable locally (example):

1. Install tracing packages in your venv:

   pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

2. Start a local OTLP compatible backend (Jaeger, Grafana Tempo, or open-telemetry
   collector). For a quick start you can run Jaeger in Docker:

   docker run -p 4317:4317 -p 16686:16686 --rm --name jaeger otel/opentelemetry-collector:latest

3. Point the exporter to the endpoint and enable service name (example):

   export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
   export OTEL_SERVICE_NAME="qai-local"

4. Run your script (autotrain / train_lora / evaluation) and inspect traces
   in the backend UI (e.g. Jaeger UI at http://localhost:16686).

If you prefer Application Insights / Azure Monitor, set
`APPLICATIONINSIGHTS_CONNECTION_STRING` and `shared.telemetry.init_telemetry()`
will be used automatically by `shared.tracing.init_tracing()`.
