"""
Hybrid Quantum-Classical Neural Network
Combines quantum circuits with classical deep learning
"""

import logging
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.primitives import Sampler

try:
    from qiskit_machine_learning.connectors import TorchConnector
    from qiskit_machine_learning.neural_networks import SamplerQNN

    QISKIT_ML_AVAILABLE = True
except ImportError:
    QISKIT_ML_AVAILABLE = False
    _import_error_msg = (
        "qiskit-machine-learning is not installed or not found in your environment.\n"
        "To fix:\n"
        "1. Activate your Python environment: .\\venv\\Scripts\\Activate.ps1\n"
        "2. Run: pip install qiskit-machine-learning>=0.7.0\n"
        "3. Or install all requirements: pip install -r requirements.txt\n"
        "4. Verify installation: pip list | findstr qiskit-machine-learning"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumLayer(nn.Module):
    """
    Quantum layer that can be integrated into PyTorch models
    """

    def __init__(self, num_qubits: int, num_layers: int = 2):
        """
        Initialize quantum layer

        Args:
            num_qubits: Number of qubits
            num_layers: Number of quantum circuit layers
        """
        if not QISKIT_ML_AVAILABLE:
            raise ImportError(_import_error_msg)

        super().__init__()
        self.num_qubits = num_qubits
        self.num_layers = num_layers

        # Build quantum circuit
        self.qnn = self._build_qnn()

        # Wrap QNN for PyTorch
        self.quantum_layer = TorchConnector(self.qnn)

        logger.info(
            f"Created QuantumLayer with {num_qubits} qubits, {num_layers} layers"
        )

    def _build_qnn(self):
        """Build the quantum neural network"""
        # Input and weight parameters
        inputs = ParameterVector("x", self.num_qubits)
        num_weights = self.num_layers * self.num_qubits * 3
        weights = ParameterVector("θ", num_weights)

        qc = QuantumCircuit(self.num_qubits)

        # Encode input
        for i in range(self.num_qubits):
            qc.ry(inputs[i], i)

        # Variational layers
        weight_idx = 0
        for layer in range(self.num_layers):
            # Rotation gates
            for i in range(self.num_qubits):
                qc.rx(weights[weight_idx], i)
                weight_idx += 1
                qc.ry(weights[weight_idx], i)
                weight_idx += 1
                qc.rz(weights[weight_idx], i)
                weight_idx += 1

            # Entanglement
            for i in range(self.num_qubits - 1):
                qc.cx(i, i + 1)
            if self.num_qubits > 2:
                qc.cx(self.num_qubits - 1, 0)

        # Create QNN
        qnn = SamplerQNN(
            circuit=qc, input_params=inputs, weight_params=weights, sampler=Sampler()
        )

        return qnn

    def forward(self, x):
        """Forward pass through quantum layer"""
        return self.quantum_layer(x)


class HybridQNN(nn.Module):
    """
    Hybrid Quantum-Classical Neural Network
    Classical layers -> Quantum layer -> Classical layers
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        num_qubits: int,
        quantum_layers: int,
        output_dim: int,
        dropout: float = 0.2,
    ):
        """
        Initialize hybrid QNN

        Args:
            input_dim: Input feature dimension
            hidden_dim: Hidden layer dimension
            num_qubits: Number of qubits in quantum layer
            quantum_layers: Number of quantum circuit layers
            output_dim: Output dimension (number of classes)
            dropout: Dropout rate
        """
        super().__init__()

        self.input_dim = input_dim
        self.output_dim = output_dim

        # Classical pre-processing layers
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.dropout1 = nn.Dropout(dropout)

        self.fc2 = nn.Linear(hidden_dim, num_qubits)
        self.bn2 = nn.BatchNorm1d(num_qubits)

        # Quantum layer
        self.quantum_layer = QuantumLayer(num_qubits, quantum_layers)

        # Calculate quantum output dimension (2^num_qubits for full measurement)
        quantum_output_dim = 2**num_qubits

        # Classical post-processing layers
        self.fc3 = nn.Linear(quantum_output_dim, hidden_dim)
        self.bn3 = nn.BatchNorm1d(hidden_dim)
        self.dropout2 = nn.Dropout(dropout)

        self.fc4 = nn.Linear(hidden_dim, output_dim)

        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)

        logger.info(
            f"Created HybridQNN: {input_dim} -> {hidden_dim} -> Q({num_qubits}) -> {hidden_dim} -> {output_dim}"
        )

    def forward(self, x):
        """Forward pass through hybrid network"""
        # Classical pre-processing
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)

        x = self.fc2(x)
        x = self.bn2(x)
        x = torch.tanh(x) * np.pi  # Scale to quantum parameter range

        # Quantum layer
        x = self.quantum_layer(x)

        # Classical post-processing
        x = self.fc3(x)
        x = self.bn3(x)
        x = self.relu(x)
        x = self.dropout2(x)

        x = self.fc4(x)

        return x

    def predict(self, x):
        """Make predictions with softmax"""
        logits = self.forward(x)
        return self.softmax(logits)


class QuantumClassicalTrainer:
    """
    Trainer for hybrid quantum-classical models
    """

    def __init__(
        self, model: nn.Module, learning_rate: float = 0.001, device: str = "cpu"
    ):
        """
        Initialize trainer

        Args:
            model: Hybrid QNN model
            learning_rate: Learning rate
            device: Device to train on ('cpu' or 'cuda')
        """
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()

        self.train_losses = []
        self.val_accuracies = []

        logger.info(f"Initialized trainer with lr={learning_rate}, device={device}")

    def train_epoch(self, train_loader: torch.utils.data.DataLoader) -> float:
        """
        Train for one epoch

        Args:
            train_loader: Training data loader

        Returns:
            avg_loss: Average loss for the epoch
        """
        self.model.train()
        total_loss = 0.0

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(self.device), target.to(self.device)

            # Zero gradients
            self.optimizer.zero_grad()

            # Forward pass
            output = self.model(data)

            # Compute loss
            loss = self.criterion(output, target)

            # Backward pass
            loss.backward()

            # Update weights
            self.optimizer.step()

            total_loss += loss.item()

            if (batch_idx + 1) % 10 == 0:
                logger.info(
                    f"Batch {batch_idx + 1}/{len(train_loader)}, Loss: {loss.item():.4f}"
                )

        avg_loss = total_loss / len(train_loader)
        self.train_losses.append(avg_loss)

        return avg_loss

    def evaluate(self, val_loader: torch.utils.data.DataLoader) -> Tuple[float, float]:
        """
        Evaluate model

        Args:
            val_loader: Validation data loader

        Returns:
            accuracy, loss: Validation accuracy and loss
        """
        self.model.eval()
        correct = 0
        total = 0
        total_loss = 0.0

        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(self.device), target.to(self.device)

                output = self.model(data)
                loss = self.criterion(output, target)
                total_loss += loss.item()

                _, predicted = torch.max(output.data, 1)
                total += target.size(0)
                correct += (predicted == target).sum().item()

        accuracy = 100 * correct / total
        avg_loss = total_loss / len(val_loader)

        self.val_accuracies.append(accuracy)

        return accuracy, avg_loss

    def train(
        self,
        train_loader: torch.utils.data.DataLoader,
        val_loader: torch.utils.data.DataLoader,
        num_epochs: int,
    ):
        """
        Full training loop

        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Number of epochs
        """
        logger.info(f"Starting training for {num_epochs} epochs...")

        for epoch in range(num_epochs):
            logger.info(f"\nEpoch {epoch + 1}/{num_epochs}")

            # Train
            train_loss = self.train_epoch(train_loader)

            # Evaluate
            val_acc, val_loss = self.evaluate(val_loader)

            logger.info(
                f"Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%"
            )

        logger.info("Training complete!")


if __name__ == "__main__":
    # Example usage
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from torch.utils.data import DataLoader, TensorDataset

    # Generate synthetic data
    X, y = make_classification(
        n_samples=200,
        n_features=8,
        n_informative=6,
        n_redundant=2,
        n_classes=3,
        random_state=42,
    )

    # Split and scale
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    # Create data loaders
    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
    val_dataset = TensorDataset(torch.FloatTensor(X_val), torch.LongTensor(y_val))

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

    # Create hybrid model
    model = HybridQNN(
        input_dim=8,
        hidden_dim=16,
        num_qubits=4,
        quantum_layers=2,
        output_dim=3,
        dropout=0.2,
    )

    # Train
    trainer = QuantumClassicalTrainer(model, learning_rate=0.01)
    trainer.train(train_loader, val_loader, num_epochs=5)

    print(f"Final validation accuracy: {trainer.val_accuracies[-1]:.2f}%")
