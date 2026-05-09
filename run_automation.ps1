# Aria Automation Runner PowerShell Script
# Automatically runs core Aria systems and utilities

param(
    [string]$Mode = "standard",
    [switch]$NoTests,
    [switch]$NoValidation,
    [switch]$Verbose
)

# Color codes (using Write-Host for colors)
$Green = "Green"
$Red = "Red"
$Yellow = "Yellow"
$Blue = "Cyan"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Blue
    Write-Host $Title -ForegroundColor $Blue -BackgroundColor Black
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor $Blue
}

function Write-Ok {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor $Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor $Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor $Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor $Blue
}

# Main script
Write-Section "Aria Automation Runner"
Write-Info "Mode: $Mode"

# Get workspace root
$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to workspace
Push-Location $WorkspaceRoot

try {
    # Show workspace info
    Write-Section "Environment Status"
    Write-Ok "Workspace: $WorkspaceRoot"
    Write-Ok "PowerShell Version: $($PSVersionTable.PSVersion)"
    Write-Info "Current Directory: $(Get-Location)"

    # Find Python - prefer .venv first
    Write-Info "Searching for Python..."
    $PythonPath = $null
    
    # Check for .venv environment
    $venvPython = Join-Path $WorkspaceRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        $PythonPath = $venvPython
        Write-Ok "Using .venv Python: $PythonPath"
    }
    else {
        # Fall back to system Python
        if (Get-Command python3.14 -ErrorAction SilentlyContinue) {
            $PythonPath = (Get-Command python3.14).Source
        }
        elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
            $PythonPath = (Get-Command python3).Source
        }
        elseif (Get-Command python -ErrorAction SilentlyContinue) {
            $PythonPath = (Get-Command python).Source
        }

        if (-not $PythonPath) {
            Write-Error-Custom "Python not found in PATH or .venv"
            exit 1
        }

        Write-Ok "Python found: $PythonPath"
    }

    # Run automation
    Write-Section "Running Aria Automation"

    if (Test-Path "run_automation.py") {
        Write-Info "Executing run_automation.py..."
        & $PythonPath run_automation.py

        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Automation completed successfully!"
        }
        else {
            Write-Warning-Custom "Automation completed with warnings or errors"
        }
    }
    else {
        Write-Error-Custom "run_automation.py not found"
        exit 1
    }

    Write-Section "Aria Automation Complete"
    Write-Ok "All tasks finished"

}
catch {
    Write-Error-Custom "Error: $_"
    exit 1
}
finally {
    Pop-Location
}
