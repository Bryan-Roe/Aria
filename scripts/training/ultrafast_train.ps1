#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Ultra-fast training launcher - maximum speed optimization
    
.DESCRIPTION
    Launches training with aggressive optimization for minimum time:
    - 32-64 sample sizes
    - Batch size 4 with gradient accumulation
    - Sequence length 256 (50% reduction)
    - Phi-3.5 only (proven stable)
    - Parallel execution with 3 concurrent jobs
    
.PARAMETER Mode
    Training mode:
      ultra   - 32 samples, 1-2 minutes (quality check)
      rapid   - 64 samples, 3-5 minutes (3 datasets)
      all     - All jobs sequentially
      
.PARAMETER Parallel
    Max concurrent jobs (default: 3)
    
.EXAMPLE
    .\scripts\ultrafast_train.ps1 -Mode ultra
    .\scripts\ultrafast_train.ps1 -Mode rapid -Parallel 3
#>

param(
    [Parameter(Position=0)]
    [ValidateSet('ultra', 'rapid', 'all')]
    [string]$Mode = 'ultra',
    
    [Parameter()]
    [int]$Parallel = 3
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ultra-Fast Training Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$Root = Split-Path $PSScriptRoot -Parent
$ConfigPath = Join-Path $Root "autotrain_ultrafast.yaml"
$PythonScript = Join-Path $Root "scripts\parallel_train.py"
$VenvPython = Join-Path $Root "AI\microsoft_phi-silica-3.6_v1\venv\Scripts\python.exe"

# Verify prerequisites
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: Virtual environment not found at: $VenvPython" -ForegroundColor Red
    Write-Host "Please run: cd AI\microsoft_phi-silica-3.6_v1; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $ConfigPath)) {
    Write-Host "ERROR: Configuration not found at: $ConfigPath" -ForegroundColor Red
    exit 1
}

# Job filtering
$JobFilter = switch ($Mode) {
    'ultra' { '*ultra*'; $EstTime = "1-2 minutes" }
    'rapid' { '*rapid*'; $EstTime = "3-5 minutes per job (9-15 min total)" }
    'all' { '*'; $EstTime = "15-20 minutes total" }
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  Mode: $Mode"
Write-Host "  Parallel Jobs: $Parallel"
Write-Host "  Job Filter: $JobFilter"
Write-Host "  Estimated Time: $EstTime"
Write-Host ""

# Launch parallel training
Write-Host "Starting ultra-fast parallel training..." -ForegroundColor Yellow
Write-Host "Running with max $Parallel parallel jobs" -ForegroundColor Yellow
Write-Host ""

& $VenvPython $PythonScript --config $ConfigPath --max-parallel $Parallel --filter $JobFilter

$ExitCode = $LASTEXITCODE
Write-Host ""

if ($ExitCode -eq 0) {
    Write-Host "[OK] Training complete!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Training failed with code $ExitCode" -ForegroundColor Red
}

Write-Host ""
Write-Host "Results in: data_out\parallel_training\" -ForegroundColor Cyan
Write-Host "Status: data_out\parallel_training\status.json" -ForegroundColor Cyan

exit $ExitCode
