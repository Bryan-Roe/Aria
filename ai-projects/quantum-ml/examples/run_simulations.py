"""
Demonstration of running quantum simulations locally
"""

import matplotlib
import numpy as np
import pennylane as qml
from qiskit import QuantumCircuit, transpile
from qiskit_aer import Aer

matplotlib.use("Agg")  # Non-interactive backend
from pathlib import Path

import matplotlib.pyplot as plt

# Create results directory
results_dir = Path(__file__).parent.parent / "results"
results_dir.mkdir(exist_ok=True)

print("=" * 60)
print("QUANTUM SIMULATION EXAMPLES")
print("=" * 60)

# ============================================
# Example 1: Bell State Simulation
# ============================================
print("\n1. SIMULATING BELL STATE")
print("-" * 60)

bell = QuantumCircuit(2, 2)
bell.h(0)
bell.cx(0, 1)
bell.measure([0, 1], [0, 1])

# Run simulation
simulator = Aer.get_backend("aer_simulator")
compiled_circuit = transpile(bell, simulator)
job = simulator.run(compiled_circuit, shots=1000)
result = job.result()
counts = result.get_counts()

print("Bell state measurement results (1000 shots):")
for state, count in sorted(counts.items()):
    percentage = (count / 1000) * 100
    bar = "█" * int(percentage / 2)
    print(f"  |{state}⟩: {count:4d} ({percentage:5.1f}%) {bar}")

print("\nExpected: ~50% |00⟩ and ~50% |11⟩ (entangled state)")
print("This demonstrates quantum entanglement!")

# ============================================
# Example 2: Superposition Simulation
# ============================================
print("\n2. SIMULATING SUPERPOSITION")
print("-" * 60)

superposition = QuantumCircuit(1, 1)
superposition.h(0)  # Put qubit in superposition
superposition.measure(0, 0)

job = simulator.run(transpile(superposition, simulator), shots=1000)
result = job.result()
counts = result.get_counts()

print("Hadamard gate (superposition) results (1000 shots):")
for state, count in sorted(counts.items()):
    percentage = (count / 1000) * 100
    bar = "█" * int(percentage / 2)
    print(f"  |{state}⟩: {count:4d} ({percentage:5.1f}%) {bar}")

print("\nExpected: ~50% |0⟩ and ~50% |1⟩")

# ============================================
# Example 3: PennyLane Simulation with Gradients
# ============================================
print("\n3. PENNYLANE SIMULATION WITH GRADIENTS")
print("-" * 60)

dev = qml.device("default.qubit", wires=2)


@qml.qnode(dev)
def parameterized_circuit(params):
    qml.RY(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))


# Compute gradient
params = np.array([0.5, 1.0])
gradient = qml.grad(parameterized_circuit)(params)

print(f"Parameters: {params}")
print(f"Expectation value: {parameterized_circuit(params):.4f}")
print(f"Gradient: {gradient}")
print("\nThis enables quantum machine learning with backpropagation!")

# ============================================
# Example 4: Quantum State Tomography Simulation
# ============================================
print("\n4. QUANTUM STATE EVOLUTION")
print("-" * 60)


@qml.qnode(dev)
def evolving_state(angle):
    qml.RY(angle, wires=0)
    return qml.expval(qml.PauliZ(0))


angles = np.linspace(0, 2 * np.pi, 50)
expectations = [evolving_state(angle) for angle in angles]

print("Simulating quantum state evolution...")
print(f"Angles tested: {len(angles)}")
print(f"Expectation range: [{min(expectations):.4f}, {max(expectations):.4f}]")

# Save plot
plt.figure(figsize=(10, 6))
plt.plot(angles, expectations, "b-", linewidth=2)
plt.xlabel("Rotation Angle (radians)", fontsize=12)
plt.ylabel("⟨Z⟩ Expectation Value", fontsize=12)
plt.title("Quantum State Evolution: RY Rotation", fontsize=14)
plt.grid(True, alpha=0.3)
plt.axhline(y=0, color="r", linestyle="--", alpha=0.5)
plot_path = results_dir / "state_evolution.png"
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {plot_path}")

# ============================================
# Example 5: Multi-Qubit Simulation Performance
# ============================================
print("\n5. SCALING SIMULATION")
print("-" * 60)

for n_qubits in [2, 4, 6, 8]:
    dev_temp = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev_temp)
    def benchmark_circuit(params):
        for i in range(n_qubits):
            qml.RY(params[i], wires=i)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
        return qml.expval(qml.PauliZ(0))

    params = np.random.random(n_qubits)
    result = benchmark_circuit(params)
    state_dim = 2**n_qubits

    print(
        f"  {n_qubits} qubits: State dimension = {state_dim:5d}, Result = {result:.4f}"
    )

print("\nNote: Classical simulation becomes exponentially harder!")
print("Real quantum hardware scales linearly with qubits.")

# ============================================
# Example 6: Noisy Simulation
# ============================================
print("\n6. NOISY QUANTUM SIMULATION")
print("-" * 60)

from qiskit_aer.noise import NoiseModel, depolarizing_error

# Create noise model
noise_model = NoiseModel()
error = depolarizing_error(0.01, 1)  # 1% error rate
noise_model.add_all_qubit_quantum_error(error, ["h", "x"])
error_2q = depolarizing_error(0.02, 2)  # 2% error on 2-qubit gates
noise_model.add_all_qubit_quantum_error(error_2q, ["cx"])

# Simulate with noise
bell_noisy = QuantumCircuit(2, 2)
bell_noisy.h(0)
bell_noisy.cx(0, 1)
bell_noisy.measure([0, 1], [0, 1])

job_noisy = simulator.run(
    transpile(bell_noisy, simulator), shots=1000, noise_model=noise_model
)
counts_noisy = job_noisy.result().get_counts()

print("Noisy Bell state (1% single-qubit, 2% two-qubit error):")
for state, count in sorted(counts_noisy.items()):
    percentage = (count / 1000) * 100
    bar = "█" * int(percentage / 2)
    print(f"  |{state}⟩: {count:4d} ({percentage:5.1f}%) {bar}")

print("\nNote: Non-ideal states (|01⟩, |10⟩) appear due to noise.")
print("This simulates real quantum hardware imperfections!")

print("\n" + "=" * 60)
print("SIMULATION EXAMPLES COMPLETED!")
print("=" * 60)
