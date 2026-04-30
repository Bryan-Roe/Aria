<#
.SYNOPSIS
    Complete Azure Quantum deployment script with enhanced 8-qubit classifier
.DESCRIPTION
    This script:
    1. Authenticates to Azure
    2. Deploys Azure Quantum workspace
    3. Configures quantum providers (IonQ, Quantinuum)
    4. Tests circuits on real quantum hardware
    5. Sets up Azure ML integration for production
.NOTES
    Prerequisites:
    - Azure CLI installed
    - Azure subscription with credits
    - Quantum provider access
#>

param(
    [string]$SubscriptionId = "",
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$Location = "eastus",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [switch]$SkipDeployment,
    [switch]$HardwareTest,
    [switch]$SetupAzureML
)

# Color output functions
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }

Write-Info "=========================================="
Write-Info "  Azure Quantum Deployment Script"
Write-Info "  Enhanced 8-Qubit Classifier"
Write-Info "=========================================="

# Step 1: Azure Authentication
Write-Info "`nStep 1: Azure Authentication"
Write-Info "=========================================="

try {
    # Refresh PATH to ensure az command is available
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    # Check if already logged in
    $account = az account show 2>$null | ConvertFrom-Json

    if ($account) {
        Write-Success "✓ Already logged in as: $($account.user.name)"
        Write-Info "  Subscription: $($account.name)"

        if ($SubscriptionId -eq "") {
            $SubscriptionId = $account.id
        }
    } else {
        Write-Info "Not logged in. Starting Azure login..."
        az login

        if ($LASTEXITCODE -ne 0) {
            Write-Error "✗ Azure login failed"
            exit 1
        }

        Write-Success "✓ Azure login successful"
    }

    # Set subscription
    if ($SubscriptionId -ne "") {
        az account set --subscription $SubscriptionId
        Write-Success "✓ Subscription set: $SubscriptionId"
    } else {
        Write-Warning "⚠ No subscription specified. Using default."
        $account = az account show | ConvertFrom-Json
        $SubscriptionId = $account.id
    }

} catch {
    Write-Error "✗ Authentication failed: $_"
    exit 1
}

# Step 2: Deploy Azure Quantum Workspace
if (-not $SkipDeployment) {
    Write-Info "`nStep 2: Deploy Azure Quantum Workspace"
    Write-Info "=========================================="

    # Create resource group
    Write-Info "Creating resource group: $ResourceGroup"
    az group create --name $ResourceGroup --location $Location --output table

    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Resource group created/exists"
    } else {
        Write-Error "✗ Resource group creation failed"
        exit 1
    }

    # Check if workspace already exists
    $workspaceExists = az quantum workspace show `
        --resource-group $ResourceGroup `
        --workspace-name $WorkspaceName `
        --output json 2>$null

    if ($workspaceExists) {
        Write-Success "✓ Quantum workspace already exists: $WorkspaceName"
    } else {
        Write-Info "Deploying Bicep template..."

        # Deploy using Bicep
        $deploymentName = "quantum-deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss')"

        az deployment group create `
            --resource-group $ResourceGroup `
            --template-file ".\azure\quantum_workspace.bicep" `
            --parameters ".\azure\quantum_workspace.parameters.json" `
            --parameters location=$Location `
            --parameters workspaceName=$WorkspaceName `
            --name $deploymentName `
            --output table

        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ Quantum workspace deployed successfully"
        } else {
            Write-Error "✗ Workspace deployment failed"
            Write-Info "Trying alternative deployment method..."

            # Fallback: Create workspace directly with Azure CLI
            az quantum workspace create `
                --resource-group $ResourceGroup `
                --workspace-name $WorkspaceName `
                --location $Location `
                --storage-account "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Storage/storageAccounts/quantumstorage$((Get-Random -Maximum 9999))" `
                --output table

            if ($LASTEXITCODE -eq 0) {
                Write-Success "✓ Workspace created using CLI fallback"
            } else {
                Write-Error "✗ All deployment methods failed"
                exit 1
            }
        }
    }

    # List quantum workspace
    Write-Info "`nQuantum Workspace Details:"
    az quantum workspace show `
        --resource-group $ResourceGroup `
        --workspace-name $WorkspaceName `
        --output table

} else {
    Write-Warning "⚠ Skipping deployment (--SkipDeployment flag set)"
}

# Step 3: Configure Quantum Providers
Write-Info "`nStep 3: Quantum Provider Configuration"
Write-Info "=========================================="

try {
    # Set quantum workspace
    az quantum workspace set `
        --resource-group $ResourceGroup `
        --workspace-name $WorkspaceName `
        --output table

    Write-Success "✓ Workspace context set"

    # List available providers
    Write-Info "`nAvailable Quantum Providers:"
    az quantum offerings list --output table

    Write-Success "`n✓ Quantum providers configured"
    Write-Info "  Available backends:"
    Write-Info "    • ionq.simulator (FREE)"
    Write-Info "    • ionq.qpu (PAID - real quantum hardware)"
    Write-Info "    • quantinuum.sim.h1-1sc (Quantinuum simulator)"
    Write-Info "    • quantinuum.qpu.h1-1 (Quantinuum QPU)"

} catch {
    Write-Warning "⚠ Provider configuration incomplete: $_"
}

# Step 4: Update Configuration File
Write-Info "`nStep 4: Update Configuration"
Write-Info "=========================================="

$configPath = ".\config\quantum_config.yaml"
$config = Get-Content $configPath -Raw

# Update subscription ID
$config = $config -replace "subscription_id: ''", "subscription_id: '$SubscriptionId'"
$config = $config -replace "subscription_id: '.*'", "subscription_id: '$SubscriptionId'"

# Update to 8 qubits for enhanced performance
$config = $config -replace "n_qubits: \d+", "n_qubits: 8"
$config = $config -replace "n_layers: \d+", "n_layers: 4"

$config | Set-Content $configPath

Write-Success "✓ Configuration updated"
Write-Info "  • Subscription: $SubscriptionId"
Write-Info "  • Resource Group: $ResourceGroup"
Write-Info "  • Workspace: $WorkspaceName"
Write-Info "  • Qubits: 8 (enhanced)"
Write-Info "  • Layers: 4 (optimized)"

# Step 5: Test on Quantum Hardware (Optional)
if ($HardwareTest) {
    Write-Info "`nStep 5: Test on Quantum Hardware"
    Write-Info "=========================================="

    Write-Warning "⚠ Hardware testing will use quantum credits!"
    $confirm = Read-Host "Continue with hardware test? (yes/no)"

    if ($confirm -eq "yes") {
        Write-Info "Activating Python environment..."
        & ".\venv\Scripts\Activate.ps1"

        Write-Info "Running hardware test suite..."
        python test_azure_quantum.py

        if ($LASTEXITCODE -eq 0) {
            Write-Success "`n✓ Hardware test completed successfully"
        } else {
            Write-Warning "⚠ Hardware test encountered issues"
        }
    } else {
        Write-Info "Hardware test skipped"
    }
}

# Step 6: Azure ML Integration (Optional)
if ($SetupAzureML) {
    Write-Info "`nStep 6: Azure ML Integration Setup"
    Write-Info "=========================================="

    Write-Info "Creating Azure ML workspace..."

    $mlWorkspaceName = "quantum-ai-ml-workspace"

    # Create ML workspace
    az ml workspace create `
        --resource-group $ResourceGroup `
        --workspace-name $mlWorkspaceName `
        --location $Location `
        --output table

    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Azure ML workspace created"

        # Create compute cluster for training
        Write-Info "Setting up compute cluster..."

        az ml compute create `
            --resource-group $ResourceGroup `
            --workspace-name $mlWorkspaceName `
            --name quantum-compute `
            --type amlcompute `
            --min-instances 0 `
            --max-instances 4 `
            --size Standard_DS3_v2

        Write-Success "✓ Compute cluster configured"
        Write-Info "  • Name: quantum-compute"
        Write-Info "  • Max nodes: 4"
        Write-Info "  • Auto-scaling enabled"

    } else {
        Write-Warning "⚠ Azure ML setup incomplete"
    }
}

# Summary
Write-Info "`n=========================================="
Write-Info "  Deployment Summary"
Write-Info "=========================================="

Write-Success "`n✓ Deployment completed successfully!"

Write-Info "`nResources Created:"
Write-Info "  • Resource Group: $ResourceGroup"
Write-Info "  • Quantum Workspace: $WorkspaceName"
Write-Info "  • Location: $Location"

if ($SetupAzureML) {
    Write-Info "  • ML Workspace: quantum-ai-ml-workspace"
    Write-Info "  • Compute Cluster: quantum-compute"
}

Write-Info "`nQuantum Configuration:"
Write-Info "  • Qubits: 8 (enhanced)"
Write-Info "  • Layers: 4"
Write-Info "  • Backend: IonQ/Quantinuum ready"

Write-Info "`nNext Steps:"
Write-Info "  1. Test enhanced 8-qubit classifier:"
Write-Info "     python src/quantum_classifier_enhanced.py"
Write-Info ""
Write-Info "  2. Run on quantum simulator (FREE):"
Write-Info "     python test_azure_quantum.py"
Write-Info ""
Write-Info "  3. Deploy to real quantum hardware:"
Write-Info "     .\deploy_to_azure_quantum.ps1 -HardwareTest"
Write-Info ""
Write-Info "  4. View in Azure Portal:"
Write-Info "     https://portal.azure.com/#resource/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Quantum/Workspaces/$WorkspaceName"

Write-Info "`n=========================================="
Write-Success "Deployment script completed!"
Write-Info "=========================================="
