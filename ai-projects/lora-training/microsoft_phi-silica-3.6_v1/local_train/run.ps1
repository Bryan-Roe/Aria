# Quick-start runner for local LoRA fine-tuning
# PowerShell convenience script for common training workflows

param(
    [Parameter(Position = 0, Mandatory = $false)]
    [ValidateSet("train", "quick-test", "resume", "evaluate", "help")]
    [string]$Action = "help",

    [Parameter(Mandatory = $false)]
    [string]$Config = "local_config.yaml",

    [Parameter(Mandatory = $false)]
    [string]$Checkpoint = "",

    [Parameter(Mandatory = $false)]
    [int]$MaxSamples = 0,

    [Parameter(Mandatory = $false)]
    [switch]$Use4Bit,

    [Parameter(Mandatory = $false)]
    [switch]$Use8Bit
)

function Show-Help {
    Write-Host @"
Local LoRA Fine-Tuning - Quick Runner

USAGE:
    .\run.ps1 <action> [options]

ACTIONS:
    train         Full training run with config defaults
    quick-test    Fast test with 10 samples (validate setup)
    resume        Resume from checkpoint (requires -Checkpoint)
    evaluate      Evaluate trained model (requires -Checkpoint)
    help          Show this help message

OPTIONS:
    -Config <path>       Path to config YAML (default: local_config.yaml)
    -Checkpoint <path>   Path to checkpoint directory
    -MaxSamples <n>      Limit dataset size (for testing)
    -Use4Bit             Enable 4-bit quantization (QLoRA)
    -Use8Bit             Enable 8-bit quantization

EXAMPLES:
    # Quick validation (10 samples)
    .\run.ps1 quick-test

    # Full training
    .\run.ps1 train

    # Train with 4-bit quantization
    .\run.ps1 train -Use4Bit

    # Train on first 100 samples
    .\run.ps1 train -MaxSamples 100

    # Resume from checkpoint
    .\run.ps1 resume -Checkpoint outputs/checkpoint-500

    # Evaluate trained model
    .\run.ps1 evaluate -Checkpoint outputs/final_model

SETUP:
    1. Create venv:       python -m venv venv
    2. Activate:          .\venv\Scripts\Activate.ps1
    3. Install deps:      pip install -r requirements.txt
    4. Prepare data:      Create data/train.json and data/test.json
    5. Run quick test:    .\run.ps1 quick-test

"@
}

function Invoke-Training {
    param(
        [string]$ConfigPath,
        [int]$Samples,
        [string]$CheckpointPath,
        [bool]$EvalOnly,
        [bool]$Quant4Bit,
        [bool]$Quant8Bit
    )

    # Build command
    $cmd = "python train_local.py --config `"$ConfigPath`""

    if ($Samples -gt 0) {
        $cmd += " --max-samples $Samples"
    }

    if ($CheckpointPath) {
        $cmd += " --resume-from `"$CheckpointPath`""
    }

    if ($EvalOnly) {
        $cmd += " --eval-only"
    }

    if ($Quant4Bit) {
        $cmd += " --use-4bit"
    }

    if ($Quant8Bit) {
        $cmd += " --use-8bit"
    }

    Write-Host "Running: $cmd" -ForegroundColor Cyan
    Write-Host ""

    Invoke-Expression $cmd
}

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "WARNING: Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Execute action
switch ($Action) {
    "train" {
        Write-Host "=== Starting Full Training ===" -ForegroundColor Green
        Invoke-Training -ConfigPath $Config -Samples $MaxSamples `
                        -Quant4Bit:$Use4Bit -Quant8Bit:$Use8Bit
    }

    "quick-test" {
        Write-Host "=== Quick Test (10 samples) ===" -ForegroundColor Green
        $testSamples = if ($MaxSamples -gt 0) { $MaxSamples } else { 10 }
        Invoke-Training -ConfigPath $Config -Samples $testSamples `
                        -Quant4Bit:$Use4Bit -Quant8Bit:$Use8Bit
    }

    "resume" {
        if (-not $Checkpoint) {
            Write-Host "ERROR: -Checkpoint is required for resume action" -ForegroundColor Red
            Write-Host "Example: .\run.ps1 resume -Checkpoint outputs/checkpoint-500" -ForegroundColor Yellow
            exit 1
        }

        Write-Host "=== Resuming from Checkpoint ===" -ForegroundColor Green
        Write-Host "Checkpoint: $Checkpoint" -ForegroundColor Cyan
        Invoke-Training -ConfigPath $Config -CheckpointPath $Checkpoint `
                        -Samples $MaxSamples -Quant4Bit:$Use4Bit -Quant8Bit:$Use8Bit
    }

    "evaluate" {
        if (-not $Checkpoint) {
            Write-Host "ERROR: -Checkpoint is required for evaluate action" -ForegroundColor Red
            Write-Host "Example: .\run.ps1 evaluate -Checkpoint outputs/final_model" -ForegroundColor Yellow
            exit 1
        }

        Write-Host "=== Evaluating Model ===" -ForegroundColor Green
        Write-Host "Checkpoint: $Checkpoint" -ForegroundColor Cyan
        Invoke-Training -ConfigPath $Config -CheckpointPath $Checkpoint `
                        -EvalOnly $true -Quant4Bit:$Use4Bit -Quant8Bit:$Use8Bit
    }

    "help" {
        Show-Help
    }

    default {
        Write-Host "Unknown action: $Action" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
