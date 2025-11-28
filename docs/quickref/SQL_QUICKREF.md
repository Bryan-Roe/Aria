# SQL Integration - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

### Local Development
```powershell
# 1. Set connection string
$env:QAI_SQL_URL = "sqlite:///./data.sqlite"

# 2. Run tests
.\venv\Scripts\python.exe -m pytest tests\test_sql_integration.py -v

# 3. Start Function App
func host start

# 4. Check status
Invoke-RestMethod http://localhost:7071/api/ai/status | ConvertTo-Json -Depth 5
```

### Azure Production
```powershell
# 1. Deploy alerts
.\scripts\setup_azure_alerts.ps1 -ResourceGroup "your-rg" -FunctionAppName "your-func" -ActionGroupName "sql-alerts" -EmailRecipient "admin@example.com"

# 2. Configure connection
az functionapp config appsettings set --name your-func --resource-group your-rg --settings QAI_SQL_URL="mssql+pyodbc://..."

# 3. Monitor in Application Insights (see AZURE_MONITOR_SQL_SETUP.md for KQL queries)
```

## 📊 Key Endpoints

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `/api/ai/status` | Health + SQL metrics | `curl http://localhost:7071/api/ai/status` |
| `engine_stats()` | Pool metrics (code) | `from shared.sql_engine import engine_stats; stats = engine_stats()` |
| `sql_health()` | Connectivity probe | `from shared.sql_engine import sql_health; ok, msg = sql_health()` |

## 🔧 Environment Variables

| Variable | Required | Example |
|----------|----------|---------|
| `QAI_SQL_URL` | No | `sqlite:///./data.sqlite` or `mssql+pyodbc://...` |
| `QAI_SQL_SLOW_MS` | No | `300` (milliseconds) |
| `QAI_ENABLE_QUERY_TRACKING` | No | `true` (enable persistent metrics) |
| `AZURE_FUNCTIONS_ENVIRONMENT` | No | `development` / `staging` / `production` |

## 📈 Monitoring Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `saturation_pct` | > 60% | > 80% | Scale pool size |
| `slow_queries_1min` | > 5 | > 10 | Tune threshold or optimize queries |
| `execution_time_ms` | > P95 | > P99 | Add indexes, review query plan |

## 🛠️ Common Commands

### Migrations
```powershell
# Apply all pending migrations
python .\scripts\sql_migrate.py

# Check migration status (look at output: "2 applied; 1 pending")
python .\scripts\sql_migrate.py
```

### Testing
```powershell
# Run all SQL tests
.\venv\Scripts\python.exe -m pytest tests\test_sql_integration.py -v

# Run specific test
.\venv\Scripts\python.exe -m pytest tests\test_sql_integration.py::test_saturation_detection -v
```

### Pool Scaling
```powershell
# Increase pool size to 30 connections
$env:QAI_SQL_URL = "postgresql://user:pass@host/db?pool_size=30&max_overflow=10"
```

### Alert Deployment
```powershell
# Dry-run (validate without deploying)
.\scripts\setup_azure_alerts.ps1 -ResourceGroup "rg" -FunctionAppName "func" -DryRun

# Deploy with new Action Group
.\scripts\setup_azure_alerts.ps1 -ResourceGroup "rg" -FunctionAppName "func" -ActionGroupName "alerts" -EmailRecipient "admin@example.com"

# Use existing Action Group
.\scripts\setup_azure_alerts.ps1 -ResourceGroup "rg" -FunctionAppName "func" -SkipActionGroup
```

## 📝 Key Files

| File | Purpose |
|------|---------|
| `DATABASE_SQL_SETUP.md` | Complete setup & usage guide (20 sections) |
| `AZURE_MONITOR_SQL_SETUP.md` | Azure deployment & KQL queries |
| `SQL_INTEGRATION_COMPLETE.md` | Implementation summary & architecture |
| `shared/sql_engine.py` | Core engine with pool metrics |
| `shared/sql_repository.py` | Key-value CRUD abstraction |
| `scripts/sql_migrate.py` | Migration runner |
| `scripts/setup_azure_alerts.ps1` | Alert deployment automation |
| `config/azure_monitor_alerts.json` | ARM template for alerts |
| `tests/test_sql_integration.py` | Test suite (7 tests) |

## 🔍 Troubleshooting Quick Hits

| Issue | Solution |
|-------|----------|
| "No SQL configured" in status | Set `QAI_SQL_URL` or `QAI_DB_CONN` env var |
| Pool saturation > 80% | Increase `pool_size` URL parameter (see DATABASE_SQL_SETUP.md section 18) |
| Too many slow query alerts | Increase `QAI_SQL_SLOW_MS` or optimize queries |
| Migrations not applying | Check `QAI_Migrations` table exists, verify SQL file syntax |
| Tests failing | Ensure SQLAlchemy installed in venv: `.\venv\Scripts\pip install sqlalchemy` |
| Alerts not firing | Verify Application Insights enabled, check KQL query in portal |

## 📚 KQL Quick Queries

### Pool Saturation Trend
```kql
traces | where message has "saturated" | extend saturation_pct = todouble(extract(@"(\d+\.\d+)% saturated", 1, message)) | render timechart
```

### Slow Query Frequency
```kql
traces | where message has "slow query" | summarize count() by bin(timestamp, 5m) | render timechart
```

### Top Slow Queries
```kql
traces | where message has "slow query" | extend sql = extract(@"sql=(.{1,120})", 1, message) | summarize count() by sql | order by count_ desc | take 10
```

## ✅ Production Deployment Checklist

- [ ] Tests passing locally (7/7)
- [ ] Connection string configured in Azure
- [ ] Alert rules deployed via PowerShell script
- [ ] Action Group configured with team emails
- [ ] Application Insights enabled on Function App
- [ ] Baseline threshold set (`QAI_SQL_SLOW_MS=500`)
- [ ] Pool size calculated based on load (`pool_size=20` for medium traffic)
- [ ] KQL dashboard created in Application Insights
- [ ] Weekly review scheduled for slow query trends
- [ ] Retention cleanup scheduled (if query tracking enabled)

## 🎯 Performance Targets

| Environment | Slow Query Threshold | Pool Size | Target P95 |
|-------------|---------------------|-----------|------------|
| Development | 100ms | 5 | < 150ms |
| Staging | 300ms | 10-20 | < 400ms |
| Production | 500ms | 20-50 | < 600ms |

## 🚨 Alert Response Playbook

### Saturation Alert Fires
1. Check current load in Application Insights
2. Review recent deployments (correlation)
3. Increase `pool_size` by 50% via URL parameter
4. Monitor for 24 hours, iterate

### Slow Query Alert Fires
1. Run "Top Slow Queries" KQL in Application Insights
2. Identify frequently-executed queries
3. Add indexes via new migration file
4. Deploy migration, monitor improvement

### Both Alerts Fire Together
1. Likely indicates high load or database performance issue
2. Scale pool size immediately
3. Check database server metrics (CPU, I/O, locks)
4. Consider read replicas or query optimization

---

**Full Documentation**: [DATABASE_SQL_SETUP.md](./DATABASE_SQL_SETUP.md) | [AZURE_MONITOR_SQL_SETUP.md](./AZURE_MONITOR_SQL_SETUP.md)  
**Implementation Details**: [SQL_INTEGRATION_COMPLETE.md](./SQL_INTEGRATION_COMPLETE.md)  
**Tests**: `.\venv\Scripts\python.exe -m pytest tests\test_sql_integration.py -v`
