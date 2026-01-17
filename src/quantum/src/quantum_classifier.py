"""
Quantum Classifier using PennyLane and Azure Quantum
"""
import pennylane as qml
import numpy as np
import torch
import torch.nn as nn
from typing import List, Tuple, Optional
import yaml
import logging
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumClassifier:
    """
    A quantum classifier implementing a variational quantum circuit
    for binary and multi-class classification tasks.
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize the quantum classifier.
        
        Args:
            config_path: Path to the configuration file
        """
        if config_path is None:
            # Get the directory of this file and construct path to config
            current_dir = Path(__file__).parent
            config_path = current_dir.parent / "config" / "quantum_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.n_qubits = self.config['ml']['model']['n_qubits']
        self.n_layers = self.config['ml']['model']['n_layers']
        self.entanglement = self.config['ml']['model']['entanglement']
        
        # Initialize quantum device
        self.dev = qml.device(
            self.config['quantum']['simulator']['backend'],
            wires=self.n_qubits
        )
        
        # Create quantum circuit
        self.qnode = qml.QNode(self._circuit, self.dev, interface='torch')
        
        logger.info(f"Initialized QuantumClassifier with {self.n_qubits} qubits and {self.n_layers} layers")
    
    def _circuit(self, inputs: torch.Tensor, weights: torch.Tensor) -> List[float]:
        """
        Define the quantum circuit architecture.
        
        Args:
            inputs: Input features (normalized to [0, 2π])
            weights: Trainable quantum parameters
            
        Returns:
            Expectation values of Pauli-Z measurements
        """
        # Enhanced data encoding with amplitude and phase
        for i in range(self.n_qubits):
            idx = i % len(inputs)
            # RY for amplitude encoding
            qml.RY(inputs[idx], wires=i)
            # Add RZ for phase encoding (increases circuit expressiveness)
            if i < len(inputs):
                qml.RZ(inputs[idx] * 0.5, wires=i)
        
        # Variational layers
        for layer in range(self.n_layers):
            # Rotation gates
            for i in range(self.n_qubits):
                qml.RY(weights[layer, i, 0], wires=i)
                qml.RZ(weights[layer, i, 1], wires=i)
            
            # Entanglement
            if self.entanglement == 'linear':
                for i in range(self.n_qubits - 1):
                    qml.CNOT(wires=[i, i + 1])
            elif self.entanglement == 'circular':
                for i in range(self.n_qubits):
                    qml.CNOT(wires=[i, (i + 1) % self.n_qubits])
            elif self.entanglement == 'full':
                for i in range(self.n_qubits):
                    for j in range(i + 1, self.n_qubits):
                        qml.CNOT(wires=[i, j])
        
                # Final rotation layer for enhanced expressiveness
                for i in range(self.n_qubits):
                    qml.RY(weights[-1, i, 0] * 0.5, wires=i)
        
        # Measurements
        return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]
    
    def forward(self, inputs: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the quantum circuit.
        
        Args:
            inputs: Batch of input features
            weights: Quantum circuit parameters
            
        Returns:
            Circuit outputs
        """
        batch_size = inputs.shape[0]
        
        # Pre-allocate output tensor for better memory efficiency
        outputs = torch.empty(batch_size, self.n_qubits, dtype=torch.float32)
        
        for i, inp in enumerate(inputs):
            result = self.qnode(inp, weights)
            # Convert list of expectation values to tensor
            if isinstance(result, list):
                outputs[i] = torch.tensor(result, dtype=torch.float32)
            else:
                outputs[i] = result
        
        return outputs
    
    def initialize_weights(self) -> torch.Tensor:
        """
        Initialize random weights for the quantum circuit.
        
        Returns:
            Random weight tensor
        """
        weights = torch.randn(
            self.n_layers, 
            self.n_qubits, 
            2,  # RY and RZ parameters
            requires_grad=True
        )
        return weights
    
    def preprocess_data(self, X: np.ndarray) -> torch.Tensor:
        """
        Preprocess classical data for quantum encoding.
        
        Args:
            X: Classical feature data
            
        Returns:
            Normalized torch tensor
        """
        # Normalize to [0, 2π] for quantum encoding
        # Use in-place operations for better memory efficiency
        X_min = X.min()
        X_range = X.max() - X_min
        # Use small epsilon to avoid division by zero when all values are identical
        if X_range == 0:
            X_range = 1e-8
        X_normalized = (X - X_min) / X_range * (2 * np.pi)
        return torch.FloatTensor(X_normalized)
    
    def predict(self, X: np.ndarray, weights: torch.Tensor) -> np.ndarray:
        """
        Make predictions on new data.
        
        Args:
            X: Input features
            weights: Trained quantum parameters
            
        Returns:
            Predictions
        """
        X_processed = self.preprocess_data(X)
        outputs = self.forward(X_processed, weights)
        predictions = torch.sign(outputs[:, 0])  # Binary classification
        return predictions.detach().numpy()


class HybridQuantumClassifier(nn.Module):
    """
    Hybrid classical-quantum neural network combining
    classical preprocessing with quantum processing.
    """
    
    def __init__(self, input_dim: int, quantum_classifier: QuantumClassifier):
        """
        Initialize hybrid model.
        
        Args:
            input_dim: Dimension of input features
            quantum_classifier: Quantum classifier instance
        """
        super().__init__()
        self.quantum_classifier = quantum_classifier
        
        # Classical preprocessing layers
        self.classical_layers = nn.Sequential(
            nn.Linear(input_dim, 8),
            nn.ReLU(),
            nn.Linear(8, quantum_classifier.n_qubits)
        )
        
        # Quantum weights
        self.quantum_weights = nn.Parameter(
            quantum_classifier.initialize_weights()
        )
        
        # Classical postprocessing
        self.output_layer = nn.Linear(quantum_classifier.n_qubits, 1)
        
        logger.info(f"Initialized HybridQuantumClassifier with input_dim={input_dim}")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the hybrid model.
        
        Args:
            x: Input features
            
        Returns:
            Model predictions
        """
        # Classical preprocessing
        x = self.classical_layers(x)
        
        # Quantum processing
        quantum_out = self.quantum_classifier.forward(x, self.quantum_weights)
        
        # Classical postprocessing
        output = self.output_layer(quantum_out)
        return torch.sigmoid(output)


def train_quantum_model(
    model: HybridQuantumClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    config_path: str = None
) -> dict:
    """
    Train the hybrid quantum model.
    
    Args:
        model: Hybrid quantum classifier
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        config_path: Path to configuration file
        
    Returns:
        Training history
    """
    if config_path is None:
        # Get the directory of this file and construct path to config
        current_dir = Path(__file__).parent
        config_path = current_dir.parent / "config" / "quantum_config.yaml"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Training parameters
    epochs = config['ml']['training']['epochs']
    batch_size = config['ml']['training']['batch_size']
    lr = config['ml']['training']['learning_rate']
    
    # Setup
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    
    X_train_tensor = torch.FloatTensor(X_train)
    y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1)
    
    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    
    logger.info(f"Starting training for {epochs} epochs")
    
    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        
        # Mini-batch training
        for i in range(0, len(X_train), batch_size):
            batch_X = X_train_tensor[i:i+batch_size]
            batch_y = y_train_tensor[i:i+batch_size]
            
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = criterion(predictions, batch_y)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / (len(X_train) // batch_size)
        history['train_loss'].append(avg_loss)
        
        # Validation
        if X_val is not None and y_val is not None:
            model.eval()
            with torch.no_grad():
                X_val_tensor = torch.FloatTensor(X_val)
                y_val_tensor = torch.FloatTensor(y_val).unsqueeze(1)
                
                val_predictions = model(X_val_tensor)
                val_loss = criterion(val_predictions, y_val_tensor)
                
                # Calculate accuracy
                val_acc = ((val_predictions > 0.5).float() == y_val_tensor).float().mean()
                
                history['val_loss'].append(val_loss.item())
                history['val_acc'].append(val_acc.item())
        
        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch}/{epochs} - Loss: {avg_loss:.4f}")
            if X_val is not None:
                logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
    
    logger.info("Training completed")
    return history


if __name__ == "__main__":
    # Example usage
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    # Generate sample data
    X, y = make_classification(n_samples=200, n_features=4, n_classes=2, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Initialize and train
    qc = QuantumClassifier()
    model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)
    
    history = train_quantum_model(model, X_train, y_train, X_val, y_val)
    
    print("Training completed!")
    print(f"Final validation accuracy: {history['val_acc'][-1]:.4f}")
