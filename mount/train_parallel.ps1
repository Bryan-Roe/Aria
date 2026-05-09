# Parallel Training Script - Train multiple models simultaneously
# WARNING: This will heavily load your system!

Write-Host "⚡ PARALLEL AI TRAINING - MAXIMUM UTILIZATION" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

Write-Host "⚠️  WARNING: This will start multiple training processes!" -ForegroundColor Yellow
Write-Host "   - Very high CPU/GPU usage" -ForegroundColor Yellow
Write-Host "   - Maximum RAM consumption" -ForegroundColor Yellow
Write-Host "   - System may become slow/unresponsive" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continue with parallel training? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "❌ Cancelled" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting parallel training jobs..." -ForegroundColor Green
Write-Host ""

# Navigate to workspace root
$workspaceRoot = Split-Path -Parent $PSScriptRoot

# Job 1: LoRA Training on Dolly
Write-Host "📦 Job 1: LoRA on Dolly dataset" -ForegroundColor Cyan
$job1 = Start-Job -ScriptBlock {
    Set-Location $using:workspaceRoot
    & venv\Scripts\Activate.ps1
    Set-Location "AI\microsoft_phi-silica-3.6_v1"
    python scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config lora\lora.yaml --max-train-samples 500 --epochs 2 --save-dir ..\..\data_out\lora_training\parallel_job1
}

Start-Sleep -Seconds 5

# Job 2: Quantum Training on multiple datasets
Write-Host "📦 Job 2: Quantum training on heart dataset" -ForegroundColor Cyan
$job2 = Start-Job -ScriptBlock {
    Set-Location $using:workspaceRoot
    Set-Location "quantum-ai"
    & venv\Scripts\Activate.ps1
    python train_custom_dataset.py --preset heart --epochs 20 --backend qiskit_aer
}

Start-Sleep -Seconds 5

# Job 3: Another LoRA training
Write-Host "📦 Job 3: LoRA on Mixed Chat dataset" -ForegroundColor Cyan
$job3 = Start-Job -ScriptBlock {
    Set-Location $using:workspaceRoot
    & venv\Scripts\Activate.ps1
    Set-Location "AI\microsoft_phi-silica-3.6_v1"
    python scripts\train_lora.py --dataset ..\..\datasets\chat\mixed_chat --config lora\lora.yaml --max-train-samples 500 --epochs 2 --save-dir ..\..\data_out\lora_training\parallel_job3
}

Write-Host ""
Write-Host "✅ All jobs started!" -ForegroundColor Green
Write-Host ""
Write-Host "Monitoring progress (Ctrl+C to stop monitoring, jobs will continue):" -ForegroundColor Cyan
Write-Host "=" * 70
Write-Host ""

# Monitor all jobs
$running = $true
while ($running) {
    Clear-Host
    Write-Host "⚡ PARALLEL TRAINING STATUS" -ForegroundColor Cyan
    Write-Host "=" * 70
    Write-Host ""

    # Check job statuses
    Write-Host "Job 1 (LoRA Dolly):     " -NoNewline
    if ($job1.State -eq "Running") {
        Write-Host "🟢 RUNNING" -ForegroundColor Green
    } elseif ($job1.State -eq "Completed") {
        Write-Host "✅ COMPLETED" -ForegroundColor Green
    } else {
        Write-Host "❌ $($job1.State)" -ForegroundColor Red
    }

    Write-Host "Job 2 (Quantum Heart):  " -NoNewline
    if ($job2.State -eq "Running") {
        Write-Host "🟢 RUNNING" -ForegroundColor Green
    } elseif ($job2.State -eq "Completed") {
        Write-Host "✅ COMPLETED" -ForegroundColor Green
    } else {
        Write-Host "❌ $($job2.State)" -ForegroundColor Red
    }

    Write-Host "Job 3 (LoRA Mixed):     " -NoNewline
    if ($job3.State -eq "Running") {
        Write-Host "🟢 RUNNING" -ForegroundColor Green
    } elseif ($job3.State -eq "Completed") {
        Write-Host "✅ COMPLETED" -ForegroundColor Green
    } else {
        Write-Host "❌ $($job3.State)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "=" * 70
    Write-Host ""

    # System resources
    $cpu = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction SilentlyContinue
    $mem = Get-Counter '\Memory\% Committed Bytes In Use' -ErrorAction SilentlyContinue

    if ($cpu) {
        Write-Host "💻 CPU Usage:  " -NoNewline
        Write-Host "$([math]::Round($cpu.CounterSamples[0].CookedValue, 1))%" -ForegroundColor Yellow
    }

    if ($mem) {
        Write-Host "💾 RAM Usage:  " -NoNewline
        Write-Host "$([math]::Round($mem.CounterSamples[0].CookedValue, 1))%" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Press Ctrl+C to stop monitoring (jobs will continue in background)" -ForegroundColor Gray

    # Check if all jobs are done
    if ($job1.State -ne "Running" -and $job2.State -ne "Running" -and $job3.State -ne "Running") {
        $running = $false
    }

    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "=" * 70
Write-Host "✅ ALL JOBS COMPLETED!" -ForegroundColor Green
Write-Host ""

# Show results
Write-Host "Job 1 Status: $($job1.State)" -ForegroundColor $(if($job1.State -eq "Completed"){"Green"}else{"Red"})
Write-Host "Job 2 Status: $($job2.State)" -ForegroundColor $(if($job2.State -eq "Completed"){"Green"}else{"Red"})
Write-Host "Job 3 Status: $($job3.State)" -ForegroundColor $(if($job3.State -eq "Completed"){"Green"}else{"Red"})

Write-Host ""
Write-Host "📊 View job outputs:" -ForegroundColor Cyan
Write-Host "   Get-Job | Receive-Job" -ForegroundColor Yellow
Write-Host ""
Write-Host "🧹 Clean up jobs:" -ForegroundColor Cyan
Write-Host "   Get-Job | Remove-Job" -ForegroundColor Yellow
Write-Host ""
