"""
Test provider-specific gate sets and circuit patterns for Azure Quantum backends.

This script creates GHZ circuits using different gate decompositions optimized
for specific providers (Rigetti, Quantinuum, IonQ) and compares results.

Usage:
  python .\\quantum-ai\\scripts\\test_provider_gates.py [--backend <name>] [--shots <int>]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_OPTIONAL_IMPORT_ERROR: Optional[ImportError] = None

# Add parent src to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    import numpy as np
    import yaml
    from azure_quantum_integration import AzureQuantumIntegration
    from qiskit import QuantumCircuit, transpile
except ImportError as exc:  # pragma: no cover - environment dependent
    _OPTIONAL_IMPORT_ERROR = exc

if _OPTIONAL_IMPORT_ERROR is not None and "pytest" in sys.modules:
    import pytest

    pytest.skip(
        f"Optional quantum dependencies unavailable: {_OPTIONAL_IMPORT_ERROR}",
        allow_module_level=True,
    )


CONFIG_PATH = REPO_ROOT / "config" / "quantum_config.yaml"


def create_ghz_standard(n_qubits: int = 4) -> QuantumCircuit:
    """Standard GHZ using H + CX gates (works for Rigetti, IonQ)."""
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_ghz_quantinuum_native(n_qubits: int = 4) -> QuantumCircuit:
    """
    GHZ using Quantinuum native gates: RZ, RX, ZZ (instead of CX).

    Quantinuum H-series systems have native gates:
    - Single-qubit: RZ(θ), RX(π/2), RX(-π/2)
    - Two-qubit: ZZ(θ) = exp(-i θ/2 Z⊗Z)

    CX can be decomposed as: CX = (RX(π/2) ⊗ I) · ZZ(π/2) · (RX(-π/2) ⊗ I)
    But for GHZ, we can use a more direct approach with RX and ZZ.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    # Create |+⟩ state on first qubit using RX instead of H
    # H = (1/√2)(X + Z) can be implemented as RZ(π/2) RX(π/2) RZ(π/2)
    qc.rz(np.pi / 2, 0)
    qc.rx(np.pi / 2, 0)
    qc.rz(np.pi / 2, 0)

    # Entangle using ZZ gates
    # For GHZ, we need controlled operations. ZZ doesn't directly give CX,
    # but we can build entanglement differently.
    # Alternative: Use standard CX and let Quantinuum transpiler handle it
    for i in range(n_qubits - 1):
        # Decompose CX using Quantinuum-friendly gates
        # CX(i, i+1) = RX(π/2)[i+1] · ZZ(π/2)[i,i+1] · RX(-π/2)[i+1]
        qc.rx(np.pi / 2, i + 1)
        qc.rzz(np.pi / 2, i, i + 1)  # ZZ rotation
        qc.rx(-np.pi / 2, i + 1)

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_ghz_ionq_native(n_qubits: int = 4) -> QuantumCircuit:
    """
    GHZ using IonQ native gates: GPi, GPi2, MS (Mølmer-Sørensen).

    IonQ uses:
    - GPi(φ): single-qubit rotation
    - GPi2(φ): π/2 rotation
    - MS(φ0, φ1): two-qubit Mølmer-Sørensen gate

    However, Qiskit doesn't have direct GPi gates, so we use standard gates
    and rely on IonQ's transpiler. Alternatively, use RX/RY which IonQ supports.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    # IonQ prefers all-to-all connectivity with MS gate
    # For GHZ, we can use H + CX (IonQ will transpile efficiently)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_ghz_rigetti_native(n_qubits: int = 4) -> QuantumCircuit:
    """
    GHZ using Rigetti native gates: RX, RZ, CZ.

    Rigetti systems use:
    - Single-qubit: RX(θ), RZ(θ)
    - Two-qubit: CZ (controlled-Z)

    H can be made from RZ and RX.
    CX can be made from CZ with basis rotations.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)

    # H = RZ(π) RX(π/2) RZ(π) up to global phase
    # Simpler: H = RX(π/2) RZ(π/2) RX(π/2)
    qc.rz(np.pi, 0)
    qc.rx(np.pi / 2, 0)
    qc.rz(np.pi, 0)

    # CX(i, i+1) = HI · CZ · HI where H acts on target
    for i in range(n_qubits - 1):
        # Apply H to target (i+1) using RZ + RX
        qc.rz(np.pi, i + 1)
        qc.rx(np.pi / 2, i + 1)
        qc.rz(np.pi, i + 1)

        # CZ gate (native to Rigetti)
        qc.cz(i, i + 1)

        # Apply H to target again
        qc.rz(np.pi, i + 1)
        qc.rx(np.pi / 2, i + 1)
        qc.rz(np.pi, i + 1)

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_ghz_provider_native(
    n_qubits: int = 4, provider: str = "standard"
) -> QuantumCircuit:
    """Factory for provider-specific GHZ circuit construction."""
    provider_key = provider.lower().strip()
    if provider_key == "quantinuum":
        return create_ghz_quantinuum_native(n_qubits)
    if provider_key == "ionq":
        return create_ghz_ionq_native(n_qubits)
    if provider_key == "rigetti":
        return create_ghz_rigetti_native(n_qubits)
    # Default generic decomposition
    return create_ghz_standard(n_qubits)


def compute_entropy(counts: dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p = np.array([v / total for v in counts.values() if v > 0], dtype=float)
    return float(-(p * np.log2(p)).sum())


def main() -> int:
    if _OPTIONAL_IMPORT_ERROR is not None:
        print(f"Missing optional quantum dependencies: {_OPTIONAL_IMPORT_ERROR}")
        return 1

    parser = argparse.ArgumentParser(
        description="Test provider-specific gate decompositions"
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Backend name (auto-detect if not specified)",
    )
    parser.add_argument(
        "--shots", type=int, default=1000, help="Number of shots (default: 1000)"
    )
    parser.add_argument(
        "--n-qubits", type=int, default=4, help="Number of qubits (default: 4)"
    )
    parser.add_argument(
        "--pattern",
        choices=["standard", "quantinuum", "ionq", "rigetti", "all"],
        default="all",
        help="Circuit pattern to test (default: all)",
    )
    args = parser.parse_args()

    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    results_dir = (
        REPO_ROOT / Path(cfg["logging"]["results_dir"]).expanduser()
    ).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Provider-Specific Circuit Pattern Tests ===")
    print(f"Qubits: {args.n_qubits}, Shots: {args.shots}\n")

    # Connect to Azure Quantum
    print("Connecting to Azure Quantum...")
    azure = AzureQuantumIntegration(config_path=str(CONFIG_PATH))
    try:
        azure.connect()
    except Exception as e:
        print(f"Error connecting to Azure Quantum: {e}")
        return 1

    # Determine backend
    available = azure.list_backends()
    if args.backend and args.backend in available:
        backend_name = args.backend
    elif args.backend:
        print(f"\nWarning: {args.backend} not available.")
        print(f"Available: {', '.join(available)}")
        backend_name = available[0] if available else None
    else:
        # Auto-select based on provider preference
        for pref in ["rigetti", "ionq", "quantinuum"]:
            for b in available:
                if pref in b.lower():
                    backend_name = b
                    break
            if backend_name:
                break
        if not backend_name:
            backend_name = available[0] if available else None

    if not backend_name:
        print("No backends available.")
        return 1

    print(f"Selected backend: {backend_name}\n")

    # Determine which patterns to test
    patterns = {}
    if args.pattern == "all":
        patterns = {
            "standard": create_ghz_standard,
            "quantinuum": create_ghz_quantinuum_native,
            "ionq": create_ghz_ionq_native,
            "rigetti": create_ghz_rigetti_native,
        }
    else:
        pattern_map = {
            "standard": create_ghz_standard,
            "quantinuum": create_ghz_quantinuum_native,
            "ionq": create_ghz_ionq_native,
            "rigetti": create_ghz_rigetti_native,
        }
        patterns[args.pattern] = pattern_map[args.pattern]

    # Test each pattern
    for pattern_name, circuit_fn in patterns.items():
        print(f"Testing {pattern_name} pattern...")
        qc = circuit_fn(args.n_qubits)
        print(f"  Circuit depth: {qc.depth()}, gates: {sum(qc.count_ops().values())}")

        try:
            job_name = f"ghz_{args.n_qubits}q_{pattern_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            job = azure.submit_circuit(
                qc, backend_name=backend_name, shots=args.shots, job_name=job_name
            )
            print(f"  Job submitted: {job.id()}")
            print("  Waiting for results...")
            result_data = azure.get_job_results(job)

            counts = result_data.get("counts", {})
            entropy = compute_entropy(counts)
            max_entropy = float(args.n_qubits)

            # Save results
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            out = {
                "job_id": result_data.get("job_id"),
                "counts": {str(k): int(v) for k, v in counts.items()},
                "success": result_data.get("success", False),
                "metadata": {
                    "backend": backend_name,
                    "n_qubits": args.n_qubits,
                    "pattern": pattern_name,
                    "circuit": "ghz",
                    "shots": args.shots,
                    "entropy": entropy,
                    "max_entropy": max_entropy,
                    "circuit_depth": qc.depth(),
                    "circuit_gates": sum(qc.count_ops().values()),
                },
            }

            out_path = (
                results_dir
                / f"pattern_{pattern_name}_{args.n_qubits}q_{backend_name.replace('.', '_')}_{ts}.json"
            )
            out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

            unique = len(counts)
            print(
                f"  ✓ Results: {unique} unique states, entropy: {entropy:.3f}/{max_entropy:.3f}"
            )
            print(f"  Saved: {out_path.name}\n")

        except Exception as e:
            print(f"  ✗ Error: {e}\n")

    print("Pattern testing complete!")
    print("Run visualizer to see charts:")
    print("  python .\\quantum-ai\\scripts\\visualize_hardware_results.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
