"""
Grover's Search Algorithm Implementation
Quantum search algorithm for finding marked items in an unsorted database
"""
import pennylane as qml
import numpy as np
from typing import List, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class GroverCircuit:
    """
    Grover's algorithm for quantum search.
    Finds a marked item in O(√N) time vs O(N) classically.
    """
    
    def __init__(
        self, 
        n_qubits: int = 3,
        backend: str = "lightning.qubit",
        shots: Optional[int] = 1000
    ):
        """
        Initialize Grover's algorithm circuit.
        
        Args:
            n_qubits: Number of qubits (search space size = 2^n_qubits)
            backend: PennyLane device backend
            shots: Number of measurement shots (None for exact simulation)
        """
        self.n_qubits = n_qubits
        self.search_space_size = 2 ** n_qubits
        self.dev = qml.device(backend, wires=n_qubits, shots=shots)
        
        # Optimal number of Grover iterations
        self.n_iterations = int(np.pi / 4 * np.sqrt(self.search_space_size))
        
        logger.info(
            f"Grover circuit initialized: {n_qubits} qubits, "
            f"search space = {self.search_space_size}, "
            f"optimal iterations = {self.n_iterations}"
        )
    
    def create_oracle(self, marked_states: List[int]) -> Callable:
        """
        Create an oracle that marks target states with a phase flip.
        
        Args:
            marked_states: List of integers representing marked computational basis states
            
        Returns:
            Oracle function
        """
        def oracle():
            """Apply phase flip to marked states"""
            for state in marked_states:
                # Convert state to binary string
                binary = format(state, f'0{self.n_qubits}b')
                
                # Apply X gates to qubits that should be 0
                for i, bit in enumerate(binary):
                    if bit == '0':
                        qml.PauliX(wires=i)
                
                # Multi-controlled Z gate (marks the state)
                if self.n_qubits == 1:
                    qml.PauliZ(wires=0)
                elif self.n_qubits == 2:
                    qml.CZ(wires=[0, 1])
                else:
                    # Use multi-controlled Z via ancilla-free approach
                    qml.MultiControlledX(
                        wires=list(range(self.n_qubits)),
                        control_values='1' * (self.n_qubits - 1)
                    )
                    qml.PauliZ(wires=self.n_qubits - 1)
                    qml.MultiControlledX(
                        wires=list(range(self.n_qubits)),
                        control_values='1' * (self.n_qubits - 1)
                    )
                
                # Uncompute X gates
                for i, bit in enumerate(binary):
                    if bit == '0':
                        qml.PauliX(wires=i)
        
        return oracle
    
    def diffusion_operator(self):
        """
        Grover diffusion operator (inversion about average).
        Amplifies amplitude of marked states.
        """
        # Apply H to all qubits
        for i in range(self.n_qubits):
            qml.Hadamard(wires=i)
        
        # Apply X to all qubits
        for i in range(self.n_qubits):
            qml.PauliX(wires=i)
        
        # Multi-controlled Z (same as oracle for all-ones state)
        if self.n_qubits == 1:
            qml.PauliZ(wires=0)
        elif self.n_qubits == 2:
            qml.CZ(wires=[0, 1])
        else:
            qml.MultiControlledX(
                wires=list(range(self.n_qubits)),
                control_values='1' * (self.n_qubits - 1)
            )
            qml.PauliZ(wires=self.n_qubits - 1)
            qml.MultiControlledX(
                wires=list(range(self.n_qubits)),
                control_values='1' * (self.n_qubits - 1)
            )
        
        # Apply X to all qubits
        for i in range(self.n_qubits):
            qml.PauliX(wires=i)
        
        # Apply H to all qubits
        for i in range(self.n_qubits):
            qml.Hadamard(wires=i)
    
    def search(self, marked_states: List[int], iterations: Optional[int] = None) -> dict:
        """
        Execute Grover's search algorithm.
        
        Args:
            marked_states: States to search for (list of integers)
            iterations: Number of Grover iterations (None for optimal)
            
        Returns:
            Dictionary with measurement results
        """
        if iterations is None:
            iterations = self.n_iterations
        
        oracle = self.create_oracle(marked_states)
        
        @qml.qnode(self.dev)
        def circuit():
            # Initialize in superposition
            for i in range(self.n_qubits):
                qml.Hadamard(wires=i)
            
            # Grover iterations
            for _ in range(iterations):
                oracle()
                self.diffusion_operator()
            
            return qml.counts()
        
        results = circuit()
        
        # Convert results to probabilities
        total = sum(results.values())
        probabilities = {state: count / total for state, count in results.items()}
        
        logger.info(f"Grover search completed with {iterations} iterations")
        logger.info(f"Top 3 results: {sorted(probabilities.items(), key=lambda x: x[1], reverse=True)[:3]}")
        
        return {
            'counts': results,
            'probabilities': probabilities,
            'marked_states': marked_states,
            'iterations': iterations,
            'success_probability': sum(probabilities.get(format(s, f'0{self.n_qubits}b'), 0) for s in marked_states)
        }
    
    def visualize_amplitudes(self, marked_states: List[int]) -> None:
        """
        Visualize amplitude amplification over iterations.
        
        Args:
            marked_states: States to search for
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.warning("matplotlib not available for visualization")
            return
        
        oracle = self.create_oracle(marked_states)
        iterations_range = range(0, min(self.n_iterations * 2, 20))
        probabilities = []
        
        for n_iter in iterations_range:
            @qml.qnode(self.dev)
            def circuit():
                for i in range(self.n_qubits):
                    qml.Hadamard(wires=i)
                
                for _ in range(n_iter):
                    oracle()
                    self.diffusion_operator()
                
                return qml.probs(wires=range(self.n_qubits))
            
            probs = circuit()
            # Sum probability of all marked states
            marked_prob = sum(probs[state] for state in marked_states)
            probabilities.append(marked_prob)
        
        plt.figure(figsize=(10, 6))
        plt.plot(iterations_range, probabilities, 'b-o', linewidth=2, markersize=8)
        plt.axvline(x=self.n_iterations, color='r', linestyle='--', label='Optimal iterations')
        plt.xlabel('Number of Grover Iterations', fontsize=12)
        plt.ylabel('Success Probability', fontsize=12)
        plt.title(f"Grover's Algorithm Amplitude Amplification\n{self.n_qubits} qubits, marked states: {marked_states}", fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig('grover_amplification.png', dpi=150)
        logger.info("Visualization saved to grover_amplification.png")
        plt.show()


def demo():
    """Demonstrate Grover's algorithm"""
    print("=" * 70)
    print("  GROVER'S QUANTUM SEARCH ALGORITHM")
    print("=" * 70)
    
    # Example 1: Search in 8-item database (3 qubits)
    print("\n[Example 1] Searching for item '5' in 8-item database")
    print("-" * 70)
    
    grover = GroverCircuit(n_qubits=3, shots=1000)
    results = grover.search(marked_states=[5])
    
    print(f"Search space size: {grover.search_space_size}")
    print(f"Optimal iterations: {grover.n_iterations}")
    print(f"Success probability: {results['success_probability']:.3f}")
    print(f"\nTop 3 measured states:")
    for state, prob in sorted(results['probabilities'].items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  |{state}⟩ (decimal {int(state, 2)}): {prob:.3f}")
    
    # Example 2: Multiple target states
    print("\n[Example 2] Searching for items '2' and '6' in 8-item database")
    print("-" * 70)
    
    results = grover.search(marked_states=[2, 6])
    print(f"Success probability: {results['success_probability']:.3f}")
    print(f"\nTop 3 measured states:")
    for state, prob in sorted(results['probabilities'].items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  |{state}⟩ (decimal {int(state, 2)}): {prob:.3f}")
    
    # Visualize amplitude amplification
    print("\n[Visualization] Generating amplitude amplification plot...")
    grover.visualize_amplitudes(marked_states=[5])
    
    print("\n" + "=" * 70)
    print("✓ Demo completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
