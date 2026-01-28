#!/usr/bin/env python3
"""
Custom Quantum Circuit
Create and run your own quantum circuit
"""
import pennylane as qml
import numpy as np
import matplotlib.pyplot as plt

print("=" * 70)
print("  CREATING YOUR QUANTUM CIRCUIT")
print("=" * 70)

# Create a quantum device
n_qubits = 3
dev = qml.device('lightning.qubit', wires=n_qubits, shots=1000)

@qml.qnode(dev)
def my_circuit(params):
    """
    Custom 3-qubit quantum circuit with:
    - Superposition (Hadamard gates)
    - Rotation gates (parameterized)
    - Entanglement (CNOT gates)
    - Measurements
    """
    # Step 1: Create superposition on all qubits
    for i in range(n_qubits):
        qml.Hadamard(wires=i)
    
    # Step 2: Apply parameterized rotations
    qml.RY(params[0], wires=0)
    qml.RZ(params[1], wires=1)
    qml.RX(params[2], wires=2)
    
    # Step 3: Create entanglement
    qml.CNOT(wires=[0, 1])
    qml.CNOT(wires=[1, 2])
    
    # Step 4: More rotations
    qml.RY(params[3], wires=0)
    qml.RZ(params[4], wires=1)
    
    # Return measurement probabilities
    return qml.probs(wires=range(n_qubits))

# Run the circuit with sample parameters
print("\n[1] Circuit Configuration:")
print(f"  • Qubits: {n_qubits}")
print(f"  • Device: {dev.name}")
print(f"  • Shots: {dev.shots}")

# Test parameters
params = np.array([0.5, 1.0, 0.3, 0.8, 0.4])
print(f"\n[2] Running circuit with parameters: {params.tolist()}")

# Execute
results = my_circuit(params)

print(f"\n[3] Measurement Results:")
print(f"  • Total states: {len(results)}")
print(f"\n  Top 5 probable states:")
for i, prob in enumerate(results):
    if prob > 0.05:  # Show states with >5% probability
        binary = format(i, f'0{n_qubits}b')
        print(f"    |{binary}⟩ (decimal {i}): {prob:.3f} ({prob*100:.1f}%)")

# Visualize circuit
print(f"\n[4] Circuit Diagram:")
print("-" * 70)
print(qml.draw(my_circuit)(params))

# Visualize results
print(f"\n[5] Creating probability distribution plot...")
fig, ax = plt.subplots(figsize=(12, 6))
states = [format(i, f'0{n_qubits}b') for i in range(len(results))]
bars = ax.bar(states, results, color='steelblue', edgecolor='black', linewidth=1.5)

# Highlight high-probability states
for i, bar in enumerate(bars):
    if results[i] > 0.1:
        bar.set_color('coral')

ax.set_xlabel('Quantum State', fontsize=12, fontweight='bold')
ax.set_ylabel('Probability', fontsize=12, fontweight='bold')
ax.set_title('Quantum Circuit Measurement Results', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('my_circuit_results.png', dpi=150, bbox_inches='tight')
print(f"  ✓ Saved to: my_circuit_results.png")

# Try different parameters
print(f"\n[6] Testing with different parameters...")
test_params = [
    np.array([0.0, 0.0, 0.0, 0.0, 0.0]),  # No rotations
    np.array([np.pi, np.pi, np.pi, 0.0, 0.0]),  # π rotations
    np.array([np.pi/2, np.pi/2, np.pi/2, np.pi/2, np.pi/2]),  # π/2 rotations
]

for i, test_p in enumerate(test_params):
    test_result = my_circuit(test_p)
    max_prob = np.max(test_result)
    max_state = format(np.argmax(test_result), f'0{n_qubits}b')
    print(f"  Test {i+1}: max_state=|{max_state}⟩ prob={max_prob:.3f}")

print("\n" + "=" * 70)
print("  ✓ CIRCUIT COMPLETE!")
print("=" * 70)
print("\nNext steps:")
print("  • Modify parameters in the code")
print("  • Add more gates (RX, RZ, Toffoli, etc.)")
print("  • Try different entanglement patterns")
print("  • Increase qubit count")
print("=" * 70)
