"""
Demonstration of creating various quantum circuits
"""

import sys
from pathlib import Path

import numpy as np
import pennylane as qml
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter

# Add parent directory to path for imports
sys.path.append(
    str(
        Path(__file__).parent.parent.parent.parent
        / "ai-projects"
        / "quantum-ml"
        / "src"
    )
)

print("=" * 60)
print("QUANTUM CIRCUIT CREATION EXAMPLES")
print("=" * 60)

# ============================================
# Example 1: Bell State (Entanglement)
# ============================================
print("\n1. BELL STATE CIRCUIT")
print("-" * 60)

bell_circuit = QuantumCircuit(2, 2)
bell_circuit.h(0)  # Hadamard on qubit 0
bell_circuit.cx(0, 1)  # CNOT from qubit 0 to 1
bell_circuit.measure([0, 1], [0, 1])

print("Circuit: Creates maximally entangled state |Φ+⟩ = (|00⟩ + |11⟩)/√2")
print(bell_circuit)

# ============================================
# Example 2: GHZ State (3-qubit entanglement)
# ============================================
print("\n2. GHZ STATE CIRCUIT (3 qubits)")
print("-" * 60)

ghz_circuit = QuantumCircuit(3, 3)
ghz_circuit.h(0)
ghz_circuit.cx(0, 1)
ghz_circuit.cx(0, 2)
ghz_circuit.measure([0, 1, 2], [0, 1, 2])

print("Circuit: Creates |GHZ⟩ = (|000⟩ + |111⟩)/√2")
print(ghz_circuit)

# ============================================
# Example 3: Quantum Fourier Transform
# ============================================
print("\n3. QUANTUM FOURIER TRANSFORM (3 qubits)")
print("-" * 60)


def create_qft_circuit(n_qubits):
    """Create a Quantum Fourier Transform circuit"""
    qc = QuantumCircuit(n_qubits)

    for j in range(n_qubits):
        qc.h(j)
        for k in range(j + 1, n_qubits):
            qc.cp(np.pi / (2 ** (k - j)), k, j)

    # Swap qubits
    for i in range(n_qubits // 2):
        qc.swap(i, n_qubits - i - 1)

    return qc


qft_circuit = create_qft_circuit(3)
print("Circuit: Quantum Fourier Transform for 3 qubits")
print(qft_circuit)

# ============================================
# Example 4: Variational Quantum Circuit (for ML)
# ============================================
print("\n4. VARIATIONAL QUANTUM CIRCUIT (for Machine Learning)")
print("-" * 60)

n_qubits = 4
n_layers = 2

vqc = QuantumCircuit(n_qubits)

print(f"Circuit: {n_layers}-layer variational circuit with {n_qubits} qubits")
print("Features: RY rotations + Linear entanglement")

# Create parameters
params = [
    [Parameter(f"θ_{layer}_{i}_{gate}") for gate in ["y", "z"]]
    for i in range(n_qubits)
    for layer in range(n_layers)
]

for layer in range(n_layers):
    # Rotation layer
    for i in range(n_qubits):
        theta_y = Parameter(f"θ_{layer}_{i}_y")
        theta_z = Parameter(f"θ_{layer}_{i}_z")
        vqc.ry(theta_y, i)
        vqc.rz(theta_z, i)

    # Entanglement layer (linear)
    for i in range(n_qubits - 1):
        vqc.cx(i, i + 1)

print(vqc)

# ============================================
# Example 5: PennyLane Circuit
# ============================================
print("\n5. PENNYLANE QUANTUM CIRCUIT")
print("-" * 60)

dev = qml.device("default.qubit", wires=2)


@qml.qnode(dev)
def pennylane_circuit(params):
    """PennyLane circuit with parameterized rotations"""
    qml.RY(params[0], wires=0)
    qml.RY(params[1], wires=1)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0)), qml.expval(qml.PauliZ(1))


print("Circuit: PennyLane parameterized circuit")
print("Operations: RY(θ0) on qubit 0, RY(θ1) on qubit 1, CNOT(0→1)")
print("Measurements: Expectation values of Z on both qubits")
print(qml.draw(pennylane_circuit)([0.5, 1.0]))

# ============================================
# Example 6: Custom Quantum Classifier Circuit
# ============================================
print("\n6. QUANTUM CLASSIFIER CIRCUIT (from our QML model)")
print("-" * 60)

from src.quantum_classifier import QuantumClassifier

qc = QuantumClassifier()
weights = qc.initialize_weights()

print("Circuit configuration:")
print(f"  - Qubits: {qc.n_qubits}")
print(f"  - Layers: {qc.n_layers}")
print(f"  - Entanglement: {qc.entanglement}")
print(f"  - Parameters: {weights.numel()}")
print("\nThis circuit is used for hybrid quantum-classical classification!")

print("\n" + "=" * 60)
print("CIRCUIT CREATION COMPLETED!")
print("=" * 60)
