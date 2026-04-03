---
name: "Shared-Python"
description: "Common infrastructure guidance for shared/**/*.py"
applyTo: "shared/**/*.py"
---
# Shared Infrastructure – Python files

- Provider detection (`shared/chat_providers.py`): Azure OpenAI → OpenAI → LoRA → Local.
  - Azure requires: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
  - LoRA readiness: adapter dir must contain `adapter_config.json` and `adapter_model.safetensors`.
- Memory & embeddings (`shared/chat_memory.py`): ensure consistent schema; avoid mutating immutable datasets.
- SQL engine (`shared/sql_engine.py`): unified connection via `QAI_DB_CONN`.
  - Pooling: tune with `QAI_SQL_POOL_SIZE`; saturation surfaced via `/api/ai/status` (≥80% alerts).
  - Safe logging wrappers in `shared/db_logging.py` degrade gracefully when DB unavailable.
- Cosmos client (`shared/cosmos_client.py`): feature-flagged persistence.
  - Enable via `QAI_ENABLE_COSMOS=true` and set `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`.
  - Recommended: partition key `/session_id`, enable TTL for ephemeral items; prefer point reads to reduce RU cost.
- Telemetry (`shared/telemetry.py`): Application Insights with `APPLICATIONINSIGHTS_CONNECTION_STRING`; failures are non-blocking.
- Config precedence: base YAML < CLI flags < per-job YAML overrides < env vars.
- Data conventions: read-only `datasets/`; write-only outputs under `data_out/`.
- Observability: check `/api/ai/status` for provider readiness, SQL pool saturation, Cosmos enablement.
- Tests: use `python .\\scripts\\test_runner.py --all` and VS Code Test Explorer (🧪) for fast local validation; prefer markers `not slow and not azure`.

## Connection string examples (PowerShell)

- SQLite (local dev):
  - `$env:QAI_DB_CONN = "sqlite:///c:/Users/Bryan/OneDrive/AI/data_out/qai.db"`
- PostgreSQL:
  - `$env:QAI_DB_CONN = "postgresql://user:pass@localhost:5432/qai"`
- Azure SQL (ODBC):
  - `$env:QAI_DB_CONN = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=qai;Uid=myuser;Pwd=mypass;Encrypt=yes;TrustServerCertificate=no;"`
- Pool size tuning:
  - Default is small (e.g., 10); increase via `$env:QAI_SQL_POOL_SIZE = "20"` if `/api/ai/status` shows `saturation_alert: true`.
