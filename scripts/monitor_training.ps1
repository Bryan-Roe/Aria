# Training Monitor - Real-time status of all training jobs
# Usage: .\scripts\monitor_training.ps1 [-Continuous]

param(
    [switch]$Continuous,
    [int]$RefreshSeconds = 30
)

function Show-TrainingStatus {
    Clear-Host
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Information "`n=== TRAINING MONITOR === $timestamp"
    Write-Information ("=" * 80)
    
    # Check LoRA Training
    Write-Information "`n[LoRA TRAINING]"
    if (Test-Path "data_out\autotrain\status.json") {
        $loraStatus = Get-Content "data_out\autotrain\status.json" -Raw | ConvertFrom-Json
        
        foreach ($job in $loraStatus.jobs) {
            $statusColor = switch ($job.status) {
                'succeeded' { 'Green' }
                'failed' { 'Red' }
                'running' { 'Yellow' }
                default { 'Gray' }
            }
            
            $duration = if ($job.duration_sec) { 
                "$([math]::Round($job.duration_sec/60, 1)) min" 
            } else { 
                "running..." 
            }
            
            Write-Information "  $($job.name): $($job.status) ($duration)"
        }
        
        $succeeded = ($loraStatus.jobs | Where-Object {$_.status -eq 'succeeded'}).Count
        $failed = ($loraStatus.jobs | Where-Object {$_.status -eq 'failed'}).Count
        $total = $loraStatus.jobs.Count
        Write-Information "`n  Summary: $succeeded/$total succeeded, $failed failed"
    } else {
        Write-Information "  No status file found"
    }
    
    # Check Quantum Training
    Write-Information "`n[QUANTUM TRAINING]"
    if (Test-Path "data_out\quantum_autorun\status.json") {
        $quantumStatus = Get-Content "data_out\quantum_autorun\status.json" -Raw | ConvertFrom-Json
        
        foreach ($job in $quantumStatus.jobs) {
            $statusColor = switch ($job.status) {
                'succeeded' { 'Green' }
                'failed' { 'Red' }
                'running' { 'Yellow' }
                default { 'Gray' }
            }
            
            $duration = if ($job.duration_sec) { 
                "$([math]::Round($job.duration_sec/60, 1)) min" 
            } else { 
                "running..." 
            }
            
            $accuracy = if ($job.meta.final_accuracy) {
                " | Acc: $([math]::Round($job.meta.final_accuracy * 100, 1))%"
            } else {
                ""
            }
            
            Write-Information "  $($job.name): $($job.status) ($duration)$accuracy"
        }
        
        $succeeded = ($quantumStatus.jobs | Where-Object {$_.status -eq 'succeeded'}).Count
        $failed = ($quantumStatus.jobs | Where-Object {$_.status -eq 'failed'}).Count
        $total = $quantumStatus.jobs.Count
        Write-Information "`n  Summary: $succeeded/$total succeeded, $failed failed"
    } else {
        Write-Information "  No status file found"
    }
    
    # Check Running Processes
    Write-Information "`n[SYSTEM STATUS]"
    $pythonProcs = Get-Process -Name python -ErrorAction SilentlyContinue
    if ($pythonProcs) {
        $totalMemMB = ($pythonProcs | Measure-Object -Property WorkingSet64 -Sum).Sum / 1MB
        Write-Information "  Python processes: $($pythonProcs.Count) (Memory: $([math]::Round($totalMemMB, 0)) MB)"
    } else {
        Write-Information "  No Python processes running"
    }
    
    # Check Disk Usage
    $loraSize = if (Test-Path "data_out\lora_training") {
        (Get-ChildItem "data_out\lora_training" -Recurse -File -ErrorAction SilentlyContinue | 
            Measure-Object -Property Length -Sum).Sum / 1GB
    } else { 0 }
    
    $quantumSize = if (Test-Path "data_out\quantum_autorun") {
        (Get-ChildItem "data_out\quantum_autorun" -Recurse -File -ErrorAction SilentlyContinue | 
            Measure-Object -Property Length -Sum).Sum / 1MB
    } else { 0 }
    
    Write-Information "  LoRA outputs: $([math]::Round($loraSize, 2)) GB"
    Write-Information "  Quantum outputs: $([math]::Round($quantumSize, 0)) MB"
    
    $separator = "=" * 80
    Write-Information "`n$separator"
    
    if ($Continuous) {
        Write-Information "Press Ctrl+C to stop monitoring. Refreshing in $RefreshSeconds seconds..."
    }
}

# Set preference to display Information messages
$InformationPreference = 'Continue'

if ($Continuous) {
    while ($true) {
        Show-TrainingStatus
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-TrainingStatus
}
