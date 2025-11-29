# Chat Web - Quick Start Script
# This script starts the Azure Functions local server for the chat website

Write-Host "🚀 Starting Chat Web Application..." -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
$rootPath = "c:\Users\Bryan\OneDrive\AI"
if ((Get-Location).Path -ne $rootPath) {
    Write-Host "Navigating to workspace root..." -ForegroundColor Yellow
    Set-Location $rootPath
}

# Check dependencies
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan
$pythonCmd = if (Test-Path ".\venv\Scripts\python.exe") { ".\venv\Scripts\python.exe" } else { "python" }

try {
    & $pythonCmd -c "import azure.functions" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing Azure Functions..." -ForegroundColor Yellow
        & $pythonCmd -m pip install azure-functions --quiet
    }
    
    & $pythonCmd -c "import colorama" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Installing colorama..." -ForegroundColor Yellow
        & $pythonCmd -m pip install colorama --quiet
    }
} catch {
    Write-Host "⚠️  Error checking dependencies: $_" -ForegroundColor Red
}

# Check if talk-to-ai requirements are installed
Write-Host "Checking chat provider dependencies..." -ForegroundColor Cyan
if (Test-Path ".\talk-to-ai\requirements.txt") {
    try {
        & $pythonCmd -c "import openai" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing talk-to-ai requirements (for OpenAI/Azure support)..." -ForegroundColor Yellow
            & $pythonCmd -m pip install -r .\talk-to-ai\requirements.txt --quiet
        }
    } catch {
        Write-Host "Note: OpenAI package not found. Local provider will be used." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Dependencies ready!" -ForegroundColor Green
Write-Host ""

# Display provider info
Write-Host "🤖 Provider Configuration:" -ForegroundColor Cyan
if ($env:AZURE_OPENAI_API_KEY) {
    Write-Host "  ✓ Azure OpenAI configured" -ForegroundColor Green
} elseif ($env:OPENAI_API_KEY) {
    Write-Host "  ✓ OpenAI configured" -ForegroundColor Green
} else {
    Write-Host "  ℹ Using FREE local provider (no API keys required)" -ForegroundColor Yellow
    Write-Host "    To use OpenAI, set: `$env:OPENAI_API_KEY = 'sk-...'" -ForegroundColor DarkGray
    Write-Host "    To use Azure OpenAI, set: AZURE_OPENAI_* variables" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "🌐 Starting Azure Functions..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Once started, open your browser to:" -ForegroundColor Green
Write-Host "  http://localhost:7071/api/chat-web" -ForegroundColor White -BackgroundColor DarkBlue
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor DarkGray
Write-Host ""
Write-Host "─────────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# Start Functions
func start
