"""
Run a grid of simulation experiments and save results for visualization.

Experiments:
- MPS variational: n in {32,64}, layers in {1,2}, entanglement in {linear,circular,full}
  - Clean and with small Pauli noise (px=pz=0.005)
- Stabilizer random: n in {128,256}, clifford_layers in {2,4,8}

Outputs are JSON files under quantum-ai/results/ used by visualize_hardware_results.py.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_simulated_circuit.py"


def run(cmd: list[str]) -> None:
    print("\n$", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")


def main() -> int:
    py = sys.executable or "python"

    # 1) MPS variational experiments
    for n in (32, 64):
        for L in (1, 2):
            shots = 500 if n == 64 else 1000
            for ent in ("linear", "circular", "full"):
                # Clean
                run(
                    [
                        py,
                        str(SCRIPT),
                        "--n-qubits",
                        str(n),
                        "--layers",
                        str(L),
                        "--entanglement",
                        ent,
                        "--method",
                        "matrix_product_state",
                        "--shots",
                        str(shots),
                    ]
                )
                # With small Pauli noise
                run(
                    [
                        py,
                        str(SCRIPT),
                        "--n-qubits",
                        str(n),
                        "--layers",
                        str(L),
                        "--entanglement",
                        ent,
                        "--method",
                        "matrix_product_state",
                        "--shots",
                        str(shots),
                        "--noise-pauli-px",
                        "0.005",
                        "--noise-pauli-pz",
                        "0.005",
                        "--noise-seed",
                        "1234",
                    ]
                )

    # 2) Stabilizer random experiments
    for n in (128, 256):
        for layers in (2, 4, 8):
            run(
                [
                    py,
                    str(SCRIPT),
                    "--n-qubits",
                    str(n),
                    "--circuit",
                    "stabilizer_random",
                    "--stabilizer-type",
                    "random",
                    "--clifford-layers",
                    str(layers),
                    "--twoq-density",
                    "0.5",
                    "--method",
                    "stabilizer",
                    "--shots",
                    "500",
                    "--noise-seed",
                    "42",
                ]
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
