# Azure Quantum CLI Automation Script
# Automates resource management and job lifecycle

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$Location = "eastus",
    [string]$QasmFile = "bell.qasm",
    [string]$TargetId = '',
    [switch]$AutoMonitor
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum CLI Automation ==" -ForegroundColor Cyan

# 1. List available quantum targets
Info "Listing available quantum targets..."
az quantum target list --resource-group $ResourceGroup --workspace-name $WorkspaceName --location $Location

# Helper: Get available target IDs for this workspace/location
function Get-AvailableTargetIds {
    param(
        [string]$ResourceGroup,
        [string]$WorkspaceName,
        [string]$Location
    )
    try {
        $targets = az quantum target list --resource-group $ResourceGroup --workspace-name $WorkspaceName --location $Location --output json | ConvertFrom-Json
        if (-not $targets) { return @() }
        $ids = @()
        foreach ($t in $targets) {
            if ($null -ne $t.id -and "$($t.id)".Trim()) { $ids += "$($t.id)"; continue }
            if ($null -ne $t.targetId -and "$($t.targetId)".Trim()) { $ids += "$($t.targetId)"; continue }
            if ($null -ne $t.target_id -and "$($t.target_id)".Trim()) { $ids += "$($t.target_id)"; continue }
            if ($null -ne $t.name -and "$($t.name)".Trim()) { $ids += "$($t.name)"; continue }
        }
        return ($ids | Where-Object { $_ -and $_.Trim() -ne '' } | Select-Object -Unique)
    } catch {
        Err "Failed to list available targets: $_"
        return @()
    }
}

# 2. Dynamically select a target if not provided and validate target
$availableTargets = Get-AvailableTargetIds -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location
if (-not $availableTargets -or $availableTargets.Count -eq 0) {
    Err "No available targets returned by Azure Quantum. Ensure providers are enabled in the workspace."
    return
}
if (-not $TargetId -or $TargetId.Trim() -eq '') {
    $q = $availableTargets | Where-Object { $_ -match '^quantinuum\.' } | Select-Object -First 1
    $r = $availableTargets | Where-Object { $_ -match '^rigetti\.' } | Select-Object -First 1
    if ($q) { $TargetId = $q }
    elseif ($r) { $TargetId = $r }
    else { $TargetId = ($availableTargets | Select-Object -First 1) }
    Info "Auto-selected target: $TargetId"
} elseif ($availableTargets -notcontains $TargetId) {
    Info "Requested target '$TargetId' not available. Available: $($availableTargets -join ', ')"
    $TargetId = ($availableTargets | Select-Object -First 1)
    Info "Falling back to: $TargetId"
}

# Verify QASM exists
if (-not (Test-Path $QasmFile)) {
    Err "QASM file not found: $QasmFile"
    return
}

# 3. Submit a job
Info "Submitting job to $TargetId with QASM '$QasmFile'..."
$job = az quantum job submit --resource-group $ResourceGroup --workspace-name $WorkspaceName --target-id $TargetId --input-data $QasmFile --output json | ConvertFrom-Json
if ($job -and $job.id) {
    Ok ("Submitted job {0} to {1}" -f $job.id, $TargetId)
} else {
    Err "Job submission did not return a job id."
}

if ($AutoMonitor -and $job -and $job.id) {
    $JobId = $job.id
    Info "Auto-monitoring job $JobId ..."
    while ($true) {
        $status = az quantum job show --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $JobId --query "status" --output tsv
        Write-Host "  Status: $status"
        if ($status -in @("Succeeded","Failed","Cancelled")) { break }
        Start-Sleep -Seconds 10
    }
    if ($status -eq "Succeeded") {
        $output = az quantum job output --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $JobId
        Write-Host "  Output: $output"
    }
} else {
    # 3. List jobs
    Info "Listing recent jobs..."
    az quantum job list --resource-group $ResourceGroup --workspace-name $WorkspaceName

    # 4. Monitor job status/results (manual)
    $JobId = Read-Host "Enter Job ID to monitor"
    Info "Showing job status..."
    az quantum job show --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $JobId
    Info "Retrieving job output..."
    az quantum job output --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $JobId
}

# 5. Resource group management (optional)
# Info "Creating resource group if needed..."
# az group create --name $ResourceGroup --location $Location

# 6. Workspace info
Info "Showing workspace info..."
az quantum workspace show --resource-group $ResourceGroup --workspace-name $WorkspaceName

Ok "Automation complete. Edit this script to customize targets, files, or add more steps!"
