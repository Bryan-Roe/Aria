# Quick Azure ML Setup for Phi-3.6 Training
# This script sets up everything needed for Azure ML training

param(
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "rg-phi36-ml",
    
    [Parameter(Mandatory=$false)]
    [string]$WorkspaceName = "phi36-ml-workspace",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDatasetUpload
)

$ErrorActionPreference = "Stop"

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*69) -ForegroundColor Cyan
Write-Host "  Azure ML Setup for Phi-3.6 LoRA Training" -ForegroundColor Yellow
Write-Host ("="*70) -ForegroundColor Cyan

# Check if Azure CLI is installed
Write-Host "`n[1/7] Checking Azure CLI..." -ForegroundColor Green
try {
    $azVersion = az --version 2>&1 | Select-String "azure-cli"
    Write-Host "  ✓ Azure CLI installed: $azVersion" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Azure CLI not found!" -ForegroundColor Red
    Write-Host "  Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "`n[2/7] Checking Azure authentication..." -ForegroundColor Green
try {
    $account = az account show 2>&1 | ConvertFrom-Json
    Write-Host "  ✓ Logged in as: $($account.user.name)" -ForegroundColor Gray
} catch {
    Write-Host "  ! Not logged in. Launching login..." -ForegroundColor Yellow
    az login
}

# Set subscription
Write-Host "`n[3/7] Setting subscription..." -ForegroundColor Green
az account set --subscription $SubscriptionId
$sub = az account show | ConvertFrom-Json
Write-Host "  ✓ Using subscription: $($sub.name)" -ForegroundColor Gray

# Create resource group
Write-Host "`n[4/7] Creating resource group..." -ForegroundColor Green
$rgExists = az group exists --name $ResourceGroup | ConvertFrom-Json
if ($rgExists) {
    Write-Host "  ✓ Resource group exists: $ResourceGroup" -ForegroundColor Gray
} else {
    az group create --name $ResourceGroup --location $Location | Out-Null
    Write-Host "  ✓ Resource group created: $ResourceGroup" -ForegroundColor Gray
}

# Create ML workspace
Write-Host "`n[5/7] Creating ML workspace..." -ForegroundColor Green
$wsExists = az ml workspace show --name $WorkspaceName --resource-group $ResourceGroup 2>$null
if ($wsExists) {
    Write-Host "  ✓ Workspace exists: $WorkspaceName" -ForegroundColor Gray
} else {
    Write-Host "  Creating workspace (this may take 2-3 minutes)..." -ForegroundColor Yellow
    az ml workspace create `
        --name $WorkspaceName `
        --resource-group $ResourceGroup `
        --location $Location | Out-Null
    Write-Host "  ✓ Workspace created: $WorkspaceName" -ForegroundColor Gray
}

# Install Python dependencies
Write-Host "`n[6/7] Installing Python dependencies..." -ForegroundColor Green
if (Test-Path ".\azure-requirements.txt") {
    pip install -r .\azure-requirements.txt --quiet
    Write-Host "  ✓ Azure ML SDK installed" -ForegroundColor Gray
} else {
    Write-Host "  ! azure-requirements.txt not found, skipping" -ForegroundColor Yellow
}

# Setup compute and environment
Write-Host "`n[7/7] Setting up compute cluster and environment..." -ForegroundColor Green
python azure_ml_training.py `
    --action setup `
    --subscription-id $SubscriptionId `
    --resource-group $ResourceGroup `
    --workspace-name $WorkspaceName `
    --vm-size Standard_NC6s_v3

Write-Host "`n" -NoNewline
Write-Host ("="*70) -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host ("="*70) -ForegroundColor Cyan

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Upload dataset:" -ForegroundColor White
Write-Host "     python azure_ml_training.py --action upload ``" -ForegroundColor Gray
Write-Host "       --subscription-id $SubscriptionId ``" -ForegroundColor Gray
Write-Host "       --resource-group $ResourceGroup ``" -ForegroundColor Gray
Write-Host "       --workspace-name $WorkspaceName" -ForegroundColor Gray

Write-Host "`n  2. Start training:" -ForegroundColor White
Write-Host "     python azure_ml_training.py --action train ``" -ForegroundColor Gray
Write-Host "       --subscription-id $SubscriptionId ``" -ForegroundColor Gray
Write-Host "       --resource-group $ResourceGroup ``" -ForegroundColor Gray
Write-Host "       --workspace-name $WorkspaceName ``" -ForegroundColor Gray
Write-Host "       --max-train-samples 64  # Quick test" -ForegroundColor Gray

Write-Host "`n  3. Monitor at:" -ForegroundColor White
Write-Host "     https://ml.azure.com/" -ForegroundColor Cyan

if (-not $SkipDatasetUpload) {
    Write-Host "`n  ! Remember to upload dataset before training" -ForegroundColor Yellow
}

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  Subscription: $SubscriptionId" -ForegroundColor Gray
Write-Host "  Resource Group: $ResourceGroup" -ForegroundColor Gray
Write-Host "  Workspace: $WorkspaceName" -ForegroundColor Gray
Write-Host "  Location: $Location" -ForegroundColor Gray
Write-Host "  Compute: phi36-gpu-cluster (Standard_NC6s_v3, 1x V100)" -ForegroundColor Gray

Write-Host "`n" -NoNewline
Write-Host ("="*70) -ForegroundColor Cyan
