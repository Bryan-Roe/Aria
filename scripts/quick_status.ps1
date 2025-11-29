#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick status dashboard for all training and data generation
    
.DESCRIPTION
    Shows real-time status of:
    - Data generation pipelines
    - Training jobs (parallel, Azure ML)
    - Model performance
    - Resource usage
    
.EXAMPLE
    .\scripts\quick_status.ps1
    .\scripts\quick_status.ps1 -Watch
#>

param(
    [switch]$Watch,
    [int]$RefreshSeconds = 5
)

$ErrorActionPreference = "Continue"

function Show-Status {
    Clear-Host
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host "  QAI Training & Data Pipeline Status" -ForegroundColor Cyan
    Write-Host "  $timestamp" -ForegroundColor Cyan
    Write-Host "=" * 80 -ForegroundColor Cyan
    Write-Host ""
    
    # === Training Status ===
    Write-Host "🤖 TRAINING STATUS" -ForegroundColor Yellow
    Write-Host "-" * 80 -ForegroundColor DarkGray
    
    # Parallel training
    $statusFile = "data_out\parallel_training\status.json"
    if (Test-Path $statusFile) {
        $status = Get-Content $statusFile | ConvertFrom-Json
        $succeeded = ($status.jobs | Where-Object { $_.status -eq 'succeeded' }).Count
        $failed = ($status.jobs | Where-Object { $_.status -eq 'failed' }).Count
        $running = ($status.jobs | Where-Object { $_.status -eq 'running' }).Count
        $total = $status.jobs.Count
        
        Write-Host "  Parallel Training:" -ForegroundColor Green
        Write-Host "    ✓ Succeeded: $succeeded/$total" -ForegroundColor Green
        if ($failed -gt 0) {
            Write-Host "    ✗ Failed: $failed" -ForegroundColor Red
        }
        if ($running -gt 0) {
            Write-Host "    ⏳ Running: $running" -ForegroundColor Yellow
        }
        
        # Show last completed job
        $lastJob = $status.jobs | Where-Object { $_.end_time } | Sort-Object end_time -Descending | Select-Object -First 1
        if ($lastJob) {
            Write-Host "    Last: $($lastJob.name) ($(([Math]::Round($lastJob.duration, 1)))s)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No parallel training status" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # === Data Generation ===
    Write-Host "📊 DATA GENERATION" -ForegroundColor Yellow
    Write-Host "-" * 80 -ForegroundColor DarkGray
    
    # Check auto_generated dataset
    $autoGenDir = "datasets\chat\auto_generated"
    if (Test-Path $autoGenDir\metadata.json) {
        $meta = Get-Content $autoGenDir\metadata.json | ConvertFrom-Json
        Write-Host "  Auto-Generated Dataset:" -ForegroundColor Green
        Write-Host "    📈 Total: $($meta.total_samples) samples" -ForegroundColor Green
        Write-Host "    📚 Train: $($meta.train_samples)" -ForegroundColor Gray
        Write-Host "    🧪 Test: $($meta.test_samples)" -ForegroundColor Gray
        Write-Host "    🕐 Generated: $($meta.generated_at)" -ForegroundColor Gray
    } else {
        Write-Host "  No auto-generated dataset yet" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # === Models ===
    Write-Host "🎯 TRAINED MODELS" -ForegroundColor Yellow
    Write-Host "-" * 80 -ForegroundColor DarkGray
    
    $modelDirs = Get-ChildItem "data_out\lora_training" -Directory -ErrorAction SilentlyContinue
    if ($modelDirs) {
        $recentModels = $modelDirs | Sort-Object LastWriteTime -Descending | Select-Object -First 5
        foreach ($model in $recentModels) {
            $hasAdapter = Test-Path "$($model.FullName)\adapter_model.safetensors"
            $icon = if ($hasAdapter) { "✓" } else { "⏳" }
            $color = if ($hasAdapter) { "Green" } else { "Yellow" }
            
            Write-Host "  $icon $($model.Name)" -ForegroundColor $color
            Write-Host "    Last Modified: $($model.LastWriteTime)" -ForegroundColor Gray
            
            if ($hasAdapter) {
                $size = (Get-Item "$($model.FullName)\adapter_model.safetensors").Length / 1MB
                Write-Host "    Size: $([Math]::Round($size, 1)) MB" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  No trained models found" -ForegroundColor Gray
    }
    
    Write-Host ""
    
    # === Datasets ===
    Write-Host "📁 DATASETS" -ForegroundColor Yellow
    Write-Host "-" * 80 -ForegroundColor DarkGray
    
    $chatDatasets = Get-ChildItem "datasets\chat" -Directory -ErrorAction SilentlyContinue
    if ($chatDatasets) {
        foreach ($ds in $chatDatasets | Select-Object -First 5) {
            $trainFile = "$($ds.FullName)\train.json"
            if (Test-Path $trainFile) {
                $lineCount = (Get-Content $trainFile | Measure-Object -Line).Lines
                Write-Host "  📦 $($ds.Name): $lineCount samples" -ForegroundColor Cyan
            }
        }
    }
    
    Write-Host ""
    
    # === Quick Actions ===
    Write-Host "⚡ QUICK ACTIONS" -ForegroundColor Yellow
    Write-Host "-" * 80 -ForegroundColor DarkGray
    Write-Host "  Generate & Train:  " -NoNewline
    Write-Host "python scripts\auto_data_train.py --quick" -ForegroundColor White
    Write-Host "  Ultra-Fast Train:  " -NoNewline
    Write-Host ".\scripts\ultrafast_train.ps1 -Mode ultra" -ForegroundColor White
    Write-Host "  Rapid Train:       " -NoNewline
    Write-Host ".\scripts\ultrafast_train.ps1 -Mode rapid" -ForegroundColor White
    Write-Host "  Test Model:        " -NoNewline
    Write-Host "python talk-to-ai\src\chat_cli.py --once 'test'" -ForegroundColor White
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Cyan
    
    if ($Watch) {
        Write-Host "Refreshing in $RefreshSeconds seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    }
}

# Main loop
do {
    Show-Status
    
    if ($Watch) {
        Start-Sleep -Seconds $RefreshSeconds
    }
} while ($Watch)
