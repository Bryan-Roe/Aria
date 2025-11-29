# Azure Monitor & Application Insights - SQL Observability Setup

This guide provides step-by-step instructions for deploying Azure Monitor alerts and querying Application Insights for SQL performance tracking.

## Prerequisites

- Azure Function App deployed with Application Insights enabled
- Azure CLI installed (`az --version`)
- Contributor access to the resource group
- Action Group created for alert notifications

## Quick Start

### 1. Deploy Alerts via ARM Template

```powershell
# Set variables
$resourceGroup = "your-rg-name"
$functionAppName = "your-function-app"
$actionGroupId = "/subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.Insights/actionGroups/{name}"

# Deploy alert rules
az deployment group create `
  --resource-group $resourceGroup `
  --template-file config/azure_monitor_alerts.json `
  --parameters functionAppName=$functionAppName actionGroupId=$actionGroupId
```

### 2. Verify Deployment

```powershell
# List alert rules
az monitor metrics alert list --resource-group $resourceGroup --output table
az monitor scheduled-query list --resource-group $resourceGroup --output table
```

## Application Insights KQL Queries

### Query 1: Pool Saturation Over Time

```kql
traces
| where message has "[sql_engine]" and message has "saturated"
| extend saturation_pct = extract(@"(\d+\.\d+)% saturated", 1, message)
| project timestamp, saturation_pct = todouble(saturation_pct), message
| render timechart
```

**Use Case**: Visualize pool saturation trends to identify peak load periods.

### Query 2: Slow Query Frequency Heatmap

```kql
traces
| where message has "[sql_engine] slow query"
| extend duration_ms = extract(@"slow query \((\d+\.\d+) ms", 1, message)
| summarize SlowQueryCount = count(), AvgDuration = avg(todouble(duration_ms)) by bin(timestamp, 5m)
| render timechart
```

**Use Case**: Detect slow query spikes correlated with deployments or load changes.

### Query 3: Top Slow Queries by Frequency

```kql
traces
| where message has "[sql_engine] slow query"
| extend sql_snippet = extract(@"sql=(.{1,120})", 1, message)
| extend duration_ms = todouble(extract(@"slow query \((\d+\.\d+) ms", 1, message))
| summarize 
    Count = count(), 
    AvgDuration = avg(duration_ms), 
    MaxDuration = max(duration_ms) 
  by sql_snippet
| order by Count desc
| take 20
```

**Use Case**: Identify queries that are consistently slow (caching candidates).

### Query 4: Pool Saturation Alert Summary

```kql
requests
| where url endswith "/api/ai/status"
| extend sql_data = parse_json(tostring(customDimensions.sql))
| extend saturation_pct = todouble(sql_data.pool.saturation_pct)
| extend saturation_alert = tostring(sql_data.alert)
| where isnotempty(saturation_alert)
| summarize AlertCount = count(), MaxSaturation = max(saturation_pct) by bin(timestamp, 10m)
| render timechart
```

**Use Case**: Track how often saturation alerts trigger over time.

### Query 5: Query Performance Percentiles (P50, P95, P99)

```kql
traces
| where message has "[sql_engine] slow query"
| extend duration_ms = todouble(extract(@"slow query \((\d+\.\d+) ms", 1, message))
| summarize 
    P50 = percentile(duration_ms, 50),
    P95 = percentile(duration_ms, 95),
    P99 = percentile(duration_ms, 99),
    Count = count()
  by bin(timestamp, 1h)
| render timechart
```

**Use Case**: Tune `QAI_SQL_SLOW_MS` threshold based on P95 latency.

### Query 6: Correlation Between Saturation and Slow Queries

```kql
let saturation = traces
| where message has "saturated"
| extend saturation_pct = todouble(extract(@"(\d+\.\d+)% saturated", 1, message))
| summarize AvgSaturation = avg(saturation_pct) by bin(timestamp, 5m);
let slowQueries = traces
| where message has "slow query"
| summarize SlowCount = count() by bin(timestamp, 5m);
saturation
| join kind=inner slowQueries on timestamp
| project timestamp, AvgSaturation, SlowCount
| render timechart
```

**Use Case**: Determine if high saturation causes query slowdown.

## Alert Configuration Details

### Alert 1: Pool Saturation (Metric Alert)

- **Metric**: `sql_pool_saturation_pct` (custom metric)
- **Threshold**: > 80%
- **Window**: 5 minutes
- **Evaluation Frequency**: 1 minute
- **Severity**: Warning (2)
- **Action**: Fire when saturation sustained above 80% for 5 minutes

### Alert 2: Slow Query Frequency (Log Alert)

- **Query**: Count of `slow query` traces in last 1 minute
- **Threshold**: > 10 queries
- **Window**: 5 minutes
- **Evaluation Frequency**: 5 minutes
- **Severity**: Informational (3)
- **Action**: Fire when slow query burst detected

### Alert 3: Saturation Status Alert (Log Alert)

- **Query**: Presence of `saturation_alert` field in `/api/ai/status` responses
- **Threshold**: > 0 occurrences
- **Window**: 5 minutes
- **Evaluation Frequency**: 5 minutes
- **Severity**: Warning (2)
- **Failing Periods**: 2 consecutive periods (reduces flapping)

## Tuning Thresholds Based on Metrics

### Step 1: Collect Baseline (7 days)

```powershell
# Run for 1 week with default thresholds
$env:QAI_SQL_SLOW_MS = "500"
$env:AZURE_FUNCTIONS_ENVIRONMENT = "production"
```

### Step 2: Analyze P95 Latency

Run **Query 5** in Application Insights and note P95 value.

**Tuning Decision Matrix:**

| P95 Latency | Recommended Threshold | Rationale |
|-------------|----------------------|-----------|
| < 100ms | 150ms | Catch outliers early |
| 100-300ms | 400ms | Balanced sensitivity |
| 300-500ms | 600ms | Reduce alert noise |
| > 500ms | 750ms | Focus on severe cases |

### Step 3: Adjust Threshold

```powershell
# Update based on analysis
$env:QAI_SQL_SLOW_MS = "400"  # Example: P95 was 250ms
```

### Step 4: Monitor Alert Frequency

Target: < 5 alerts per day per environment.

## Scaling Pool Size

### Option 1: URL Parameter (Recommended)

```powershell
# PostgreSQL example
$env:QAI_SQL_URL = "postgresql+psycopg://user:pass@host/db?pool_size=30&max_overflow=10"

# Azure SQL with ODBC
$env:QAI_SQL_URL = "mssql+pyodbc://user:pass@host/db?driver=ODBC+Driver+18+for+SQL+Server&pool_size=30"
```

**Common Pool Size Guidelines:**

| Scenario | Pool Size | Max Overflow | Rationale |
|----------|-----------|--------------|-----------|
| Low traffic (< 10 req/s) | 10 | 5 | Minimize idle connections |
| Medium traffic (10-50 req/s) | 20 | 10 | Balanced for burst capacity |
| High traffic (> 50 req/s) | 30-50 | 20 | Prevent saturation under load |
| Background workers | 5 | 2 | Dedicated pool for async jobs |

### Option 2: Engine Creation Override (Code)

```python
# In shared/sql_engine.py (manual override)
_ENGINE = create_engine(
    url,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=30,        # Override default (5)
    max_overflow=10,     # Override default (10)
    future=True,
)
```

### Monitoring Pool Size Effectiveness

```kql
traces
| where message has "[sql_engine]" and message has "saturated"
| extend saturation_pct = todouble(extract(@"(\d+\.\d+)% saturated", 1, message))
| summarize AvgSaturation = avg(saturation_pct), MaxSaturation = max(saturation_pct) by bin(timestamp, 1h)
| where MaxSaturation > 60  // Still experiencing pressure
```

**Action**: If `MaxSaturation` consistently > 60% after scaling, increase pool size by 50%.

## Enabling Query Tracking (Historical Analysis)

### Step 1: Apply Migration

```powershell
# Ensure migration table exists
python .\scripts\sql_migrate.py
```

### Step 2: Enable Feature

```powershell
# Production
$env:QAI_ENABLE_QUERY_TRACKING = "true"

# Verify in status endpoint
Invoke-RestMethod -Uri "http://localhost:7071/api/ai/status" | ConvertTo-Json -Depth 5
```

### Step 3: Query Historical Data

```sql
-- Top 10 slowest queries (last 24 hours)
SELECT 
    query_hash,
    sql_snippet,
    COUNT(*) as execution_count,
    AVG(execution_time_ms) as avg_duration,
    MAX(execution_time_ms) as max_duration
FROM QAI_QueryMetrics
WHERE executed_at > datetime('now', '-1 day')
GROUP BY query_hash
ORDER BY avg_duration DESC
LIMIT 10;
```

### Step 4: Cleanup Old Data (Retention Policy)

```sql
-- Delete metrics older than 7 days (run weekly via Azure Automation)
DELETE FROM QAI_QueryMetrics
WHERE executed_at < datetime('now', '-7 days');
```

## Action Group Setup

### Create Action Group via Azure Portal

1. Navigate to **Monitor** > **Alerts** > **Action groups**
2. Click **+ Create**
3. Configure:
   - **Resource group**: Same as Function App
   - **Action group name**: `sql-alerts-action-group`
   - **Notification types**: Email, SMS, Push (select as needed)
   - **Actions**: Add webhook for incident management (optional)

### Create via Azure CLI

```powershell
az monitor action-group create `
  --name sql-alerts-action-group `
  --resource-group your-rg-name `
  --short-name sqlalertsql `
  --email-receiver name=admin email=admin@example.com
```

## Troubleshooting

### Issue: Alerts Not Firing

**Check 1**: Verify Application Insights connection

```powershell
az monitor app-insights component show --app your-app --resource-group your-rg
```

**Check 2**: Confirm traces are being logged

```kql
traces
| where message has "[sql_engine]"
| take 10
```

**Check 3**: Validate alert rule query

```kql
// Run the exact alert query in Application Insights
traces
| where message has 'slow query'
| where timestamp > ago(1m)
| summarize count()
```

### Issue: Too Many False Positives

**Solution 1**: Increase evaluation window

```json
"windowSize": "PT10M"  // Change from 5 to 10 minutes
```

**Solution 2**: Add failing period threshold

```json
"failingPeriods": {
  "numberOfEvaluationPeriods": 3,
  "minFailingPeriodsToAlert": 2  // Fire only if 2 out of 3 windows fail
}
```

### Issue: Query Tracking Table Growing Too Large

**Solution**: Implement retention cleanup

```powershell
# Azure Automation runbook (schedule weekly)
$env:QAI_SQL_URL = "your-connection-string"
python -c "from shared.sql_engine import get_engine; from sqlalchemy import text; e = get_engine(); e.execute(text('DELETE FROM QAI_QueryMetrics WHERE executed_at < datetime(\"now\", \"-7 days\")'))"
```

## Cost Optimization

- **Log Ingestion**: ~$2.76/GB (Application Insights)
- **Query Execution**: First 5GB/month free, then $0.13/GB
- **Alert Evaluations**: First 250 evaluations free, then $0.10 per evaluation

**Recommendations:**

1. Use log sampling if ingestion > 100GB/month
2. Aggregate metrics before alerting (hourly rollups)
3. Disable query tracking in non-production environments

## Next Steps

1. ✅ Deploy alert templates
2. ✅ Create Application Insights dashboard with queries
3. ✅ Set up Action Group with team notification channels
4. ✅ Run baseline collection (7 days)
5. ✅ Tune thresholds based on P95 metrics
6. ✅ Enable query tracking in production (if needed)
7. ✅ Schedule weekly retention cleanup job

---
For additional support, refer to [DATABASE_SQL_SETUP.md](../DATABASE_SQL_SETUP.md) for core SQL configuration details.
