# QAI Workspace Fix Script
# Fixes common issues in the QAI workspace

Write-Host "QAI Workspace Fix Script" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"

# Fix 1: Recreate missing virtual environments
Write-Host "1. Checking virtual environments..." -ForegroundColor Yellow

# quantum-ai venv
if (Test-Path "quantum-ai\venv\Scripts\python.exe") {
    Write-Host "   quantum-ai venv OK" -ForegroundColor Green
} else {
    Write-Host "   quantum-ai venv missing - creating..." -ForegroundColor Red
    Push-Location quantum-ai
    python -m venv venv
    Pop-Location
    Write-Host "   Created quantum-ai venv" -ForegroundColor Green
}

# talk-to-ai venv
if (Test-Path "talk-to-ai\venv\Scripts\python.exe") {
    Write-Host "   talk-to-ai venv OK" -ForegroundColor Green
} else {
    Write-Host "   talk-to-ai venv missing - creating..." -ForegroundColor Red
    Push-Location talk-to-ai
    python -m venv venv
    Pop-Location
    Write-Host "   Created talk-to-ai venv" -ForegroundColor Green
}

# Root venv
if (Test-Path "venv\Scripts\python.exe") {
    Write-Host "   Root venv OK" -ForegroundColor Green
} else {
    Write-Host "   Root venv missing - creating..." -ForegroundColor Red
    python -m venv venv
    Write-Host "   Created root venv" -ForegroundColor Green
}

# Fix 2: Install dependencies
Write-Host ""
Write-Host "2. Installing dependencies..." -ForegroundColor Yellow

# Root dependencies (Azure Functions)
Write-Host "   Installing root dependencies..." -ForegroundColor Gray
if (Test-Path "requirements.txt") {
    & ".\venv\Scripts\python.exe" -m pip install -q -r requirements.txt
    Write-Host "   Root dependencies installed" -ForegroundColor Green
}

# quantum-ai dependencies
Write-Host "   Installing quantum-ai dependencies..." -ForegroundColor Gray
if (Test-Path "quantum-ai\requirements.txt") {
    & ".\quantum-ai\venv\Scripts\python.exe" -m pip install -q -r quantum-ai\requirements.txt
    Write-Host "   Quantum-AI dependencies installed" -ForegroundColor Green
}

# talk-to-ai dependencies
Write-Host "   Installing talk-to-ai dependencies..." -ForegroundColor Gray
if (Test-Path "talk-to-ai\requirements.txt") {
    & ".\talk-to-ai\venv\Scripts\python.exe" -m pip install -q -r talk-to-ai\requirements.txt
    Write-Host "   Talk-to-AI dependencies installed" -ForegroundColor Green
}

# Fix 3: Verify quantum integration
Write-Host ""
Write-Host "3. Verifying quantum integration..." -ForegroundColor Yellow

Write-Host "   Testing quantum provider..." -ForegroundColor Gray
$quantumTest = "import sys; sys.path.insert(0, 'talk-to-ai/src'); sys.path.insert(0, 'quantum-ai/src'); from quantum_provider import create_quantum_provider; print('   Quantum provider OK')"
& ".\venv\Scripts\python.exe" -c $quantumTest

Write-Host "   Testing chat providers..." -ForegroundColor Gray
$chatTest = "import sys; sys.path.insert(0, 'talk-to-ai/src'); from chat_providers import detect_provider; print('   Chat providers OK')"
& ".\venv\Scripts\python.exe" -c $chatTest

# Fix 4: Check git status
Write-Host ""
Write-Host "4. Checking git status..." -ForegroundColor Yellow
$gitStatus = git status --porcelain 2>&1
if ($gitStatus) {
    Write-Host "   Uncommitted changes detected:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    Write-Host "   Run 'git add .' and 'git commit' to commit changes" -ForegroundColor Gray
} else {
    Write-Host "   No uncommitted changes" -ForegroundColor Green
}

# Fix 5: Test quantum endpoints
Write-Host ""
Write-Host "5. Testing quantum endpoints..." -ForegroundColor Yellow

Write-Host "   Initializing quantum classifier..." -ForegroundColor Gray
$qcTest = "import sys; sys.path.insert(0, 'quantum-ai/src'); from quantum_classifier import QuantumClassifier; qc = QuantumClassifier(); print(f'   QuantumClassifier initialized ({qc.n_qubits} qubits, {qc.n_layers} layers)')"
& ".\venv\Scripts\python.exe" -c $qcTest

# Summary
Write-Host ""
Write-Host "============================" -ForegroundColor Cyan
Write-Host "QAI Workspace Fix Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test chat web: .\start-chat-web.ps1" -ForegroundColor Gray
Write-Host "  2. Run quantum tests: cd quantum-ai; .\venv\Scripts\python.exe src\quantum_classifier.py" -ForegroundColor Gray
Write-Host "  3. Test chat CLI: cd talk-to-ai; .\venv\Scripts\python.exe src\chat_cli.py --provider local" -ForegroundColor Gray
