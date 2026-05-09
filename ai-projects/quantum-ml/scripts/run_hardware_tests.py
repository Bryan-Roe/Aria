"""
Run Azure Quantum hardware tests non-interactively and save results.
- Verifies connection
- Runs Bell state on selected backend (default: ionq.simulator)
- Optionally runs optimized circuit test
Results are saved to `quantum-ai/results/` via test_azure_quantum utilities.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure module imports work when running from repo root or script dir
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from test_azure_quantum import (test_azure_quantum_connection,
                                test_bell_state_on_hardware,
                                test_optimized_circuit_on_hardware)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run Azure Quantum hardware tests non-interactively"
    )
    p.add_argument(
        "--backend",
        default="ionq.simulator",
        help="Backend to use (e.g., ionq.simulator, ionq.qpu). Default: ionq.simulator",
    )
    p.add_argument(
        "--optimized",
        action="store_true",
        help="Also run the optimized circuit test after Bell state",
    )
    p.add_argument(
        "--skip-bell",
        action="store_true",
        help="Skip the Bell state test and only run the optimized circuit (if --optimized)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    print("\n=== Non-interactive Azure Quantum Hardware Tests ===\n")

    # 1) Connect and list backends
    azure, backends = test_azure_quantum_connection()
    if azure is None:
        print("Cannot proceed without Azure Quantum connection.")
        return 1

    print(f"Using backend: {args.backend}")
    if args.backend not in backends:
        print(
            "Warning: chosen backend not found in workspace backends. Proceeding anyway...\n"
        )

    # 2) Run Bell state unless skipped
    if not args.skip_bell:
        bell = test_bell_state_on_hardware(azure, args.backend)
        if bell is None:
            print("Bell state test failed or produced no results.")
        else:
            print("Bell state test completed and results saved.\n")

    # 3) Optionally run optimized circuit
    if args.optimized:
        opt = test_optimized_circuit_on_hardware(azure, args.backend)
        if opt is None:
            print("Optimized circuit test failed or produced no results.")
        else:
            print("Optimized circuit test completed and results saved.\n")

    print("\n=== Done ===")
    print("Results (JSON) are in quantum-ai/results/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
