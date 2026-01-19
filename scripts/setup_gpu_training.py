#!/usr/bin/env python3
"""
GPU-Aware Training Launcher
Automatically configures PyTorch for GPU usage based on available hardware
"""

import subprocess
import sys
import os
import json
from pathlib import Path

# Add workspace root to path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

try:
    import torch
except ImportError:
    print("❌ PyTorch not installed. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "torch"], check=True)
    import torch


def detect_device():
    """Detect available GPU device"""
    
    if torch.cuda.is_available():
        device = "cuda"
        device_name = f"NVIDIA {torch.cuda.get_device_name(0)}"
        device_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU: {device_name} ({device_memory:.1f}GB)")
        return device
    
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        print("✅ GPU: Apple Metal Performance Shaders (MPS)")
        return "mps"
    
    print("⚠️  GPU not available, using CPU")
    return "cpu"


def update_config_for_gpu(config_path, device):
    """Update config file to use detected device"""
    
    if not Path(config_path).exists():
        print(f"⚠️  Config not found: {config_path}")
        return
    
    # Read config
    with open(config_path, 'r') as f:
        content = f.read()
    
    # Check if device is already set
    if f"device: {device}" in content:
        print(f"✅ Config already configured for {device}")
        return
    
    # Update device setting (basic YAML replacement)
    old_patterns = [
        "device: cpu",
        "device: cuda",
        "device: mps",
    ]
    
    for pattern in old_patterns:
        if pattern in content:
            content = content.replace(pattern, f"device: {device}")
    
    # If device not found, add it (for autotrain.yaml specific jobs)
    if "device:" not in content:
        # This is a more complex file, log it
        print(f"⚠️  Could not auto-update device in {config_path}")
        print("    (Config structure may be different)")
        return
    
    with open(config_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {config_path} to use device: {device}")


def enable_gpu_optimizations(device):
    """Enable GPU optimizations"""
    
    if device == "cuda":
        # Enable cuDNN benchmarking for NVIDIA GPUs
        torch.backends.cudnn.benchmark = True
        print("✅ Enabled cuDNN benchmarking (NVIDIA)")
        
        # Set environment variables
        os.environ["CUDA_LAUNCH_BLOCKING"] = "0"
        os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"


def save_device_info(device):
    """Save detected device info to file"""
    
    data_dir = workspace_root / "data_out"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    info_file = data_dir / "gpu_info.json"
    
    gpu_info = {
        "device": device,
        "pytorch_version": torch.__version__,
    }
    
    if device == "cuda":
        gpu_info.update({
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "devices": [
                {
                    "index": i,
                    "name": torch.cuda.get_device_name(i),
                    "memory_gb": torch.cuda.get_device_properties(i).total_memory / 1e9,
                }
                for i in range(torch.cuda.device_count())
            ]
        })
    elif device == "mps":
        gpu_info.update({
            "mps_available": torch.backends.mps.is_available(),
            "mps_built": torch.backends.mps.is_built(),
        })
    
    with open(info_file, 'w') as f:
        json.dump(gpu_info, f, indent=2)
    
    print(f"✅ Saved GPU info to {info_file}")
    return info_file


def main():
    """Main entry point"""
    
    print("=" * 80)
    print("🚀 GPU-AWARE TRAINING LAUNCHER")
    print("=" * 80)
    print()
    
    # Detect device
    device = detect_device()
    
    # Update configs
    print("\n📝 Updating training configs...")
    
    config_files = [
        workspace_root / "config" / "autonomous_training.yaml",
        workspace_root / "config" / "training" / "autotrain.yaml",
    ]
    
    for config_file in config_files:
        if config_file.exists():
            update_config_for_gpu(str(config_file), device)
    
    # Enable optimizations
    print("\n⚙️  Enabling GPU optimizations...")
    enable_gpu_optimizations(device)
    
    # Save device info
    print("\n💾 Saving device information...")
    save_device_info(device)
    
    print("\n" + "=" * 80)
    print("✅ GPU CONFIGURATION COMPLETE")
    print("=" * 80)
    print(f"\n🎯 Device: {device.upper()}")
    print("\n🚀 Ready to train! Start training with:")
    print("   python scripts/training/autotrain.py")
    print("   python scripts/training/autonomous_training_orchestrator.py")
    print("\n📊 Monitor GPU usage with:")
    print("   nvidia-smi -l 1                    (NVIDIA)")
    print("   watch -n 1 nvidia-smi              (NVIDIA)")
    print("   powermetrics -i 1                  (Apple)")


if __name__ == "__main__":
    main()
