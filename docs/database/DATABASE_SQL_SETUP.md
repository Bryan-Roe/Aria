# Multi-Database SQL Integration (Extended)

This guide supplements the existing Azure SQL logging system by enabling **multi-database** access through a unified SQLAlchemy engine. It adds support for Azure SQL (SQL Server), PostgreSQL, MySQL/MariaDB, and SQLite with minimal configuration.

## 1. Overview

Existing logging uses stored procedures via `pyodbc` and `QAI_DB_CONN`. New layer adds:

- Unified engine in `shared/sql_engine.py`
- Generic key-value repository in `shared/sql_repository.py`
- Health exposure via `/api/ai/status` (`sql` section)
- Pool metrics + slow query logging
- Optional multi-vendor support with a single environment variable: `QAI_SQL_URL`

| Feature | Legacy (Stored Proc) | New (Engine/Repository) |
| --------- | ---------------------- | -------------------------- |
| Training / Chat Logging | ✅ (sp_Log*) | ✅ (unchanged) |
| Embeddings | ✅ | ✅ |
| Ad-hoc Queries | ❌ | ✅ (`quick_query`) |
| Multi-Vendor | Limited (SQL Server) | ✅ (Postgres, MySQL, SQLite) |
| Health Surface | Cosmos only | ✅ (`sql` payload) |
| Fault Tolerance | ✅ | ✅ |
| Pool Metrics | ❌ | ✅ (`engine_stats`) |
| Slow Query Warn | ❌ | ✅ (threshold env var) |

## 2. Environment Variables

Set **one** of:

- `QAI_SQL_URL` – Preferred full SQLAlchemy URL.
  - Examples:
    - PostgreSQL: `postgresql+psycopg://user:pass@host/dbname`
    - MySQL: `mysql+mysqlclient://user:pass@host/dbname`
    - SQLite file: `sqlite:///data_out/dev.db`
    - SQLite memory: `sqlite:///:memory:` (tests only)
- `QAI_DB_CONN` – Existing ODBC string (auto-wrapped to SQLAlchemy URL internally).

Optional:

- `QAI_SQL_SLOW_MS` – Milliseconds threshold for slow query logging (default `500`).

If both URL and ODBC are set, `QAI_SQL_URL` wins.

## 3. Installation

Dependencies already include:

```text
pyodbc>=5.0.1
sqlalchemy>=2.0.29
```

Optional (uncomment in `requirements.txt` if needed):

```text
# psycopg2-binary>=2.9.9   # PostgreSQL
# mysqlclient>=2.2.4       # MySQL/MariaDB
```

Then install:

```powershell
pip install -r requirements.txt
```

## 4. Status Endpoint Extension

`/api/ai/status` now includes:

```json
"sql": {
  "enabled": true,
  "url": "sqlite:///data_out/dev.db",
  "vendor": "sqlite",
  "connectivity": true,
  "error": null,
  "pool": {
    "enabled": true,
    "type": "SingletonThreadPool",
    "size": null,
    "checkedout": null,
    "overflow": null,
    "recycle": 1800,
    "timeout": 30,
    "status": "Pool size: ..."
  }
}
```

If misconfigured:

```json
"sql": {"enabled": false, "url": null}
```

## 5. Using the Repository

```python
from shared.sql_repository import put_value, get_value, list_values, delete_value

put_value("last_model", "phi3.6-mini")
print(get_value("last_model"))  # => phi3.6-mini
print(list_values())
delete_value("last_model")
```

## 6. Quick Ad-Hoc Queries

```python
from shared.sql_engine import quick_query
rows = quick_query("SELECT TOP 5 * FROM QuantumTrainingRuns ORDER BY CreatedAt DESC")
for r in rows:
    print(r)
```

(Use dialect-appropriate syntax; `TOP` works for SQL Server, use `LIMIT` for others.)

### Slow Query Example (Artificial Delay for Testing)

```python
from shared.sql_engine import quick_query
rows = quick_query("SELECT 1", simulate_delay=0.6)  # sleeps 0.6s before execution
```

If `QAI_SQL_SLOW_MS=500`, a warning log is emitted:

```
[sql_engine] slow query (602.3 ms > 500 ms) vendor=sqlite sql=SELECT 1
```

## 7. Table Creation Logic

The key-value table auto-creates using vendor-specific syntax:

- SQLite: `CREATE TABLE IF NOT EXISTS`
- PostgreSQL / MySQL: `CREATE TABLE IF NOT EXISTS`
- SQL Server: `IF NOT EXISTS (...) BEGIN CREATE TABLE ... END`

## 8. Migration Script

`scripts/sql_migrate.py` now:

- Scans `database/migrations/*.sql`
- Ensures `QAI_Migrations` metadata table
- Skips already-applied migrations
- Logs summary counts

Example output:

```
[sql_migrate] Found 3 migration(s); 1 already applied; 2 pending.
[sql_migrate] Applied 002_add_index.sql
[sql_migrate] Completed 2 migration(s).
```

Sample migration added:

```sql
-- database/migrations/001_keyvalue_index.sql
CREATE INDEX idx_qai_keyvalue_k ON QAI_KeyValue (k);
```

## 9. Testing

`tests/test_sql_integration.py` uses an **in-memory SQLite** URL:

```powershell
set QAI_SQL_URL=sqlite:///:memory:
pytest -k sql_integration
```

Additional tests cover:

- Pool stats presence (`engine_stats`)
- Slow query warning via `simulate_delay`

## 10. Best Practices (Azure Functions)

- Reuse engine (global caching) – avoids SNAT exhaustion.
- Use `pool_pre_ping=True` to drop stale connections.
- Prefer `QAI_SQL_URL` for non-SQL Server backends.
- Keep write operations concise; batch where feasible.
- For high-throughput logging, consider async queue + worker pattern.
- Keep slow query threshold realistic (start 500–1000 ms; adjust via metrics).

## 11. Security Notes

- Do NOT commit secrets in `local.settings.json` or repo files.
- Use Managed Identity for Azure SQL (passwordless) once deployed.
- Rotate credentials regularly; prefer secret store (Key Vault).

## 12. Fallback Behavior

- Missing env vars → `sql.enabled=false` in status.
- Engine creation failure → logged warning, silent degradation.
- Repository operations return default (empty / None / False) without raising.
- Pool stats degrade gracefully (None values) if pool type lacks metrics.

## 13. Future Enhancements

- Additional migrations (schema evolution / analytics indexes)
- ORM models for complex analytics
- Connection saturation alerts (checked-out vs size)
- Retry & circuit breaker wrappers
- Write queue for high-frequency events
- Query tracing (OpenTelemetry spans) for diagnostics

## 14. Quick Setup Examples

### A. SQLite (Local Dev, Zero Config)

```powershell
$env:QAI_SQL_URL = "sqlite:///data_out/dev.db"
func host start
```

### B. PostgreSQL

```powershell
$env:QAI_SQL_URL = "postgresql+psycopg://user:pass@host:5432/qai"
pip install psycopg2-binary
func host start
```

### C. Azure SQL via ODBC (Existing)

```powershell
$env:QAI_DB_CONN = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:your-server.database.windows.net,1433;Database=qai-db;Uid=user;Pwd=***;Encrypt=yes;TrustServerCertificate=no;"
func host start
```

## 15. Verification Checklist

- [ ] `sql.enabled=true` in `/api/ai/status`
- [ ] Key-value CRUD succeeds
- [ ] Pool stats visible (`sql.pool.enabled=true`)
- [ ] Slow query warning triggers when threshold exceeded
- [ ] Legacy logging continues without change
- [ ] No unexpected exceptions in function logs

## 16. Troubleshooting

| Symptom | Cause | Action |
| --------- | ------- | -------- |
| `sql.enabled=false` | Missing env vars | Set `QAI_SQL_URL` or `QAI_DB_CONN` |
| Slow query warnings too frequent | Threshold too low | Raise `QAI_SQL_SLOW_MS` |
| Pool stats show `None` | Pool type lacks metrics (e.g., SQLite memory pool) | Accept defaults; switch to file-based SQLite or external DB |
| Migration fails | SQL dialect mismatch | Adjust SQL syntax for target vendor |
| `saturation_alert` appearing | Too many concurrent connections | Scale pool size or reduce workload concurrency |

## 17. Advanced Monitoring Features

### Pool Saturation Alerts

The engine automatically monitors connection pool utilization and emits warnings when saturation exceeds **80%**:

```json
"sql": {
  "pool": {
    "saturation_pct": 85.0,
    "saturation_alert": "Pool 85.0% saturated (17/20)",
    "size": 20,
    "checkedout": 17
  },
  "alert": "Pool 85.0% saturated (17/20)"
}
```

**Actions on high saturation:**

- Increase pool size: Add `?pool_size=50` to SQLAlchemy URL
- Review long-running queries (may hold connections)
- Enable connection logging: `?echo_pool=true`
- Consider read replicas or connection multiplexing

### Slow Query Frequency Tracking

Engine tracks slow queries in a **rolling 60-second window** (in-memory):

```json
"sql": {
  "pool": {
    "slow_queries_1min": 15,
    "slow_query_threshold_ms": 500
  },
  "slow_query_alert": "15 slow queries in last 60s (threshold=500ms)"
}
```

**High frequency indicators (>10 in 60s):**

- Database performance degradation (check indexes, query plans)
- Network latency to database server
- Threshold too aggressive for workload
- Missing query optimization (consider caching frequent reads)

### Environment-Aware Threshold Tuning

Slow query threshold automatically adjusts based on deployment environment:

| Environment | Threshold | Rationale |
| ------------- | ----------- | ----------- |
| `development` (local) | 100ms | Fast feedback during development |
| `staging` / `test` | 300ms | Balanced for integration testing |
| `production` (default) | 500ms | Conservative for variable load |

**Override with explicit env var:**

```powershell
$env:QAI_SQL_SLOW_MS = "250"  # Custom threshold
```

**Auto-detection via Azure Functions environment:**

```powershell
$env:AZURE_FUNCTIONS_ENVIRONMENT = "staging"  # Uses 300ms
```

### Query Performance Migration (Optional)

Migration `002_query_performance_tracking.sql` creates a table for persistent query metrics:

```sql
-- Tracks: query_hash, sql_snippet, vendor, execution_time_ms, executed_at
-- Enables: Historical analysis, trend detection, query frequency patterns
```

**Enable tracking** (future implementation):

```powershell
$env:QAI_ENABLE_QUERY_TRACKING = "true"
```

**Use cases:**

- Identify queries that degrade over time (growing data volume)
- Discover frequently-executed queries (caching candidates)
- Correlate slow queries with deployment or schema changes
- Generate weekly performance reports

## 18. Pool Scaling Strategies

When `sql.pool.saturation_pct` consistently exceeds 60-80%, consider scaling the connection pool.

### URL Parameter Method (Recommended)

SQLAlchemy supports pool configuration via URL query parameters:

```powershell
# PostgreSQL with custom pool size
$env:QAI_SQL_URL = "postgresql+psycopg2://user:pass@host/db?pool_size=30&max_overflow=10"

# Azure SQL via ODBC with custom pool
$env:QAI_SQL_URL = "mssql+pyodbc://user:pass@host.database.windows.net/db?driver=ODBC+Driver+18+for+SQL+Server&pool_size=30&max_overflow=15"

# SQLite with custom timeout
$env:QAI_SQL_URL = "sqlite:///path/to/db.sqlite?timeout=30"
```

### Pool Size Guidelines

| Scenario | Pool Size | Max Overflow | Rationale |
| ---------- | ----------- | -------------- | ----------- |
| Low traffic (< 10 req/s) | 10 | 5 | Minimize idle connections |
| Medium traffic (10-50 req/s) | 20-30 | 10 | Balanced for burst capacity |
| High traffic (> 50 req/s) | 30-50 | 20 | Prevent saturation under load |
| Background workers | 5 | 2 | Dedicated small pool |

**Calculation formula:**

```text
pool_size = (function_instances × avg_concurrent_requests_per_instance) × 1.2
```

**Example:**

- 5 function instances (Azure Functions consumption plan)
- 4 concurrent requests per instance average
- Pool size = 5 × 4 × 1.2 = **24 connections**

### Additional URL Parameters

| Parameter | Default | Description |
| ----------- | --------- | ------------- |
| `pool_size` | 5 | Core pool size (always open) |
| `max_overflow` | 10 | Additional connections on demand |
| `pool_timeout` | 30 | Seconds to wait for available connection |
| `pool_recycle` | 1800 | Seconds before recycling connection (30 min) |
| `pool_pre_ping` | false | Test connection before using (recommended: true, set in code) |

### Code Override (Not Recommended)

If URL parameters don't work, modify `shared/sql_engine.py`:

```python
_ENGINE = create_engine(
    url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=30,        # Override
    max_overflow=10,     # Override
    future=True,
)
```

**Downside**: Requires code changes per environment.

### Monitoring Pool Effectiveness

After scaling, monitor for 24-48 hours:

```kql
// Application Insights KQL
traces
| where message has "[sql_engine]" and message has "saturated"
| extend saturation_pct = todouble(extract(@"(\d+\.\d+)% saturated", 1, message))
| summarize MaxSaturation = max(saturation_pct) by bin(timestamp, 1h)
| where MaxSaturation > 60
```

**Action**: If `MaxSaturation` still > 60%, increase pool size by 50%.

## 19. Azure Monitor Integration

For production deployments, integrate with Azure Monitor for automated alerting and historical analysis.

**Quick Start:**

```powershell
# Deploy alerts with automation script
.\scripts\setup_azure_alerts.ps1 `
  -ResourceGroup "your-rg" `
  -FunctionAppName "your-func-app" `
  -ActionGroupName "sql-alerts" `
  -EmailRecipient "admin@example.com"
```

**Features:**

- Metric alerts for pool saturation > 80%
- Scheduled query rules for slow query frequency bursts
- KQL queries for P50/P95/P99 latency analysis
- Action Groups for email/SMS/webhook notifications

**Full documentation**: [AZURE_MONITOR_SQL_SETUP.md](./AZURE_MONITOR_SQL_SETUP.md)

## 20. Monitoring Checklist for Production

- [ ] Set `QAI_SQL_SLOW_MS` appropriate for workload (start 500ms, tune down)
- [ ] Monitor `sql.pool.saturation_pct` in Application Insights or logs
- [ ] Deploy Azure Monitor alerts via `setup_azure_alerts.ps1`
- [ ] Review `slow_queries_1min` during load testing
- [ ] Enable query tracking migration if historical analysis needed
- [ ] Configure pool size based on concurrent function instances (see section 18)
- [ ] Use Managed Identity for passwordless Azure SQL connections
- [ ] Schedule periodic review of migration `QAI_Migrations` table
- [ ] Set up weekly retention cleanup for `QAI_QueryMetrics` (if enabled)
- [ ] Review KQL dashboards weekly for performance trends

---
Multi-database support is additive and non-invasive. If you do not set a URL, the system behaves exactly as before.
