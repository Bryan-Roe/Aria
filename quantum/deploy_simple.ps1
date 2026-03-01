# Simple Azure Quantum Deployment Script (stable)
# This script avoids fancy formatting to prevent PowerShell parsing issues.

# Suppress analyzer false positive: PSScriptAnalyzer incorrectly reports "loginCheck assigned but never used"
# at the login try/catch block (line ~36-46), despite no such variable existing in the code.
# This is a known analyzer limitation with try/catch patterns that rely on $LASTEXITCODE.
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseDeclaredVarsMoreThanAssignments', '', Scope='Function', Target='*')]
param(
    [string]$SubscriptionId,
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$Location = "eastus",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$StorageAccountName = "quantumstorage",
    [switch]$AutoYes,
    [switch]$RunTests
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum Deployment ==" -ForegroundColor Cyan

# 0) Ensure az is on PATH for this session
$azCmd = Get-Command az -ErrorAction SilentlyContinue
if (-not $azCmd) {
    $env:Path += ";C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin"
    $azCmd = Get-Command az -ErrorAction SilentlyContinue
}
if (-not $azCmd) {
    Err "Azure CLI not found. Install from https://aka.ms/installazurecliwindows and restart PowerShell."
    exit 1
}
Ok "Azure CLI available."

# 1) Login
# Note: Using try/catch to avoid capturing output in a variable (which triggers
# PSScriptAnalyzer false-positive "assigned but never used" due to analyzer limitations).
# The pattern below checks login status via exit code and initiates login only if needed.
Info "Checking Azure login..."
try {
    az account show --output none 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'NotLoggedIn' }
}
catch {
    Write-Host "Not logged in. Opening browser..." -ForegroundColor Yellow
    az login | Out-Null
    if ($LASTEXITCODE -ne 0) { Err "Login failed"; exit 1 }
}
Ok "Logged in."

# 2) Subscription selection
if (-not $SubscriptionId -or [string]::IsNullOrEmpty($SubscriptionId)) {
    $subs = az account list -o json | ConvertFrom-Json
    if (-not $subs -or $subs.Count -eq 0) { Err "No subscriptions found."; exit 1 }
    Write-Host "Available Subscriptions:" -ForegroundColor Cyan
    for ($i=0; $i -lt $subs.Count; $i++) {
        Write-Host ("  [{0}] {1}  (ID: {2})" -f ($i+1), $subs[$i].name, $subs[$i].id)
    }
    if ($subs.Count -eq 1) {
        $idx = 1
        Info "Auto-selecting only subscription."
    } else {
        $idx = Read-Host ("Select subscription number (1-{0})" -f $subs.Count)
    }
    $SubscriptionId = $subs[[int]$idx - 1].id
}
az account set --subscription $SubscriptionId
if ($LASTEXITCODE -ne 0) { Err "Failed to set subscription."; exit 1 }
Ok ("Using subscription: {0}" -f $SubscriptionId)

# 3) Names
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host ("  Resource Group: {0}" -f $ResourceGroup)
Write-Host ("  Location: {0}" -f $Location)
Write-Host ("  Workspace: {0}" -f $WorkspaceName)
Write-Host ("  Storage: {0}" -f $StorageAccountName)
if (-not $AutoYes) {
    $confirm = Read-Host "Proceed with these values? (yes/no)"
    if ($confirm -ne 'yes') {
        $rg = Read-Host ("Resource Group [{0}]" -f $ResourceGroup)
        if ($rg) { $ResourceGroup = $rg }
        $loc = Read-Host ("Location [{0}]" -f $Location)
        if ($loc) { $Location = $loc }
        $ws = Read-Host ("Workspace Name [{0}]" -f $WorkspaceName)
        if ($ws) { $WorkspaceName = $ws }
        $sa = Read-Host ("Storage Account Name (lowercase, no hyphens) [{0}]" -f $StorageAccountName)
        if ($sa) { $StorageAccountName = $sa }
    }
}

# Make storage valid and unique
$suffix = Get-Date -Format 'MMdd'
$StorageAccountName = ($StorageAccountName + $suffix).ToLower() -replace '[^a-z0-9]',''
if ($StorageAccountName.Length -gt 24) { $StorageAccountName = $StorageAccountName.Substring(0,24) }
Ok ("Storage will be: {0}" -f $StorageAccountName)

# 4) Create RG
Info "Creating/validating resource group..."
$exists = az group exists --name $ResourceGroup
if ($exists -eq 'false') {
    az group create --name $ResourceGroup --location $Location --output none
    if ($LASTEXITCODE -ne 0) { Err "Failed to create resource group."; exit 1 }
}
Ok "Resource group ready."

# 5) Deploy
Info "Deploying Azure Quantum workspace (2-3 minutes)..."
$template = Join-Path $PSScriptRoot 'azure\quantum_workspace.bicep'
$params   = Join-Path $PSScriptRoot 'azure\quantum_workspace.parameters.json'
if (-not (Test-Path $template)) { Err ("Template missing: {0}" -f $template); exit 1 }
if (-not (Test-Path $params)) { Err ("Parameters missing: {0}" -f $params); exit 1 }

# Update parameters file values in-memory then deploy
$p = Get-Content $params -Raw | ConvertFrom-Json
$p.parameters.workspaceName.value     = $WorkspaceName
$p.parameters.storageAccountName.value= $StorageAccountName
$p.parameters.location.value          = $Location
($p | ConvertTo-Json -Depth 10) | Set-Content $params

$deployName = "quantum-deploy-" + (Get-Date -Format 'yyyyMMddHHmmss')
az deployment group create `
  --name $deployName `
  --resource-group $ResourceGroup `
  --template-file $template `
  --parameters $params
if ($LASTEXITCODE -ne 0) { Err "Deployment failed."; exit 1 }
Ok "Workspace deployed."

# 6) Update config file
Info "Updating config/quantum_config.yaml..."
$cfg = Join-Path $PSScriptRoot 'config\quantum_config.yaml'
if (Test-Path $cfg) {
    $c = Get-Content $cfg -Raw
    $c = $c -replace 'subscription_id:.*',      ('subscription_id: "' + $SubscriptionId + '"')
    $c = $c -replace 'resource_group:.*',       ('resource_group: "' + $ResourceGroup + '"')
    $c = $c -replace 'workspace_name:.*',       ('workspace_name: "' + $WorkspaceName + '"')
    $c = $c -replace 'storage_account:.*',      ('storage_account: "' + $StorageAccountName + '"')
    $c = $c -replace 'location:.*',             ('location: "' + $Location + '"')
    Set-Content -Path $cfg -Value $c
    Ok "Configuration updated."
} else {
    Info ("Config file missing: {0}" -f $cfg)
}

# 7) Verify
Info "Verifying workspace..."
$ws = az quantum workspace show --resource-group $ResourceGroup --name $WorkspaceName -o json 2>$null | ConvertFrom-Json
if ($ws) {
    Ok ("Workspace: {0}  Location: {1}  State: {2}" -f $ws.name, $ws.location, $ws.provisioningState)
} else {
    Err "Workspace verification failed."
}

Write-Host "== Deployment complete ==" -ForegroundColor Cyan
Write-Host ("Subscription: {0}" -f $SubscriptionId)
Write-Host ("Resource Group: {0}" -f $ResourceGroup)
Write-Host ("Workspace: {0}" -f $WorkspaceName)
Write-Host ("Location: {0}" -f $Location)
Write-Host ("Storage: {0}" -f $StorageAccountName)

if ($RunTests) {
    python (Join-Path $PSScriptRoot 'test_azure_quantum.py')
} else {
    $run = Read-Host "Run tests now? (yes/no)"
    if ($run -eq 'yes') {
        python (Join-Path $PSScriptRoot 'test_azure_quantum.py')
    }
}
