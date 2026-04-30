# Maximum Performance AI Training
# Quick launcher for intensive training

Write-Host "MAX PERFORMANCE AI TRAINING" -ForegroundColor Cyan
Write-Host "========================================================================"
Write-Host ""

# Check if we're in the mount directory
if (-not (Test-Path "train_max_performance.py")) {
    Write-Host "Error: Run this script from the mount directory" -ForegroundColor Red
    Write-Host "   cd C:\Users\Bryan\OneDrive\AI\mount" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
if (Test-Path "..\venv\Scripts\Activate.ps1") {
    Write-Host "Activating workspace virtual environment..." -ForegroundColor Cyan
    & ..\venv\Scripts\Activate.ps1
} else {
    Write-Host "No virtual environment found, using system Python" -ForegroundColor Yellow
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Cyan
$depsCheck = python -c "import torch, transformers, datasets, peft; print('OK')" 2>&1

if ($depsCheck -notmatch "OK") {
    Write-Host "Missing dependencies. Installing..." -ForegroundColor Yellow
    pip install torch transformers datasets peft accelerate psutil
}

Write-Host ""

# Menu
Write-Host "SELECT TRAINING MODE:" -ForegroundColor Cyan
Write-Host "========================================================================"
Write-Host ""
Write-Host "1. QUICK TEST (64 samples, 1 epoch) - 5-10 minutes"
Write-Host "2. MEDIUM INTENSITY (500 samples, 2 epochs) - 30-60 minutes"
Write-Host "3. MAXIMUM POWER (Full dataset, 3 epochs) - 2-4 hours"
Write-Host "4. MULTI-DATASET (All datasets, 3 epochs) - 4-8 hours"
Write-Host "5. CHECK RESOURCES ONLY"
Write-Host "0. Cancel"
Write-Host ""

$choice = Read-Host "Enter choice (0-5)"

$workspaceRoot = "C:\Users\Bryan\OneDrive\AI"

switch ($choice) {
    "1" {
        Write-Host "`nStarting QUICK TEST..." -ForegroundColor Green
        python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\dolly" --epochs 1
    }
    "2" {
        Write-Host "`nStarting MEDIUM INTENSITY training..." -ForegroundColor Green
        python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\mixed_chat" --epochs 2
    }
    "3" {
        Write-Host "`nStarting MAXIMUM POWER training..." -ForegroundColor Green
        Write-Host "WARNING: This will max out your system for 2-4 hours!" -ForegroundColor Yellow
        $confirm = Read-Host "Continue? (yes/no)"
        if ($confirm -eq "yes") {
            python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\dolly" --epochs 3
        } else {
            Write-Host "Cancelled" -ForegroundColor Yellow
        }
    }
    "4" {
        Write-Host "`nStarting MULTI-DATASET training..." -ForegroundColor Green
        Write-Host "WARNING: This will take 4-8 hours and max out your system!" -ForegroundColor Yellow
        $confirm = Read-Host "Continue? (yes/no)"
        if ($confirm -eq "yes") {
            # Train on multiple datasets sequentially
            Write-Host "`nTraining on Dolly dataset..." -ForegroundColor Cyan
            python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\dolly" --epochs 2

            Write-Host "`nTraining on OpenAssistant dataset..." -ForegroundColor Cyan
            python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\openassistant" --epochs 2

            Write-Host "`nTraining on Mixed Chat dataset..." -ForegroundColor Cyan
            python train_max_performance.py --dataset "$workspaceRoot\datasets\chat\mixed_chat" --epochs 1
        } else {
            Write-Host "Cancelled" -ForegroundColor Yellow
        }
    }
    "5" {
        Write-Host "`nChecking system resources..." -ForegroundColor Green
        python train_max_performance.py --check-only
    }
    "0" {
        Write-Host "`nCancelled" -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "`nInvalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "========================================================================"
Write-Host "Done!" -ForegroundColor Green
