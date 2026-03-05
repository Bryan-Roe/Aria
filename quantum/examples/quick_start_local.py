"""
Minimal quick-start example for local quantum simulation.

Run:
    python quantum/examples/quick_start_local.py

No cloud accounts required — everything runs on your CPU.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Ensure quantum/src is importable
QUANTUM_SRC = Path(__file__).resolve().parents[1] / "src"
if str(QUANTUM_SRC) not in sys.path:
    sys.path.insert(0, str(QUANTUM_SRC))

_qs = importlib.import_module("quantum_quick_start")
run_aer_bell_state = _qs.run_aer_bell_state
run_aer_ghz = _qs.run_aer_ghz
train_local_classifier = _qs.train_local_classifier


def main():
    # 1. Aer Bell state
    print("── Bell State ──")
    bell = run_aer_bell_state(shots=512)
    print(f"   Counts: {bell['counts']}")

    # 2. GHZ 3-qubit
    print("\n── GHZ 3-qubit ──")
    ghz = run_aer_ghz(n_qubits=3, shots=512)
    print(f"   Counts: {ghz['counts']}")

    # 3. Train a tiny classifier on the banknote dataset
    print("\n── Classifier (banknote, 4 qubits, 2 epochs) ──")
    result = train_local_classifier(
        dataset="banknote",
        n_qubits=4,
        n_layers=2,
        epochs=2,
        batch_size=16,
        learning_rate=0.01,
    )
    print(f"   Val accuracy: {result['final_val_acc']:.4f}")
    print(f"   Elapsed:      {result['elapsed_seconds']}s")

    print("\n✓ Local quantum quick-start succeeded.")


if __name__ == "__main__":
    main()
