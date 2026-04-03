param(
    [string]$SubscriptionId = "a07fbd16-e722-446d-8efd-0681e85b725c",
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$Location = "eastus",
    [string]$WorkspaceName = "quantum-ai-workspace"
)

Write-Host "Azure Quantum Deployment" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan

# Refresh PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Set subscription
Write-Host "`nSetting subscription..." -ForegroundColor Yellow
az account set --subscription $SubscriptionId

if ($LASTEXITCODE -eq 0) {
    Write-Host "Subscription set successfully" -ForegroundColor Green
} else {
    Write-Host "Failed to set subscription" -ForegroundColor Red
    exit 1
}

# Create resource group
Write-Host "`nCreating resource group: $ResourceGroup" -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output table

if ($LASTEXITCODE -eq 0) {
    Write-Host "Resource group created/verified" -ForegroundColor Green
} else {
    Write-Host "Warning: Resource group creation had issues" -ForegroundColor Yellow
}

# Create storage account for quantum workspace
$storageAccountName = "quantumstorage$(Get-Random -Maximum 9999)"
Write-Host "`nCreating storage account: $storageAccountName" -ForegroundColor Yellow

az storage account create `
    --name $storageAccountName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku Standard_LRS `
    --output table

# Create quantum workspace
Write-Host "`nCreating Azure Quantum workspace: $WorkspaceName" -ForegroundColor Yellow

az quantum workspace create `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName `
    --location $Location `
    --storage-account "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/$storageAccountName" `
    --output table

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nQuantum workspace created successfully!" -ForegroundColor Green
} else {
    Write-Host "`nWorkspace creation failed - it may already exist" -ForegroundColor Yellow
    Write-Host "Checking existing workspace..." -ForegroundColor Yellow

    az quantum workspace show `
        --resource-group $ResourceGroup `
        --workspace-name $WorkspaceName `
        --output table
}

# Set workspace context
Write-Host "`nSetting quantum workspace context..." -ForegroundColor Yellow
az quantum workspace set `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName

# List available providers
Write-Host "`nListing quantum providers..." -ForegroundColor Yellow
az quantum offerings list --location $Location --output table

# Update config file
Write-Host "`nUpdating configuration file..." -ForegroundColor Yellow
$configPath = ".\config\quantum_config.yaml"

if (Test-Path $configPath) {
    $config = Get-Content $configPath -Raw
    $config = $config -replace "subscription_id: ''", "subscription_id: '$SubscriptionId'"
    $config = $config -replace "subscription_id: '.*'", "subscription_id: '$SubscriptionId'"
    $config = $config -replace "n_qubits: \d+", "n_qubits: 8"
    $config = $config -replace "n_layers: \d+", "n_layers: 4"
    $config | Set-Content $configPath
    Write-Host "Configuration updated" -ForegroundColor Green
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nResources Created:" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "  Quantum Workspace: $WorkspaceName" -ForegroundColor White
Write-Host "  Location: $Location" -ForegroundColor White
Write-Host "  Storage: $storageAccountName" -ForegroundColor White
Write-Host "  Subscription: $SubscriptionId" -ForegroundColor White

Write-Host "`nConfiguration:" -ForegroundColor White
Write-Host "  Qubits: 8 (enhanced)" -ForegroundColor White
Write-Host "  Layers: 4 (optimized)" -ForegroundColor White

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Test locally: python src\quantum_classifier_enhanced.py" -ForegroundColor White
Write-Host "  2. Test on Azure: python test_azure_quantum.py" -ForegroundColor White
Write-Host "  3. View in portal: https://portal.azure.com" -ForegroundColor White

Write-Host "`nDeployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
