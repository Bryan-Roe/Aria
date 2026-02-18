#!/usr/bin/env python3
"""
GPU Training Orchestrator
One-command GPU-aware training launcher with monitoring

Usage:
    python gpu_train.py                    # Start GPU autotrain
    python gpu_train.py --autonomous       # Start autonomous cycles
    python gpu_train.py --monitor          # Monitor active training
    python gpu_train.py --status          # Show training status
"""

import subprocess
import sys
import json
import time
from pathlib import Path
from argparse import ArgumentParser
from datetime import datetime

workspace_root = Path(__file__).resolve().parent.parent  # repo root (one level up from scripts/)
sys.path.insert(0, str(workspace_root))


def run_command(cmd, description=""):
    """Run shell command and handle errors"""
    if description:
        print(f"\n▶️  {description}...")
    print(f"   Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=workspace_root)
    return result.returncode == 0


def detect_gpu():
    """Quick GPU detection"""
    try:
        import torch
        if torch.cuda.is_available():
            return f"NVIDIA ({torch.cuda.get_device_name(0)})"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "Apple Metal"
    except:
        pass
    return "CPU (No GPU detected)"


def setup_gpu():
    """Setup GPU configuration"""
    print("\n" + "="*80)
    print("🚀 GPU TRAINING ORCHESTRATOR")
    print("="*80)
    print(f"\n🔍 GPU Detection: {detect_gpu()}")
    
    # Setup GPU training
    if not run_command(
        [sys.executable, "scripts/setup_gpu_training.py"],
        "Setting up GPU configuration"
    ):
        print("⚠️  GPU setup completed with warnings")
    
    # Save config
    config = {
        "timestamp": datetime.now().isoformat(),
        "gpu": detect_gpu(),
        "command": " ".join(sys.argv),
    }
    
    config_file = workspace_root / "data_out" / "gpu_training_config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def start_autotrain():
    """Start autotrain on GPU"""
    print("\n" + "="*80)
    print("🎯 STARTING AUTOTRAIN (14 GPU JOBS)")
    print("="*80)
    
    run_command(
        [sys.executable, "scripts/training/autotrain.py"],
        "Starting 14-job GPU training pipeline"
    )


def start_autonomous():
    """Start autonomous training"""
    print("\n" + "="*80)
    print("🔄 STARTING AUTONOMOUS TRAINING (CONTINUOUS)")
    print("="*80)
    
    print("\n📝 Autonomous training will:")
    print("   • Run 30-minute training cycles")
    print("   • Self-discover datasets")
    print("   • Adapt epochs based on performance")
    print("   • Auto-deploy best models")
    print("   • Log to: data_out/autonomous_training.log")
    print("\n💡 To trigger immediate cycle: pkill -USR1 -f autonomous_training")
    print("💡 To stop gracefully: pkill -TERM -f autonomous_training")
    
    input("\n✅ Press Enter to start...")
    
    run_command(
        [sys.executable, "scripts/training/autonomous_training_orchestrator.py"],
        "Starting autonomous training orchestrator"
    )


def monitor_training():
    """Monitor active training"""
    print("\n" + "="*80)
    print("📊 MONITORING GPU TRAINING")
    print("="*80)
    
    print("\n📈 Training Metrics:")
    print("   File: data_out/autotrain/status.json")
    print("   Updates: Every job completion")
    
    print("\n🖥️  GPU Utilization:")
    print("   Command: nvidia-smi -l 1")
    print("   OR: watch -n 1 nvidia-smi")
    
    print("\n📊 Dashboard:")
    print("   URL: http://localhost:8765")
    print("   Start: python dashboard/app.py")
    
    print("\n📝 Full Logs:")
    print("   File: data_out/autotrain/job_*.log")
    print("   View: tail -f data_out/autotrain/job_*.log")
    
    # Show current status
    status_file = workspace_root / "data_out" / "autotrain" / "status.json"
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        print(f"\n✅ Current Status:")
        print(f"   Total Jobs: {status.get('total_jobs', '?')}")
        print(f"   Completed: {status.get('completed_jobs', 0)}")
        print(f"   Failed: {status.get('failed_jobs', 0)}")
        print(f"   Running: {status.get('running_jobs', 0)}")
        print(f"   Last Update: {status.get('last_updated', 'Unknown')}")
    
    # Run monitoring loop
    print("\n🔄 Live Monitoring (press Ctrl+C to exit):")
    try:
        while True:
            # Check status
            if status_file.exists():
                with open(status_file) as f:
                    status = json.load(f)
                completed = status.get('completed_jobs', 0)
                total = status.get('total_jobs', 1)
                progress = (completed / total) * 100
                print(f"   [{completed}/{total}] {progress:.0f}% complete", end='\r')
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")


def show_status():
    """Show training status"""
    print("\n" + "="*80)
    print("📊 TRAINING STATUS")
    print("="*80)
    
    status_file = workspace_root / "data_out" / "autotrain" / "status.json"
    autonomous_file = workspace_root / "data_out" / "autonomous_training_status.json"
    
    # Autotrain status
    print("\n🎯 Autotrain Status:")
    if status_file.exists():
        with open(status_file) as f:
            status = json.load(f)
        print(json.dumps(status, indent=2))
    else:
        print("   No autotrain data (not started yet)")
    
    # Autonomous status
    print("\n🔄 Autonomous Training Status:")
    if autonomous_file.exists():
        with open(autonomous_file) as f:
            status = json.load(f)
        print(json.dumps(status, indent=2))
    else:
        print("   No autonomous training data (not started yet)")
    
    # GPU info
    print("\n🖥️  GPU Information:")
    gpu_file = workspace_root / "data_out" / "gpu_info.json"
    if gpu_file.exists():
        with open(gpu_file) as f:
            gpu_info = json.load(f)
        print(json.dumps(gpu_info, indent=2))
    else:
        print("   GPU info not available (run setup first)")


def main():
    """Main entry point"""
    parser = ArgumentParser(description="GPU Training Orchestrator")
    parser.add_argument("--autonomous", action="store_true", help="Start autonomous training")
    parser.add_argument("--monitor", action="store_true", help="Monitor active training")
    parser.add_argument("--status", action="store_true", help="Show training status")
    parser.add_argument("--no-setup", action="store_true", help="Skip GPU setup")
    
    args = parser.parse_args()
    
    # Setup GPU (unless skipped)
    if not args.no_setup:
        setup_gpu()
    
    # Execute requested action
    if args.autonomous:
        start_autonomous()
    elif args.monitor:
        monitor_training()
    elif args.status:
        show_status()
    else:
        # Default: autotrain
        start_autotrain()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
