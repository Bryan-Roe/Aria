<#
.SYNOPSIS
    Fast training launcher - optimized for speed

.DESCRIPTION
    Runs training with aggressive optimizations:
    - Smaller sample sizes (64-500 samples)
    - Parallel job execution (2 concurrent by default)
    - Reduced LoRA rank for faster training
    - Optimized batch sizes and checkpointing

.PARAMETER Mode
    Training mode: quick (64 samples), medium (256), focused (500)

.PARAMETER Parallel
    Number of parallel jobs (default: 2 for dual-GPU/CPU)

.PARAMETER Model
    Filter by model: phi35, qwen25, or * for all

.EXAMPLE
    .\scripts\fast_train.ps1 -Mode quick
    
.EXAMPLE
    .\scripts\fast_train.ps1 -Mode medium -Parallel 4 -Model phi35
#>

param(
    [ValidateSet("quick", "medium", "focused", "all")]
    [string]$Mode = "quick",
    
    [int]$Parallel = 2,
    
    [string]$Model = "*"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ScriptRoot "AI\microsoft_phi-silica-3.6_v1\venv\Scripts\python.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Fast Training Launcher" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "`nConfiguration:" -ForegroundColor Yellow
Write-Host "  Mode: $Mode" -ForegroundColor Gray
Write-Host "  Parallel Jobs: $Parallel" -ForegroundColor Gray
Write-Host "  Model Filter: $Model" -ForegroundColor Gray

# Build filter pattern
$filter = switch ($Mode) {
    "quick"   { "*quick*" }
    "medium"  { "*medium*" }
    "focused" { "*focused*" }
    "all"     { "*" }
}

# Combine with model filter
if ($Model -ne "*") {
    $filter = "$Model$filter"
}

Write-Host "`nJob Filter: $filter" -ForegroundColor Gray

# Estimated times
$estimatedTime = switch ($Mode) {
    "quick"   { "5-10 minutes total" }
    "medium"  { "20-30 minutes total" }
    "focused" { "40-60 minutes total" }
    "all"     { "60-90 minutes total" }
}

Write-Host "Estimated Time: $estimatedTime" -ForegroundColor Gray

Write-Host "`nStarting parallel training..." -ForegroundColor Yellow

# Run parallel trainer
& $VenvPython "$ScriptRoot\scripts\parallel_train.py" `
    --config "autotrain_fast.yaml" `
    --max-parallel $Parallel `
    --filter $filter

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[OK] Training complete!" -ForegroundColor Green
    Write-Host "`nResults in: data_out\parallel_training\" -ForegroundColor Cyan
    Write-Host "Status: data_out\parallel_training\status.json" -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Training failed" -ForegroundColor Red
    exit 1
}
