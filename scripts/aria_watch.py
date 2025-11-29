#!/usr/bin/env python
"""Watch for Aria training completion and auto-test"""
import time
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
adapter_path = REPO_ROOT / "data_out" / "aria_models" / "aria_simple_v1" / "lora_adapter" / "adapter_model.safetensors"
test_script = REPO_ROOT / "scripts" / "aria_test.py"

print("⏳ Watching for training completion...")
print(f"   Checking: {adapter_path.relative_to(REPO_ROOT)}")

while not adapter_path.exists():
    print(".", end="", flush=True)
    time.sleep(2)

print("\n\n✅ Training complete! Running tests...\n")
time.sleep(1)

result = subprocess.run([sys.executable, str(test_script)], cwd=REPO_ROOT)
sys.exit(result.returncode)
