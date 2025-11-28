# Marathon Training Monitor
# Quick status checks for extended training runs

param(
    [switch]$Watch,
    [int]$RefreshSeconds = 30
)

$ErrorActionPreference = "SilentlyContinue"

function Get-TrainingStatus {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  MARATHON TRAINING STATUS" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    
    # Check status.json
    $statusFile = "data_out\autotrain\status.json"
    if (Test-Path $statusFile) {
        $status = Get-Content $statusFile | ConvertFrom-Json
        
        Write-Host "📊 Overall Progress:" -ForegroundColor Yellow
        $completed = ($status.jobs | Where-Object { $_.status -eq "succeeded" }).Count
        $failed = ($status.jobs | Where-Object { $_.status -eq "failed" }).Count
        $running = ($status.jobs | Where-Object { $_.status -eq "running" }).Count
        $total = $status.jobs.Count
        
        Write-Host "  ✅ Completed: $completed / $total"
        Write-Host "  🏃 Running: $running"
        if ($failed -gt 0) {
            Write-Host "  ❌ Failed: $failed" -ForegroundColor Red
        }
        
        $percentComplete = [math]::Round(($completed / $total) * 100, 1)
        Write-Host "  Progress: $percentComplete%`n"
        
        # Recent jobs
        Write-Host "📋 Recent Jobs:" -ForegroundColor Yellow
        $status.jobs | Select-Object -Last 5 | ForEach-Object {
            $icon = switch ($_.status) {
                "succeeded" { "✅" }
                "failed" { "❌" }
                "running" { "🏃" }
                default { "⏳" }
            }
            $duration = if ($_.duration_human) { " ($($_.duration_human))" } else { "" }
            Write-Host "  $icon $($_.name): $($_.status)$duration"
        }
        
        # Estimate remaining time
        if ($completed -gt 0) {
            $avgDuration = ($status.jobs | Where-Object { $_.duration_sec } | Measure-Object -Property duration_sec -Average).Average
            if ($avgDuration -and $avgDuration -gt 0) {
                $remainingJobs = $total - $completed - $running
                $etaSeconds = $avgDuration * $remainingJobs
                $etaMinutes = [math]::Round($etaSeconds / 60, 0)
                $etaHours = [math]::Round($etaMinutes / 60, 1)
                Write-Host "`n⏱️  Estimated Time Remaining: $etaHours hours ($etaMinutes minutes)" -ForegroundColor Green
            }
        }
    } else {
        Write-Host "⚠️  Status file not found. Training may not have started yet." -ForegroundColor Yellow
    }
    
    # Check for active PIDs
    Write-Host "`n🔄 Active Training Processes:" -ForegroundColor Yellow
    $pidFiles = Get-ChildItem "data_out\autotrain\*.pid" -ErrorAction SilentlyContinue
    if ($pidFiles) {
        foreach ($pidFile in $pidFiles) {
            $pid = Get-Content $pidFile.FullName
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                $cpuPercent = [math]::Round($process.CPU, 1)
                $memMB = [math]::Round($process.WorkingSet64 / 1MB, 0)
                Write-Host "  PID $pid ($($pidFile.BaseName)): CPU $cpuPercent%, RAM ${memMB}MB"
            }
        }
    } else {
        Write-Host "  No active processes detected."
    }
    
    # GPU status (if nvidia-smi available)
    $nvidiaSmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($nvidiaSmi) {
        Write-Host "`n🎮 GPU Status:" -ForegroundColor Yellow
        $gpuInfo = nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
        if ($gpuInfo) {
            $parts = $gpuInfo -split ','
            Write-Host "  GPU Utilization: $($parts[0].Trim())%"
            Write-Host "  VRAM: $($parts[1].Trim())MB / $($parts[2].Trim())MB"
        }
    }
    
    Write-Host "`n========================================`n" -ForegroundColor Cyan
}

# Main execution
if ($Watch) {
    Write-Host "Starting watch mode (refresh every $RefreshSeconds seconds). Press Ctrl+C to stop.`n" -ForegroundColor Cyan
    while ($true) {
        Clear-Host
        Get-TrainingStatus
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Get-TrainingStatus
}
