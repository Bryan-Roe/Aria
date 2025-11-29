<#
.SYNOPSIS
    Deploy Azure Monitor alerts for SQL pool monitoring.

.DESCRIPTION
    Automates deployment of SQL pool saturation and slow query alerts using ARM templates.
    Creates Action Group if needed and validates deployment.

.PARAMETER ResourceGroup
    Azure resource group containing the Function App.

.PARAMETER FunctionAppName
    Name of the Azure Function App to monitor.

.PARAMETER ActionGroupName
    Name of the Action Group for alert notifications. Created if doesn't exist.

.PARAMETER EmailRecipient
    Email address for alert notifications.

.PARAMETER SkipActionGroup
    Skip Action Group creation (use existing).

.PARAMETER DryRun
    Validate parameters without deploying.

.EXAMPLE
    .\setup_azure_alerts.ps1 -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -ActionGroupName "sql-alerts" -EmailRecipient "admin@example.com"

.EXAMPLE
    .\setup_azure_alerts.ps1 -ResourceGroup "qai-rg" -FunctionAppName "qai-func" -SkipActionGroup -DryRun
#>

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

$ErrorActionPreference = "Stop"

# Script configuration
$TemplateFile = "$PSScriptRoot\..\config\azure_monitor_alerts.json"
$SubscriptionId = $null
$ActionGroupId = $null

function Write-StepHeader {
    param([string]$Message)
    Write-Host "`n===================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "===================================`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Test-AzureCliInstalled {
    try {
        $version = az --version | Select-Object -First 1
        Write-Success "Azure CLI installed: $version"
        return $true
    }
    catch {
        Write-Error "Azure CLI not installed. Install from: https://aka.ms/installazurecliwindows"
        return $false
    }
}

function Test-AzureLogin {
    try {
        $account = az account show 2>$null | ConvertFrom-Json
        if ($account) {
            Write-Success "Logged in as: $($account.user.name)"
            Write-Success "Subscription: $($account.name) ($($account.id))"
            $script:SubscriptionId = $account.id
            return $true
        }
    }
    catch {
        Write-Error "Not logged in to Azure. Run: az login"
        return $false
    }
}

function Test-ResourceGroupExists {
    try {
        $rg = az group show --name $ResourceGroup 2>$null | ConvertFrom-Json
        if ($rg) {
            Write-Success "Resource group exists: $($rg.name) ($($rg.location))"
            return $true
        }
    }
    catch {
        Write-Error "Resource group '$ResourceGroup' not found"
        return $false
    }
}

function Test-FunctionAppExists {
    try {
        $app = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
        if ($app) {
            Write-Success "Function App exists: $($app.name)"
            
            # Check Application Insights
            if ($app.properties.instrumentationKey) {
                Write-Success "Application Insights enabled"
            }
            else {
                Write-Warning "Application Insights not configured. Alerts may not work correctly."
            }
            return $true
        }
    }
    catch {
        Write-Error "Function App '$FunctionAppName' not found in resource group '$ResourceGroup'"
        return $false
    }
}

function Get-OrCreateActionGroup {
    if ($SkipActionGroup) {
        # Try to find existing Action Group
        $existingGroups = az monitor action-group list --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
        if ($existingGroups -and $existingGroups.Count -gt 0) {
            $ag = $existingGroups | Where-Object { $_.name -eq $ActionGroupName } | Select-Object -First 1
            if ($ag) {
                $script:ActionGroupId = $ag.id
                Write-Success "Using existing Action Group: $($ag.name)"
                return $true
            }
            else {
                Write-Warning "Action Group '$ActionGroupName' not found. Available groups:"
                $existingGroups | ForEach-Object { Write-Host "  - $($_.name)" }
                return $false
            }
        }
        else {
            Write-Error "No Action Groups found in resource group"
            return $false
        }
    }

    # Check if Action Group already exists
    $existingAg = az monitor action-group show --name $ActionGroupName --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
    if ($existingAg) {
        $script:ActionGroupId = $existingAg.id
        Write-Success "Action Group already exists: $($existingAg.name)"
        return $true
    }

    # Create new Action Group
    if (-not $EmailRecipient) {
        Write-Error "EmailRecipient required to create new Action Group"
        return $false
    }

    Write-Host "Creating Action Group: $ActionGroupName"
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create Action Group with email: $EmailRecipient"
        $script:ActionGroupId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Insights/actionGroups/$ActionGroupName"
        return $true
    }

    try {
        $newAg = az monitor action-group create `
            --name $ActionGroupName `
            --resource-group $ResourceGroup `
            --short-name "sqlalertsql" `
            --action email admin $EmailRecipient `
            2>&1 | ConvertFrom-Json

        if ($newAg) {
            $script:ActionGroupId = $newAg.id
            Write-Success "Action Group created: $($newAg.name)"
            return $true
        }
    }
    catch {
        Write-Error "Failed to create Action Group: $_"
        return $false
    }
}

function Deploy-AlertRules {
    Write-Host "Deploying alert rules from: $TemplateFile"

    if (-not (Test-Path $TemplateFile)) {
        Write-Error "ARM template not found: $TemplateFile"
        return $false
    }

    if ($DryRun) {
        Write-Host "[DRY RUN] Would deploy ARM template with parameters:"
        Write-Host "  functionAppName: $FunctionAppName"
        Write-Host "  actionGroupId: $ActionGroupId"
        return $true
    }

    try {
        $deployment = az deployment group create `
            --resource-group $ResourceGroup `
            --template-file $TemplateFile `
            --parameters functionAppName=$FunctionAppName actionGroupId=$ActionGroupId `
            --output json 2>&1 | ConvertFrom-Json

        if ($deployment.properties.provisioningState -eq "Succeeded") {
            Write-Success "Deployment succeeded"
            
            # Display outputs
            if ($deployment.properties.outputs) {
                Write-Host "`nDeployed Alert Rules:"
                $deployment.properties.outputs.PSObject.Properties | ForEach-Object {
                    Write-Host "  - $($_.Name): $($_.Value.value)"
                }
            }
            return $true
        }
        else {
            Write-Error "Deployment failed: $($deployment.properties.provisioningState)"
            return $false
        }
    }
    catch {
        Write-Error "Deployment error: $_"
        return $false
    }
}

function Show-AlertPortalLinks {
    $portalBase = "https://portal.azure.com/#@/resource"
    $rgPath = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup"
    
    Write-Host "`nAzure Portal Links:"
    Write-Host "  Metric Alerts: $portalBase$rgPath/providers/Microsoft.Insights/metricAlerts" -ForegroundColor Cyan
    Write-Host "  Query Alerts: $portalBase$rgPath/providers/Microsoft.Insights/scheduledQueryRules" -ForegroundColor Cyan
    Write-Host "  Action Group: $portalBase$ActionGroupId" -ForegroundColor Cyan
}

function Test-Deployment {
    Write-Host "Validating alert deployment..."

    # List metric alerts
    $metricAlerts = az monitor metrics alert list --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
    $sqlMetricAlerts = $metricAlerts | Where-Object { $_.name -like "*$FunctionAppName*sql*" }
    
    if ($sqlMetricAlerts) {
        Write-Success "Found $($sqlMetricAlerts.Count) metric alert(s)"
        $sqlMetricAlerts | ForEach-Object {
            Write-Host "  - $($_.name) (Severity: $($_.severity))"
        }
    }
    else {
        Write-Warning "No SQL metric alerts found"
    }

    # List scheduled query rules
    $queryAlerts = az monitor scheduled-query list --resource-group $ResourceGroup 2>$null | ConvertFrom-Json
    $sqlQueryAlerts = $queryAlerts | Where-Object { $_.name -like "*$FunctionAppName*sql*" }
    
    if ($sqlQueryAlerts) {
        Write-Success "Found $($sqlQueryAlerts.Count) query alert(s)"
        $sqlQueryAlerts | ForEach-Object {
            Write-Host "  - $($_.name) (Severity: $($_.severity))"
        }
    }
    else {
        Write-Warning "No SQL query alerts found"
    }
}

# ========================================
# Main Execution
# ========================================

Write-StepHeader "Azure SQL Alerts Setup"

Write-Host "Configuration:"
Write-Host "  Resource Group: $ResourceGroup"
Write-Host "  Function App: $FunctionAppName"
Write-Host "  Action Group: $ActionGroupName"
if ($EmailRecipient) {
    Write-Host "  Email: $EmailRecipient"
}
Write-Host "  Mode: $(if ($DryRun) { 'DRY RUN' } else { 'DEPLOY' })"
Write-Host ""

# Pre-flight checks
Write-StepHeader "Pre-flight Checks"

if (-not (Test-AzureCliInstalled)) { exit 1 }
if (-not (Test-AzureLogin)) { exit 1 }
if (-not (Test-ResourceGroupExists)) { exit 1 }
if (-not (Test-FunctionAppExists)) { exit 1 }

# Action Group setup
Write-StepHeader "Action Group Setup"

if (-not (Get-OrCreateActionGroup)) {
    Write-Error "Action Group setup failed"
    exit 1
}

# Deploy alerts
Write-StepHeader "Deploying Alert Rules"

if (-not (Deploy-AlertRules)) {
    Write-Error "Alert deployment failed"
    exit 1
}

if (-not $DryRun) {
    # Validate deployment
    Write-StepHeader "Validation"
    Test-Deployment

    # Show portal links
    Show-AlertPortalLinks
}

Write-StepHeader "Setup Complete"

Write-Host @"

Next Steps:
1. Verify alerts in Azure Portal (links above)
2. Test alerts by triggering saturation or slow queries
3. Configure additional notification channels (SMS, webhook) if needed
4. Review KQL queries in Application Insights
5. Tune thresholds based on baseline metrics (see AZURE_MONITOR_SQL_SETUP.md)

"@ -ForegroundColor Green

if ($DryRun) {
    Write-Warning "This was a DRY RUN. Re-run without -DryRun to deploy."
}
