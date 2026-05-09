"""
Safe Azure Quantum deployment helper.
- Connects to Azure Quantum workspace using DefaultAzureCredential
- Prefers simulator backends by default to avoid costs
- Submits a small GHZ circuit to validate end-to-end flow

Usage:
  python deploy_to_azure_quantum.py [--backend BACKEND_NAME] [--shots N]

Notes:
- Requires azure credentials (az login) and a configured workspace in config/quantum_config.yaml
- To run on real QPU, pass a specific backend (e.g., ionq.qpu) consciously
"""

import argparse
from datetime import datetime
from pathlib import Path

from qiskit import QuantumCircuit
# Local import
from src.azure_quantum_integration import AzureQuantumIntegration


def create_ghz(n_qubits=3):
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def main():
    parser = argparse.ArgumentParser(
        description="Deploy a test circuit to Azure Quantum (simulator by default)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Target backend (default: prefer simulator)",
    )
    parser.add_argument(
        "--shots",
        type=int,
        default=None,
        help="Number of shots (default: config value)",
    )
    parser.add_argument(
        "--qubits", type=int, default=3, help="Number of qubits in GHZ test circuit"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("  AZURE QUANTUM DEPLOYMENT (Safe Default: Simulator)")
    print("=" * 70)

    # Connect
    azure = AzureQuantumIntegration()
    try:
        workspace = azure.connect()
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to Azure Quantum: {e}")
        print(
            "Ensure az login is complete and config/quantum_config.yaml is set correctly."
        )
        return

    # List backends
    try:
        backends = azure.list_backends()
        print("\nAvailable backends:")
        for b in backends:
            print(f" - {b}")
    except Exception as e:
        print(f"\n[WARNING] Could not list backends: {e}")

    # Build test circuit
    qc = create_ghz(n_qubits=args.qubits)
    print("\nTest circuit (GHZ):")
    try:
        print(qc.draw(output="text"))
    except Exception:
        # Fallback if Unicode rendering fails
        print(
            f"GHZ circuit: {args.qubits} qubits, Hadamard + {args.qubits-1} CNOTs + measurement"
        )

    # Submit job
    try:
        job = azure.submit_circuit(
            qc, backend_name=args.backend, shots=args.shots, job_name="ghz-validation"
        )
        results = azure.get_job_results(job)

        # Save
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = results_dir / f"azure_ghz_results_{ts}.json"
        with open(out_path, "w") as f:
            import json

            json.dump(results, f, indent=2)
        print(f"\n[SUCCESS] Job complete. Results saved to: {out_path}")
    except Exception as e:
        print(f"\n[ERROR] Submission failed: {e}")
        print(
            "Tip: This script prefers simulator backends by default via config.\n"
            "     To target a specific backend, pass --backend explicitly (e.g., --backend quantinuum.sim.h2-1sc)."
        )


if __name__ == "__main__":
    main()
