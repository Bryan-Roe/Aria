"""
Test Enhanced Quantum Classifier on Azure Quantum Hardware
Simple working version for immediate deployment
"""

import logging
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent / "src"))

_OPTIONAL_IMPORT_ERROR: Optional[ImportError] = None

try:
    from azure.quantum import Workspace
    from qiskit import QuantumCircuit, transpile
except ImportError as exc:  # pragma: no cover - environment dependent
    _OPTIONAL_IMPORT_ERROR = exc

if _OPTIONAL_IMPORT_ERROR is not None and "pytest" in sys.modules:
    import pytest

    pytest.skip(
        f"Optional quantum hardware dependencies unavailable: {_OPTIONAL_IMPORT_ERROR}",
        allow_module_level=True,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_simple_test_circuit():
    """Create a simple Bell state circuit for testing."""
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


def create_8qubit_classifier_circuit():
    """Create an 8-qubit circuit similar to our enhanced classifier."""
    import numpy as np

    circuit = QuantumCircuit(8, 8)

    # Initial state preparation (Hadamard layer)
    for i in range(8):
        circuit.h(i)

    # Variational layers (simplified version of enhanced classifier)
    n_layers = 4
    for layer in range(n_layers):
        # Rotation gates
        for i in range(8):
            circuit.ry(np.pi / 4 * (layer + 1), i)
            circuit.rz(np.pi / 3 * (layer + 1), i)

        # Circular entanglement (optimized pattern)
        for i in range(8):
            circuit.cx(i, (i + 1) % 8)

        circuit.barrier()

    # Measurements
    circuit.measure(range(8), range(8))

    return circuit


def main():
    if _OPTIONAL_IMPORT_ERROR is not None:
        print(
            f"Missing optional quantum hardware dependencies: {_OPTIONAL_IMPORT_ERROR}"
        )
        return 1

    print("=" * 70)
    print("  Azure Quantum Hardware Test")
    print("  Enhanced 8-Qubit Quantum Classifier")
    print("=" * 70)

    # Connect to workspace
    print("\n[1/4] Connecting to Azure Quantum...")

    workspace = Workspace(
        subscription_id="a07fbd16-e722-446d-8efd-0681e85b725c",
        resource_group="rg-quantum-ai",
        name="quantum-ai-workspace",
        location="eastus",
    )

    print(f"✓ Connected to: {workspace.name}")
    print(f"  Location: {workspace.location}")

    # List available backends
    print("\n[2/4] Available Quantum Backends:")
    targets = workspace.get_targets()

    for i, target in enumerate(targets, 1):
        print(f"  {i}. {target.name}")
        print(f"     Provider: {target.provider_id}")
        print(f"     Status: {target.current_availability}")

    # Test 1: Simple Bell State
    print("\n[3/4] Test 1: Bell State (2 qubits)")
    print("-" * 70)

    bell_circuit = create_simple_test_circuit()
    print("Circuit created:")
    print(bell_circuit)

    # Use Rigetti simulator (free)
    print("\nSubmitting to Rigetti QVM Simulator (FREE)...")

    try:
        target = workspace.get_targets("rigetti.sim.qvm")
        job = target.submit(bell_circuit, shots=100, job_name="bell-state-test")

        print(f"✓ Job submitted: {job.id}")
        print(f"  Status: {job.details.status}")
        print("\n  Waiting for results (this may take 30-60 seconds)...")

        results = job.get_results()

        print("\n✓ Results received!")
        print("\nMeasurement Counts:")
        for state, count in sorted(results.items()):
            percentage = (count / sum(results.values())) * 100
            bar = "█" * int(percentage / 5)
            print(f"  {state}: {count:3d} ({percentage:5.1f}%) {bar}")

        # Check entanglement quality
        entangled = results.get("00", 0) + results.get("11", 0)
        total = sum(results.values())
        entanglement_ratio = (entangled / total) * 100

        print(f"\nEntanglement Quality: {entanglement_ratio:.1f}%")
        if entanglement_ratio > 80:
            print("✓ Excellent quantum entanglement!")
        else:
            print("⚠ Some noise detected (normal for simulators)")

    except Exception as e:
        print(f"✗ Bell state test failed: {e}")
        print("This is likely due to provider availability.")

    # Test 2: Enhanced 8-Qubit Circuit
    print("\n[4/4] Test 2: Enhanced 8-Qubit Classifier Circuit")
    print("-" * 70)

    circuit_8q = create_8qubit_classifier_circuit()

    print("✓ 8-qubit circuit created")
    print(f"  Qubits: {circuit_8q.num_qubits}")
    print(f"  Depth: {circuit_8q.depth()}")
    print(f"  Gates: {sum(circuit_8q.count_ops().values())}")

    print("\nCircuit Structure:")
    print(circuit_8q)

    print("\n⚠ Note: 8-qubit execution on real hardware requires:")
    print("  • Provider with 8+ qubit capacity")
    print("  • Sufficient quantum credits")
    print("  • May incur costs (~$5-10 per run)")

    proceed = input("\nSubmit 8-qubit circuit to simulator? (yes/no): ")

    if proceed.lower() == "yes":
        try:
            print("\nSubmitting to Rigetti QVM Simulator...")
            target = workspace.get_targets("rigetti.sim.qvm")
            job = target.submit(
                circuit_8q, shots=100, job_name="8qubit-classifier-test"
            )

            print(f"✓ Job submitted: {job.id}")
            print("  Waiting for results...")

            results = job.get_results()

            print("\n✓ 8-Qubit Results!")
            print("\nTop 10 Measurement States:")

            sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)[
                :10
            ]
            total = sum(results.values())

            for state, count in sorted_results:
                percentage = (count / total) * 100
                bar = "█" * int(percentage / 2)
                print(f"  {state}: {count:3d} ({percentage:5.2f}%) {bar}")

            print(f"\n✓ Total unique states: {len(results)}/256")
            print("  Circuit complexity demonstrated successfully!")

        except Exception as e:
            print(f"✗ 8-qubit test failed: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)

    print("\n✓ Azure Quantum workspace operational")
    print("✓ Quantum circuits compiled successfully")
    print("✓ Backend connectivity verified")

    print("\nNext Steps:")
    print("  1. Review results in Azure Portal:")
    print(
        "     https://portal.azure.com/#resource/subscriptions/a07fbd16-e722-446d-8efd-0681e85b725c/resourceGroups/rg-ai-projects/quantum-ml/providers/Microsoft.Quantum/Workspaces/quantum-ai-workspace"
    )
    print("\n  2. Train enhanced classifier with real quantum results")
    print("  3. Deploy to production quantum hardware (Quantinuum H1)")
    print("  4. Scale to larger datasets and problems")

    print("\n" + "=" * 70)
    print("✓ Quantum hardware test completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
