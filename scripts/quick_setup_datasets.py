"""
Quick Dataset Setup
===================

One-command setup to download and prepare datasets for immediate AI training.

Usage:
    python quick_setup_datasets.py

This script will:
1. Install required dependencies (datasets, tqdm)
2. Download quantum datasets (UCI ML Repository)
3. Download Dolly 15k chat dataset (small, high-quality)
4. Validate all downloads
5. Print training commands

Author: AI Workspace
Date: October 31, 2025
"""

import subprocess
import sys
from pathlib import Path


def check_and_install_dependencies():
    """Check and install required packages."""
    print("\n" + "="*60)
    print("📦 CHECKING DEPENDENCIES")
    print("="*60)
    
    required = ["datasets", "tqdm"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"✗ {package} is missing")
            missing.append(package)
    
    if missing:
        print(f"\n🔧 Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", *missing
        ])
        print("✅ Dependencies installed")
    else:
        print("\n✅ All dependencies satisfied")


def run_script(script_name: str, args: list):
    """Run a Python script with arguments."""
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)] + args
    
    print(f"\n🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    return result.returncode == 0


def main():
    print("="*60)
    print("🎯 QUICK DATASET SETUP")
    print("="*60)
    print("\nThis will download and prepare datasets for AI training.")
    print("Estimated time: 2-5 minutes")
    print("Estimated storage: ~500 MB")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Step 1: Install dependencies
    check_and_install_dependencies()
    
    # Step 2: Download quantum datasets
    print("\n" + "="*60)
    print("STEP 1: Quantum Datasets")
    print("="*60)
    success = run_script("download_datasets.py", ["--category", "quantum"])
    if not success:
        print("⚠️  Quantum dataset download had issues (continuing...)")
    
    # Step 3: Download chat dataset (Dolly - small and high quality)
    print("\n" + "="*60)
    print("STEP 2: Chat Dataset (Dolly 15k)")
    print("="*60)
    success = run_script("download_datasets.py", [
        "--category", "chat",
        "--dataset", "dolly"
    ])
    if not success:
        print("⚠️  Chat dataset download had issues (continuing...)")
    
    # Step 4: Validate
    print("\n" + "="*60)
    print("STEP 3: Validation")
    print("="*60)
    run_script("validate_datasets.py", ["--verbose"])
    
    # Step 5: Print next steps
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    
    print("\n📚 Next Steps:\n")
    
    print("1️⃣  Train Quantum AI Model:")
    print("   cd quantum-ai")
    print("   python .\\train_custom_dataset.py")
    print()
    
    print("2️⃣  Fine-tune Phi-3.6 (requires GPU):")
    print("   cd lora")
    print("   python .\\scripts\\train_lora.py --dataset ..\\..\\datasets\\chat\\dolly --config .\\lora\\lora.yaml --max-train-samples 64")
    print()
    
    print("3️⃣  Download more datasets:")
    print("   python .\\scripts\\download_datasets.py --category chat --dataset openassistant")
    print()
    
    print("4️⃣  View dataset catalog:")
    print("   See AI_DATASETS_CATALOG.md for full dataset list")
    print()
    
    base_dir = Path(__file__).parent.parent
    datasets_dir = base_dir / "datasets"
    print(f"📁 Datasets location: {datasets_dir}")
    print()


if __name__ == "__main__":
    main()
