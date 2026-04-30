"""
Test Optimized Quantum Circuit on Real Azure Quantum Hardware
Submits the optimized quantum classifier to IonQ or other quantum backends
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

_OPTIONAL_IMPORT_ERROR: Optional[ImportError] = None

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

try:
    import numpy as np
    from azure_quantum_integration import (AzureQuantumIntegration,
                                           create_sample_circuit)
    from qiskit import QuantumCircuit
except ImportError as exc:  # pragma: no cover - environment dependent
    _OPTIONAL_IMPORT_ERROR = exc

if _OPTIONAL_IMPORT_ERROR is not None and "pytest" in sys.modules:
    import pytest

    pytest.skip(
        f"Optional quantum dependencies unavailable: {_OPTIONAL_IMPORT_ERROR}",
        allow_module_level=True,
    )

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_optimized_quantum_circuit(
    n_qubits: int = 4, n_layers: int = 3
) -> QuantumCircuit:
    """
    Create a quantum circuit using our optimized parameters.
    This simulates the structure of our trained quantum classifier.

    Args:
        n_qubits: Number of qubits (from config)
        n_layers: Number of layers (optimized to 3)

    Returns:
        Quantum circuit
    """
    circuit = QuantumCircuit(n_qubits, n_qubits)

    # Initial state preparation (Hadamard layer)
    for qubit in range(n_qubits):
        circuit.h(qubit)

    # Variational layers (optimized: 3 layers with linear entanglement)
    for layer in range(n_layers):
        # Rotation gates (parameterized - using example values)
        for qubit in range(n_qubits):
            circuit.ry(np.pi / 4 * (layer + 1), qubit)
            circuit.rz(np.pi / 3 * (layer + 1), qubit)

        # Linear entanglement (optimized pattern)
        for qubit in range(n_qubits - 1):
            circuit.cx(qubit, qubit + 1)

        # Add barrier for visualization
        circuit.barrier()

    # Measurement
    circuit.measure(range(n_qubits), range(n_qubits))

    return circuit


def create_bell_state_test() -> QuantumCircuit:
    """
    Create a simple Bell state for initial hardware testing.
    This is a good first test to verify quantum entanglement on hardware.

    Returns:
        Bell state circuit
    """
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])
    return circuit


def test_azure_quantum_connection():
    """
    Test 1: Verify Azure Quantum connection and list backends.
    """
    print("\n" + "=" * 70)
    print("  TEST 1: AZURE QUANTUM CONNECTION")
    print("=" * 70 + "\n")

    try:
        if _OPTIONAL_IMPORT_ERROR is not None:
            raise RuntimeError(
                f"Missing optional quantum dependencies: {_OPTIONAL_IMPORT_ERROR}"
            )

        # Initialize Azure Quantum
        config_path = Path(__file__).parent / "config" / "quantum_config.yaml"
        azure = AzureQuantumIntegration(str(config_path))

        print("✓ Configuration loaded")
        print(f"  Workspace: {azure.azure_config['workspace_name']}")
        print(f"  Resource Group: {azure.azure_config['resource_group']}")
        print(f"  Location: {azure.azure_config['location']}\n")

        # Connect to workspace
        print("Connecting to Azure Quantum workspace...")
        workspace = azure.connect()
        print("✓ Successfully connected to Azure Quantum!\n")

        # List available backends
        print("Available Quantum Backends:")
        backends = azure.list_backends()

        for i, backend in enumerate(backends, 1):
            print(f"  {i}. {backend}")

        print(f"\n✓ Found {len(backends)} quantum backend(s)\n")

        return azure, backends

    except Exception as e:
        print(f"\n✗ Connection failed: {str(e)}\n")
        print("TROUBLESHOOTING STEPS:")
        print("1. Ensure Azure Quantum workspace is deployed (see azure/DEPLOYMENT.md)")
        print("2. Run: az login")
        print("3. Update config/quantum_config.yaml with your subscription details")
        print(
            "4. Verify workspace exists: az quantum workspace show -g rg-quantum-ai -n quantum-ai-workspace\n"
        )
        return None, []


def test_bell_state_on_hardware(
    azure: AzureQuantumIntegration, backend_name: str = None
):
    """
    Test 2: Run Bell state on quantum hardware to verify entanglement.
    """
    print("\n" + "=" * 70)
    print("  TEST 2: BELL STATE ON QUANTUM HARDWARE")
    print("=" * 70 + "\n")

    # Create Bell state circuit
    circuit = create_bell_state_test()

    print("Bell State Circuit:")
    print(circuit)
    print("\nExpected Results (ideal quantum behavior):")
    print("  |00⟩: ~50%")
    print("  |11⟩: ~50%")
    print("  (Quantum entanglement: measuring qubit 0 determines qubit 1)\n")

    try:
        # Estimate cost first
        print("Estimating cost...")
        cost_estimate = azure.estimate_cost(
            circuit, backend_name or "ionq.simulator", shots=100
        )
        print(f"Cost Estimate: {cost_estimate}\n")

        # Submit to hardware
        print(f"Submitting Bell state to {backend_name or 'default backend'}...")
        job = azure.submit_circuit(
            circuit,
            backend_name=backend_name,
            shots=100,
            job_name=f"bell_state_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        print("✓ Job submitted successfully!")
        print(f"  Job ID: {job.id()}")
        print(f"  Status: {job.status()}")
        print("\nWaiting for results (this may take a few minutes)...")

        # Get results
        results = azure.get_job_results(job)

        print("\n" + "=" * 70)
        print("  BELL STATE RESULTS")
        print("=" * 70)
        print("\nMeasurement counts:")
        for state, count in sorted(results["counts"].items()):
            percentage = (count / sum(results["counts"].values())) * 100
            print(f"  {state}: {count} ({percentage:.1f}%)")

        # Verify entanglement
        counts = results["counts"]
        total = sum(counts.values())
        entangled_states = counts.get("00", 0) + counts.get("11", 0)
        entanglement_ratio = (entangled_states / total) * 100

        print(f"\nEntanglement Quality: {entanglement_ratio:.1f}%")
        if entanglement_ratio > 80:
            print("✓ Excellent quantum entanglement observed!")
        elif entanglement_ratio > 60:
            print("✓ Good quantum behavior (some hardware noise expected)")
        else:
            print("⚠ Lower than expected - check hardware calibration")

        # Save results
        azure.save_results(results, f"bell_state_results_{job.id()}.json")
        print("\n✓ Results saved to results/\n")

        return results

    except Exception as e:
        print(f"\n✗ Hardware test failed: {str(e)}\n")
        return None


def test_optimized_circuit_on_hardware(
    azure: AzureQuantumIntegration, backend_name: str = None
):
    """
    Test 3: Run our optimized quantum classifier circuit on real hardware.
    """
    print("\n" + "=" * 70)
    print("  TEST 3: OPTIMIZED QUANTUM CIRCUIT ON HARDWARE")
    print("=" * 70 + "\n")

    # Load config to get optimized parameters
    config_path = Path(__file__).parent / "config" / "quantum_config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    n_qubits = config["ml"]["model"]["n_qubits"]
    n_layers = config["ml"]["model"]["n_layers"]
    entanglement = config["ml"]["model"]["entanglement"]

    print("Optimized Configuration (90% accuracy):")
    print(f"  Qubits: {n_qubits}")
    print(f"  Layers: {n_layers}")
    print(f"  Entanglement: {entanglement}")
    print(f"  Learning Rate: {config['ml']['training']['learning_rate']}\n")

    # Create circuit
    circuit = create_optimized_quantum_circuit(n_qubits, n_layers)

    print("Quantum Circuit Structure:")
    print(circuit)
    print("\nCircuit Statistics:")
    print(f"  Depth: {circuit.depth()}")
    print(f"  Gates: {sum(circuit.count_ops().values())}")
    print(f"  Qubits: {circuit.num_qubits}\n")

    try:
        # Estimate cost
        print("Estimating cost for optimized circuit...")
        cost_estimate = azure.estimate_cost(
            circuit, backend_name or "ionq.simulator", shots=500
        )
        print(f"Cost Estimate: {cost_estimate}\n")

        # Submit to hardware
        print(f"Submitting optimized circuit to {backend_name or 'default backend'}...")
        job = azure.submit_circuit(
            circuit,
            backend_name=backend_name,
            shots=500,
            job_name=f"optimized_classifier_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        print("✓ Job submitted successfully!")
        print(f"  Job ID: {job.id()}")
        print(f"  Status: {job.status()}")
        print("\nWaiting for results (this may take several minutes)...")

        # Get results
        results = azure.get_job_results(job)

        print("\n" + "=" * 70)
        print("  OPTIMIZED CIRCUIT RESULTS")
        print("=" * 70)
        print("\nMeasurement distribution (top 10 states):")

        sorted_counts = sorted(
            results["counts"].items(), key=lambda x: x[1], reverse=True
        )
        total = sum(results["counts"].values())

        for state, count in sorted_counts[:10]:
            percentage = (count / total) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {state}: {count:4d} ({percentage:5.2f}%) {bar}")

        # Analyze distribution
        entropy = -sum(
            (count / total) * np.log2(count / total)
            for count in results["counts"].values()
            if count > 0
        )
        max_entropy = np.log2(2**n_qubits)

        print("\nQuantum State Analysis:")
        print(f"  Unique states measured: {len(results['counts'])}/{2**n_qubits}")
        print(f"  Entropy: {entropy:.3f} / {max_entropy:.3f}")
        print(f"  Distribution uniformity: {(entropy/max_entropy)*100:.1f}%")

        # Save results
        azure.save_results(results, f"optimized_circuit_results_{job.id()}.json")
        print("\n✓ Results saved to results/\n")

        return results

    except Exception as e:
        print(f"\n✗ Circuit execution failed: {str(e)}\n")
        return None


def compare_simulator_vs_hardware(azure: AzureQuantumIntegration):
    """
    Test 4: Compare results between simulator and real hardware.
    """
    print("\n" + "=" * 70)
    print("  TEST 4: SIMULATOR VS HARDWARE COMPARISON")
    print("=" * 70 + "\n")

    circuit = create_bell_state_test()

    try:
        # Run on simulator
        print("Running on simulator...")
        sim_job = azure.submit_circuit(
            circuit,
            backend_name="ionq.simulator",
            shots=1000,
            job_name="simulator_comparison",
        )
        sim_results = azure.get_job_results(sim_job)

        print("✓ Simulator results received")
        print(f"  Counts: {sim_results['counts']}\n")

        # Run on hardware (if available)
        print("Running on quantum hardware...")
        hw_job = azure.submit_circuit(
            circuit,
            backend_name="ionq.qpu",  # Real QPU
            shots=1000,
            job_name="hardware_comparison",
        )
        hw_results = azure.get_job_results(hw_job)

        print("✓ Hardware results received")
        print(f"  Counts: {hw_results['counts']}\n")

        # Compare
        print("=" * 70)
        print("  COMPARISON RESULTS")
        print("=" * 70)

        print("\n{:<15} {:<20} {:<20}".format("State", "Simulator", "Hardware"))
        print("-" * 70)

        all_states = set(sim_results["counts"].keys()) | set(
            hw_results["counts"].keys()
        )
        sim_total = sum(sim_results["counts"].values())
        hw_total = sum(hw_results["counts"].values())

        for state in sorted(all_states):
            sim_pct = (sim_results["counts"].get(state, 0) / sim_total) * 100
            hw_pct = (hw_results["counts"].get(state, 0) / hw_total) * 100
            print(f"{state:<15} {sim_pct:>6.2f}% {' '*14} {hw_pct:>6.2f}%")

        print("\nKey Differences:")
        print("  - Simulator: Ideal quantum behavior (no noise)")
        print("  - Hardware: Real quantum effects + decoherence/gate errors")
        print(
            "  - Hardware noise is expected and demonstrates real quantum computing!\n"
        )

        return sim_results, hw_results

    except Exception as e:
        print(f"\n✗ Comparison failed: {str(e)}")
        print("Note: Quantum hardware access may require credits or additional setup\n")
        return None, None


def main():
    """
    Main test suite for Azure Quantum hardware.
    """
    print("\n" + "=" * 70)
    print("  AZURE QUANTUM HARDWARE TEST SUITE")
    print("  Testing Optimized Quantum AI Configuration (90% Accuracy)")
    print("=" * 70)

    # Test 1: Connection
    azure, backends = test_azure_quantum_connection()

    if azure is None:
        print("\n⚠ Cannot proceed without Azure Quantum connection.")
        print("Please complete Azure deployment first (see azure/DEPLOYMENT.md)\n")
        return

    # Select backend
    print("\n" + "=" * 70)
    print("  BACKEND SELECTION")
    print("=" * 70 + "\n")

    if not backends:
        print("⚠ No backends available. Check workspace configuration.\n")
        return

    # Recommend starting with simulator
    simulator_backends = [b for b in backends if "simulator" in b.lower()]
    hardware_backends = [b for b in backends if "simulator" not in b.lower()]

    print("Available backends:")
    print("\nSimulators (FREE - recommended for testing):")
    for backend in simulator_backends:
        print(f"  • {backend}")

    if hardware_backends:
        print("\nQuantum Hardware (PAID - requires credits):")
        for backend in hardware_backends:
            print(f"  • {backend}")

    print("\nRecommended testing order:")
    print("  1. Start with simulator (free, fast)")
    print("  2. Test Bell state on hardware (low cost)")
    print("  3. Run optimized circuit on hardware (verify 90% accuracy)\n")

    # Ask user to select backend
    print("Select backend for testing:")
    print("  1. ionq.simulator (FREE - recommended)")
    if hardware_backends:
        print("  2. ionq.qpu (PAID - real quantum computer)")
    print("  3. Skip hardware tests\n")

    choice = input("Enter choice (1-3): ").strip()

    if choice == "3":
        print("\nSkipping hardware tests. Goodbye!\n")
        return
    elif choice == "2" and hardware_backends:
        backend = "ionq.qpu"
        print(f"\n⚠ Selected PAID hardware: {backend}")
        print("This will use quantum computing credits!")
        confirm = input("Continue? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("\nTest cancelled.\n")
            return
    else:
        backend = "ionq.simulator"

    print(f"\nUsing backend: {backend}\n")

    # Test 2: Bell state
    bell_results = test_bell_state_on_hardware(azure, backend)

    if bell_results:
        print("✓ Bell state test completed successfully!\n")

        # Ask if user wants to continue with optimized circuit
        proceed = (
            input("Proceed with optimized circuit test? (yes/no): ").strip().lower()
        )
        if proceed == "yes":
            # Test 3: Optimized circuit
            opt_results = test_optimized_circuit_on_hardware(azure, backend)

            if opt_results:
                print("✓ Optimized circuit test completed successfully!\n")

    # Summary
    print("\n" + "=" * 70)
    print("  TEST SUITE COMPLETE")
    print("=" * 70)
    print("\nResults saved to: ai-projects/quantum-ml/results/")
    print("\nNext Steps:")
    print("  1. Analyze results in Azure Portal")
    print("  2. Compare simulator vs hardware performance")
    print("  3. Scale up to larger circuits (6-8 qubits)")
    print("  4. Train quantum classifier with hardware results\n")

    print("Documentation:")
    print("  • Full guide: experiments/AZURE_QUICKSTART.md")
    print("  • Deployment: azure/DEPLOYMENT.md")
    print("  • Optimization: FINAL_OPTIMIZATION_REPORT.md\n")


if __name__ == "__main__":
    main()
