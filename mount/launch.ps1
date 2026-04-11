# Launch QAI Control Center
# Starts the service and opens the browser

Write-Host "🚀 Launching QAI Control Center..." -ForegroundColor Cyan
Write-Host ""

# Check if service is already running
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✓ Service is already running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:8000"
    exit 0
}
catch {
    Write-Host "Starting service..." -ForegroundColor Yellow
}

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Setting up virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    & venv\Scripts\Activate.ps1
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -q -r requirements.txt
}

# Start service in background
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & venv\Scripts\Activate.ps1
    python app.py
}

Write-Host "Waiting for service to start..." -ForegroundColor Yellow

# Wait for service to be ready (max 30 seconds)
$maxAttempts = 30
$attempt = 0
$ready = $false

while ($attempt -lt $maxAttempts -and -not $ready) {
    $attempt++
    Start-Sleep -Seconds 1

    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        $ready = $true
    }
    catch {
        Write-Host "." -NoNewline
    }
}

Write-Host ""

if ($ready) {
    Write-Host ""
    Write-Host "✓ QAI Control Center is ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Web UI: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8000"

    Write-Host ""
    Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow

    # Keep showing job output
    Receive-Job -Job $job -Wait
}
else {
    Write-Host "✗ Failed to start service" -ForegroundColor Red
    Write-Host "Check the output above for errors" -ForegroundColor Yellow
    Stop-Job -Job $job
    Remove-Job -Job $job
    exit 1
}
