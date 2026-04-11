"""
Submit a small stabilizer circuit (GHZ 4-qubit) to Azure Quantum and save results.

This script:
1. Connects to Azure Quantum workspace using config/quantum_config.yaml
2. Creates a 4-qubit GHZ stabilizer circuit
3. Submits to an available backend (default: rigetti.sim.qvm)
4. Waits for result and saves JSON compatible with visualize_hardware_results.py

Usage:
  python .\\quantum-ai\\scripts\\submit_small_stabilizer.py [--backend <name>] [--shots <int>]

Example:
  python .\\quantum-ai\\scripts\\submit_small_stabilizer.py --backend rigetti.sim.qvm --shots 1000
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import yaml
from qiskit import QuantumCircuit

# Add parent src to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from azure_quantum_integration import AzureQuantumIntegration

CONFIG_PATH = REPO_ROOT / "config" / "quantum_config.yaml"


def create_ghz_circuit(n_qubits: int = 4) -> QuantumCircuit:
    """Create a GHZ stabilizer circuit for n qubits."""
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def compute_entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p = np.array([v / total for v in counts.values() if v > 0], dtype=float)
    return float(-(p * np.log2(p)).sum())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Submit a small stabilizer circuit to Azure Quantum"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="rigetti.sim.qvm",
        help="Backend name (default: rigetti.sim.qvm)",
    )
    parser.add_argument(
        "--shots", type=int, default=1000, help="Number of shots (default: 1000)"
    )
    parser.add_argument(
        "--n-qubits",
        type=int,
        default=4,
        help="Number of qubits for GHZ circuit (default: 4)",
    )
    args = parser.parse_args()

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    results_dir = (
        REPO_ROOT / Path(cfg["logging"]["results_dir"]).expanduser()
    ).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Azure Quantum Stabilizer Submission ===")
    print(f"Circuit: GHZ {args.n_qubits}-qubit")
    print(f"Backend: {args.backend}, Shots: {args.shots}\n")

    # Create circuit
    qc = create_ghz_circuit(args.n_qubits)
    print("Circuit created:")
    print(qc)

    # Connect to Azure Quantum
    print("\nConnecting to Azure Quantum...")
    azure = AzureQuantumIntegration(config_path=str(CONFIG_PATH))
    try:
        azure.connect()
    except Exception as e:
        print(f"Error connecting to Azure Quantum: {e}")
        print("\nEnsure you have:")
        print("1. Valid Azure credentials configured (az login)")
        print("2. Updated config/quantum_config.yaml with your workspace details")
        print("3. Azure Quantum workspace created and accessible")
        return 1

    # List backends to confirm target is available
    available = azure.list_backends()
    if args.backend not in available:
        print(f"\nWarning: Backend {args.backend} not found in workspace.")
        print(f"Available backends: {', '.join(available)}")
        print("Attempting to use first available backend...")
        args.backend = available[0] if available else None
        if not args.backend:
            print("No backends available. Exiting.")
            return 1

    # Submit job
    print(f"\nSubmitting job to {args.backend}...")
    job_name = f"ghz_{args.n_qubits}q_stabilizer_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    try:
        job = azure.submit_circuit(
            qc, backend_name=args.backend, shots=args.shots, job_name=job_name
        )
        print(f"Job submitted: {job.id()}")
        print("Waiting for results...")
        result_data = azure.get_job_results(job)
    except Exception as e:
        print(f"Error submitting or retrieving job: {e}")
        return 1

    # Compute metadata
    counts = result_data.get("counts", {})
    entropy = compute_entropy(counts)
    max_entropy = float(args.n_qubits)

    # Save in schema compatible with visualizer
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = {
        "job_id": result_data.get("job_id"),
        "counts": {str(k): int(v) for k, v in counts.items()},
        "success": result_data.get("success", False),
        "metadata": {
            "backend": args.backend,
            "n_qubits": args.n_qubits,
            "layers": 1,  # GHZ is effectively 1 layer (H + CNOTs)
            "entanglement": "linear",
            "method": "hardware",
            "circuit": "stabilizer_ghz",
            "shots": args.shots,
            "entropy": entropy,
            "max_entropy": max_entropy,
            "noise": {
                "pauli_px": 0.0,
                "pauli_pz": 0.0,
                "depolarizing_p": 0.0,
                "amp_damp_gamma": 0.0,
                "seed": None,
            },
            "stabilizer": {
                "type": "ghz",
                "clifford_layers": 0,
                "twoq_density": 0.0,
            },
        },
    }

    out_path = results_dir / f"azure_ghz_{args.n_qubits}q_results_{ts}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nResults saved to {out_path}")
    print(f"Unique states: {len(counts)} / {2 ** args.n_qubits}")
    print(
        f"Entropy: {entropy:.3f} / {max_entropy:.3f} ({(entropy/max_entropy*100 if max_entropy>0 else 0):.1f}%)"
    )
    print("\nTip: Now run the visualizer to see side-by-side comparison:")
    print("  python .\\quantum-ai\\scripts\\visualize_hardware_results.py")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
