# Overnight Dataset Download Script
# Downloads 100 high-quality datasets from OpenML in batches
# Automatically retries on failures, logs progress

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = Split-Path -Parent $scriptDir
$logFile = Join-Path $workspaceRoot "data_out\overnight_download.log"

# Create log directory
New-Item -ItemType Directory -Force -Path (Join-Path $workspaceRoot "data_out") | Out-Null

function Log-Message {
    param([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp - $message"
    Write-Host $logEntry
    Add-Content -Path $logFile -Value $logEntry
}

Log-Message "=== OVERNIGHT DOWNLOAD STARTED ==="
Log-Message "Target: 100 datasets (score >= 90)"
Log-Message "Strategy: 10 batches of 10 datasets each"

$totalDownloaded = 0
$totalFailed = 0

# Download in batches of 10 to handle failures gracefully
for ($batch = 0; $batch -lt 10; $batch++) {
    $startIdx = $batch * 10
    $batchSize = 10
    
    Log-Message ""
    Log-Message "--- BATCH $($batch + 1)/10 (Datasets $startIdx to $($startIdx + $batchSize - 1)) ---"
    
    try {
        # Run download batch
        $output = python "$workspaceRoot\scripts\massive_dataset_expansion.py" --download --start $startIdx --batch-size $batchSize --min-score 90 2>&1
        
        # Parse results
        if ($output -match "(\d+)/\d+ successful") {
            $successCount = [int]$matches[1]
            $totalDownloaded += $successCount
            Log-Message "Batch complete: $successCount datasets downloaded"
        } else {
            Log-Message "Batch had issues (check output)"
        }
        
        # Small delay between batches
        Start-Sleep -Seconds 30
        
    } catch {
        Log-Message "ERROR in batch $($batch + 1): $_"
        $totalFailed += $batchSize
        
        # Wait longer on error
        Start-Sleep -Seconds 60
    }
    
    # Status update
    Log-Message "Progress: $totalDownloaded downloaded, $totalFailed failed"
    
    # Check if we should continue
    if ($totalDownloaded -ge 100) {
        Log-Message "Target reached: $totalDownloaded datasets"
        break
    }
}

Log-Message ""
Log-Message "=== OVERNIGHT DOWNLOAD COMPLETE ==="
Log-Message "Total Downloaded: $totalDownloaded"
Log-Message "Total Failed: $totalFailed"
Log-Message "Log saved to: $logFile"

# Run validation
Log-Message ""
Log-Message "Running validation..."
python "$workspaceRoot\scripts\massive_dataset_expansion.py" --validate

# Show status
python "$workspaceRoot\scripts\massive_dataset_expansion.py" --status

Log-Message "All operations complete!"
