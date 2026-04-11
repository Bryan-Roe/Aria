---
applyTo: "**/telemetry.py"
---

# Telemetry — Instruction Guide

## Setup

```python
from shared.telemetry import init_telemetry, is_enabled

# Initialize once at startup
initialized = init_telemetry()
# Returns True if APPLICATIONINSIGHTS_CONNECTION_STRING is set and Azure Monitor loaded
# Returns False if env var missing or azure-monitor-opentelemetry unavailable
```

## Behavior

- **Single-initialization guard**: `init_telemetry()` only configures once (idempotent)
- **Graceful degradation**: If Azure Monitor SDK is not installed, telemetry silently disables
- **Non-blocking**: Telemetry operations do not block the main thread
- **Zero-config fallback**: Application works identically with or without telemetry

## Environment Variable

```
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...;IngestionEndpoint=...
```

## Coding Conventions

- Never make telemetry a hard dependency — always check `is_enabled()` before custom tracing
- Telemetry is optional infrastructure — no feature should require it
- Use Azure Monitor OpenTelemetry (not the legacy Application Insights SDK)
- Initialize in `function_app.py` startup, not per-request
