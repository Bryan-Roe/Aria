#!/usr/bin/env python3
"""
Quantum GGUF Quick Start - Setup and validation script
"""

import sys
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parents[1]


def check_dependencies():
    """Check required dependencies"""
    print("\n📦 Checking dependencies...")
    
    dependencies = {
        "yaml": "PyYAML",
        "numpy": "numpy",
    }
    
    optional = {
        "llama_cpp": "llama-cpp-python (for serving)",
        "pennylane": "PennyLane (for quantum features)",
        "qiskit": "Qiskit (alternative quantum backend)",
    }
    
    missing_required = []
    missing_optional = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name}")
            missing_required.append(name)
    
    for module, name in optional.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ⚠️  {name} (optional)")
            missing_optional.append(name)
    
    if missing_required:
        print(f"\n❌ Missing required packages:")
        for pkg in missing_required:
            print(f"   pip install {pkg}")
        return False
    
    return True


def create_directory_structure():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    dirs = [
        REPO_ROOT / "data_out" / "quantum_gguf_training",
        REPO_ROOT / "data_out" / "quantum_gguf_training" / "lora_models",
        REPO_ROOT / "data_out" / "quantum_gguf_training" / "gguf_models",
        REPO_ROOT / "data_out" / "quantum_gguf_training" / "quantum_data",
        REPO_ROOT / "data_out" / "quantum_gguf_training" / "metrics",
        REPO_ROOT / "data_out" / "quantum_gguf_training" / "reports",
        REPO_ROOT / "scripts" / "quantum_gguf",
        REPO_ROOT / "config" / "training",
        REPO_ROOT / "deployed_models",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path.relative_to(REPO_ROOT)}")
    
    return True


def check_config():
    """Check configuration file"""
    print("\n⚙️  Checking configuration...")
    
    config_path = REPO_ROOT / "config" / "training" / "quantum_gguf.yaml"
    
    if config_path.exists():
        print(f"  ✅ Config found: {config_path.relative_to(REPO_ROOT)}")
        return True
    else:
        print(f"  ⚠️  Config not found: {config_path.relative_to(REPO_ROOT)}")
        return False


def check_modules():
    """Check quantum_gguf modules"""
    print("\n📦 Checking quantum_gguf modules...")
    
    modules = [
        "gguf_orchestrator.py",
        "gguf_registry.py",
        "quantum_gguf_integration.py",
        "gguf_serving.py",
        "gguf_validation.py",
    ]
    
    module_dir = REPO_ROOT / "scripts" / "quantum_gguf"
    
    for module in modules:
        path = module_dir / module
        if path.exists():
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ {module} (missing)")
    
    return True


def check_datasets():
    """Check datasets"""
    print("\n📊 Checking datasets...")
    
    dataset_dir = REPO_ROOT / "datasets"
    
    if dataset_dir.exists():
        subdirs = [d for d in dataset_dir.iterdir() if d.is_dir()]
        if subdirs:
            print(f"  ✅ Found {len(subdirs)} dataset categories:")
            for subdir in subdirs:
                files = list(subdir.glob("*.jsonl"))
                print(f"     - {subdir.name}: {len(files)} files")
            return True
        else:
            print(f"  ⚠️  No datasets found in {dataset_dir}")
            return False
    else:
        print(f"  ⚠️  Datasets directory not found: {dataset_dir}")
        return False


def print_quick_commands():
    """Print quick commands"""
    print("\n" + "="*70)
    print("🚀 QUICK START COMMANDS")
    print("="*70)
    
    commands = [
        ("Dry-run validation", "python scripts/quantum_gguf/gguf_orchestrator.py --dry-run"),
        ("Full pipeline", "python scripts/quantum_gguf/gguf_orchestrator.py --full"),
        ("Check registry", "python scripts/quantum_gguf/gguf_orchestrator.py --registry"),
        ("Create quantum dataset", "python scripts/quantum_gguf/quantum_gguf_integration.py"),
        ("Validate model", "python scripts/quantum_gguf/gguf_validation.py"),
        ("List status", "python scripts/quantum_gguf/gguf_orchestrator.py --status"),
    ]
    
    for i, (desc, cmd) in enumerate(commands, 1):
        print(f"\n{i}. {desc}")
        print(f"   $ {cmd}")
    
    print("\n" + "="*70 + "\n")


def main():
    """Run quickstart"""
    print("\n" + "🔮"*35)
    print("QUANTUM GGUF INFRASTRUCTURE - QUICKSTART")
    print("🔮"*35)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Directory Structure", create_directory_structure),
        ("Configuration", check_config),
        ("Modules", check_modules),
        ("Datasets", check_datasets),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            result = check_func()
            results[name] = result
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("✅ SETUP SUMMARY")
    print("="*70)
    
    for name, passed in results.items():
        status = "✅" if passed else "⚠️"
        print(f"{status} {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 Infrastructure is ready!")
        print_quick_commands()
        return 0
    else:
        print("\n⚠️  Some checks failed. Please review above.")
        print("For help, see: docs/QUANTUM_GGUF_INFRASTRUCTURE.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
