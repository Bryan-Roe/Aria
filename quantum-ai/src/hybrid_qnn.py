"""
Hybrid Quantum-Classical Neural Network
Combines quantum circuits with classical neural networks for enhanced learning
"""
import pennylane as qml
import torch
import torch.nn as nn
import numpy as np
from typing import Callable, List, Tuple
import yaml
import logging

logger = logging.getLogger(__name__)


class QuantumLayer(nn.Module):
    """
    A custom PyTorch layer that implements a quantum circuit.
    """
    
    def __init__(self, n_qubits: int, n_layers: int, device: str = "default.qubit"):
        """
        Initialize quantum layer.
        
        Args:
            n_qubits: Number of qubits
            n_layers: Number of variational layers
            device: PennyLane device
        """
        super().__init__()
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        
        # Create quantum device
        self.dev = qml.device(device, wires=n_qubits)
        
        # Initialize quantum weights
        weight_shapes = {"weights": (n_layers, n_qubits, 3)}
        self.qlayer = qml.qnn.TorchLayer(self._quantum_circuit, weight_shapes)
        
    def _quantum_circuit(self, inputs, weights):
        """
        Define the variational quantum circuit.
        
        Args:
            inputs: Classical inputs encoded into quantum states
            weights: Trainable quantum parameters
        """
        # Amplitude encoding
        qml.AmplitudeEmbedding(
            features=inputs,
            wires=range(self.n_qubits),
            normalize=True,
            pad_with=0.0
        )
        
        # Variational layers
        for layer in range(self.n_layers):
            # Rotation layer
            for i in range(self.n_qubits):
                qml.Rot(*weights[layer, i], wires=i)
            
            # Entangling layer
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
        
        # Measurement
        return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
    
    def forward(self, x):
        """Forward pass through quantum layer."""
        return self.qlayer(x)


class HybridQNN(nn.Module):
    """
    Hybrid Quantum-Classical Neural Network architecture.
    Combines classical layers for preprocessing and postprocessing
    with a quantum layer for quantum feature extraction.
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        n_qubits: int,
        n_quantum_layers: int,
        output_dim: int = 1,
        dropout: float = 0.2
    ):
        """
        Initialize hybrid QNN.
        
        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            n_qubits: Number of qubits in quantum layer
            n_quantum_layers: Number of quantum variational layers
            output_dim: Output dimension
            dropout: Dropout rate
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.n_qubits = n_qubits
        
        # Classical preprocessing
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2**n_qubits)  # Prepare for quantum encoding
        )
        
        # Quantum layer
        self.quantum_layer = QuantumLayer(n_qubits, n_quantum_layers)
        
        # Classical postprocessing
        self.decoder = nn.Sequential(
            nn.Linear(n_qubits, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim)
        )
        
        logger.info(
            f"Initialized HybridQNN: input_dim={input_dim}, "
            f"n_qubits={n_qubits}, n_quantum_layers={n_quantum_layers}"
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the hybrid network.
        
        Args:
            x: Input tensor
            
        Returns:
            Network output
        """
        # Classical encoding
        x = self.encoder(x)
        
        # Normalize for amplitude encoding
        x = torch.nn.functional.normalize(x, p=2, dim=1)
        
        # Quantum processing
        x = self.quantum_layer(x)
        
        # Classical decoding
        x = self.decoder(x)
        
        return x


class QuantumConvolutionalLayer(nn.Module):
    """
    Quantum convolutional layer for processing spatial/sequential data.
    """
    
    def __init__(self, n_qubits: int, stride: int = 1):
        """
        Initialize quantum convolutional layer.
        
        Args:
            n_qubits: Number of qubits in the quantum filter
            stride: Stride for the convolution
        """
        super().__init__()
        self.n_qubits = n_qubits
        self.stride = stride
        
        self.dev = qml.device("default.qubit", wires=n_qubits)
        
        # Trainable quantum filter
        self.weights = nn.Parameter(torch.randn(2, n_qubits, 3))
        
    def _quantum_filter(self, inputs):
        """Quantum convolution filter circuit."""
        # Encode inputs
        for i in range(self.n_qubits):
            qml.RY(inputs[i], wires=i)
        
        # Apply trainable quantum filter
        for layer in range(2):
            for i in range(self.n_qubits):
                qml.Rot(*self.weights[layer, i], wires=i)
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
        
        return qml.expval(qml.PauliZ(0))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply quantum convolution.
        
        Args:
            x: Input tensor of shape (batch, features)
            
        Returns:
            Convolved output
        """
        batch_size, n_features = x.shape
        outputs = []
        
        qnode = qml.QNode(self._quantum_filter, self.dev, interface='torch')
        
        # Slide quantum filter across input
        for i in range(0, n_features - self.n_qubits + 1, self.stride):
            window = x[:, i:i + self.n_qubits]
            window_outputs = []
            
            for sample in window:
                out = qnode(sample)
                window_outputs.append(out)
            
            outputs.append(torch.stack(window_outputs))
        
        return torch.stack(outputs, dim=1)


class QCNN(nn.Module):
    """
    Quantum Convolutional Neural Network.
    """
    
    def __init__(
        self,
        input_dim: int,
        n_qubits: int = 4,
        n_filters: int = 2,
        output_dim: int = 1
    ):
        """
        Initialize QCNN.
        
        Args:
            input_dim: Input feature dimension
            n_qubits: Qubits per quantum filter
            n_filters: Number of quantum filters
            output_dim: Output dimension
        """
        super().__init__()
        
        # Quantum convolutional layers
        self.qconv_layers = nn.ModuleList([
            QuantumConvolutionalLayer(n_qubits, stride=2)
            for _ in range(n_filters)
        ])
        
        # Calculate output size after convolutions
        conv_output_size = input_dim
        for _ in range(n_filters):
            conv_output_size = (conv_output_size - n_qubits) // 2 + 1
        
        # Classical fully connected layers
        self.fc_layers = nn.Sequential(
            nn.Linear(conv_output_size * n_filters, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_dim)
        )
        
        logger.info(f"Initialized QCNN with {n_filters} quantum filters")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through QCNN."""
        # Apply quantum convolutions
        conv_outputs = []
        for qconv in self.qconv_layers:
            conv_out = qconv(x)
            conv_outputs.append(conv_out)
        
        # Concatenate and flatten
        x = torch.cat(conv_outputs, dim=1)
        x = x.view(x.size(0), -1)
        
        # Fully connected layers
        x = self.fc_layers(x)
        
        return x


def create_hybrid_model(config_path: str = "../config/quantum_config.yaml") -> HybridQNN:
    """
    Create a hybrid QNN model from configuration.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Initialized hybrid model
    """
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    input_dim = config['ml']['data']['feature_dimension']
    n_qubits = config['ml']['model']['n_qubits']
    n_layers = config['ml']['model']['n_layers']
    
    model = HybridQNN(
        input_dim=input_dim,
        hidden_dim=16,
        n_qubits=n_qubits,
        n_quantum_layers=n_layers,
        output_dim=1
    )
    
    return model


if __name__ == "__main__":
    # Test the hybrid model
    model = HybridQNN(
        input_dim=10,
        hidden_dim=16,
        n_qubits=4,
        n_quantum_layers=2,
        output_dim=1
    )
    
    # Test forward pass
    x = torch.randn(8, 10)  # Batch of 8 samples
    output = model(x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print("Hybrid QNN test completed successfully!")
