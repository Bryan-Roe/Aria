# Azure Quantum Batch Job Automation Script
# Submits multiple QASM files to multiple hardware targets, monitors status/results, and logs job info

param(
    [string]$ResourceGroup = "rg-quantum-ai",
    [string]$WorkspaceName = "quantum-ai-workspace",
    [string]$Location = "eastus",
    [string[]]$QasmFiles = @("bell.qasm", "ghz.qasm"),
    # Targets default to empty; we'll dynamically pick Quantinuum/Rigetti if available
    [string[]]$Targets = @()
)

function Info($msg) { Write-Host $msg -ForegroundColor Yellow }
function Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Err($msg) { Write-Host $msg -ForegroundColor Red }

Write-Host "== Azure Quantum Batch Job Automation ==" -ForegroundColor Cyan

$JobLog = @()

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

# Discover available targets and dynamically select defaults when none provided
$availableTargets = Get-AvailableTargetIds -ResourceGroup $ResourceGroup -WorkspaceName $WorkspaceName -Location $Location
if (-not $availableTargets -or $availableTargets.Count -eq 0) {
    Err "No available targets returned by Azure Quantum. Ensure providers are enabled in the workspace."
}

# If user didn't pass -Targets, auto-pick Quantinuum and Rigetti if present
if (-not $Targets -or $Targets.Count -eq 0) {
    $auto = @()
    $qTargets = $availableTargets | Where-Object { $_ -match '^quantinuum\.' }
    $rTargets = $availableTargets | Where-Object { $_ -match '^rigetti\.' }
    if ($qTargets) { $auto += $qTargets[0] }
    if ($rTargets) { $auto += $rTargets[0] }
    if ($auto.Count -eq 0) { $auto = $availableTargets | Select-Object -First 2 }
    $Targets = $auto
    Info ("Auto-selected targets: {0}" -f ($Targets -join ', '))
}

# Filter requested targets to only those available
$requested = $Targets
$invalidTargets = $requested | Where-Object { $availableTargets -notcontains $_ }
if ($invalidTargets -and $invalidTargets.Count -gt 0) {
    Info ("These targets are not available and will be skipped: {0}" -f ($invalidTargets -join ', '))
}
$Targets = $requested | Where-Object { $availableTargets -contains $_ }
if (-not $Targets -or $Targets.Count -eq 0) {
    Err "No valid targets to submit to after filtering. Available: $($availableTargets -join ', ')"
    return
}

# Verify QASM files exist; skip missing
$existingQasm = @()
foreach ($q in $QasmFiles) {
    if (Test-Path $q) { $existingQasm += $q } else { Info "QASM file not found, skipping: $q" }
}
if (-not $existingQasm -or $existingQasm.Count -eq 0) {
    Err "No QASM files found to submit. Ensure your QASM files exist in the current folder or pass -QasmFiles."
    return
}

Info ("Final targets to submit: {0}" -f ($Targets -join ', '))

foreach ($qasm in $existingQasm) {
    foreach ($target in $Targets) {
        Info "Submitting $qasm to $target..."
        $job = az quantum job submit --resource-group $ResourceGroup --workspace-name $WorkspaceName --target-id $target --input-data $qasm --output json | ConvertFrom-Json
        if ($job -and $job.id) {
            Ok "Submitted job $($job.id) for $qasm on $target"
            $JobLog += [PSCustomObject]@{
                QasmFile = $qasm
                Target = $target
                JobId = $job.id
            }
        } else {
            Err "Failed to submit $qasm to $target"
        }
    }
}

# Monitor jobs
foreach ($entry in $JobLog) {
    Info "Monitoring job $($entry.JobId) ($($entry.QasmFile) on $($entry.Target))..."
    $status = az quantum job show --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $entry.JobId --query "status" --output tsv
    Write-Host "  Status: $status"
    if ($status -eq "Succeeded") {
        $output = az quantum job output --resource-group $ResourceGroup --workspace-name $WorkspaceName --job-id $entry.JobId
        Write-Host "  Output: $output"
    }
}

Ok "Batch job automation complete. See above for job IDs and results."
