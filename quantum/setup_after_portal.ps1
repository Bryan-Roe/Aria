# Quick Setup After Portal Creation
# Run this after creating the workspace via Azure Portal

Write-Host "`n=== Azure Quantum Post-Creation Setup ===" -ForegroundColor Cyan
Write-Host "This will verify your workspace and run initial tests.`n" -ForegroundColor Yellow

# 1. Verify workspace exists and update config
Write-Host "[1/3] Verifying workspace..." -ForegroundColor Cyan
& "$PSScriptRoot\verify_workspace.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nWorkspace verification failed. Please ensure:" -ForegroundColor Red
    Write-Host "  - Workspace creation completed in Azure Portal" -ForegroundColor Yellow
    Write-Host "  - Workspace name is: quantum-ai-workspace" -ForegroundColor Yellow
    Write-Host "  - Resource group is: rg-quantum-ai" -ForegroundColor Yellow
    exit 1
}

# 2. Activate virtual environment if not already active
Write-Host "`n[2/3] Checking Python environment..." -ForegroundColor Cyan
$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "Virtual environment found." -ForegroundColor Green
    $pythonCmd = $venvPython
} else {
    Write-Host "Using system Python." -ForegroundColor Yellow
    $pythonCmd = "python"
}

# 3. Run a quick test
Write-Host "`n[3/3] Running quick connectivity test..." -ForegroundColor Cyan
$testScript = @"
from azure.quantum import Workspace
from azure.identity import DefaultAzureCredential
import yaml

# Load config
with open('config/quantum_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Connect to workspace
print('Connecting to Azure Quantum workspace...')
workspace = Workspace(
    subscription_id=config['subscription_id'],
    resource_group=config['resource_group'],
    workspace_name=config['workspace_name'],
    credential=DefaultAzureCredential()
)

print(f'✓ Connected to: {workspace.name}')
print(f'  Location: {workspace.location}')

# List targets
print('\nAvailable quantum targets:')
targets = workspace.get_targets()
for i, target in enumerate(targets[:10], 1):
    print(f'  {i}. {target.name}')
if len(targets) > 10:
    print(f'  ... and {len(targets) - 10} more')

print('\n✓ Workspace is ready for quantum computing!')
"@

$testScript | & $pythonCmd -

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
    Write-Host "`nYou can now run:" -ForegroundColor White
    Write-Host "  python src\quantum_classifier.py" -ForegroundColor Cyan
    Write-Host "  python src\azure_quantum_integration.py" -ForegroundColor Cyan
} else {
    Write-Host "`nConnectivity test failed. This might be due to:" -ForegroundColor Yellow
    Write-Host "  - Missing Python dependencies (run: pip install -r requirements.txt)" -ForegroundColor Yellow
    Write-Host "  - Workspace still provisioning (wait a few minutes)" -ForegroundColor Yellow
}
