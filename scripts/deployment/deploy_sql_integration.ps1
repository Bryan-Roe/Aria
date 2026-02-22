<#
.SYNOPSIS
    Master deployment script for SQL integration with automated testing and monitoring setup.

.DESCRIPTION
    Orchestrates the complete SQL integration deployment including:
    - Environment validation
    - Database migrations
    - Test execution
    - Azure alert deployment
    - Health verification
    - Documentation generation

.PARAMETER Environment
    Target environment: Local, Staging, Production

.PARAMETER ResourceGroup
    Azure resource group (required for Staging/Production)

.PARAMETER FunctionAppName
    Azure Function App name (required for Staging/Production)

.PARAMETER EmailRecipient
    Email for alert notifications (required for Production)

.PARAMETER SkipTests
    Skip test execution (not recommended for Production)

.PARAMETER SkipAlerts
    Skip Azure alert deployment

.PARAMETER DryRun
    Validate without deploying

.EXAMPLE
    .\deploy_sql_integration.ps1 -Environment Local

.EXAMPLE
    .\deploy_sql_integration.ps1 -Environment Production -ResourceGroup "qai-prod-rg" -FunctionAppName "qai-prod-func" -EmailRecipient "alerts@example.com"
#>

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

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ScriptRoot "venv\Scripts\python.exe"
$DeploymentLog = Join-Path $ScriptRoot "data_out\sql_deployment_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
$StatusFile = Join-Path $ScriptRoot "data_out\sql_deployment_status.json"

# Ensure output directory exists
$null = New-Item -ItemType Directory -Force -Path (Join-Path $ScriptRoot "data_out")

function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Console output with colors
    switch ($Level) {
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        default { Write-Host $logMessage }
    }
    
    # File output
    Add-Content -Path $DeploymentLog -Value $logMessage
}

function Write-StepHeader {
    param([string]$Message)
    $separator = "=" * 60
    Write-Log ""
    Write-Log $separator "INFO"
    Write-Log $Message "INFO"
    Write-Log $separator "INFO"
}

function Test-Prerequisites {
    Write-StepHeader "Step 1: Validating Prerequisites"
    
    $errors = @()
    
    # Check Python venv
    if (-not (Test-Path $VenvPython)) {
        $errors += "Python venv not found at: $VenvPython"
    } else {
        Write-Log "[OK] Python venv found" "SUCCESS"
    }
    
    # Check required Python packages
    $requiredPackages = @("sqlalchemy", "pytest")
    foreach ($package in $requiredPackages) {
        $result = & $VenvPython -m pip show $package 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "[OK] Python package '$package' installed" "SUCCESS"
        } else {
            $errors += "Python package '$package' not installed"
        }
    }
    
    # Check Azure CLI for cloud environments
    if ($Environment -ne "Local") {
        try {
            $null = az --version 2>&1
            Write-Log "[OK] Azure CLI installed" "SUCCESS"
            
            # Check Azure login
            $account = az account show 2>$null | ConvertFrom-Json
            if ($account) {
                Write-Log "[OK] Logged in to Azure as: $($account.user.name)" "SUCCESS"
            } else {
                $errors += "Not logged in to Azure. Run: az login"
            }
        } catch {
            $errors += "Azure CLI not installed or not in PATH"
        }
        
        # Validate required parameters
        if (-not $ResourceGroup) {
            $errors += "ResourceGroup parameter required for $Environment environment"
        }
        if (-not $FunctionAppName) {
            $errors += "FunctionAppName parameter required for $Environment environment"
        }
        if ($Environment -eq "Production" -and -not $EmailRecipient -and -not $SkipAlerts) {
            $errors += "EmailRecipient parameter required for Production alerts"
        }
    }
    
    # Check required scripts
    $requiredScripts = @(
        "scripts\sql_migrate.py",
        "tests\test_sql_integration.py"
    )
    
    if ($Environment -ne "Local" -and -not $SkipAlerts) {
        $requiredScripts += "scripts\setup_azure_alerts.ps1"
    }
    
    foreach ($script in $requiredScripts) {
        $scriptPath = Join-Path $ScriptRoot $script
        if (Test-Path $scriptPath) {
            Write-Log "[OK] Found: $script" "SUCCESS"
        } else {
            $errors += "Missing required script: $script"
        }
    }
    
    if ($errors.Count -gt 0) {
        Write-Log "Prerequisites validation failed:" "ERROR"
        foreach ($error in $errors) {
            Write-Log "  - $error" "ERROR"
        }
        return $false
    }
    
    Write-Log "All prerequisites validated successfully" "SUCCESS"
    return $true
}

function Set-EnvironmentVariables {
    Write-StepHeader "Step 2: Configuring Environment"
    
    # Set environment-specific variables
    switch ($Environment) {
        "Local" {
            if (-not $env:QAI_SQL_URL) {
                $env:QAI_SQL_URL = "sqlite:///./data_out/qai_local.sqlite"
                Write-Log "Set QAI_SQL_URL to local SQLite" "INFO"
            }
            $env:AZURE_FUNCTIONS_ENVIRONMENT = "development"
            $env:QAI_SQL_SLOW_MS = "100"
        }
        "Staging" {
            $env:AZURE_FUNCTIONS_ENVIRONMENT = "staging"
            $env:QAI_SQL_SLOW_MS = "300"
        }
        "Production" {
            $env:AZURE_FUNCTIONS_ENVIRONMENT = "production"
            $env:QAI_SQL_SLOW_MS = "500"
        }
    }
    
    Write-Log "Environment: $Environment" "INFO"
    Write-Log "AZURE_FUNCTIONS_ENVIRONMENT: $env:AZURE_FUNCTIONS_ENVIRONMENT" "INFO"
    Write-Log "QAI_SQL_SLOW_MS: $env:QAI_SQL_SLOW_MS" "INFO"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would configure environment variables" "WARNING"
    }
    
    return $true
}

function Invoke-DatabaseMigrations {
    Write-StepHeader "Step 3: Running Database Migrations"
    
    $migrationScript = Join-Path $ScriptRoot "scripts\sql_migrate.py"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would run migrations from: $migrationScript" "WARNING"
        return $true
    }
    
    try {
        Write-Log "Executing: python $migrationScript" "INFO"
        $output = & $VenvPython $migrationScript 2>&1
        $exitCode = $LASTEXITCODE
        
        # Log output
        $output | ForEach-Object { Write-Log $_ "INFO" }
        
        if ($exitCode -eq 0) {
            Write-Log "Migrations completed successfully" "SUCCESS"
            return $true
        } else {
            Write-Log "Migrations failed with exit code: $exitCode" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Migration execution failed: $_" "ERROR"
        return $false
    }
}

function Invoke-Tests {
    Write-StepHeader "Step 4: Running Test Suite"
    
    if ($SkipTests) {
        Write-Log "Tests skipped (-SkipTests flag)" "WARNING"
        return $true
    }
    
    $testFile = Join-Path $ScriptRoot "tests\test_sql_integration.py"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would run tests: pytest $testFile -v" "WARNING"
        return $true
    }
    
    try {
        Write-Log "Executing: pytest $testFile -v" "INFO"
        $output = & $VenvPython -m pytest $testFile -v --tb=short 2>&1
        $exitCode = $LASTEXITCODE
        
        # Log output
        $output | ForEach-Object { Write-Log $_ "INFO" }
        
        if ($exitCode -eq 0) {
            Write-Log "All tests passed" "SUCCESS"
            return $true
        } else {
            Write-Log "Tests failed with exit code: $exitCode" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Test execution failed: $_" "ERROR"
        return $false
    }
}

function Deploy-AzureAlerts {
    Write-StepHeader "Step 5: Deploying Azure Monitor Alerts"
    
    if ($Environment -eq "Local") {
        Write-Log "Skipping alert deployment for Local environment" "INFO"
        return $true
    }
    
    if ($SkipAlerts) {
        Write-Log "Alert deployment skipped (-SkipAlerts flag)" "WARNING"
        return $true
    }
    
    $alertScript = Join-Path $ScriptRoot "scripts\setup_azure_alerts.ps1"
    
    $params = @{
        ResourceGroup = $ResourceGroup
        FunctionAppName = $FunctionAppName
        ActionGroupName = "sql-alerts-$Environment"
    }
    
    if ($EmailRecipient) {
        $params.EmailRecipient = $EmailRecipient
    } else {
        $params.SkipActionGroup = $true
    }
    
    if ($DryRun) {
        $params.DryRun = $true
    }
    
    try {
        Write-Log "Executing: setup_azure_alerts.ps1 with parameters" "INFO"
        & $alertScript @params
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Alert deployment completed successfully" "SUCCESS"
            return $true
        } else {
            Write-Log "Alert deployment failed with exit code: $LASTEXITCODE" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Alert deployment failed: $_" "ERROR"
        return $false
    }
}

function Test-HealthEndpoint {
    Write-StepHeader "Step 6: Verifying Health Endpoint"
    
    if ($DryRun) {
        Write-Log "[DRY RUN] Would verify health endpoint" "WARNING"
        return $true
    }
    
    $baseUrl = if ($Environment -eq "Local") {
        "http://localhost:7071"
    } else {
        "https://$FunctionAppName.azurewebsites.net"
    }
    
    $statusUrl = "$baseUrl/api/ai/status"
    
    try {
        Write-Log "Checking health endpoint: $statusUrl" "INFO"
        
        if ($Environment -eq "Local") {
            # For local, just log the URL (function app may not be running)
            Write-Log "Local health check URL: $statusUrl" "INFO"
            Write-Log "Start Function App with: func host start" "INFO"
            return $true
        }
        
        # For cloud environments, attempt to call the endpoint
        $response = Invoke-RestMethod -Uri $statusUrl -Method Get -TimeoutSec 30 -ErrorAction Stop
        
        if ($response.sql) {
            Write-Log "[OK] SQL health data present in status endpoint" "SUCCESS"
            
            if ($response.sql.healthy) {
                Write-Log "[OK] SQL connection healthy" "SUCCESS"
            } else {
                Write-Log "⚠ SQL connection unhealthy: $($response.sql.message)" "WARNING"
            }
            
            if ($response.sql.pool) {
                Write-Log "[OK] Pool metrics available: size=$($response.sql.pool.size), saturation=$($response.sql.pool.saturation_pct)%" "SUCCESS"
            }
            
            return $true
        } else {
            Write-Log "⚠ SQL data not present in status endpoint" "WARNING"
            return $true  # Not a failure, just not configured
        }
    } catch {
        Write-Log "Health endpoint check failed: $_" "WARNING"
        return $true  # Don't fail deployment on health check issues
    }
}

function Save-DeploymentStatus {
    param(
        [bool]$Success,
        [hashtable]$Steps
    )
    
    $status = @{
        timestamp = (Get-Date -Format "o")
        environment = $Environment
        success = $Success
        dryRun = $DryRun.IsPresent
        steps = $Steps
        resourceGroup = $ResourceGroup
        functionAppName = $FunctionAppName
        logFile = $DeploymentLog
    }
    
    $status | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusFile
    Write-Log "Deployment status saved to: $StatusFile" "INFO"
}

function Show-DeploymentSummary {
    param(
        [bool]$Success,
        [hashtable]$Steps
    )
    
    Write-StepHeader "Deployment Summary"
    
    Write-Log "Environment: $Environment" "INFO"
    Write-Log "Overall Status: $(if ($Success) { 'SUCCESS' } else { 'FAILED' })" $(if ($Success) { "SUCCESS" } else { "ERROR" })
    Write-Log ""
    Write-Log "Step Results:" "INFO"
    
    foreach ($step in $Steps.GetEnumerator() | Sort-Object Name) {
        $status = if ($step.Value) { "[PASS]" } else { "[FAIL]" }
        $level = if ($step.Value) { "SUCCESS" } else { "ERROR" }
        Write-Log "  $status - $($step.Name)" $level
    }
    
    Write-Log ""
    Write-Log "Log file: $DeploymentLog" "INFO"
    Write-Log "Status file: $StatusFile" "INFO"
    
    if ($Success -and -not $DryRun) {
        Write-Log ""
        Write-Log "Next Steps:" "INFO"
        
        if ($Environment -eq "Local") {
            Write-Log "  1. Start Function App: func host start" "INFO"
            Write-Log "  2. Check status: Invoke-RestMethod http://localhost:7071/api/ai/status" "INFO"
        } else {
            Write-Log "  1. Monitor Application Insights for alerts" "INFO"
            Write-Log "  2. Review KQL queries in: AZURE_MONITOR_SQL_SETUP.md" "INFO"
            Write-Log "  3. Baseline collection period: 7 days" "INFO"
            Write-Log "  4. Tune thresholds based on P95 metrics" "INFO"
        }
    }
    
    if ($DryRun) {
        Write-Log ""
        Write-Log "This was a DRY RUN. Re-run without -DryRun to deploy." "WARNING"
    }
}

# ========================================
# Main Execution
# ========================================

Write-Log "========================================" "INFO"
Write-Log "SQL Integration Deployment Automation" "INFO"
Write-Log "========================================" "INFO"
Write-Log "Started: $(Get-Date)" "INFO"
Write-Log "Environment: $Environment" "INFO"
Write-Log "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'DEPLOY' })" "INFO"

$steps = @{}
$overallSuccess = $true

try {
    # Step 1: Prerequisites
    $steps["Prerequisites"] = Test-Prerequisites
    if (-not $steps["Prerequisites"]) {
        throw "Prerequisites validation failed"
    }
    
    # Step 2: Environment Configuration
    $steps["Environment"] = Set-EnvironmentVariables
    if (-not $steps["Environment"]) {
        throw "Environment configuration failed"
    }
    
    # Step 3: Database Migrations
    $steps["Migrations"] = Invoke-DatabaseMigrations
    if (-not $steps["Migrations"]) {
        throw "Database migrations failed"
    }
    
    # Step 4: Tests
    $steps["Tests"] = Invoke-Tests
    if (-not $steps["Tests"] -and $Environment -eq "Production" -and -not $SkipTests) {
        throw "Tests failed - blocking Production deployment"
    }
    
    # Step 5: Azure Alerts (if applicable)
    if ($Environment -ne "Local" -and -not $SkipAlerts) {
        $steps["Alerts"] = Deploy-AzureAlerts
        if (-not $steps["Alerts"]) {
            Write-Log "Alert deployment failed but continuing..." "WARNING"
        }
    } else {
        $steps["Alerts"] = $true  # N/A
    }
    
    # Step 6: Health Check
    $steps["Health"] = Test-HealthEndpoint
    
    # Determine overall success
    $overallSuccess = ($steps.Values | Where-Object { $_ -eq $false }).Count -eq 0
    
} catch {
    Write-Log "Deployment failed with exception: $_" "ERROR"
    Write-Log $_.ScriptStackTrace "ERROR"
    $overallSuccess = $false
} finally {
    # Save status and show summary
    Save-DeploymentStatus -Success $overallSuccess -Steps $steps
    Show-DeploymentSummary -Success $overallSuccess -Steps $steps
    
    Write-Log ""
    Write-Log "Completed: $(Get-Date)" "INFO"
    
    # Exit with appropriate code
    if ($overallSuccess) {
        exit 0
    } else {
        exit 1
    }
}
