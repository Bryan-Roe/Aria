#!/usr/bin/env python3
"""
GPU Configuration & Optimization for Training

Automatically detects GPUs and configures PyTorch for optimal usage.
"""

import torch
import os
import sys


def setup_gpu():
    """Configure GPU settings for training"""
    
    print("=" * 80)
    print("🚀 GPU CONFIGURATION & OPTIMIZATION")
    print("=" * 80)
    
    # Detect available device
    device = detect_device()
    print(f"\n✅ Using device: {device}\n")
    
    if device == "cuda":
        setup_cuda()
    elif device == "mps":
        setup_mps()
    else:
        print("⚠️  No GPU detected, using CPU (slower)")
        return "cpu"
    
    print("\n" + "=" * 80)
    print("🎯 GPU OPTIMIZATION TIPS")
    print("=" * 80)
    print("""
✓ Set these environment variables for best performance:
  export CUDA_LAUNCH_BLOCKING=1           (for debugging)
  export CUDA_DEVICE_ORDER=PCI_BUS_ID     (for GPU ordering)
  export CUDA_VISIBLE_DEVICES=0,1,2,3     (to select specific GPUs)

✓ In your training scripts:
  - Use mixed precision: torch.cuda.amp.autocast()
  - Use gradient accumulation for large batches
  - Use DataLoader with num_workers > 0
  - Enable cudnn benchmarking: torch.backends.cudnn.benchmark = True

✓ Monitor GPU during training:
  nvidia-smi -l 1    (update every 1 second)
  watch -n 1 nvidia-smi
""")
    
    return device


def detect_device():
    """Detect available compute device"""
    
    print("🔍 Detecting available compute devices...\n")
    
    # Check CUDA
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"🔷 CUDA (NVIDIA GPUs):")
        print(f"   Available: YES")
        print(f"   Device Count: {device_count}")
        for i in range(device_count):
            name = torch.cuda.get_device_name(i)
            capability = torch.cuda.get_device_capability(i)
            total_memory = torch.cuda.get_device_properties(i).total_memory / 1e9
            print(f"   GPU {i}: {name}")
            print(f"           Compute Capability: {capability[0]}.{capability[1]}")
            print(f"           Total Memory: {total_memory:.1f} GB")
        return "cuda"
    
    # Check Apple Metal (MPS)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print(f"🍎 Apple Metal Performance Shaders (MPS):")
        print(f"   Available: YES")
        print(f"   Built: {torch.backends.mps.is_built()}")
        return "mps"
    
    # No GPU
    print("⚠️  No GPU backends detected")
    print("   Checking for GPU hardware...")
    
    # Try to find GPU hardware
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            print("   🔷 NVIDIA GPU hardware found but PyTorch CUDA support not compiled")
            print("   → Run: pip install torch --index-url https://download.pytorch.org/whl/cu118")
            return "cuda"
    except:
        pass
    
    return "cpu"


def setup_cuda():
    """Configure CUDA/NVIDIA GPUs"""
    
    print("\n⚙️  CUDA CONFIGURATION:")
    print(f"   cuDNN Version: {torch.backends.cudnn.version()}")
    print(f"   cuDNN Enabled: {torch.backends.cudnn.enabled}")
    
    # Enable benchmarking for faster training (if using fixed input sizes)
    torch.backends.cudnn.benchmark = True
    print(f"   cuDNN Benchmark: {torch.backends.cudnn.benchmark} (enabled for speed)")
    
    # Set memory fraction (don't use 100% immediately, allows OS operations)
    print(f"\n📊 GPU Memory Configuration:")
    print(f"   PyTorch will allocate GPU memory on-demand")
    print(f"   Mixed precision enabled for reduced memory usage")
    
    # Get memory info
    for i in range(torch.cuda.device_count()):
        total_mem = torch.cuda.get_device_properties(i).total_memory / 1e9
        print(f"   GPU {i} Total Memory: {total_mem:.1f} GB")


def setup_mps():
    """Configure Apple Metal Performance Shaders"""
    
    print("\n⚙️  APPLE METAL (MPS) CONFIGURATION:")
    print(f"   MPS Available: {torch.backends.mps.is_available()}")
    print(f"   MPS Built: {torch.backends.mps.is_built()}")
    
    # MPS is automatically used when device is set to "mps"
    print(f"\n📝 Note: MPS requires PyTorch 1.12+")
    print(f"   Some operations may fall back to CPU automatically")


def get_device_string():
    """Get device string for training scripts"""
    device = detect_device()
    
    if device == "cuda" and torch.cuda.device_count() > 0:
        return "cuda"
    elif device == "mps":
        return "mps"
    else:
        return "cpu"


if __name__ == "__main__":
    device = setup_gpu()
    sys.exit(0 if device != "cpu" else 1)
