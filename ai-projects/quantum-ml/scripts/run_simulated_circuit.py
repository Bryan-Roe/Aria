"""
Run a local Qiskit Aer simulation of a variational circuit and save results.

Usage example:
  python .\\quantum-ai\\scripts\\run_simulated_circuit.py --n-qubits 16 --layers 4 --entanglement circular --shots 2000

Outputs JSON compatible with visualize_hardware_results.py under quantum-ai/results/.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import yaml
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import (NoiseModel, amplitude_damping_error,
                              depolarizing_error)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "quantum_config.yaml"


def create_variational_circuit(
    n_qubits: int,
    n_layers: int,
    entanglement: str,
    noise_px: float = 0.0,
    noise_pz: float = 0.0,
    rng: Optional[np.random.Generator] = None,
) -> QuantumCircuit:
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

        # Monte Carlo Pauli noise injection (small px/pz), keeps simulation scalable for large N
        if noise_px > 0 or noise_pz > 0:
            if rng is None:
                rng = np.random.default_rng()
            for i in range(n_qubits):
                if noise_px > 0 and rng.random() < noise_px:
                    qc.x(i)
                if noise_pz > 0 and rng.random() < noise_pz:
                    qc.z(i)

        qc.barrier()

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_stabilizer_ghz_circuit(n_qubits: int) -> QuantumCircuit:
    """Create a GHZ-like stabilizer circuit (Clifford-only) scalable to large n.

    Uses only H and CX to remain compatible with Aer 'stabilizer' method.
    """
    qc = QuantumCircuit(n_qubits, n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def create_stabilizer_random_circuit(
    n_qubits: int,
    layers: int,
    twoq_density: float = 0.5,
    seed: Optional[int] = None,
) -> QuantumCircuit:
    """Random Clifford circuit using H, S, X, Z, and CX gates.

    twoq_density controls fraction of qubits participating in two-qubit CNOTs per layer.
    """
    rng = np.random.default_rng(seed)
    qc = QuantumCircuit(n_qubits, n_qubits)
    # Start with random single-qubit Cliffords
    for i in range(n_qubits):
        if rng.random() < 0.5:
            qc.h(i)
        if rng.random() < 0.5:
            qc.s(i)
        if rng.random() < 0.25:
            qc.x(i)
        if rng.random() < 0.25:
            qc.z(i)
    qc.barrier()

    for _ in range(layers):
        # Random single-qubit Clifford layer
        for i in range(n_qubits):
            r = rng.random()
            if r < 0.25:
                qc.h(i)
            elif r < 0.5:
                qc.s(i)
            elif r < 0.75:
                qc.x(i)
            else:
                qc.z(i)

        # Random pairings for CNOTs respecting density
        indices = list(range(n_qubits))
        rng.shuffle(indices)
        pair_count = int((n_qubits // 2) * twoq_density)
        for k in range(pair_count):
            a = indices[2 * k]
            b = indices[2 * k + 1]
            # Random control/target direction
            if rng.random() < 0.5:
                qc.cx(a, b)
            else:
                qc.cx(b, a)
        qc.barrier()

    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def compute_entropy(counts: Dict[str, int]) -> float:
    total = sum(counts.values())
    if total == 0:
        return 0.0
    p = np.array([v / total for v in counts.values() if v > 0], dtype=float)
    return float(-(p * np.log2(p)).sum())


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run a local Qiskit Aer simulation (variational or stabilizer)"
    )
    p.add_argument(
        "--n-qubits", type=int, default=16, help="Number of qubits (default: 16)"
    )
    p.add_argument(
        "--layers",
        type=int,
        default=4,
        help="Number of variational layers (default: 4)",
    )
    p.add_argument(
        "--entanglement",
        choices=["linear", "circular", "full"],
        default="circular",
        help="Entanglement topology (default: circular)",
    )
    p.add_argument(
        "--shots", type=int, default=2000, help="Number of shots (default: 2000)"
    )
    # Noise injection (Monte Carlo Pauli)
    p.add_argument(
        "--noise-pauli-px",
        type=float,
        default=0.0,
        help="Probability of X per qubit per layer (default: 0.0)",
    )
    p.add_argument(
        "--noise-pauli-pz",
        type=float,
        default=0.0,
        help="Probability of Z per qubit per layer (default: 0.0)",
    )
    p.add_argument(
        "--noise-seed",
        type=int,
        default=None,
        help="Seed for noise RNG (default: None)",
    )
    # NoiseModel options (Aer). If provided, a NoiseModel will be attached to the simulator.
    p.add_argument(
        "--noise-depolarizing-p",
        type=float,
        default=0.0,
        help="Depolarizing error probability p for 1q/2q gates (default: 0.0)",
    )
    p.add_argument(
        "--noise-amp-damp-gamma",
        type=float,
        default=0.0,
        help="Amplitude damping gamma for 1q gates (default: 0.0)",
    )
    p.add_argument(
        "--method",
        choices=[
            "statevector",
            "matrix_product_state",
            "stabilizer",
            "extended_stabilizer",
            "tensor_network",
        ],
        default="statevector",
        help="Aer simulation method (default: statevector)",
    )
    p.add_argument(
        "--circuit",
        choices=["variational", "stabilizer_ghz", "stabilizer_random"],
        default="variational",
        help="Circuit type to simulate (default: variational)",
    )
    p.add_argument(
        "--clifford-layers",
        type=int,
        default=4,
        help="Random Clifford layers (used for stabilizer_random)",
    )
    p.add_argument(
        "--twoq-density",
        type=float,
        default=0.5,
        help="Fraction of qubits in 2-qubit CNOT pairs per layer [0,1] (stabilizer_random)",
    )
    p.add_argument(
        "--stabilizer-type",
        choices=["ghz", "random"],
        default="ghz",
        help="Stabilizer circuit subtype: ghz or random (default: ghz)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Load config to resolve results_dir relative to project root
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    results_dir = (
        REPO_ROOT / Path(cfg["logging"]["results_dir"]).expanduser()
    ).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    print("\n=== Local Aer Simulation ===")
    # Decide effective circuit kind and layer count for display/metadata
    using_stab_random = False
    if args.circuit == "stabilizer_random" or (
        args.circuit == "variational" and args.stabilizer_type == "random"
    ):
        using_stab_random = True
    effective_layers = (
        args.clifford_layers
        if using_stab_random or args.circuit == "stabilizer_ghz"
        else args.layers
    )
    effective_circuit = (
        "stabilizer_random"
        if using_stab_random
        else ("stabilizer_ghz" if args.circuit == "stabilizer_ghz" else "variational")
    )

    print(
        f"Qubits: {args.n_qubits}, Layers: {effective_layers}, Entanglement: {args.entanglement}, Shots: {args.shots}"
    )
    print(f"Method: {args.method}, Circuit: {effective_circuit}")

    rng = (
        np.random.default_rng(args.noise_seed)
        if (args.noise_pauli_px > 0 or args.noise_pauli_pz > 0)
        else None
    )

    if args.circuit == "stabilizer_ghz":
        qc = create_stabilizer_ghz_circuit(args.n_qubits)
    elif using_stab_random:
        qc = create_stabilizer_random_circuit(
            n_qubits=args.n_qubits,
            layers=args.clifford_layers,
            twoq_density=max(0.0, min(1.0, args.twoq_density)),
            seed=args.noise_seed,
        )
    else:
        qc = create_variational_circuit(
            args.n_qubits,
            args.layers,
            args.entanglement,
            noise_px=args.noise_pauli_px,
            noise_pz=args.noise_pauli_pz,
            rng=rng,
        )
    print("Circuit depth:", qc.depth(), " | gates:", sum(qc.count_ops().values()))

    # Build optional Aer NoiseModel
    noise_model: Optional[NoiseModel] = None
    if (args.noise_depolarizing_p > 0.0) or (args.noise_amp_damp_gamma > 0.0):
        noise_model = NoiseModel()
        # Attach depolarizing to 1q and 2q gates used in circuits
        if args.noise_depolarizing_p > 0.0:
            p = args.noise_depolarizing_p
            # Reasonable mapping: depol on rx/ry/rz/h/s/x/z and cx
            dep1 = depolarizing_error(p, 1)
            dep2 = depolarizing_error(min(2 * p, 1.0), 2)
            for g in ["h", "s", "sdg", "x", "z", "ry", "rz", "rx", "id"]:
                try:
                    noise_model.add_all_qubit_quantum_error(dep1, g)
                except Exception:
                    pass
            for g2 in ["cx", "cz"]:
                try:
                    noise_model.add_all_qubit_quantum_error(dep2, g2)
                except Exception:
                    pass
        # Attach amplitude damping to 1q gates
        if args.noise_amp_damp_gamma > 0.0:
            gamma = args.noise_amp_damp_gamma
            amp = amplitude_damping_error(gamma)
            for g in ["h", "s", "sdg", "x", "z", "ry", "rz", "rx", "id"]:
                try:
                    noise_model.add_all_qubit_quantum_error(amp, g)
                except Exception:
                    pass

    sim = (
        AerSimulator(method=args.method, noise_model=noise_model)
        if noise_model
        else AerSimulator(method=args.method)
    )
    # Avoid backend coupling_map limits during transpile for large-n; Aer will handle compilation.
    # For stabilizer method/circuits, restrict basis_gates to Clifford set to avoid u1/u2/u3 decomposition.
    is_stabilizer_flow = args.method == "stabilizer" or args.circuit.startswith(
        "stabilizer"
    )
    if is_stabilizer_flow:
        basis = ["h", "s", "sdg", "x", "z", "cx", "cz", "id", "measure"]
        tqc = transpile(qc, basis_gates=basis, optimization_level=0)
    else:
        tqc = transpile(qc, optimization_level=2)
    job = sim.run(tqc, shots=args.shots)
    result = job.result()
    counts = result.get_counts()

    # Compute simple metrics
    entropy = compute_entropy(counts)
    # Avoid huge integer exponentiation; max entropy in bits equals number of qubits
    max_entropy = float(args.n_qubits)

    print("Unique states:", len(counts), f"/ {2 ** args.n_qubits}")
    print(
        f"Entropy: {entropy:.3f} / {max_entropy:.3f} ({(entropy/max_entropy*100 if max_entropy>0 else 0):.1f}%)"
    )

    # Save JSON in the same schema as Azure results so the visualizer can pick it up
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    job_id = f"local-aer-{args.n_qubits}q-{ts}"
    out = {
        "job_id": job_id,
        "counts": {str(k): int(v) for k, v in counts.items()},
        "success": True,
        "metadata": {
            "backend": "aer_simulator",
            "n_qubits": args.n_qubits,
            "layers": effective_layers,
            "entanglement": args.entanglement,
            "method": args.method,
            "circuit": effective_circuit,
            "shots": args.shots,
            "entropy": entropy,
            "max_entropy": max_entropy,
            "noise": {
                "pauli_px": args.noise_pauli_px,
                "pauli_pz": args.noise_pauli_pz,
                "depolarizing_p": args.noise_depolarizing_p,
                "amp_damp_gamma": args.noise_amp_damp_gamma,
                "seed": args.noise_seed,
            },
            "stabilizer": {
                "type": args.stabilizer_type,
                "clifford_layers": args.clifford_layers,
                "twoq_density": args.twoq_density,
            },
        },
    }

    out_path = results_dir / f"sim_{args.n_qubits}q_results_{ts}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Saved results to {out_path}")

    print("Tip: Now run the visualizer to generate charts:")
    print("  python .\\quantum-ai\\scripts\\visualize_hardware_results.py")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
