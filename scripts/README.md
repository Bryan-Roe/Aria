# Scripts

This folder contains small utilities for working with the repo.

## run_local_lora_training.py

One-command offline LoRA training for TinyLlama on CPU. It auto-creates a venv under `AI/microsoft_phi-silica-3.6_v1/local_train`, installs requirements, and runs the training script with a small dataset and minimal epochs so it completes quickly on Windows.

Usage (PowerShell):

```powershell
# From repo root
python .\scripts\run_local_lora_training.py

# Customize
python .\scripts\run_local_lora_training.py --max-samples 50 --epochs 2 --config local_config.yaml

# Force reinstall deps in the venv
python .\scripts\run_local_lora_training.py --reinstall

# Preview without training
python .\scripts\run_local_lora_training.py --dry-run
```

Outputs are written to `AI/microsoft_phi-silica-3.6_v1/local_train/outputs/final` (LoRA adapter + tokenizer files).

Notes:

- 4-bit quantization is disabled by default for Windows/CPU; the tiny training still runs fast with TinyLlama.
- The runner sets `HF_HUB_DISABLE_SYMLINKS_WARNING=1` to reduce warnings on Windows filesystems.

## Start-LocalLoraTraining.ps1 (Windows Task Scheduler friendly)

PowerShell wrapper that resolves paths, sets env, logs to a timestamped file, and runs the Python runner.

Usage (PowerShell):

```powershell
# From repo root (or any folder)
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -MaxSamples 10 -Epochs 1 -Config local_config.yaml

# Optional flags
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -Reinstall
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\Start-LocalLoraTraining.ps1 -DryRun
```

Logs:

- Default log directory: `AI/microsoft_phi-silica-3.6_v1/local_train/logs`
- File name: `train_YYYYMMDD_HHMMSS.log`

Task Scheduler tip:

- Action: `Start a program`
- Program/script: `powershell.exe`
- Add arguments:
  `-NoProfile -ExecutionPolicy Bypass -File "C:\Users\Bryan\OneDrive\AI\scripts\Start-LocalLoraTraining.ps1" -MaxSamples 10 -Epochs 1`
- Start in: `C:\Users\Bryan\OneDrive\AI`

## VS Code task: one-click run

A task labeled `Run: Local LoRA training` is available. Open the Command Palette → “Run Task…” → select it to run.
