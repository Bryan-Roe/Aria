# Ultra Marathon Training - Launch & Monitor
# 25+ training jobs, 8-12 hour estimated runtime

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ULTRA MARATHON TRAINING SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Total Jobs: 25+"
Write-Host "Estimated Runtime: 8-12 hours"
Write-Host "New Datasets: Generated"
Write-Host "`n"

# Check if current marathon is still running
$CurrentPID = Get-Content "data_out\autotrain\marathon_runner.pid" -ErrorAction SilentlyContinue
if ($CurrentPID) {
    $Process = Get-Process -Id $CurrentPID -ErrorAction SilentlyContinue
    if ($Process) {
        Write-Host "⚠️  Current marathon training is still running (PID: $CurrentPID)" -ForegroundColor Yellow
        Write-Host "   Options:" -ForegroundColor Yellow
        Write-Host "   1. Wait for current training to complete" -ForegroundColor White
        Write-Host "   2. Stop current: Stop-Process -Id $CurrentPID" -ForegroundColor White
        Write-Host "   3. Queue ultra marathon to start after" -ForegroundColor White
        Write-Host "`n"
        
        $choice = Read-Host "Continue with ultra marathon? (y/N)"
        if ($choice -ne 'y' -and $choice -ne 'Y') {
            Write-Host "Cancelled. Current training continues." -ForegroundColor Yellow
            exit 0
        }
    }
}

# Wait for data generation to complete
Write-Host "📊 Waiting for ultra synthetic data generation..." -ForegroundColor Yellow
$MaxWait = 120
$Elapsed = 0
while ($Elapsed -lt $MaxWait) {
    if (Test-Path "datasets\chat\ultra_synthetic\train.json") {
        $TrainFile = Get-Item "datasets\chat\ultra_synthetic\train.json"
        if ($TrainFile.Length -gt 100KB) {
            Write-Host "✅ Ultra synthetic dataset ready!" -ForegroundColor Green
            break
        }
    }
    Start-Sleep -Seconds 5
    $Elapsed += 5
    Write-Host "." -NoNewline
}

if ($Elapsed -ge $MaxWait) {
    Write-Host "`n⚠️  Dataset generation timeout. Proceeding with existing datasets." -ForegroundColor Yellow
}

Write-Host "`n"
Write-Host "🚀 Launching Ultra Marathon Training..." -ForegroundColor Green
Write-Host "`n"

# Launch training
& ".\scripts\start_marathon_training.ps1" -Resume

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Monitor commands:" -ForegroundColor Yellow
Write-Host "  .\scripts\monitor_marathon.ps1" -ForegroundColor White
Write-Host "  .\scripts\monitor_marathon.ps1 -Watch" -ForegroundColor White
Write-Host "`nView logs:" -ForegroundColor Yellow
Write-Host "  Get-Content data_out\autotrain\marathon_runner.log -Wait" -ForegroundColor White
Write-Host "`nCheck status:" -ForegroundColor Yellow
Write-Host "  Get-Content data_out\autotrain\status.json | ConvertFrom-Json" -ForegroundColor White
Write-Host "========================================`n" -ForegroundColor Cyan
