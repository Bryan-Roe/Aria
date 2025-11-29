import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

# Optional observability imports
try:
    from applicationinsights import TelemetryClient  # type: ignore
except Exception:
    TelemetryClient = None  # type: ignore

try:
    from opentelemetry import trace  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
except Exception:
    trace = None  # type: ignore
    TracerProvider = OTLPSpanExporter = BatchSpanProcessor = None  # type: ignore


class MetricsLogger:
    """
    Logs metrics to a local JSONL file and optionally to:
    - Azure Log Analytics workspace via HTTP Data Collector API
    - Application Insights via TelemetryClient
    - OpenTelemetry OTLP endpoint

    Env vars:
      Azure Log Analytics:
        - AZURE_LOG_ANALYTICS_WORKSPACE_ID
        - AZURE_LOG_ANALYTICS_SHARED_KEY
        - AZURE_LOG_TYPE (optional, default: LLMTrainingMetrics)
      
      Application Insights:
        - APPLICATIONINSIGHTS_CONNECTION_STRING
      
      OpenTelemetry:
        - OTEL_EXPORTER_OTLP_ENDPOINT (e.g., http://localhost:4317)
        - OTEL_SERVICE_NAME (optional, default: lora-training)
    """

    def __init__(self, save_dir: Path):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.save_dir / "metrics.jsonl"
        
        # Azure Log Analytics
        self.workspace_id = os.environ.get("AZURE_LOG_ANALYTICS_WORKSPACE_ID")
        self.shared_key = os.environ.get("AZURE_LOG_ANALYTICS_SHARED_KEY")
        self.log_type = os.environ.get("AZURE_LOG_TYPE", "LLMTrainingMetrics")
        
        # Application Insights
        self.appinsights_client: Optional[Any] = None
        appinsights_conn = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if appinsights_conn and TelemetryClient:
            try:
                self.appinsights_client = TelemetryClient(appinsights_conn)
            except Exception as e:
                print(f"[metrics] Failed to init Application Insights: {e}", file=sys.stderr)
        
        # OpenTelemetry
        self.otel_tracer: Optional[Any] = None
        otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        if otel_endpoint and trace and TracerProvider and OTLPSpanExporter and BatchSpanProcessor:
            try:
                provider = TracerProvider()
                exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                trace.set_tracer_provider(provider)
                service_name = os.environ.get("OTEL_SERVICE_NAME", "lora-training")
                self.otel_tracer = trace.get_tracer(service_name)
            except Exception as e:
                print(f"[metrics] Failed to init OpenTelemetry: {e}", file=sys.stderr)

    def log(self, record: Dict[str, Any]) -> None:
        record = dict(record)
        record["timestamp"] = dt.datetime.now(timezone.utc).isoformat() + "Z"
        # Write locally
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        # Optionally send to Azure Log Analytics
        if self.workspace_id and self.shared_key:
            try:
                self._post_to_azure(record)
            except Exception as e:
                print(f"[metrics] Azure post failed: {e}", file=sys.stderr)
        # Optionally send to Application Insights
        if self.appinsights_client:
            try:
                self._track_appinsights(record)
            except Exception as e:
                print(f"[metrics] Application Insights failed: {e}", file=sys.stderr)
        # Optionally emit OpenTelemetry event
        if self.otel_tracer:
            try:
                self._emit_otel_event(record)
            except Exception as e:
                print(f"[metrics] OpenTelemetry event failed: {e}", file=sys.stderr)

    def _track_appinsights(self, record: Dict[str, Any]) -> None:
        # Track as custom event with all fields as properties
        event_name = record.get("phase", "training_metric")
        props = {k: str(v) for k, v in record.items()}
        self.appinsights_client.track_event(event_name, props)
        # If we have numeric metrics, also track them
        if "eval_loss" in record:
            self.appinsights_client.track_metric("eval_loss", float(record["eval_loss"]))
        if "eval_perplexity" in record:
            self.appinsights_client.track_metric("eval_perplexity", float(record["eval_perplexity"]))
        self.appinsights_client.flush()

    def _emit_otel_event(self, record: Dict[str, Any]) -> None:
        # Create a short-lived span for this event
        with self.otel_tracer.start_as_current_span("evaluation_metric") as span:  # type: ignore[union-attr]
            for k, v in record.items():
                span.set_attribute(k, str(v))
            # Add numeric attributes if available
            if "eval_loss" in record:
                span.set_attribute("metric.eval_loss", float(record["eval_loss"]))
            if "eval_perplexity" in record:
                span.set_attribute("metric.eval_perplexity", float(record["eval_perplexity"]))
            if "step" in record:
                span.set_attribute("training.step", int(record["step"]))

    # --- Azure Log Analytics HTTP Data Collector ---
    def _build_signature(self, content_length: int, rfc1123date: str) -> str:
        string_to_hash = (
            f"POST\n{content_length}\napplication/json\nx-ms-date:{rfc1123date}\n/api/logs"
        )
        decoded_key = base64.b64decode(self.shared_key)  # type: ignore[arg-type]
        digest = hmac.new(decoded_key, string_to_hash.encode("utf-8"), hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    def _post_to_azure(self, record: Dict[str, Any]) -> None:
        body = json.dumps([record]).encode("utf-8")
        rfc1123date = dt.datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        signature = self._build_signature(len(body), rfc1123date)
        url = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"
        headers = {
            "Content-Type": "application/json",
            "Log-Type": self.log_type,
            "x-ms-date": rfc1123date,
            "Authorization": f"SharedKey {self.workspace_id}:{signature}",
        }
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            # 200 or 202 expected
            if resp.status not in (200, 202):
                raise RuntimeError(f"Azure ingestion failed with status {resp.status}")
