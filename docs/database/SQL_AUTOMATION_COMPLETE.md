# SQL Integration Automation Suite

**Complete automation tools for deployment, monitoring, and maintenance**

## Overview

This automation suite provides end-to-end management of the SQL integration with zero manual intervention capabilities. All scripts support dry-run mode for safety.

## Automation Components

### 1. Master Deployment Script
**File**: `scripts/deploy_sql_integration.ps1`

One-command deployment orchestrating all integration steps.

**Features**:
- Environment validation (prerequisites, Azure CLI, packages)
- Database migrations with rollback on failure
- Comprehensive test execution
- Azure alert deployment
- Health endpoint verification
- Status tracking and logging

**Usage**:
```powershell
# Local development
.\scripts\deploy_sql_integration.ps1 -Environment Local

# Production with alerts
.\scripts\deploy_sql_integration.ps1 `
  -Environment Production `
  -ResourceGroup "qai-rg" `
  -FunctionAppName "qai-func" `
  -EmailRecipient "admin@example.com"

# Dry-run mode
.\scripts\deploy_sql_integration.ps1 -Environment Production -DryRun
```

**Exit Codes**:
- `0`: Success
- `1`: Failure (check log file in `data_out/`)

### 2. Threshold Auto-Tuning
**File**: `scripts/tune_sql_thresholds.ps1`

Analyzes Application Insights metrics and recommends optimal slow query thresholds.

**Features**:
- P50/P95/P99 percentile analysis
- Alert frequency tracking
- Environment-aware recommendations
- Automatic threshold application to Azure
- JSON analysis reports

**Usage**:
```powershell
# Analyze current metrics
.\scripts\tune_sql_thresholds.ps1 `
  -ResourceGroup "qai-rg" `
  -FunctionAppName "qai-func"

# Auto-apply recommended threshold
.\scripts\tune_sql_thresholds.ps1 `
  -ResourceGroup "qai-rg" `
  -FunctionAppName "qai-func" `
  -Apply

# Custom baseline period
.\scripts\tune_sql_thresholds.ps1 `
  -ResourceGroup "qai-rg" `
  -FunctionAppName "qai-func" `
  -DaysBack 14 `
  -TargetAlertsPerDay 3
```

**Output**: Analysis report saved to `data_out/threshold_analysis_*.json`

### 3. Query Metrics Cleanup
**File**: `scripts/cleanup_query_metrics.py`

Automated retention management for query performance tracking data.

**Features**:
- Configurable retention period
- Table statistics before/after cleanup
- Dry-run mode
- Timestamped logging

**Usage**:
```powershell
# Default 7-day retention
python .\scripts\cleanup_query_metrics.py

# Custom retention period
python .\scripts\cleanup_query_metrics.py --retention-days 30

# Dry-run mode
python .\scripts\cleanup_query_metrics.py --retention-days 7 --dry-run
```

**Scheduling** (Windows Task Scheduler):
```powershell
# Run weekly on Sundays at 2 AM
$action = New-ScheduledTaskAction -Execute "python" -Argument ".\scripts\cleanup_query_metrics.py --retention-days 7" -WorkingDirectory "C:\path\to\repo"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
Register-ScheduledTask -TaskName "QAI SQL Cleanup" -Action $action -Trigger $trigger
```

### 4. Health Monitoring
**File**: `scripts/sql_health_monitor.py`

Continuous health monitoring with alerting capabilities.

**Features**:
- Connectivity probes
- Pool saturation detection
- Slow query frequency tracking
- Webhook alerts for critical issues
- Alert cooldown (5-minute intervals)
- JSON output mode

**Usage**:
```powershell
# Single health check
python .\scripts\sql_health_monitor.py --once

# JSON output (for parsing)
python .\scripts\sql_health_monitor.py --once --json

# Continuous monitoring
python .\scripts\sql_health_monitor.py --interval 60

# With webhook alerts
python .\scripts\sql_health_monitor.py `
  --interval 30 `
  --threshold-critical 90 `
  --alert-webhook "https://hooks.slack.com/services/..."
```

**Exit Codes** (--once mode):
- `0`: Healthy
- `1`: Warning
- `2`: Critical

### 5. PowerShell Module
**File**: `scripts/QAI-SQL.psm1`

Unified PowerShell cmdlet library for all SQL operations.

**Features**:
- 13 cmdlets covering all automation tasks
- Auto-completion support
- Inline help documentation
- Session configuration management

**Usage**:
```powershell
# Import module
Import-Module .\scripts\QAI-SQL.psm1

# View available commands
Get-Command -Module QAI-SQL

# Get status and configuration
Get-QAISQLStatus

# Deploy to local environment
Deploy-QAISQLIntegration -Environment Local

# Run health check
Test-QAISQLHealth

# Start continuous monitoring
Start-QAISQLMonitoring -Interval 30

# Tune thresholds
Optimize-QAISQLThresholds -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -Apply

# Cleanup old metrics
Clear-QAISQLQueryMetrics -RetentionDays 7

# Set configuration
Set-QAISQLConnection -Url "sqlite:///./data.sqlite"
Set-QAISQLSlowThreshold -Milliseconds 300
Enable-QAISQLQueryTracking
```

## Automation Workflows

### Workflow 1: Initial Deployment
```powershell
# 1. Import module
Import-Module .\scripts\QAI-SQL.psm1

# 2. Configure connection (local dev)
Set-QAISQLConnection -Url "sqlite:///./data.sqlite"

# 3. Deploy with tests
Deploy-QAISQLIntegration -Environment Local

# 4. Verify health
Test-QAISQLHealth
```

### Workflow 2: Production Deployment
```powershell
# 1. Dry-run first
.\scripts\deploy_sql_integration.ps1 `
  -Environment Production `
  -ResourceGroup "qai-prod-rg" `
  -FunctionAppName "qai-prod-func" `
  -EmailRecipient "ops@example.com" `
  -DryRun

# 2. Deploy for real
.\scripts\deploy_sql_integration.ps1 `
  -Environment Production `
  -ResourceGroup "qai-prod-rg" `
  -FunctionAppName "qai-prod-func" `
  -EmailRecipient "ops@example.com"

# 3. Start monitoring
python .\scripts\sql_health_monitor.py --interval 60 --threshold-critical 90
```

### Workflow 3: Weekly Maintenance
```powershell
# 1. Analyze and tune thresholds
.\scripts\tune_sql_thresholds.ps1 `
  -ResourceGroup "qai-prod-rg" `
  -FunctionAppName "qai-prod-func" `
  -Apply

# 2. Cleanup old metrics
python .\scripts\cleanup_query_metrics.py --retention-days 7

# 3. Health check
python .\scripts\sql_health_monitor.py --once --json > health_report.json
```

### Workflow 4: CI/CD Integration
```yaml
# Azure DevOps Pipeline example
steps:
  - task: PowerShell@2
    displayName: 'Deploy SQL Integration'
    inputs:
      filePath: 'scripts/deploy_sql_integration.ps1'
      arguments: '-Environment Production -ResourceGroup $(resourceGroup) -FunctionAppName $(functionAppName) -EmailRecipient $(alertEmail)'
  
  - task: PowerShell@2
    displayName: 'Health Check'
    inputs:
      targetType: 'inline'
      script: |
        python .\scripts\sql_health_monitor.py --once
        if ($LASTEXITCODE -ne 0) {
          Write-Error "Health check failed"
          exit 1
        }
```

## Scheduled Tasks Setup

### Windows Task Scheduler
```powershell
# Weekly cleanup (Sundays at 2 AM)
$action = New-ScheduledTaskAction -Execute "python" -Argument ".\scripts\cleanup_query_metrics.py" -WorkingDirectory "C:\QAI"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
Register-ScheduledTask -TaskName "QAI SQL Cleanup" -Action $action -Trigger $trigger

# Daily threshold tuning (Mondays at 3 AM)
$action = New-ScheduledTaskAction -Execute "powershell" -Argument "-File .\scripts\tune_sql_thresholds.ps1 -ResourceGroup qai-rg -FunctionAppName qai-func -Apply" -WorkingDirectory "C:\QAI"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 3am
Register-ScheduledTask -TaskName "QAI SQL Threshold Tuning" -Action $action -Trigger $trigger
```

### Azure Automation Runbook
```powershell
# Create runbook for query cleanup
$runbookName = "QAI-SQL-Cleanup"
$resourceGroup = "qai-automation-rg"
$automationAccount = "qai-automation"

# Create runbook
New-AzAutomationRunbook `
  -ResourceGroupName $resourceGroup `
  -AutomationAccountName $automationAccount `
  -Name $runbookName `
  -Type PowerShell

# Schedule weekly execution
New-AzAutomationSchedule `
  -ResourceGroupName $resourceGroup `
  -AutomationAccountName $automationAccount `
  -Name "Weekly-SQL-Cleanup" `
  -StartTime (Get-Date).AddDays(7) `
  -WeekInterval 1 `
  -TimeZone "UTC"
```

## Monitoring Integration

### Application Insights Integration
```powershell
# Custom metric tracking in health monitor
python .\scripts\sql_health_monitor.py --interval 60 --json | ForEach-Object {
    $health = $_ | ConvertFrom-Json
    
    # Send custom metric to Application Insights
    az monitor app-insights metrics create `
        --app qai-func `
        --name "sql_pool_saturation" `
        --value $health.pool.saturation_pct
}
```

### Slack/Teams Webhook Example
```powershell
# Health monitor with Slack webhook
$webhookUrl = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

python .\scripts\sql_health_monitor.py `
    --interval 60 `
    --threshold-critical 90 `
    --alert-webhook $webhookUrl
```

## Error Handling and Recovery

### Deployment Failures
```powershell
# Check deployment status
$statusFile = ".\data_out\sql_deployment_status.json"
$status = Get-Content $statusFile | ConvertFrom-Json

if (-not $status.success) {
    Write-Host "Deployment failed. Check log: $($status.logFile)"
    
    # Rollback steps
    if (-not $status.steps.Migrations) {
        Write-Host "Migrations failed - no rollback needed"
    }
    
    if ($status.steps.Migrations -and -not $status.steps.Tests) {
        Write-Host "Consider rolling back migrations if database is corrupt"
    }
}
```

### Alert Deployment Failures
```powershell
# Retry with skip flags
.\scripts\deploy_sql_integration.ps1 `
    -Environment Production `
    -ResourceGroup "qai-rg" `
    -FunctionAppName "qai-func" `
    -SkipTests `  # If tests already passed
    -SkipAlerts   # Deploy alerts manually later
```

## Best Practices

1. **Always dry-run production deployments first**
2. **Enable query tracking only after 002 migration applied**
3. **Start with conservative thresholds (500ms) and tune down**
4. **Schedule cleanup during low-traffic periods**
5. **Monitor health checks after every deployment**
6. **Keep deployment logs for audit trail**
7. **Use PowerShell module for consistent operations**
8. **Test automation scripts in staging before production**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Deployment fails at prerequisites | Run `pip install -r requirements.txt` |
| Health monitor shows "critical" | Check `QAI_SQL_URL` environment variable |
| Threshold tuning finds no data | Verify Application Insights is logging traces |
| Cleanup script fails | Ensure 002 migration applied and tracking enabled |
| Module import fails | Run from repo root: `Import-Module .\scripts\QAI-SQL.psm1` |

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/deploy_sql_integration.ps1` | Master deployment orchestrator | 450+ |
| `scripts/tune_sql_thresholds.ps1` | Automated threshold tuning | 300+ |
| `scripts/cleanup_query_metrics.py` | Retention cleanup automation | 200+ |
| `scripts/sql_health_monitor.py` | Health monitoring daemon | 300+ |
| `scripts/QAI-SQL.psm1` | PowerShell cmdlet module | 400+ |

**Total**: ~1,650 lines of automation code

## Next Steps

1. ✅ Import PowerShell module
2. ✅ Run local deployment test
3. ✅ Schedule weekly cleanup task
4. ✅ Configure health monitoring alerts
5. ✅ Set up CI/CD pipeline integration
6. ✅ Enable automated threshold tuning

---

**Related Documentation**:
- [DATABASE_SQL_SETUP.md](./DATABASE_SQL_SETUP.md) - Core setup and configuration
- [AZURE_MONITOR_SQL_SETUP.md](./AZURE_MONITOR_SQL_SETUP.md) - Azure monitoring and KQL queries
- [SQL_QUICKREF.md](./SQL_QUICKREF.md) - Quick reference card

**Status**: All automation components complete and production-ready.
