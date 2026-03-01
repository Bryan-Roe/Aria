# Azure Quantum Workspace Verification Script
# Detects existing workspace and updates local configuration

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace"
)

Write-Host "`n== Azure Quantum Workspace Verification ==" -ForegroundColor Cyan

# Ensure Azure CLI is available
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Azure CLI not found in PATH" -ForegroundColor Red
    exit 1
}

# Check login
Write-Host "Checking Azure login..." -ForegroundColor Yellow
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Host "Not logged in. Running device code login..." -ForegroundColor Yellow
    az login --use-device-code
    $account = az account show | ConvertFrom-Json
}

Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host "Subscription: $($account.name) ($($account.id))" -ForegroundColor Green

# Check if resource group exists
Write-Host "`nChecking resource group '$ResourceGroup'..." -ForegroundColor Yellow
$rg = az group show --name $ResourceGroup 2>$null | ConvertFrom-Json
if (-not $rg) {
    Write-Host "ERROR: Resource group '$ResourceGroup' not found." -ForegroundColor Red
    Write-Host "Please create the workspace via Azure Portal first." -ForegroundColor Yellow
    Write-Host "See PORTAL_CREATION_GUIDE.md for instructions." -ForegroundColor Yellow
    exit 1
}
Write-Host "Resource group found: $($rg.location)" -ForegroundColor Green

# Check if workspace exists
Write-Host "Checking workspace '$WorkspaceName'..." -ForegroundColor Yellow
$workspace = az quantum workspace show `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName `
    --output json 2>$null | ConvertFrom-Json

if (-not $workspace) {
    Write-Host "ERROR: Workspace '$WorkspaceName' not found in resource group '$ResourceGroup'." -ForegroundColor Red
    Write-Host "`nPlease create the workspace via Azure Portal:" -ForegroundColor Yellow
    Write-Host "  1. Go to: https://portal.azure.com" -ForegroundColor Cyan
    Write-Host "  2. Create a resource → Search 'Azure Quantum'" -ForegroundColor Cyan
    Write-Host "  3. Use Quick Create with:" -ForegroundColor Cyan
    Write-Host "     - Resource Group: $ResourceGroup" -ForegroundColor Cyan
    Write-Host "     - Workspace Name: $WorkspaceName" -ForegroundColor Cyan
    Write-Host "     - Region: East US" -ForegroundColor Cyan
    Write-Host "`nSee PORTAL_CREATION_GUIDE.md for detailed steps." -ForegroundColor Yellow
    exit 1
}

Write-Host "Workspace found!" -ForegroundColor Green
Write-Host "  Location: $($workspace.location)" -ForegroundColor Cyan
Write-Host "  ID: $($workspace.id)" -ForegroundColor Cyan

# Get storage account
$storageAccountId = $workspace.storageAccount
$storageAccountName = ($storageAccountId -split '/')[-1]
Write-Host "  Storage: $storageAccountName" -ForegroundColor Cyan

# List providers
Write-Host "`nListing providers..." -ForegroundColor Yellow
$providers = az quantum workspace show `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName `
    --query 'providers[].{id:providerId,sku:providerSku}' `
    --output json | ConvertFrom-Json

if ($providers -and $providers.Count -gt 0) {
    Write-Host "Configured providers:" -ForegroundColor Green
    foreach ($p in $providers) {
        Write-Host "  - $($p.id) ($($p.sku))" -ForegroundColor Cyan
    }
} else {
    Write-Host "WARNING: No providers configured." -ForegroundColor Yellow
    Write-Host "Add providers via Azure Portal → Workspace → Providers tab" -ForegroundColor Yellow
}

# Update config/quantum_config.yaml
Write-Host "`nUpdating config/quantum_config.yaml..." -ForegroundColor Yellow
$configPath = Join-Path $PSScriptRoot "config\quantum_config.yaml"

if (-not (Test-Path $configPath)) {
    Write-Host "ERROR: Config file not found at $configPath" -ForegroundColor Red
    exit 1
}

# Read existing config
$configContent = Get-Content $configPath -Raw

# Update fields
$configContent = $configContent -replace 'subscription_id:\s*.*', "subscription_id: $($account.id)"
$configContent = $configContent -replace 'resource_group:\s*.*', "resource_group: $ResourceGroup"
$configContent = $configContent -replace 'workspace_name:\s*.*', "workspace_name: $WorkspaceName"
$configContent = $configContent -replace 'location:\s*.*', "location: $($workspace.location)"

# Write updated config
Set-Content -Path $configPath -Value $configContent -NoNewline
Write-Host "Config updated successfully!" -ForegroundColor Green

# Display config summary
Write-Host "`n=== Configuration Summary ===" -ForegroundColor Cyan
Write-Host "subscription_id: $($account.id)" -ForegroundColor White
Write-Host "resource_group: $ResourceGroup" -ForegroundColor White
Write-Host "workspace_name: $WorkspaceName" -ForegroundColor White
Write-Host "location: $($workspace.location)" -ForegroundColor White
Write-Host "storage_account: $storageAccountName" -ForegroundColor White

# Test connection
Write-Host "`nTesting workspace connection..." -ForegroundColor Yellow
$targets = az quantum target list `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName `
    --location $workspace.location `
    --output json 2>$null | ConvertFrom-Json

if ($targets -and $targets.Count -gt 0) {
    Write-Host "Connection successful! Available targets:" -ForegroundColor Green
    $targets | Select-Object -First 5 | ForEach-Object {
        Write-Host "  - $($_.id)" -ForegroundColor Cyan
    }
    if ($targets.Count -gt 5) {
        Write-Host "  ... and $($targets.Count - 5) more" -ForegroundColor Cyan
    }
} else {
    Write-Host "WARNING: No targets available." -ForegroundColor Yellow
    Write-Host "This might indicate provider configuration issues." -ForegroundColor Yellow
}

Write-Host "`n=== Workspace Ready! ===" -ForegroundColor Green
Write-Host "You can now run quantum programs:" -ForegroundColor White
Write-Host "  python src\quantum_classifier.py  # Local simulation" -ForegroundColor Cyan
Write-Host "  python src\azure_quantum_integration.py  # Azure Quantum jobs" -ForegroundColor Cyan
Write-Host "`n"
