# Azure Quantum Advanced Resource Orchestration Script
# Automates workspace/provider creation, resource group management, and cleanup

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$Location = "eastus"
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum Resource Orchestration ==" -ForegroundColor Cyan

# 1. Create resource group if needed
Info "Ensuring resource group exists..."
az group create --name $ResourceGroup --location $Location

# 2. Create workspace (portal recommended for providers)
Info "Creating workspace (if not exists)..."
az quantum workspace create --resource-group $ResourceGroup --name $WorkspaceName --location $Location

# 3. List providers (add via portal if needed)
Info "Listing providers..."
az quantum workspace show --resource-group $ResourceGroup --workspace-name $WorkspaceName

# 4. Cleanup (delete resource group)
$cleanup = Read-Host "Delete resource group and all resources? (yes/no)"
if ($cleanup -eq "yes") {
    Info "Deleting resource group $ResourceGroup..."
    az group delete --name $ResourceGroup --yes --no-wait
    Ok "Cleanup initiated."
} else {
    Ok "Cleanup skipped."
}
