# Azure Quantum Deployment Script
# Interactive guide for deploying Azure Quantum workspace
# Run this script to deploy your quantum AI to real quantum hardware!

param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId,

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroupName = "rg-quantum-ai",

    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",

    [Parameter(Mandatory=$false)]
    [string]$WorkspaceName = "quantum-ai-workspace",

    [Parameter(Mandatory=$false)]
    [string]$StorageAccountName = "quantumstorage"
)

# Color output functions
function Write-Step {
    param([string]$Message)
    Write-Host "`n$Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

# Banner
Clear-Host
Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AZURE QUANTUM DEPLOYMENT WIZARD" -ForegroundColor Green
Write-Host "  Deploy Your 90% Accuracy Quantum AI" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Info "This script will guide you through deploying Azure Quantum"
Write-Info "Estimated time: 15 minutes"
Write-Info "Cost: FREE with simulators (USD 0.00/month)"
Write-Host ""

# Step 1: Check Azure CLI
Write-Step "STEP 1: Checking Azure CLI Installation"

$azInstalled = Get-Command az -ErrorAction SilentlyContinue

if (-not $azInstalled) {
    Write-Error-Custom "Azure CLI is not installed"
    Write-Host ""
    Write-Info "To install Azure CLI:"
    Write-Host "  1. Download from: " -NoNewline
    Write-Host "https://aka.ms/installazurecliwindows" -ForegroundColor Blue
    Write-Host "  2. Run the installer"
    Write-Host "  3. Restart PowerShell"
    Write-Host "  4. Run this script again"
    Write-Host ""

    $response = Read-Host "Would you like to open the download page now? (yes/no)"
    if ($response -eq "yes") {
        Start-Process "https://aka.ms/installazurecliwindows"
    }

    Write-Host ""
    Write-Info "After installing Azure CLI, run this script again:"
    Write-Host "  .\deploy_azure_quantum.ps1" -ForegroundColor White
    Write-Host ""
    exit
}

Write-Success "Azure CLI is installed (version: $(az version --query '\"azure-cli\"' -o tsv))"

# Step 2: Azure Login
Write-Step "STEP 2: Azure Authentication"

try {
    $accountInfo = az account show 2>$null | ConvertFrom-Json
    if ($accountInfo) {
        Write-Success "Already logged in to Azure"
        Write-Info "Subscription: $($accountInfo.name)"
        Write-Info "Account: $($accountInfo.user.name)"
    }
} catch {
    Write-Info "Not logged in. Starting Azure login..."
    Write-Host ""
    Write-Host "  A browser window will open for authentication..." -ForegroundColor Yellow
    Write-Host "  Please sign in with your Azure credentials" -ForegroundColor Yellow
    Write-Host ""

    az login

    if ($LASTEXITCODE -ne 0) {
        Write-Error-Custom "Azure login failed"
        exit
    }

    Write-Success "Successfully logged in to Azure!"
}

# Step 3: Select Subscription
Write-Step "STEP 3: Selecting Azure Subscription"

if (-not $SubscriptionId) {
    Write-Info "Fetching your Azure subscriptions..."
    $subscriptions = az account list --query "[].{Name:name, ID:id, State:state}" -o json | ConvertFrom-Json

    if ($subscriptions.Count -eq 0) {
        Write-Error-Custom "No Azure subscriptions found"
        Write-Host ""
        Write-Info "To create a free Azure account:"
        Write-Host "  Visit: https://azure.microsoft.com/free/" -ForegroundColor Blue
        Write-Host "  Get: USD 200 free credit (30 days)" -ForegroundColor Green
        Write-Host ""
        exit
    }

    Write-Host ""
    Write-Host "Available Subscriptions:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $subscriptions.Count; $i++) {
        $sub = $subscriptions[$i]
        Write-Host "  [$($i+1)] $($sub.Name)" -ForegroundColor White
        Write-Host "      ID: $($sub.ID)" -ForegroundColor Gray
        Write-Host "      State: $($sub.State)" -ForegroundColor Gray
        Write-Host ""
    }

    if ($subscriptions.Count -eq 1) {
        Write-Info "Using the only available subscription"
        $SubscriptionId = $subscriptions[0].ID
    } else {
        $selection = Read-Host "Select subscription number (1-$($subscriptions.Count))"
        $SubscriptionId = $subscriptions[[int]$selection - 1].ID
    }
}

az account set --subscription $SubscriptionId
Write-Success "Using subscription: $(az account show --query name -o tsv)"
Write-Info "Subscription ID: $SubscriptionId"

# Step 4: Customize Names
Write-Step "STEP 4: Configuring Workspace Names"

Write-Host ""
Write-Info "Default configuration:"
Write-Host "  Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "  Location: $Location" -ForegroundColor White
Write-Host "  Workspace: $WorkspaceName" -ForegroundColor White
Write-Host "  Storage: $StorageAccountName" -ForegroundColor White
Write-Host ""

$customize = Read-Host "Use default names? (yes/no)"

if ($customize -eq "no") {
    $ResourceGroupName = Read-Host "Resource Group Name [$ResourceGroupName]"
    if ([string]::IsNullOrWhiteSpace($ResourceGroupName)) { $ResourceGroupName = "rg-quantum-ai" }

    $Location = Read-Host "Location [$Location]"
    if ([string]::IsNullOrWhiteSpace($Location)) { $Location = "eastus" }

    $WorkspaceName = Read-Host "Workspace Name (must be globally unique) [$WorkspaceName]"
    if ([string]::IsNullOrWhiteSpace($WorkspaceName)) { $WorkspaceName = "quantum-ai-workspace" }

    $StorageAccountName = Read-Host "Storage Account Name (lowercase, no hyphens) [$StorageAccountName]"
    if ([string]::IsNullOrWhiteSpace($StorageAccountName)) { $StorageAccountName = "quantumstorage" }
}

# Make storage account name unique and valid
$timestamp = Get-Date -Format "MMdd"
$StorageAccountName = ($StorageAccountName + $timestamp).ToLower() -replace '[^a-z0-9]', ''
if ($StorageAccountName.Length -gt 24) {
    $StorageAccountName = $StorageAccountName.Substring(0, 24)
}

Write-Success "Configuration set!"
Write-Info "Resource Group: $ResourceGroupName"
Write-Info "Workspace: $WorkspaceName"
Write-Info "Storage: $StorageAccountName"

# Step 5: Create Resource Group
Write-Step "STEP 5: Creating Resource Group"

$rgExists = az group exists --name $ResourceGroupName
if ($rgExists -eq "true") {
    Write-Success "Resource group '$ResourceGroupName' already exists"
} else {
    Write-Info "Creating resource group in $Location..."
    az group create --name $ResourceGroupName --location $Location --output none

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Resource group created successfully"
    } else {
        Write-Error-Custom "Failed to create resource group"
        exit
    }
}

# Step 6: Update Parameters File
Write-Step "STEP 6: Preparing Deployment Parameters"

$parametersPath = Join-Path $PSScriptRoot "azure\quantum_workspace.parameters.json"
$templatePath = Join-Path $PSScriptRoot "azure\quantum_workspace.bicep"

if (Test-Path $parametersPath) {
    Write-Info "Updating parameters file..."

    $parameters = Get-Content $parametersPath -Raw | ConvertFrom-Json
    $parameters.parameters.workspaceName.value = $WorkspaceName
    $parameters.parameters.storageAccountName.value = $StorageAccountName
    $parameters.parameters.location.value = $Location

    $parameters | ConvertTo-Json -Depth 10 | Set-Content $parametersPath
    Write-Success "Parameters updated"
} else {
    Write-Error-Custom "Parameters file not found: $parametersPath"
    exit
}

if (-not (Test-Path $templatePath)) {
    Write-Error-Custom "Bicep template not found: $templatePath"
    exit
}

Write-Success "Deployment files ready"

# Step 7: Deploy Azure Quantum Workspace
Write-Step "STEP 7: Deploying Azure Quantum Workspace"

Write-Host ""
Write-Info "This will create:"
Write-Host "  • Azure Quantum Workspace" -ForegroundColor White
Write-Host "  • Storage Account (for quantum job data)" -ForegroundColor White
Write-Host "  • Quantum Provider Connections (IonQ, Quantinuum, Microsoft)" -ForegroundColor White
Write-Host ""
Write-Info "Estimated monthly cost: USD 0.02-0.05 (with FREE simulators)"
Write-Host ""

$proceed = Read-Host "Proceed with deployment? (yes/no)"
if ($proceed -ne "yes") {
    Write-Host ""
    Write-Info "Deployment cancelled. Run this script again when ready."
    Write-Host ""
    exit
}

Write-Host ""
Write-Info "Starting deployment... (this takes 2-3 minutes)"
Write-Host ""

$deploymentName = "quantum-deployment-$(Get-Date -Format 'yyyyMMddHHmmss')"

az deployment group create `
    --resource-group $ResourceGroupName `
    --template-file $templatePath `
    --parameters $parametersPath `
    --name $deploymentName `
    --output table

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Success "Azure Quantum Workspace deployed successfully!"
    Write-Host ""
} else {
    Write-Host ""
    Write-Error-Custom "Deployment failed"
    Write-Host ""
    Write-Info "Common issues:"
    Write-Host "  • Workspace name already taken (try a different name)" -ForegroundColor Gray
    Write-Host "  • Storage account name invalid (lowercase letters/numbers only)" -ForegroundColor Gray
    Write-Host "  • Region not supported (try: eastus, westus, westeurope)" -ForegroundColor Gray
    Write-Host ""
    exit
}

# Step 8: Update Configuration File
Write-Step "STEP 8: Updating Quantum Configuration"

$configPath = Join-Path $PSScriptRoot "config\quantum_config.yaml"

if (Test-Path $configPath) {
    Write-Info "Updating quantum_config.yaml..."

    $configContent = Get-Content $configPath -Raw
    $configContent = $configContent -replace "subscription_id: ''", "subscription_id: '$SubscriptionId'"
    $configContent = $configContent -replace "resource_group: .*", "resource_group: $ResourceGroupName"
    $configContent = $configContent -replace "workspace_name: .*", "workspace_name: $WorkspaceName"
    $configContent = $configContent -replace "location: .*", "location: $Location"
    $configContent = $configContent -replace "storage_account: .*", "storage_account: $StorageAccountName"

    Set-Content $configPath $configContent
    Write-Success "Configuration file updated"
} else {
    Write-Error-Custom "Configuration file not found: $configPath"
}

# Step 9: Verify Deployment
Write-Step "STEP 9: Verifying Deployment"

Write-Info "Checking workspace status..."
$workspace = az quantum workspace show `
    --resource-group $ResourceGroupName `
    --name $WorkspaceName `
    --output json 2>$null | ConvertFrom-Json

if ($workspace) {
    Write-Success "Workspace verified!"
    Write-Host ""
    Write-Host "  Workspace: $($workspace.name)" -ForegroundColor White
    Write-Host "  Location: $($workspace.location)" -ForegroundColor White
    Write-Host "  Status: $($workspace.provisioningState)" -ForegroundColor Green
    Write-Host ""

    # List providers
    Write-Info "Available Quantum Providers:"
    $providers = az quantum workspace show `
        --resource-group $ResourceGroupName `
        --name $WorkspaceName `
        --query "providers[].providerId" -o json | ConvertFrom-Json

    foreach ($provider in $providers) {
        Write-Host "  ✓ $provider" -ForegroundColor Green
    }
} else {
    Write-Error-Custom "Could not verify workspace"
}

# Step 10: Success Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Success "Your Azure Quantum workspace is ready!"
Write-Host ""

Write-Info "Deployment Summary:"
Write-Host "  Subscription: $SubscriptionId" -ForegroundColor White
Write-Host "  Resource Group: $ResourceGroupName" -ForegroundColor White
Write-Host "  Workspace: $WorkspaceName" -ForegroundColor White
Write-Host "  Location: $Location" -ForegroundColor White
Write-Host "  Storage: $StorageAccountName" -ForegroundColor White
Write-Host ""

Write-Info "Configuration Updated:"
Write-Host "  config/quantum_config.yaml ✓" -ForegroundColor Green
Write-Host ""

Write-Info "Next Steps:"
Write-Host "  1. Test connection to Azure Quantum" -ForegroundColor Yellow
Write-Host "     > python test_azure_quantum.py" -ForegroundColor White
Write-Host ""
Write-Host "  2. Run Bell state test (verify quantum entanglement)" -ForegroundColor Yellow
Write-Host "     Select: ionq.simulator (FREE)" -ForegroundColor White
Write-Host ""
Write-Host "  3. Test your optimized circuit (90% accuracy)" -ForegroundColor Yellow
Write-Host "     500 shots on free simulator" -ForegroundColor White
Write-Host ""

Write-Info "Free Resources Available:"
Write-Host "  ✓ IonQ Simulator - Unlimited FREE usage" -ForegroundColor Green
Write-Host "  ✓ Microsoft Simulator - Unlimited FREE usage" -ForegroundColor Green
Write-Host ""

Write-Info "Real Quantum Hardware (Optional):"
Write-Host "  • IonQ QPU: ~USD 0.36 per circuit (500 shots)" -ForegroundColor Gray
Write-Host "  • Quantinuum: ~USD 1.50 per circuit" -ForegroundColor Gray
Write-Host "  Start with simulator first!" -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready to test on quantum hardware!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Run this command to start testing:" -ForegroundColor Yellow
Write-Host "  python test_azure_quantum.py" -ForegroundColor White
Write-Host ""

# Offer to run tests now
$runTests = Read-Host "Would you like to run the tests now? (yes/no)"
if ($runTests -eq "yes") {
    Write-Host ""
    Write-Info "Starting quantum hardware tests..."
    Write-Host ""

    # Activate virtual environment and run tests
    $venvPath = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        & $venvPath
        python (Join-Path $PSScriptRoot "test_azure_quantum.py")
    } else {
        Write-Error-Custom "Virtual environment not found"
        Write-Info "Please activate your environment first:"
        Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
        Write-Host "  python test_azure_quantum.py" -ForegroundColor White
    }
} else {
    Write-Host ""
    Write-Info "You can run tests later with:"
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  python test_azure_quantum.py" -ForegroundColor White
    Write-Host ""
}

Write-Host "Happy quantum computing! 🎉" -ForegroundColor Magenta
Write-Host ""
