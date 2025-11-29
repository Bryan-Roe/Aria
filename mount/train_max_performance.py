"""
Maximum Performance AI Training Script
Utilizes all available CPU/GPU resources for intensive training
"""

import os
import sys
import yaml
import time
import torch
import psutil
from pathlib import Path
from typing import Dict, Any

def check_system_resources():
    """Check and display available system resources"""
    print("=" * 70)
    print("SYSTEM RESOURCES CHECK")
    print("=" * 70)
    
    # CPU info
    cpu_count = psutil.cpu_count(logical=True)
    cpu_physical = psutil.cpu_count(logical=False)
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"\n🖥️  CPU:")
    print(f"   Logical cores: {cpu_count}")
    print(f"   Physical cores: {cpu_physical}")
    print(f"   Current usage: {cpu_percent}%")
    
    # Memory info
    memory = psutil.virtual_memory()
    print(f"\n💾 RAM:")
    print(f"   Total: {memory.total / (1024**3):.1f} GB")
    print(f"   Available: {memory.available / (1024**3):.1f} GB")
    print(f"   Used: {memory.percent}%")
    
    # GPU info
    if torch.cuda.is_available():
        print(f"\n🎮 GPU:")
        for i in range(torch.cuda.device_count()):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"   GPU {i}: {gpu_name}")
            print(f"   Memory: {gpu_memory:.1f} GB")
        device = "cuda"
        compute_capability = torch.cuda.get_device_capability()
        print(f"   CUDA Version: {torch.version.cuda}")
        print(f"   Compute Capability: {compute_capability}")
    else:
        print(f"\n⚠️  No GPU detected - will use CPU only")
        device = "cpu"
    
    # Disk info
    disk = psutil.disk_usage('C:\\')
    print(f"\n💿 Disk (C:):")
    print(f"   Total: {disk.total / (1024**3):.1f} GB")
    print(f"   Free: {disk.free / (1024**3):.1f} GB")
    
    print("\n" + "=" * 70)
    return device, cpu_count

def get_optimal_settings(device: str, cpu_count: int, memory_gb: float) -> Dict[str, Any]:
    """Calculate optimal training settings based on hardware"""
    settings = {}
    
    if device == "cuda":
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        # Aggressive settings for GPU
        if gpu_memory >= 16:
            settings['batch_size'] = 16
            settings['gradient_accumulation'] = 2
            settings['workers'] = min(8, cpu_count // 2)
        elif gpu_memory >= 8:
            settings['batch_size'] = 8
            settings['gradient_accumulation'] = 4
            settings['workers'] = min(6, cpu_count // 2)
        else:
            settings['batch_size'] = 4
            settings['gradient_accumulation'] = 8
            settings['workers'] = min(4, cpu_count // 2)
    else:
        # CPU-only settings
        settings['batch_size'] = 2
        settings['gradient_accumulation'] = 16
        settings['workers'] = max(1, cpu_count - 2)  # Leave 2 cores free
    
    return settings

def monitor_resources():
    """Monitor system resources during training"""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    
    status = f"CPU: {cpu_percent:.1f}% | RAM: {memory.percent:.1f}% ({memory.used / (1024**3):.1f}/{memory.total / (1024**3):.1f} GB)"
    
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.memory_allocated(0) / (1024**3)
        gpu_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        gpu_percent = (gpu_memory / gpu_total) * 100
        status += f" | GPU: {gpu_percent:.1f}% ({gpu_memory:.1f}/{gpu_total:.1f} GB)"
    
    return status

def setup_environment_variables(settings: Dict[str, Any]):
    """Set environment variables for maximum performance"""
    
    # PyTorch optimizations
    os.environ['OMP_NUM_THREADS'] = str(settings['workers'])
    os.environ['MKL_NUM_THREADS'] = str(settings['workers'])
    os.environ['NUMEXPR_NUM_THREADS'] = str(settings['workers'])
    
    # CUDA optimizations (if available)
    if torch.cuda.is_available():
        os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
    
    # Memory optimizations
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    print("\n✓ Environment optimized for maximum performance")

def run_max_training(dataset: str = "../../datasets/chat/dolly", 
                     model: str = "microsoft/Phi-3.5-mini-instruct",
                     epochs: int = 3):
    """Run training with maximum hardware utilization"""
    
    print("\n" + "=" * 70)
    print("MAXIMUM PERFORMANCE AI TRAINING")
    print("=" * 70)
    
    # Check system resources
    device, cpu_count = check_system_resources()
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    
    # Get optimal settings
    settings = get_optimal_settings(device, cpu_count, memory_gb)
    
    print(f"\n📊 OPTIMAL SETTINGS:")
    print(f"   Batch size: {settings['batch_size']}")
    print(f"   Gradient accumulation: {settings['gradient_accumulation']}")
    print(f"   Effective batch size: {settings['batch_size'] * settings['gradient_accumulation']}")
    print(f"   DataLoader workers: {settings['workers']}")
    print(f"   Device: {device.upper()}")
    
    # Setup environment
    setup_environment_variables(settings)
    
    # Build training command
    script_path = Path(__file__).parent.parent / "AI" / "microsoft_phi-silica-3.6_v1" / "scripts" / "train_lora.py"
    config_path = Path(__file__).parent.parent / "AI" / "microsoft_phi-silica-3.6_v1" / "lora" / "lora.yaml"
    
    # Convert dataset path to absolute
    dataset_abs = Path(dataset)
    if not dataset_abs.is_absolute():
        dataset_abs = Path(__file__).parent / dataset
    
    save_dir = Path(__file__).parent.parent / "data_out" / "lora_training" / "max_performance"
    
    cmd = [
        sys.executable,
        str(script_path),
        '--dataset', str(dataset_abs.resolve()),
        '--config', str(config_path),
        '--epochs', str(epochs),
        '--save-dir', str(save_dir)
    ]
    
    print(f"\n🚀 STARTING TRAINING...")
    print(f"   Dataset: {dataset}")
    print(f"   Model: {model}")
    print(f"   Epochs: {epochs}")
    print(f"   Output: data_out/lora_training/max_performance")
    print("\n" + "=" * 70)
    
    # Confirmation
    print("\n⚠️  WARNING: This will use maximum system resources!")
    print("   - High CPU/GPU usage")
    print("   - Significant RAM consumption")
    print("   - May slow down other applications")
    print("\nPress Ctrl+C within 5 seconds to cancel...")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n❌ Training cancelled by user")
        return
    
    print("\n▶️  Training started! Monitor resource usage below:\n")
    
    # Start training with resource monitoring
    import subprocess
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    last_update = time.time()
    
    try:
        for line in process.stdout:
            print(line, end='')
            
            # Update resource monitor every 5 seconds
            if time.time() - last_update > 5:
                print(f"\n📊 Resources: {monitor_resources()}\n")
                last_update = time.time()
        
        process.wait()
        
        if process.returncode == 0:
            print("\n" + "=" * 70)
            print("✅ TRAINING COMPLETED SUCCESSFULLY!")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ TRAINING FAILED")
            print("=" * 70)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Max Performance AI Training")
    parser.add_argument('--dataset', default='../../datasets/chat/dolly', 
                       help='Dataset path')
    parser.add_argument('--model', default='microsoft/Phi-3.5-mini-instruct',
                       help='Model to train')
    parser.add_argument('--epochs', type=int, default=3,
                       help='Number of epochs')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check system resources, do not train')
    
    args = parser.parse_args()
    
    if args.check_only:
        check_system_resources()
    else:
        run_max_training(args.dataset, args.model, args.epochs)
