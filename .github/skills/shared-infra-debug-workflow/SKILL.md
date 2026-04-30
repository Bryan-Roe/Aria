---
name: shared-infra-debug-workflow
description: Debug shared infrastructure issues in shared/**/*.py — SQL connection pool saturation, Cosmos DB feature flag, telemetry non-blocking failures, DB logging stored procedure errors, and provider detection in shared/chat_providers.py. Use when /api/ai/status shows unhealthy, SQL pool saturates, Cosmos writes fail, or logging is silently dropped.
argument-hint: "Describe the symptom: SQL pool full, Cosmos errors, telemetry not sending, DB logging skipped, or provider detection wrong."
---

# Shared Infrastructure Debug Workflow

## What This Skill Produces
Root-cause diagnosis and targeted fixes for shared Python infrastructure: SQL connection pool, Cosmos DB client, telemetry pipeline, fault-tolerant DB logging, and provider detection configuration.

## When to Use

Trigger phrases:
- "SQL pool saturated"
- "Cosmos writes failing"
- "telemetry not working"
- "DB logging skipped"
- "stored procedure error"
- "/api/ai/status showing unhealthy"
- "QAI_DB_CONN not working"
- "Cosmos container not found"
- "provider detection wrong"
- "shared infra error"
- "connection pool exhausted"
- "Application Insights not receiving data"

## Procedure

### Step 1 — Health Endpoint Snapshot
```bash
curl http://localhost:7071/api/ai/status | jq
```
Check every field:
- `active_provider` — which LLM backend is selected
- `sql_pool.saturation_alert` — `true` means ≥80% utilization
- `cosmos_enabled` / `cosmos_healthy` — Cosmos feature-flag status
- `ml_libs_available` — torch/transformers/peft in-process
- `quantum_ready` — qiskit/pennylane available
- `lora_adapter_ready` — both adapter files present

### Step 2 — SQL Pool Diagnosis
```bash
# Check pool size setting
echo $QAI_DB_CONN        # Should be set for SQL persistence
echo $QAI_SQL_POOL_SIZE  # Default 10; increase if saturated
```
Connection string examples:
- SQLite: `sqlite:///path/to/qai.db`
- PostgreSQL: `postgresql://user:pass@host:5432/db`
- Azure SQL: ODBC Driver 18 with `Encrypt=yes`

If `saturation_alert: true`, increase `QAI_SQL_POOL_SIZE` and check for connection leaks (unclosed cursors in long-running routes).

### Step 3 — DB Logging Verification
All `shared/db_logging.py` functions are fault-tolerant:
```python
result = log_chat_message_safe(session_id, provider, model, role, content)
# result == {success: False, skipped: True}  → QAI_DB_CONN not configured (expected)
# result == {success: False, error: "..."}   → DB call failed (log and continue)
# result == {success: True, ...}             → logged successfully
```
**Never block on logging failure.** `skipped: True` is normal when DB is not configured.

Stored procedures live in `database/StoredProcedures/`:
- `sp_LogChatConversation` — chat messages
- `sp_LogQuantumTrainingRun` — quantum runs
- `sp_LogLoRATrainingRun` — LoRA runs

### Step 4 — Cosmos DB Diagnosis
```python
# Enable Cosmos in environment:
# QAI_ENABLE_COSMOS=true
# COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
# COSMOS_KEY=<key>
# COSMOS_DATABASE=<db>
# COSMOS_CONTAINER=<container>
```
Validate lazy connection:
```bash
curl http://localhost:7071/api/ai/status | jq '.cosmos_healthy'
```
If `false`: check env vars, verify container exists with partition key `/session_id`, and confirm TTL is enabled for cost savings.

### Step 5 — Telemetry Diagnosis
Telemetry (`shared/telemetry.py`) uses Application Insights. Failures are **non-blocking** — a missing key or unreachable endpoint never crashes the service.
```bash
echo $APPLICATIONINSIGHTS_CONNECTION_STRING
```
If empty or malformed, telemetry silently degrades. This is expected in local dev.
For production: verify `InstrumentationKey=` or `ConnectionString=` format.

### Step 6 — Provider Detection Audit
Config precedence (in order of priority): `env vars` > `per-job YAML` > `CLI flags` > `base YAML`
Required env vars for Azure OpenAI (all 4 must be set):
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_DEPLOYMENT`
- `AZURE_OPENAI_API_VERSION`

Check `/api/ai/status` → `active_provider` field to confirm which provider was selected.
Fallback order: Azure OpenAI → OpenAI → LMStudio → Local.

### Step 7 — Run Unit Tests
```bash
python scripts/test_runner.py --unit
# or faster: pytest tests/ -m "not slow and not azure" -x
```
Shared infra tests live in `tests/test_shared_*.py`. Failing tests here indicate regression in pool, Cosmos, or telemetry modules.

## Quality Checks
- [ ] `/api/ai/status` returns 200 with all expected fields present
- [ ] `sql_pool.saturation_alert` is `false` under normal load
- [ ] `log_*_safe()` functions return `{success: False, skipped: True}` (not exceptions) when DB is unconfigured
- [ ] Cosmos health check passes when `QAI_ENABLE_COSMOS=true` and env vars are set
- [ ] `APPLICATIONINSIGHTS_CONNECTION_STRING` uses correct format (`InstrumentationKey=` or `ConnectionString=`)
- [ ] Active provider matches expected value given current env var configuration
