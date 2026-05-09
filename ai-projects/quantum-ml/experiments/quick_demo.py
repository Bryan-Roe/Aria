"""
Quick Experiment Demo - Runs a single quick experiment to demonstrate capabilities
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner(text):
    """Print a colorful banner"""
    print(f"\n\033[96m{'='*70}\033[0m")
    print(f"\033[96m{text.center(70)}\033[0m")
    print(f"\033[96m{'='*70}\033[0m\n")


print_banner("QUANTUM AI - QUICK EXPERIMENT DEMO")

print("\033[93m📊 Running Extended Datasets Experiment (XOR Dataset)\033[0m")
print(
    "\033[90mThis demonstrates quantum classifier on linearly inseparable data\033[0m\n"
)

try:
    # Import extended datasets module
    sys.path.insert(0, str(Path(__file__).parent))
    import extended_datasets as ed

    print("\033[92m▶ Starting XOR Dataset Experiment...\033[0m\n")
    start_time = time.time()

    # Run XOR experiment
    ed.run_xor_dataset()

    duration = time.time() - start_time

    print("\n\033[92m✓ XOR Experiment Completed!\033[0m")
    print(f"\033[90m   Duration: {duration:.2f} seconds\033[0m\n")

    # Check results
    results_dir = Path(__file__).parent.parent / "results" / "extended_datasets"
    if results_dir.exists():
        xor_file = results_dir / "xor_dataset.png"
        if xor_file.exists():
            size_kb = xor_file.stat().st_size / 1024
            print("\033[96m📁 Generated File:\033[0m")
            print(f"   {xor_file.name} ({size_kb:.1f} KB)")
            print(f"   Location: {xor_file}\n")

    print("\033[96m🎯 What This Demonstrates:\033[0m")
    print("   • Quantum classifier can learn XOR function")
    print("   • Classical linear models fail on this problem")
    print("   • Quantum circuits provide non-linear transformations")
    print("   • Visualization shows decision boundary\n")

    print("\033[96m📚 To Run All Experiments:\033[0m")
    print("   python .\\experiments\\run_all_experiments.py\n")

    print_banner("DEMO COMPLETE!")

except Exception as e:
    print(f"\n\033[91m✗ Error: {e}\033[0m")
    import traceback

    traceback.print_exc()
