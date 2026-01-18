# Continuous Download Script - Runs until target reached or interrupted
# Handles errors gracefully, logs progress, resumes automatically

param(
    [int]$Target = 100,
    [int]$BatchSize = 10,
    [int]$MinScore = 90,
    [int]$DelaySeconds = 60
)

$ErrorActionPreference = "Continue"
$logFile = "data_out\continuous_download.log"
$datasetDir = "datasets\massive_quantum"

function Log-Message {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp - $message"
    Write-Host $logEntry
    Add-Content -Path $logFile -Value $logEntry
}

function Get-DatasetCount {
    return (Get-ChildItem "$datasetDir\*.csv" -ErrorAction SilentlyContinue).Count
}

Log-Message "=== CONTINUOUS DOWNLOAD STARTED ==="
Log-Message "Target: $Target datasets (score >= $MinScore)"
Log-Message "Batch size: $BatchSize, Delay: $DelaySeconds sec"

$startCount = Get-DatasetCount
Log-Message "Starting count: $startCount datasets"

$batchNum = 0
$totalDownloaded = $startCount

while ($totalDownloaded -lt $Target) {
    $batchNum++
    $start = $totalDownloaded
    $remaining = $Target - $totalDownloaded
    $thisBatch = [Math]::Min($BatchSize, $remaining)
    
    Log-Message ""
    Log-Message "--- BATCH $batchNum (Datasets $start to $($start + $thisBatch - 1)) ---"
    Log-Message "Current total: $totalDownloaded, Remaining: $remaining"
    
    try {
        # Run download
        python scripts\massive_dataset_expansion.py --download --start $start --batch-size $thisBatch --min-score $MinScore
        
        # Check results
        $newCount = Get-DatasetCount
        $downloaded = $newCount - $totalDownloaded
        $totalDownloaded = $newCount
        
        Log-Message "Batch complete: $downloaded new datasets (total: $totalDownloaded)"
        
        if ($downloaded -eq 0) {
            Log-Message "WARNING: No new datasets downloaded, may have reached end of list"
            if ($batchNum -gt 3) {
                Log-Message "Stopping after multiple empty batches"
                break
            }
        }
        
    } catch {
        Log-Message "ERROR in batch $batchNum : $_"
        Log-Message "Continuing to next batch after error..."
    }
    
    # Progress update
    $progress = [Math]::Round(($totalDownloaded / $Target) * 100, 1)
    Log-Message "Progress: $totalDownloaded/$Target ($progress%)"
    
    # Check if target reached
    if ($totalDownloaded -ge $Target) {
        Log-Message "Target reached!"
        break
    }
    
    # Delay before next batch
    if ($totalDownloaded -lt $Target) {
        Log-Message "Waiting $DelaySeconds seconds before next batch..."
        Start-Sleep -Seconds $DelaySeconds
    }
}

Log-Message ""
Log-Message "=== DOWNLOAD COMPLETE ==="
Log-Message "Final count: $totalDownloaded datasets"
Log-Message "Downloaded this session: $($totalDownloaded - $startCount)"
Log-Message "Log saved to: $logFile"
