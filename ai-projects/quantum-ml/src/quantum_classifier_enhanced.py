"""
Enhanced Quantum Classifier with 6-8 Qubits Support
Optimized for complex patterns and real quantum hardware deployment
"""

import logging
from pathlib import Path
from typing import List

import numpy as np
import pennylane as qml
import torch
import torch.nn as nn
import yaml

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedQuantumClassifier:
    """
    Enhanced quantum classifier supporting 6-8 qubits with advanced features:
    - Data re-uploading for better expressivity
    - Optimized entanglement patterns
    - Hardware-ready circuit compilation
    """

    def __init__(self, n_qubits: int = 8, n_layers: int = 4, config_path: str = None):
        """
        Initialize the enhanced quantum classifier.

        Args:
            n_qubits: Number of qubits (6-8 recommended for complex patterns)
            n_layers: Number of variational layers
            config_path: Path to the configuration file
        """
        if config_path is None:
            current_dir = Path(__file__).parent
            config_path = current_dir.parent / "config" / "quantum_config.yaml"

        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        # Override with enhanced settings
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.entanglement = self.config["ml"]["model"].get("entanglement", "circular")
        self.data_reuploading = True  # Enable data re-uploading

        # Initialize quantum device
        self.dev = qml.device(
            self.config["quantum"]["simulator"]["backend"], wires=self.n_qubits
        )

        # Create quantum circuit
        self.qnode = qml.QNode(self._circuit, self.dev, interface="torch")

        logger.info(
            f"Enhanced QuantumClassifier: {self.n_qubits} qubits, {self.n_layers} layers, {self.entanglement} entanglement"
        )

    def _data_encoding(self, inputs: torch.Tensor, wire_idx: int):
        """
        Advanced data encoding with amplitude and phase information.

        Args:
            inputs: Input features
            wire_idx: Qubit wire index
        """
        # Use multiple rotation gates for richer encoding
        input_idx = wire_idx % len(inputs)
        qml.RY(inputs[input_idx] * np.pi, wires=wire_idx)
        qml.RZ(inputs[input_idx] * np.pi / 2, wires=wire_idx)

    def _variational_layer(self, weights: torch.Tensor, layer_idx: int):
        """
        Variational layer with rotation gates.

        Args:
            weights: Layer weights
            layer_idx: Current layer index
        """
        for i in range(self.n_qubits):
            qml.RY(weights[layer_idx, i, 0], wires=i)
            qml.RZ(weights[layer_idx, i, 1], wires=i)
            qml.RX(
                weights[layer_idx, i, 2], wires=i
            )  # Additional rotation for expressivity

    def _entanglement_layer(self):
        """
        Apply entanglement based on configured pattern.
        Optimized for 6-8 qubits.
        """
        if self.entanglement == "linear":
            # Adjacent qubit entanglement
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        elif self.entanglement == "circular":
            # Circular ring with all-to-all connections
            for i in range(self.n_qubits):
                qml.CNOT(wires=[i, (i + 1) % self.n_qubits])
            # Add diagonal connections for better connectivity
            for i in range(0, self.n_qubits - 2, 2):
                qml.CNOT(wires=[i, i + 2])

        elif self.entanglement == "full":
            # Full entanglement (expensive but expressive)
            for i in range(self.n_qubits):
                for j in range(i + 1, self.n_qubits):
                    qml.CNOT(wires=[i, j])

        elif self.entanglement == "ladder":
            # Ladder pattern optimized for 8 qubits
            # Horizontal connections
            for i in range(0, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i + 1])
            # Vertical connections
            for i in range(self.n_qubits // 2):
                if i + self.n_qubits // 2 < self.n_qubits:
                    qml.CNOT(wires=[i, i + self.n_qubits // 2])

    def _circuit(self, inputs: torch.Tensor, weights: torch.Tensor) -> List[float]:
        """
        Enhanced quantum circuit with data re-uploading.

        Args:
            inputs: Input features (padded to n_qubits)
            weights: Trainable quantum parameters [n_layers, n_qubits, 3]

        Returns:
            Expectation values of Pauli-Z measurements
        """
        # Ensure inputs are properly sized
        if len(inputs) < self.n_qubits:
            # Pad inputs to match qubit count
            inputs = torch.cat([inputs, torch.zeros(self.n_qubits - len(inputs))])
        elif len(inputs) > self.n_qubits:
            inputs = inputs[: self.n_qubits]

        # Initial data encoding
        for i in range(self.n_qubits):
            self._data_encoding(inputs, i)

        # Variational layers with optional data re-uploading
        for layer in range(self.n_layers):
            # Variational rotations
            self._variational_layer(weights, layer)

            # Entanglement
            self._entanglement_layer()

            # Data re-uploading (every other layer)
            if self.data_reuploading and layer < self.n_layers - 1 and layer % 2 == 0:
                for i in range(self.n_qubits):
                    qml.RY(inputs[i] * np.pi / (layer + 2), wires=i)

            # Add barrier for hardware compilation
            qml.Barrier(wires=range(self.n_qubits))

        # Measurements on all qubits
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
        outputs = []

        for i in range(batch_size):
            result = self.qnode(inputs[i], weights)
            outputs.append(torch.stack(result))

        return torch.stack(outputs)

    def initialize_weights(self) -> torch.Tensor:
        """
        Initialize quantum circuit weights with Xavier initialization.

        Returns:
            Initialized weight tensor
        """
        # Shape: [n_layers, n_qubits, 3] for RY, RZ, RX rotations
        weights = torch.randn(self.n_layers, self.n_qubits, 3) * 0.01
        return weights

    def get_circuit_info(self) -> dict:
        """
        Get information about the quantum circuit.

        Returns:
            Dictionary with circuit statistics
        """
        dummy_inputs = torch.zeros(self.n_qubits)
        dummy_weights = self.initialize_weights()

        # Create a drawing of the circuit
        try:
            drawer = qml.draw(self.qnode)
            circuit_str = drawer(dummy_inputs, dummy_weights)
        except Exception:
            circuit_str = "Circuit drawing not available"

        return {
            "n_qubits": self.n_qubits,
            "n_layers": self.n_layers,
            "entanglement": self.entanglement,
            "data_reuploading": self.data_reuploading,
            "total_parameters": self.n_layers * self.n_qubits * 3,
            "circuit": circuit_str,
        }


class HybridEnhancedClassifier(nn.Module):
    """
    Hybrid quantum-classical neural network with enhanced quantum layer.
    Supports 6-8 qubits for complex pattern recognition.
    """

    def __init__(
        self,
        input_dim: int,
        n_qubits: int = 8,
        n_layers: int = 4,
        output_dim: int = 1,
        hidden_dim: int = 16,
    ):
        """
        Initialize hybrid classifier.

        Args:
            input_dim: Input feature dimension
            n_qubits: Number of qubits (6-8 recommended)
            n_layers: Number of quantum layers
            output_dim: Output dimension (1 for binary, >1 for multi-class)
            hidden_dim: Hidden layer dimension for classical preprocessing
        """
        super().__init__()

        self.input_dim = input_dim
        self.n_qubits = n_qubits
        self.output_dim = output_dim

        # Classical preprocessing layers
        self.classical_input = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, n_qubits),
            nn.Tanh(),  # Normalize to [-1, 1] for quantum encoding
        )

        # Enhanced quantum layer
        self.quantum_classifier = EnhancedQuantumClassifier(
            n_qubits=n_qubits, n_layers=n_layers
        )

        # Initialize quantum weights as trainable parameters
        self.quantum_weights = nn.Parameter(
            self.quantum_classifier.initialize_weights()
        )

        # Classical postprocessing layers
        self.classical_output = nn.Sequential(
            nn.Linear(n_qubits, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, output_dim),
        )

        if output_dim == 1:
            self.activation = nn.Sigmoid()
        else:
            self.activation = nn.Softmax(dim=1)

        logger.info(
            f"HybridEnhancedClassifier: {input_dim}→{n_qubits}Q({n_layers}L)→{output_dim}"
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through hybrid network.

        Args:
            x: Input tensor [batch_size, input_dim]

        Returns:
            Predictions [batch_size, output_dim]
        """
        # Classical preprocessing
        x = self.classical_input(x)

        # Quantum processing
        x = self.quantum_classifier.forward(x, self.quantum_weights)

        # Ensure correct dtype for classical layers
        x = x.float()

        # Classical postprocessing
        x = self.classical_output(x)
        x = self.activation(x)

        return x


def train_enhanced_model(
    model: HybridEnhancedClassifier,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 100,
    learning_rate: float = 0.01,
    batch_size: int = 32,
) -> dict:
    """
    Train the enhanced quantum model.

    Args:
        model: HybridEnhancedClassifier instance
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        epochs: Number of training epochs
        learning_rate: Learning rate
        batch_size: Batch size

    Returns:
        Training history dictionary
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.BCELoss() if model.output_dim == 1 else nn.CrossEntropyLoss()

    # Convert to tensors
    X_train_t = torch.FloatTensor(X_train)
    y_train_t = (
        torch.FloatTensor(y_train).reshape(-1, 1)
        if model.output_dim == 1
        else torch.LongTensor(y_train)
    )
    X_val_t = torch.FloatTensor(X_val)
    y_val_t = (
        torch.FloatTensor(y_val).reshape(-1, 1)
        if model.output_dim == 1
        else torch.LongTensor(y_val)
    )

    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    logger.info(f"Starting training for {epochs} epochs")

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0

        # Mini-batch training
        n_batches = len(X_train) // batch_size
        for i in range(n_batches):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size

            batch_X = X_train_t[start_idx:end_idx]
            batch_y = y_train_t[start_idx:end_idx]

            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        epoch_loss /= n_batches

        # Validation
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val_t)
            val_loss = criterion(val_outputs, y_val_t).item()

            if model.output_dim == 1:
                predictions = (val_outputs > 0.5).float()
                val_acc = (predictions == y_val_t).float().mean().item()
            else:
                predictions = torch.argmax(val_outputs, dim=1)
                val_acc = (predictions == y_val_t).float().mean().item()

        history["train_loss"].append(epoch_loss)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch}/{epochs} - Loss: {epoch_loss:.4f}")
            logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")

    logger.info("Training completed")
    return history


if __name__ == "__main__":
    # Quick test
    print("Testing Enhanced Quantum Classifier (8 qubits)...")

    # Create sample data
    from sklearn.datasets import make_moons
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X, y = make_moons(n_samples=200, noise=0.1, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    # Create enhanced model with 8 qubits
    model = HybridEnhancedClassifier(
        input_dim=2, n_qubits=8, n_layers=4, output_dim=1, hidden_dim=16
    )

    print("\nModel Architecture:")
    print(f"  Input: {model.input_dim} features")
    print(f"  Quantum: {model.n_qubits} qubits, 4 layers")
    print(f"  Total parameters: {sum(p.numel() for p in model.parameters())}")

    # Quick training test
    print("\nRunning quick training test (20 epochs)...")
    history = train_enhanced_model(
        model,
        X_train,
        y_train,
        X_val,
        y_val,
        epochs=20,
        learning_rate=0.01,
        batch_size=16,
    )

    print("\nFinal Results:")
    print(f"  Validation Accuracy: {history['val_acc'][-1]:.4f}")
    print(f"  Validation Loss: {history['val_loss'][-1]:.4f}")
    print("\n✓ Enhanced quantum classifier test completed!")
