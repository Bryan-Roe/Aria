# Test the QAI Integration Service Web UI
# This script tests the backend API to ensure everything is working

Write-Host "🧪 Testing QAI Integration Service..." -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000"
$errors = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null
    )

    try {
        Write-Host "Testing: $Name... " -NoNewline

        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method Post -Body ($Body | ConvertTo-Json) -ContentType "application/json" -TimeoutSec 5
        }

        Write-Host "✓ PASSED" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "✗ FAILED" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# Test health endpoint
Write-Host "=== Core Endpoints ===" -ForegroundColor Cyan
if (-not (Test-Endpoint "Health Check" "$API_BASE/health")) { $errors++ }
if (-not (Test-Endpoint "Root / Web UI" "$API_BASE/")) { $errors++ }
if (-not (Test-Endpoint "Full Status" "$API_BASE/status")) { $errors++ }

Write-Host ""
Write-Host "=== Quantum Endpoints ===" -ForegroundColor Cyan
if (-not (Test-Endpoint "Quantum Status" "$API_BASE/quantum/status")) { $errors++ }
if (-not (Test-Endpoint "Quantum Datasets" "$API_BASE/quantum/datasets")) { $errors++ }
if (-not (Test-Endpoint "Quantum Backends" "$API_BASE/quantum/backends")) { $errors++ }

Write-Host ""
Write-Host "=== Chat Endpoints ===" -ForegroundColor Cyan
if (-not (Test-Endpoint "Chat Status" "$API_BASE/chat/status")) { $errors++ }
if (-not (Test-Endpoint "Chat Providers" "$API_BASE/chat/providers")) { $errors++ }
if (-not (Test-Endpoint "Detect Provider" "$API_BASE/chat/detect-provider")) { $errors++ }

Write-Host ""
Write-Host "=== Training Endpoints ===" -ForegroundColor Cyan
if (-not (Test-Endpoint "Training Status" "$API_BASE/training/status")) { $errors++ }
if (-not (Test-Endpoint "Training Datasets" "$API_BASE/training/datasets")) { $errors++ }
if (-not (Test-Endpoint "LoRA Adapter Info" "$API_BASE/training/lora-adapter")) { $errors++ }
if (-not (Test-Endpoint "AutoTrain Jobs" "$API_BASE/training/autotrain/jobs")) { $errors++ }

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "✓ All tests passed! Service is working correctly." -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Open the Web UI: $API_BASE" -ForegroundColor Cyan
    Write-Host "📚 API Documentation: $API_BASE/docs" -ForegroundColor Cyan
} else {
    Write-Host "✗ $errors test(s) failed. Check the service logs." -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the service is running:" -ForegroundColor Yellow
    Write-Host "  cd mount" -ForegroundColor Yellow
    Write-Host "  .\start.ps1" -ForegroundColor Yellow
}

Write-Host ""
