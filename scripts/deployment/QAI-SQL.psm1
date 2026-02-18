<#
.SYNOPSIS
    PowerShell module for QAI SQL Integration operations.

.DESCRIPTION
    Provides convenient cmdlets for managing SQL integration including:
    - Deployment and migration
    - Health monitoring
    - Threshold tuning
    - Retention cleanup
    - Alert management

.NOTES
    Import this module with: Import-Module .\scripts\QAI-SQL.psm1
#>

$Script:ScriptRoot = Split-Path -Parent $PSScriptRoot
$Script:VenvPython = Join-Path $Script:ScriptRoot "venv\Scripts\python.exe"

#region Deployment Functions

<#
.SYNOPSIS
    Deploy SQL integration to specified environment.
    
.EXAMPLE
    Deploy-QAISQLIntegration -Environment Local
    
.EXAMPLE
    Deploy-QAISQLIntegration -Environment Production -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -EmailRecipient "admin@example.com"
#>
function Deploy-QAISQLIntegration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Local", "Staging", "Production")]
        [string]$Environment,
        
        [Parameter(Mandatory = $false)]
        [string]$ResourceGroup,
        
        [Parameter(Mandatory = $false)]
        [string]$FunctionAppName,
        
        [Parameter(Mandatory = $false)]
        [string]$EmailRecipient,
        
        [Parameter(Mandatory = $false)]
        [switch]$SkipTests,
        
        [Parameter(Mandatory = $false)]
        [switch]$SkipAlerts,
        
        [Parameter(Mandatory = $false)]
        [switch]$DryRun
    )
    
    $deployScript = Join-Path $Script:ScriptRoot "scripts\deploy_sql_integration.ps1"
    
    $params = @{
        Environment = $Environment
    }
    
    if ($ResourceGroup) { $params.ResourceGroup = $ResourceGroup }
    if ($FunctionAppName) { $params.FunctionAppName = $FunctionAppName }
    if ($EmailRecipient) { $params.EmailRecipient = $EmailRecipient }
    if ($SkipTests) { $params.SkipTests = $true }
    if ($SkipAlerts) { $params.SkipAlerts = $true }
    if ($DryRun) { $params.DryRun = $true }
    
    & $deployScript @params
}

<#
.SYNOPSIS
    Run database migrations.
    
.EXAMPLE
    Invoke-QAISQLMigrations
#>
function Invoke-QAISQLMigrations {
    [CmdletBinding()]
    param()
    
    $migrationScript = Join-Path $Script:ScriptRoot "scripts\sql_migrate.py"
    
    if (-not (Test-Path $Script:VenvPython)) {
        Write-Error "Python venv not found at: $Script:VenvPython"
        return
    }
    
    & $Script:VenvPython $migrationScript
}

#endregion

#region Monitoring Functions

<#
.SYNOPSIS
    Check SQL integration health.
    
.EXAMPLE
    Test-QAISQLHealth
    
.EXAMPLE
    Test-QAISQLHealth -AsJson
#>
function Test-QAISQLHealth {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [switch]$AsJson,
        
        [Parameter(Mandatory = $false)]
        [switch]$Continuous,
        
        [Parameter(Mandatory = $false)]
        [int]$Interval = 60
    )
    
    $healthScript = Join-Path $Script:ScriptRoot "scripts\sql_health_monitor.py"
    
    $params = @("--once")
    
    if ($AsJson) {
        $params += "--json"
    }
    
    if ($Continuous) {
        $params = @("--interval", $Interval)
    }
    
    & $Script:VenvPython $healthScript @params
}

<#
.SYNOPSIS
    Start continuous SQL health monitoring.
    
.EXAMPLE
    Start-QAISQLMonitoring -Interval 30
#>
function Start-QAISQLMonitoring {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [int]$Interval = 60,
        
        [Parameter(Mandatory = $false)]
        [int]$ThresholdWarning = 80,
        
        [Parameter(Mandatory = $false)]
        [int]$ThresholdCritical = 90,
        
        [Parameter(Mandatory = $false)]
        [string]$AlertWebhook
    )
    
    $healthScript = Join-Path $Script:ScriptRoot "scripts\sql_health_monitor.py"
    
    $params = @(
        "--interval", $Interval,
        "--threshold-warning", $ThresholdWarning,
        "--threshold-critical", $ThresholdCritical
    )
    
    if ($AlertWebhook) {
        $params += @("--alert-webhook", $AlertWebhook)
    }
    
    & $Script:VenvPython $healthScript @params
}

#endregion

#region Threshold Tuning Functions

<#
.SYNOPSIS
    Analyze and tune slow query thresholds.
    
.EXAMPLE
    Optimize-QAISQLThresholds -ResourceGroup "qai-rg" -FunctionAppName "qai-func"
    
.EXAMPLE
    Optimize-QAISQLThresholds -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -Apply
#>
function Optimize-QAISQLThresholds {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ResourceGroup,
        
        [Parameter(Mandatory = $true)]
        [string]$FunctionAppName,
        
        [Parameter(Mandatory = $false)]
        [int]$DaysBack = 7,
        
        [Parameter(Mandatory = $false)]
        [int]$TargetAlertsPerDay = 5,
        
        [Parameter(Mandatory = $false)]
        [switch]$Apply
    )
    
    $tuneScript = Join-Path $Script:ScriptRoot "scripts\tune_sql_thresholds.ps1"
    
    $params = @{
        ResourceGroup = $ResourceGroup
        FunctionAppName = $FunctionAppName
        DaysBack = $DaysBack
        TargetAlertsPerDay = $TargetAlertsPerDay
    }
    
    if ($Apply) {
        $params.Apply = $true
    }
    
    & $tuneScript @params
}

#endregion

#region Maintenance Functions

<#
.SYNOPSIS
    Cleanup old query metrics data.
    
.EXAMPLE
    Clear-QAISQLQueryMetrics -RetentionDays 7
    
.EXAMPLE
    Clear-QAISQLQueryMetrics -RetentionDays 30 -DryRun
#>
function Clear-QAISQLQueryMetrics {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [int]$RetentionDays = 7,
        
        [Parameter(Mandatory = $false)]
        [switch]$DryRun
    )
    
    $cleanupScript = Join-Path $Script:ScriptRoot "scripts\cleanup_query_metrics.py"
    
    $params = @("--retention-days", $RetentionDays)
    
    if ($DryRun) {
        $params += "--dry-run"
    }
    
    & $Script:VenvPython $cleanupScript @params
}

#endregion

#region Alert Management Functions

<#
.SYNOPSIS
    Deploy Azure Monitor alerts for SQL integration.
    
.EXAMPLE
    Deploy-QAISQLAlerts -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -ActionGroupName "alerts" -EmailRecipient "admin@example.com"
#>
function Deploy-QAISQLAlerts {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$ResourceGroup,
        
        [Parameter(Mandatory = $true)]
        [string]$FunctionAppName,
        
        [Parameter(Mandatory = $false)]
        [string]$ActionGroupName = "sql-alerts-action-group",
        
        [Parameter(Mandatory = $false)]
        [string]$EmailRecipient,
        
        [Parameter(Mandatory = $false)]
        [switch]$SkipActionGroup,
        
        [Parameter(Mandatory = $false)]
        [switch]$DryRun
    )
    
    $alertScript = Join-Path $Script:ScriptRoot "scripts\setup_azure_alerts.ps1"
    
    $params = @{
        ResourceGroup = $ResourceGroup
        FunctionAppName = $FunctionAppName
        ActionGroupName = $ActionGroupName
    }
    
    if ($EmailRecipient) { $params.EmailRecipient = $EmailRecipient }
    if ($SkipActionGroup) { $params.SkipActionGroup = $true }
    if ($DryRun) { $params.DryRun = $true }
    
    & $alertScript @params
}

#endregion

#region Configuration Functions

<#
.SYNOPSIS
    Set QAI SQL connection string for current session.
    
.EXAMPLE
    Set-QAISQLConnection -Url "sqlite:///./data.sqlite"
#>
function Set-QAISQLConnection {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )
    
    $env:QAI_SQL_URL = $Url
    Write-Host "SQL connection set: $Url" -ForegroundColor Green
}

<#
.SYNOPSIS
    Set slow query threshold for current session.
    
.EXAMPLE
    Set-QAISQLSlowThreshold -Milliseconds 300
#>
function Set-QAISQLSlowThreshold {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [int]$Milliseconds
    )
    
    $env:QAI_SQL_SLOW_MS = $Milliseconds
    Write-Host "Slow query threshold set: $Milliseconds ms" -ForegroundColor Green
}

<#
.SYNOPSIS
    Enable query performance tracking for current session.
    
.EXAMPLE
    Enable-QAISQLQueryTracking
#>
function Enable-QAISQLQueryTracking {
    [CmdletBinding()]
    param()
    
    $env:QAI_ENABLE_QUERY_TRACKING = "true"
    Write-Host "Query tracking enabled" -ForegroundColor Green
}

<#
.SYNOPSIS
    Disable query performance tracking for current session.
    
.EXAMPLE
    Disable-QAISQLQueryTracking
#>
function Disable-QAISQLQueryTracking {
    [CmdletBinding()]
    param()
    
    $env:QAI_ENABLE_QUERY_TRACKING = "false"
    Write-Host "Query tracking disabled" -ForegroundColor Yellow
}

#endregion

#region Testing Functions

<#
.SYNOPSIS
    Run SQL integration test suite.
    
.EXAMPLE
    Test-QAISQLIntegration
    
.EXAMPLE
    Test-QAISQLIntegration -Verbose
#>
function Test-QAISQLIntegration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [switch]$Coverage
    )
    
    $testFile = Join-Path $Script:ScriptRoot "tests\test_sql_integration.py"
    
    $params = @($testFile, "-v")
    
    if ($Coverage) {
        $params += @("--cov=shared.sql_engine", "--cov=shared.sql_repository")
    }
    
    & $Script:VenvPython -m pytest @params
}

#endregion

#region Helper Functions

<#
.SYNOPSIS
    Show SQL integration status and configuration.
    
.EXAMPLE
    Get-QAISQLStatus
#>
function Get-QAISQLStatus {
    [CmdletBinding()]
    param()
    
    Write-Host "`nQAI SQL Integration Status" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor Cyan
    
    Write-Host "`nConfiguration:" -ForegroundColor Yellow
    Write-Host "  QAI_SQL_URL: $(if ($env:QAI_SQL_URL) { $env:QAI_SQL_URL } else { 'Not set' })"
    Write-Host "  QAI_SQL_SLOW_MS: $(if ($env:QAI_SQL_SLOW_MS) { $env:QAI_SQL_SLOW_MS } else { 'Default (environment-aware)' })"
    Write-Host "  QAI_ENABLE_QUERY_TRACKING: $(if ($env:QAI_ENABLE_QUERY_TRACKING) { $env:QAI_ENABLE_QUERY_TRACKING } else { 'false' })"
    Write-Host "  AZURE_FUNCTIONS_ENVIRONMENT: $(if ($env:AZURE_FUNCTIONS_ENVIRONMENT) { $env:AZURE_FUNCTIONS_ENVIRONMENT } else { 'production (default)' })"
    
    Write-Host "`nAvailable Commands:" -ForegroundColor Yellow
    Get-Command -Module QAI-SQL | ForEach-Object {
        Write-Host "  - $($_.Name)" -ForegroundColor Green
    }
    
    Write-Host ""
}

#endregion

# Export module members
Export-ModuleMember -Function @(
    'Deploy-QAISQLIntegration',
    'Invoke-QAISQLMigrations',
    'Test-QAISQLHealth',
    'Start-QAISQLMonitoring',
    'Optimize-QAISQLThresholds',
    'Clear-QAISQLQueryMetrics',
    'Deploy-QAISQLAlerts',
    'Set-QAISQLConnection',
    'Set-QAISQLSlowThreshold',
    'Enable-QAISQLQueryTracking',
    'Disable-QAISQLQueryTracking',
    'Test-QAISQLIntegration',
    'Get-QAISQLStatus'
)
