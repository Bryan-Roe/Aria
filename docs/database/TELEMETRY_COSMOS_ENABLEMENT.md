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
  "id": "session_test-session-1",
  "userId": "user-123",
  "sessionId": "test-session-1",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ],
  "timestamp": 1700000000.123,
  "provider": "azure",
  "model": "gpt-4o-mini"
}
```
- **Pros**: Fewer writes (1 write per chat turn), better for cost optimization
- **Cons**: May hit document size limits on long conversations (~2 MB per document max)

### Cosmos Code Structure

**Client initialization** (`shared/cosmos_client.py`):
```python
from azure.cosmos import CosmosClient

class QAICosmosClient:
    def __init__(self):
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        self.client = CosmosClient(endpoint, credential=key)
        self.database = self.client.get_database_client(os.getenv("COSMOS_DATABASE", "qai"))
        self.container = self.database.get_container_client(os.getenv("COSMOS_CONTAINER", "chat_sessions"))

    def record_chat_message(self, user_id: str, message: dict, provider: str, model: str):
        doc = {
            "id": f"msg_{int(time.time() * 1000)}_{message['role']}",
            "userId": user_id,
            "sessionId": message.get("session_id", "default"),
            **message,
            "provider": provider,
            "model": model,
        }
        self.container.create_item(doc)

    def health(self) -> dict:
        # Returns {"enabled": true, "settings_present": true, ...}
        ...
```

**Usage in endpoint** (`function_app.py`):
```python
if cosmos_client and os.getenv("QAI_ENABLE_COSMOS", "false").lower() == "true":
    strategy = os.getenv("QAI_COSMOS_PERSIST_STRATEGY", "messages")
    if strategy == "messages":
        cosmos_client.record_chat_message(user_id, {"role": "user", "content": "..."}, provider, model)
        cosmos_client.record_chat_message(user_id, {"role": "assistant", "content": "..."}, provider, model)
    else:
        cosmos_client.record_chat_session(user_id, messages, provider, model)
```

### Disabling Cosmos DB

Set `QAI_ENABLE_COSMOS=false` or remove the environment variable. The system will operate without persistence (all chat state is ephemeral).

---

## Combined Configuration Example

**Full local.settings.json with both telemetry and Cosmos enabled:**

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    
    "APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=abc-123;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/",
    
    "QAI_ENABLE_COSMOS": "true",
    "COSMOS_ENDPOINT": "https://qai-cosmos.documents.azure.com:443/",
    "COSMOS_KEY": "your_primary_key_here",
    "COSMOS_DATABASE": "qai",
    "COSMOS_CONTAINER": "chat_sessions",
    "QAI_COSMOS_PERSIST_STRATEGY": "messages",
    
    "AZURE_OPENAI_API_KEY": "your_azure_openai_key",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o-mini",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview"
  }
}
```

---

## Status Endpoint Reference

### New Fields (as of latest version)

**Telemetry section:**
```json
"telemetry": {
  "enabled": true  // true if APPLICATIONINSIGHTS_CONNECTION_STRING is set
}
```

**Quantum section:**
```json
"quantum": {
  "enabled": true,  // true if qiskit imports successfully
  "qiskit": "0.46.0",  // or error message
  "pennylane": "0.43.0",
  "azure_quantum": {
    "workspace_connected": false,  // true if QAI_STATUS_CONNECT_AZURE_QUANTUM=true and connected
    "backends": [],  // list of backend names (e.g., ["rigetti.sim.qvm", "ionq.simulator"])
    "attempted": false,  // true if probe was attempted
    "error": null  // or error string
  },
  "conflict": false  // true if mixed Qiskit >=1.x + legacy aer detected
}
```

**Cosmos section:**
```json
"cosmos": {
  "enabled": false,  // true if QAI_ENABLE_COSMOS=true
  "settings_present": false,  // true if COSMOS_ENDPOINT and COSMOS_KEY set
  "initialized": false,  // true if client successfully connected
  "container_id": null,  // container name if connected
  "database": "qai",
  "container": "chat_sessions",
  "error": null  // or error string
}
```

---

## Troubleshooting

### Telemetry Not Appearing in Portal

1. **Check connection string format:**
   ```powershell
   $env:APPLICATIONINSIGHTS_CONNECTION_STRING
   # Should be: InstrumentationKey=...;IngestionEndpoint=https://...
   ```

2. **Verify telemetry.enabled in status:**
   ```powershell
   curl http://localhost:7071/api/ai/status | jq '.telemetry.enabled'
   # Should return: true
   ```

3. **Check startup logs:**
   ```powershell
   # Look for: [startup] Telemetry initialized successfully
   # Or: [startup] Telemetry init skipped: <error>
   ```

4. **Allow 2-5 minutes for ingestion latency** in Azure Portal

### Cosmos Writes Failing

1. **Verify credentials:**
   ```powershell
   # Test connection using Azure Cosmos DB Data Explorer in Portal
   ```

2. **Check firewall rules:**
   - Ensure your IP is allowlisted in Cosmos DB → Settings → Firewall and virtual networks
   - Or enable "Allow access from Azure Portal" for testing

3. **Review status error field:**
   ```powershell
   curl http://localhost:7071/api/ai/status | jq '.cosmos.error'
   # Common errors:
   # - "Unauthorized" → wrong key
   # - "Forbidden" → firewall blocking
   # - "NotFound" → database/container doesn't exist
   ```

4. **Check container partition key:**
   - Must be `/userId` (or update client code to match your schema)

### Conflict Detection Showing True

**Current status shows:**
```json
"quantum": {
  "conflict": true,
  "qiskit": "1.4.5"
}
```

**This indicates:** Mixed Qiskit ≥1.x with legacy aer/machine-learning packages detected in the root Functions environment. This is **expected** if root venv has Qiskit 1.x while `quantum-ai/venv` has the downgraded 0.46.0 stack.

**Resolution options:**

1. **Ignore** (recommended if quantum endpoints aren't used in production):
   - Root venv conflict doesn't affect isolated `quantum-ai/` training
   - Quantum MCP server uses dedicated venv

2. **Upgrade root venv to Qiskit 1.x** (use upgrade script):
   ```powershell
   cd quantum-ai
   python .\scripts\upgrade_qiskit_to_1x.py --dry-run  # preview changes
   python .\scripts\upgrade_qiskit_to_1x.py --install   # apply upgrade
   ```

3. **Disable quantum status probing** (prevent import attempts):
   - Set `QAI_STATUS_CONNECT_AZURE_QUANTUM=false` or leave unset (default)

---

## Cost Optimization

### Telemetry

- **Free tier**: 5 GB ingestion/month (usually sufficient for dev/test)
- **Sampling**: Configure in `shared/telemetry.py`:
  ```python
  from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
  sampler = TraceIdRatioBased(0.1)  # 10% sampling
  ```
- **Filtering**: Exclude low-value operations (e.g., health checks)

### Cosmos DB

- **Serverless tier**: Pay per request (~$0.25/million reads, ~$1.25/million writes)
  - Best for dev/test or low-traffic apps
- **Provisioned throughput**: Fixed monthly cost (400 RU/s minimum ~$24/month)
  - Best for predictable workloads
- **Strategy impact**:
  - Per-message: ~2 writes per chat turn (user + assistant)
  - Session-level: ~1 write per chat turn

**Example costs (per-message strategy, 1000 chat turns/day):**
- Serverless: 2000 writes/day × 30 days = 60K writes/month → **~$0.08/month**
- Provisioned 400 RU/s: **$24/month** (fixed)

---

## Best Practices

1. **Always test with status endpoint first:**
   ```powershell
   curl http://localhost:7071/api/ai/status | jq '.telemetry, .cosmos'
   ```

2. **Use feature flags for gradual rollout:**
   - Enable telemetry first (zero cost to test)
   - Add Cosmos after confirming telemetry works
   - Enable Azure Quantum probing only if needed (adds latency)

3. **Monitor ingestion limits:**
   - Application Insights free tier: 5 GB/month
   - Cosmos DB serverless: 1 million RU/s per container (very high)

4. **Secure credentials:**
   - Never commit keys to source control
   - Use Azure Key Vault references in production:
     ```json
     "COSMOS_KEY": "@Microsoft.KeyVault(SecretUri=https://...)"
     ```

5. **Document environment variables in README:**
   - Keep this guide in sync with `.env.example` or `local.settings.json.example`

---

## See Also

- **Upgrade Script**: `quantum-ai/scripts/upgrade_qiskit_to_1x.py` (Qiskit 1.x migration)
- **Validation Script**: `quantum-ai/scripts/validate_qiskit_env.py` (conflict detection)
- **Unit Tests**: `tests/test_validate_qiskit_env.py` (conflict detection logic)
- **Azure Documentation**:
  - [Application Insights for Azure Functions](https://learn.microsoft.com/azure/azure-functions/functions-monitoring)
  - [Cosmos DB Python SDK](https://learn.microsoft.com/azure/cosmos-db/nosql/sdk-python)
