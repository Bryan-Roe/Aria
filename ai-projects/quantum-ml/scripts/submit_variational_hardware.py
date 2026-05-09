"""
Submit variational quantum circuits to Azure Quantum hardware for comparison
with local MPS simulations.

This tests whether hardware can reproduce the entropy and state distribution
patterns we observed in MPS simulations at different layer depths.

Usage:
  python .\\quantum-ai\\scripts\\submit_variational_hardware.py --backend rigetti.sim.qvm --n-qubits 4 --layers 2
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

# Add parent src to path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from azure_quantum_integration import AzureQuantumIntegration

CONFIG_PATH = REPO_ROOT / "config" / "quantum_config.yaml"


def create_variational_circuit(
    n_qubits: int, n_layers: int, entanglement: str = "linear"
) -> QuantumCircuit:
    """
    Create a variational circuit matching the MPS simulation pattern.

    Same structure as run_simulated_circuit.py for direct comparison.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Initial layer
    for i in range(n_qubits):
        qc.h(i)

    for layer in range(n_layers):
        # Parameterized single-qubit rotations
        for i in range(n_qubits):
            qc.ry(np.pi / 4 * (layer + 1), i)
            qc.rz(np.pi / 3 * (layer + 1), i)

        # Entanglement pattern
        if entanglement == "linear":
            for i in range(n_qubits - 1):
                qc.cx(i, i + 1)
        elif entanglement == "full":
            for i in range(n_qubits):
                for j in range(i + 1, n_qubits):
                    qc.cx(i, j)
        else:  # circular (default)
            for i in range(n_qubits):
                qc.cx(i, (i + 1) % n_qubits)

        qc.barrier()

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
        description="Submit variational circuits to Azure Quantum"
    )
    parser.add_argument(
        "--backend", type=str, default="rigetti.sim.qvm", help="Backend name"
    )
    parser.add_argument(
        "--n-qubits", type=int, default=4, help="Number of qubits (default: 4)"
    )
    parser.add_argument(
        "--layers", type=int, default=2, help="Number of layers (default: 2)"
    )
    parser.add_argument(
        "--entanglement",
        choices=["linear", "circular", "full"],
        default="linear",
        help="Entanglement pattern (default: linear)",
    )
    parser.add_argument(
        "--shots", type=int, default=1000, help="Number of shots (default: 1000)"
    )
    args = parser.parse_args()

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    results_dir = (
        REPO_ROOT / Path(cfg["logging"]["results_dir"]).expanduser()
    ).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Variational Circuit Hardware Submission ===")
    print(
        f"Circuit: {args.n_qubits}-qubit, {args.layers} layers, {args.entanglement} entanglement"
    )
    print(f"Backend: {args.backend}, Shots: {args.shots}\n")

    # Create circuit
    qc = create_variational_circuit(args.n_qubits, args.layers, args.entanglement)
    print("Circuit created:")
    print(f"  Depth: {qc.depth()}, Gates: {sum(qc.count_ops().values())}")
    print(f"  Structure: H + {args.layers}×(RY+RZ+{args.entanglement.upper()})\n")

    # Connect and submit
    print("Connecting to Azure Quantum...")
    azure = AzureQuantumIntegration(config_path=str(CONFIG_PATH))
    try:
        azure.connect()
    except Exception as e:
        print(f"Error: {e}")
        return 1

    available = azure.list_backends()
    if args.backend not in available:
        print(f"\nWarning: {args.backend} not found.")
        print(f"Available: {', '.join(available)}")
        if available:
            args.backend = available[0]
            print(f"Using: {args.backend}")
        else:
            return 1

    print(f"\nSubmitting to {args.backend}...")
    job_name = f"variational_{args.n_qubits}q_L{args.layers}_{args.entanglement}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    try:
        job = azure.submit_circuit(
            qc, backend_name=args.backend, shots=args.shots, job_name=job_name
        )
        print(f"Job ID: {job.id()}")
        print("Waiting for results...")
        result_data = azure.get_job_results(job)
    except Exception as e:
        print(f"Submission error: {e}")
        return 1

    # Process results
    counts = result_data.get("counts", {})
    entropy = compute_entropy(counts)
    max_entropy = float(args.n_qubits)

    print("\n✓ Results received:")
    print(f"  Unique states: {len(counts)} / {2 ** args.n_qubits}")
    print(
        f"  Entropy: {entropy:.3f} / {max_entropy:.3f} ({(entropy/max_entropy*100 if max_entropy>0 else 0):.1f}%)"
    )

    # Save in same format as local simulations
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = {
        "job_id": result_data.get("job_id"),
        "counts": {str(k): int(v) for k, v in counts.items()},
        "success": result_data.get("success", False),
        "metadata": {
            "backend": args.backend,
            "n_qubits": args.n_qubits,
            "layers": args.layers,
            "entanglement": args.entanglement,
            "method": "hardware",
            "circuit": "variational",
            "shots": args.shots,
            "entropy": entropy,
            "max_entropy": max_entropy,
            "circuit_depth": qc.depth(),
            "circuit_gates": sum(qc.count_ops().values()),
            "noise": {
                "pauli_px": 0.0,
                "pauli_pz": 0.0,
                "depolarizing_p": 0.0,
                "amp_damp_gamma": 0.0,
                "seed": None,
            },
        },
    }

    out_path = (
        results_dir
        / f"azure_variational_{args.n_qubits}q_L{args.layers}_{args.entanglement}_{ts}.json"
    )
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nSaved: {out_path}")

    print("\nCompare with local MPS simulation:")
    print(
        f"  python .\\quantum-ai\\scripts\\run_simulated_circuit.py --n-qubits {args.n_qubits} --layers {args.layers} --entanglement {args.entanglement} --method matrix_product_state --shots {args.shots}"
    )
    print("\nVisualize:")
    print("  python .\\quantum-ai\\scripts\\visualize_hardware_results.py")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
