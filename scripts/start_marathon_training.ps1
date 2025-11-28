# Marathon Training Launcher - Runs training in background
# This script starts the training in a detached process that continues even if terminal is closed

param(
    [switch]$Resume,
    [switch]$ShowWindow
)

$RepoRoot = Split-Path $PSScriptRoot -Parent
$ConfigFile = Join-Path $RepoRoot "autotrain_extended_marathon.yaml"
$LogFile = Join-Path $RepoRoot "data_out\autotrain\marathon_runner.log"
$PidFile = Join-Path $RepoRoot "data_out\autotrain\marathon_runner.pid"

# Ensure data_out directory exists
$DataOutDir = Join-Path $RepoRoot "data_out\autotrain"
if (-not (Test-Path $DataOutDir)) {
    New-Item -Path $DataOutDir -ItemType Directory -Force | Out-Null
}

# Build command
$PythonExe = "python"
$Arguments = @(
    (Join-Path $RepoRoot "scripts\autotrain.py"),
    "--config",
    $ConfigFile
)

if ($Resume) {
    $Arguments += "--resume"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MARATHON TRAINING LAUNCHER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Config: $ConfigFile"
Write-Host "Log: $LogFile"
Write-Host "Resume: $Resume"
Write-Host ""

# Start training process
$ErrorLogFile = Join-Path $RepoRoot "data_out\autotrain\marathon_runner_errors.log"
$ProcessParams = @{
    FilePath = $PythonExe
    ArgumentList = $Arguments
    WorkingDirectory = $RepoRoot
    RedirectStandardOutput = $LogFile
    RedirectStandardError = $ErrorLogFile
    NoNewWindow = (-not $ShowWindow)
}

try {
    $Process = Start-Process @ProcessParams -PassThru
    
    # Save PID
    $Process.Id | Out-File -FilePath $PidFile -Encoding UTF8
    
    Write-Host "✅ Training started successfully!" -ForegroundColor Green
    Write-Host "   PID: $($Process.Id)"
    Write-Host "   Log: $LogFile"
    Write-Host ""
    Write-Host "Monitor progress with:" -ForegroundColor Yellow
    Write-Host "   .\scripts\monitor_marathon.ps1" -ForegroundColor White
    Write-Host "   Get-Content '$LogFile' -Wait" -ForegroundColor White
    Write-Host ""
    Write-Host "Stop training with:" -ForegroundColor Yellow
    Write-Host "   Stop-Process -Id $($Process.Id)" -ForegroundColor White
    
    # Wait a moment to check if process started successfully
    Start-Sleep -Seconds 2
    
    if ($Process.HasExited) {
        Write-Host ""
        Write-Host "⚠️  Process exited immediately. Check log for errors:" -ForegroundColor Red
        Write-Host "   Get-Content '$LogFile' -Tail 50" -ForegroundColor White
        exit 1
    }
    
} catch {
    Write-Host "❌ Failed to start training:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Training is running in background..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
