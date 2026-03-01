# Telemetry & Cosmos DB Enablement Guide

## Overview

This guide documents how to enable Application Insights telemetry and Cosmos DB persistence in the QAI workspace. Both features are **optional** and behind feature flags, allowing you to run the system entirely offline or enable production-grade observability and persistence as needed.

---

## Telemetry (Azure Monitor Application Insights)

### What It Provides

- **Distributed tracing**: Track request flows through `/api/chat` and other endpoints
- **Custom spans**: Measure provider latency, memory injection, Cosmos operations
- **Automatic instrumentation**: HTTP requests, dependencies, exceptions
- **Integration**: Works with Azure Monitor Logs and Application Insights portal

### Enabling Telemetry

**1. Set the connection string environment variable:**

```powershell
# Local development (local.settings.json)
{
  "Values": {
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=...;IngestionEndpoint=https://..."
  }
}

# Or as environment variable
$env:APPLICATIONINSIGHTS_CONNECTION_STRING = "InstrumentationKey=...;IngestionEndpoint=..."
```

**2. Verify telemetry initialization:**

```powershell
# Check status endpoint
curl http://localhost:7071/api/ai/status | jq '.telemetry'
# Expected output: {"enabled": true}
```

**3. What gets traced:**

- `/api/chat` endpoint: Full request lifecycle with custom attributes:
  - `provider` (azure/openai/local/lora)
  - `model` (deployment name or adapter path)
  - `duration_ms` (completion time)
  - `memory_injected` (number of memory-retrieved messages)
  - `cosmos_persisted` (whether Cosmos write succeeded)
- **Exception tracking**: All unhandled errors with stack traces
- **Dependency calls**: OpenAI SDK, Cosmos DB, Azure Quantum (if enabled)

### Telemetry Code Structure

**Initialization** (`shared/telemetry.py`):
```python
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

def init_telemetry():
    conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if conn_str:
        configure_azure_monitor(connection_string=conn_str)
        return True
    return False

def is_enabled() -> bool:
    return bool(os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"))
```

**Usage in endpoints** (`function_app.py`):
```python
from opentelemetry import trace
_tracer = trace.get_tracer("qai.functions")

with _tracer.start_as_current_span("chat_request") as span:
    # ... chat logic ...
    span.set_attribute("provider", info.name)
    span.set_attribute("model", info.model)
    span.set_attribute("duration_ms", duration_ms)
```

### Verifying Telemetry in Azure Portal

1. Navigate to your Application Insights resource in Azure Portal
2. Go to **Transaction Search** or **Logs (KQL editor)**
3. Query example traces:
```kusto
traces
| where cloud_RoleName == "qai.functions"
| where operation_Name == "chat_request"
| project timestamp, message, customDimensions
| take 100
```

4. Analyze custom attributes:
```kusto
dependencies
| where cloud_RoleName == "qai.functions"
| extend provider = tostring(customDimensions["provider"]),
         model = tostring(customDimensions["model"]),
         duration = toint(customDimensions["duration_ms"])
| summarize avg(duration), count() by provider, model
```

### Disabling Telemetry

Simply remove or leave blank the `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable. The system will log a warning at startup and run without instrumentation.

---

## Cosmos DB Persistence

### What It Provides

- **Chat message persistence**: Store user/assistant messages for retrieval and audit
- **Session management**: Track conversations by user ID or session ID
- **Flexible strategies**: Per-message writes or session-level batches
- **Azure integration**: Native support for serverless/provisioned Cosmos DB

### Enabling Cosmos DB

**1. Provision Cosmos DB (if not already done):**

```powershell
# Using Azure CLI
az cosmosdb create --name qai-cosmos --resource-group rg-qai --default-consistency-level Session

# Create database and container
az cosmosdb sql database create --account-name qai-cosmos --resource-group rg-qai --name qai
az cosmosdb sql container create --account-name qai-cosmos --resource-group rg-qai --database-name qai --name chat_sessions --partition-key-path /userId
```

**2. Set environment variables:**

```powershell
# Local development (local.settings.json)
{
  "Values": {
    "QAI_ENABLE_COSMOS": "true",
    "COSMOS_ENDPOINT": "https://qai-cosmos.documents.azure.com:443/",
    "COSMOS_KEY": "your_primary_key_here",
    "COSMOS_DATABASE": "qai",
    "COSMOS_CONTAINER": "chat_sessions",
    "QAI_COSMOS_PERSIST_STRATEGY": "messages"  # or "sessions"
  }
}

# Or as environment variables
$env:QAI_ENABLE_COSMOS = "true"
$env:COSMOS_ENDPOINT = "https://qai-cosmos.documents.azure.com:443/"
$env:COSMOS_KEY = "your_primary_key_here"
$env:COSMOS_DATABASE = "qai"
$env:COSMOS_CONTAINER = "chat_sessions"
$env:QAI_COSMOS_PERSIST_STRATEGY = "messages"
```

**3. Verify Cosmos integration:**

```powershell
# Check status endpoint
curl http://localhost:7071/api/ai/status | jq '.cosmos'
# Expected output: {"enabled": true, "settings_present": true, "initialized": true, "container_id": "chat_sessions", ...}
```

**4. Test persistence:**

```powershell
# Send a chat message
curl -X POST http://localhost:7071/api/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Hello"}],"session_id":"test-session-1"}'

# Check response for cosmos_persisted flag
# "cosmos_persisted": true
```

### Persistence Strategies

**1. Per-Message Strategy** (`QAI_COSMOS_PERSIST_STRATEGY=messages`):
- **Behavior**: Each user and assistant message is written as a separate Cosmos document
- **Document schema**:
```json
{
  "id": "msg_1234567890_user",
  "userId": "user-123",
  "sessionId": "test-session-1",
  "role": "user",
  "content": "Hello, how are you?",
  "timestamp": 1700000000.123,
  "provider": "azure",
  "model": "gpt-4o-mini"
}
```
- **Pros**: Fine-grained audit trail, easy to query individual messages
- **Cons**: Higher write throughput (2 writes per chat turn)

**2. Session Strategy** (`QAI_COSMOS_PERSIST_STRATEGY=sessions`):
- **Behavior**: Entire conversation (all messages) is written as one document per session
- **Document schema**:
```json
{
