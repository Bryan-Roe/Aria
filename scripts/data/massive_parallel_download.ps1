# Massive Parallel Download - Multiple processes downloading simultaneously
# Downloads from different score tiers in parallel for maximum throughput

$ErrorActionPreference = "Continue"

Write-Host "🚀 LAUNCHING MASSIVE PARALLEL DOWNLOAD" -ForegroundColor Green
Write-Host "Multiple download processes starting..." -ForegroundColor Cyan

# Launch 5 parallel download processes covering different ranges
$jobs = @()

# Job 1: Score 90+ (premium datasets)
$jobs += Start-Job -ScriptBlock {
    Set-Location "C:\Users\Bryan\OneDrive\AI"
    python .\scripts\massive_dataset_expansion.py --download --start 0 --batch-size 50 --min-score 90
}
Write-Host "✓ Job 1: Datasets 0-50 (score ≥90)" -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Job 2: Score 85-90 (high quality)
$jobs += Start-Job -ScriptBlock {
    Set-Location "C:\Users\Bryan\OneDrive\AI"
    python .\scripts\massive_dataset_expansion.py --download --start 50 --batch-size 50 --min-score 85
}
Write-Host "✓ Job 2: Datasets 50-100 (score ≥85)" -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Job 3: Score 80-85 (good quality)
$jobs += Start-Job -ScriptBlock {
    Set-Location "C:\Users\Bryan\OneDrive\AI"
    python .\scripts\massive_dataset_expansion.py --download --start 100 --batch-size 50 --min-score 80
}
Write-Host "✓ Job 3: Datasets 100-150 (score ≥80)" -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Job 4: Score 75-80 (decent quality)
$jobs += Start-Job -ScriptBlock {
    Set-Location "C:\Users\Bryan\OneDrive\AI"
    python .\scripts\massive_dataset_expansion.py --download --start 150 --batch-size 50 --min-score 75
}
Write-Host "✓ Job 4: Datasets 150-200 (score ≥75)" -ForegroundColor Yellow

Start-Sleep -Seconds 5

# Job 5: Score 70+ (baseline quality)
$jobs += Start-Job -ScriptBlock {
    Set-Location "C:\Users\Bryan\OneDrive\AI"
    python .\scripts\massive_dataset_expansion.py --download --start 200 --batch-size 50 --min-score 70
}
Write-Host "✓ Job 5: Datasets 200-250 (score ≥70)" -ForegroundColor Yellow

Write-Host ""
Write-Host "📊 All 5 download jobs launched!" -ForegroundColor Green
Write-Host "Target: 250+ datasets across all quality tiers" -ForegroundColor Cyan
Write-Host ""
Write-Host "Monitor progress:" -ForegroundColor White
Write-Host "  (Get-ChildItem datasets\massive_quantum\*.csv).Count" -ForegroundColor Gray
Write-Host ""
Write-Host "Wait for completion (this will take several hours)..." -ForegroundColor Yellow

# Monitor jobs
Write-Host ""
$startTime = Get-Date
$lastCount = (Get-ChildItem "datasets\massive_quantum\*.csv" -ErrorAction SilentlyContinue).Count

while ($jobs | Where-Object { $_.State -eq 'Running' }) {
    $running = ($jobs | Where-Object { $_.State -eq 'Running' }).Count
    $completed = ($jobs | Where-Object { $_.State -eq 'Completed' }).Count
    $failed = ($jobs | Where-Object { $_.State -eq 'Failed' }).Count
    $currentCount = (Get-ChildItem "datasets\massive_quantum\*.csv" -ErrorAction SilentlyContinue).Count
    $newDownloads = $currentCount - $lastCount
    $elapsed = (Get-Date) - $startTime
    
    Write-Host "`r⏳ Running: $running | ✓ Completed: $completed | ✗ Failed: $failed | 📦 Datasets: $currentCount (+$newDownloads) | ⏱️  $($elapsed.ToString('hh\:mm\:ss'))" -NoNewline
    
    $lastCount = $currentCount
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host ""
Write-Host "🎉 ALL JOBS COMPLETE!" -ForegroundColor Green

# Final statistics
$finalCount = (Get-ChildItem "datasets\massive_quantum\*.csv" -ErrorAction SilentlyContinue).Count
$totalTime = (Get-Date) - $startTime

Write-Host ""
Write-Host "📊 FINAL STATISTICS" -ForegroundColor Cyan
Write-Host "  Total datasets: $finalCount" -ForegroundColor White
Write-Host "  Total time: $($totalTime.ToString('hh\:mm\:ss'))" -ForegroundColor White
Write-Host "  Jobs completed: $($jobs | Where-Object { $_.State -eq 'Completed' } | Measure-Object).Count" -ForegroundColor White
Write-Host "  Jobs failed: $($jobs | Where-Object { $_.State -eq 'Failed' } | Measure-Object).Count" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Validate: python .\scripts\massive_dataset_expansion.py --validate" -ForegroundColor Gray
Write-Host "  2. Quick test: python .\scripts\distributed_benchmark.py --workers 10 --epochs 1 --quick-test" -ForegroundColor Gray
Write-Host "  3. Full train: python .\scripts\distributed_benchmark.py --workers 10 --epochs 25" -ForegroundColor Gray

# Cleanup jobs
$jobs | Remove-Job -Force
