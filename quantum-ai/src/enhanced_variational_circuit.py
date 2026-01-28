"""
Enhanced Variational Quantum Circuit with Advanced Data Encoding
Implements multiple encoding strategies and improved entanglement patterns
"""
import pennylane as qml
import torch
import torch.nn as nn
import numpy as np
from typing import List, Optional, Literal
import logging

logger = logging.getLogger(__name__)


class EnhancedVariationalCircuit(nn.Module):
    """
    Advanced VQC with multiple data encoding strategies:
    - Angle encoding (RY/RZ rotations)
    - Amplitude encoding (state vector preparation)
    - IQP encoding (instantaneous quantum polynomial)
    - Basis encoding (computational basis states)
    """
    
    def __init__(
        self,
        n_qubits: int = 4,
        n_layers: int = 3,
        encoding: Literal["angle", "amplitude", "iqp", "hybrid"] = "hybrid",
        entanglement: Literal["linear", "circular", "full", "pyramid", "alternating"] = "pyramid",
        backend: str = "lightning.qubit",
        shots: Optional[int] = None,
        use_data_reuploading: bool = True
    ):
        """
        Initialize enhanced variational circuit.
        
        Args:
            n_qubits: Number of qubits
            n_layers: Number of variational layers
            encoding: Data encoding strategy
            entanglement: Entanglement pattern
            backend: PennyLane device backend
            shots: Number of shots (None for statevector)
            use_data_reuploading: Whether to reupload data between layers
        """
        super().__init__()
        
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.encoding = encoding
        self.entanglement = entanglement
        self.use_data_reuploading = use_data_reuploading
        
        self.dev = qml.device(backend, wires=n_qubits, shots=shots)
        
        # Trainable parameters: 3 rotation angles per qubit per layer
        self.quantum_weights = nn.Parameter(
            torch.randn(n_layers, n_qubits, 3) * 0.1
        )
        
        # Additional parameters for hybrid encoding
        if encoding == "hybrid":
            self.encoding_weights = nn.Parameter(
                torch.randn(n_qubits, 2) * 0.1
            )
        
        logger.info(
            f"Enhanced VQC: {n_qubits} qubits, {n_layers} layers, "
            f"encoding={encoding}, entanglement={entanglement}"
        )
    
    def _angle_encoding(self, inputs: torch.Tensor):
        """
        Angle encoding: encode data as rotation angles.
        Most common for small feature spaces.
        """
        # Ensure inputs match qubit count
        if len(inputs) < self.n_qubits:
            inputs = torch.cat([inputs, torch.zeros(self.n_qubits - len(inputs))])
        elif len(inputs) > self.n_qubits:
            inputs = inputs[:self.n_qubits]
        
        for i, val in enumerate(inputs):
            qml.RY(val * np.pi, wires=i)
            qml.RZ(val * np.pi * 0.5, wires=i)
    
    def _amplitude_encoding(self, inputs: torch.Tensor):
        """
        Amplitude encoding: encode data as amplitudes of quantum state.
        Exponentially efficient but requires normalization.
        """
        # Pad to 2^n_qubits if needed
        required_size = 2 ** self.n_qubits
        if len(inputs) < required_size:
            inputs = torch.cat([inputs, torch.zeros(required_size - len(inputs))])
        elif len(inputs) > required_size:
            inputs = inputs[:required_size]
        
        qml.AmplitudeEmbedding(
            features=inputs.detach().numpy(),
            wires=range(self.n_qubits),
            normalize=True,
            pad_with=0.0
        )
    
    def _iqp_encoding(self, inputs: torch.Tensor):
        """
        IQP (Instantaneous Quantum Polynomial) encoding.
        Creates diagonal unitaries that are classically hard to simulate.
        """
        if len(inputs) < self.n_qubits:
            inputs = torch.cat([inputs, torch.zeros(self.n_qubits - len(inputs))])
        elif len(inputs) > self.n_qubits:
            inputs = inputs[:self.n_qubits]
        
        # Hadamard layer
        for i in range(self.n_qubits):
            qml.Hadamard(wires=i)
        
        # Diagonal unitaries (single-qubit phase gates)
        for i, val in enumerate(inputs):
            qml.RZ(val * np.pi, wires=i)
        
        # Two-qubit diagonal unitaries (entangling)
        for i in range(self.n_qubits - 1):
            qml.IsingZZ(inputs[i] * inputs[i+1] * np.pi * 0.5, wires=[i, i+1])
    
    def _hybrid_encoding(self, inputs: torch.Tensor):
        """
        Hybrid encoding: combines angle and amplitude encoding.
        More expressive for complex data.
        """
        if len(inputs) < self.n_qubits:
            inputs = torch.cat([inputs, torch.zeros(self.n_qubits - len(inputs))])
        elif len(inputs) > self.n_qubits:
            inputs = inputs[:self.n_qubits]
        
        # Angle encoding with learned scaling
        for i, val in enumerate(inputs):
            qml.RY(val * self.encoding_weights[i, 0] * np.pi, wires=i)
            qml.RZ(val * self.encoding_weights[i, 1] * np.pi, wires=i)
        
        # Light entangling to spread information
        for i in range(self.n_qubits - 1):
            qml.CNOT(wires=[i, i+1])
    
    def _apply_encoding(self, inputs: torch.Tensor):
        """Apply selected encoding strategy"""
        if self.encoding == "angle":
            self._angle_encoding(inputs)
        elif self.encoding == "amplitude":
            self._amplitude_encoding(inputs)
        elif self.encoding == "iqp":
            self._iqp_encoding(inputs)
        elif self.encoding == "hybrid":
            self._hybrid_encoding(inputs)
    
    def _apply_entanglement(self):
        """Apply selected entanglement pattern"""
        if self.entanglement == "linear":
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i+1])
        
        elif self.entanglement == "circular":
            for i in range(self.n_qubits):
                qml.CNOT(wires=[i, (i+1) % self.n_qubits])
        
        elif self.entanglement == "full":
            for i in range(self.n_qubits):
                for j in range(i+1, self.n_qubits):
                    qml.CNOT(wires=[i, j])
        
        elif self.entanglement == "pyramid":
            # Hierarchical entanglement: pairs, then groups of 4, etc.
            step = 1
            while step < self.n_qubits:
                for i in range(0, self.n_qubits - step, step * 2):
                    qml.CNOT(wires=[i, i + step])
                step *= 2
        
        elif self.entanglement == "alternating":
            # Alternate between even-odd and odd-even pairs
            # Even-odd pairs
            for i in range(0, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i+1])
            # Odd-even pairs
            for i in range(1, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i+1])
    
    def _variational_layer(self, layer_idx: int):
        """Apply single variational layer"""
        weights = self.quantum_weights[layer_idx]
        
        # Rotation gates (RY, RZ, RX for full expressiveness)
        for i in range(self.n_qubits):
            qml.RY(weights[i, 0], wires=i)
            qml.RZ(weights[i, 1], wires=i)
            qml.RX(weights[i, 2], wires=i)
        
        # Entanglement
        self._apply_entanglement()
    
    def circuit(self, inputs: torch.Tensor) -> List[float]:
        """
        Execute the full quantum circuit.
        
        Args:
            inputs: Input features
            
        Returns:
            Expectation values from all qubits
        """
        # Initial encoding
        self._apply_encoding(inputs)
        
        # Variational layers
        for layer in range(self.n_layers):
            self._variational_layer(layer)
            
            # Data reuploading (optional, improves expressivity)
            if self.use_data_reuploading and layer < self.n_layers - 1:
                self._apply_encoding(inputs)
        
        # Measurements
        return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through quantum circuit.
        
        Args:
            x: Input tensor [batch_size, features] or [features]
            
        Returns:
            Output tensor [batch_size, n_qubits] or [n_qubits]
        """
        if x.dim() == 1:
            # Single sample
            qnode = qml.QNode(lambda inputs: self.circuit(inputs), self.dev, interface="torch")
            result = qnode(x)
            return torch.tensor(result) if not isinstance(result, torch.Tensor) else result
        else:
            # Batch processing
            results = []
            for sample in x:
                qnode = qml.QNode(lambda inputs: self.circuit(inputs), self.dev, interface="torch")
                result = qnode(sample)
                results.append(torch.tensor(result) if not isinstance(result, torch.Tensor) else result)
            return torch.stack(results)
    
    def get_circuit_info(self) -> dict:
        """Get circuit configuration info"""
        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "encoding": self.encoding,
            "entanglement": self.entanglement,
            "data_reuploading": self.use_data_reuploading,
            "n_parameters": self.quantum_weights.numel(),
            "circuit_depth_estimate": self.n_layers * (3 + self._estimate_entanglement_depth())
        }
    
    def _estimate_entanglement_depth(self) -> int:
        """Estimate depth of entanglement layer"""
        if self.entanglement == "linear":
            return self.n_qubits - 1
        elif self.entanglement == "circular":
            return self.n_qubits
        elif self.entanglement == "full":
            return self.n_qubits * (self.n_qubits - 1) // 2
        elif self.entanglement == "pyramid":
            return int(np.ceil(np.log2(self.n_qubits)))
        elif self.entanglement == "alternating":
            return (self.n_qubits - 1)
        return self.n_qubits


def compare_encodings():
    """Compare different encoding strategies"""
    print("=" * 70)
    print("  ENCODING STRATEGY COMPARISON")
    print("=" * 70)
    
    encodings = ["angle", "amplitude", "iqp", "hybrid"]
    n_qubits = 4
    
    # Sample input
    test_input = torch.randn(4) * 0.5
    
    print(f"\nTest input: {test_input.tolist()}")
    print(f"Number of qubits: {n_qubits}\n")
    
    for encoding in encodings:
        print(f"\n[{encoding.upper()} ENCODING]")
        print("-" * 70)
        
        circuit = EnhancedVariationalCircuit(
            n_qubits=n_qubits,
            n_layers=2,
            encoding=encoding,
            entanglement="pyramid"
        )
        
        output = circuit.forward(test_input)
        info = circuit.get_circuit_info()
        
        print(f"Parameters: {info['n_parameters']}")
        print(f"Circuit depth: ~{info['circuit_depth_estimate']}")
        print(f"Output: {output[0].detach().numpy()}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    compare_encodings()
