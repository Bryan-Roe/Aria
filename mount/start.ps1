# Quick start script for QAI Integration Service (PowerShell)

Write-Host "Starting QAI Integration Service..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host ""
}

# Activate virtual environment
& venv\Scripts\Activate.ps1

# Install/upgrade requirements
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt
Write-Host ""

# Start the service
Write-Host "Starting FastAPI service on http://localhost:8000" -ForegroundColor Green
Write-Host "Interactive docs at http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
python app.py
