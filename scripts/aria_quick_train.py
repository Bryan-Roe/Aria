#!/usr/bin/env python
"""Ultra-fast Aria movement training - completes in ~10-20 seconds"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "venv" / "Scripts" / "python.exe"
TRAIN_SCRIPT = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"

cmd = [
    str(VENV_PYTHON),
    str(TRAIN_SCRIPT),
    "--dataset", "datasets/chat/aria_expanded",
    "--hf-model-id", "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "--learning-rate", "0.005",  # MUCH higher - override base model
    "--lora-dropout", "0.0",
    "--epochs", "10",  # Many more epochs to drill in the pattern
    "--max-train-samples", "63",  # Use all samples
    "--max-eval-samples", "5",
    "--save-dir", "data_out/aria_models/aria_expanded_v2",
    "--device", "auto",
    "--no-stream",
    "--train-batch-size", "4"  # Smaller for more gradient updates
]

print("🎨 Training AGGRESSIVE Aria Visuals (10 epochs, LR 0.005)")
print("=" * 80)
print(f"Command: {' '.join(cmd)}\n")

result = subprocess.run(cmd, cwd=REPO_ROOT)
sys.exit(result.returncode)
