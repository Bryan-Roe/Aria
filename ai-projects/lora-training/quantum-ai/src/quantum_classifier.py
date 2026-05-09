"""
Quantum Machine Learning Classifier using Qiskit
Implements a Variational Quantum Classifier (VQC) for binary classification
"""

import logging

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import RealAmplitudes, ZZFeatureMap
from qiskit.primitives import Sampler
from qiskit_algorithms.optimizers import COBYLA, SPSA
from qiskit_machine_learning.algorithms import VQC
from qiskit_machine_learning.neural_networks import SamplerQNN
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantumClassifier:
    """
    Variational Quantum Classifier for binary and multi-class classification
    """

    def __init__(self, num_features=4, num_qubits=None, reps=2, optimizer="COBYLA"):
        """
        Initialize the quantum classifier

        Args:
            num_features: Number of input features
            num_qubits: Number of qubits (defaults to num_features)
            reps: Number of repetitions in the variational form
            optimizer: Optimization algorithm ('COBYLA' or 'SPSA')
        """
        self.num_features = num_features
        self.num_qubits = num_qubits or num_features
        self.reps = reps
        self.vqc = None
        self.scaler = StandardScaler()

        # Select optimizer
        if optimizer == "COBYLA":
            self.optimizer = COBYLA(maxiter=100)
        elif optimizer == "SPSA":
            self.optimizer = SPSA(maxiter=100)
        else:
            raise ValueError(f"Unknown optimizer: {optimizer}")

        logger.info(f"Initialized QuantumClassifier with {self.num_qubits} qubits")

    def _create_feature_map(self):
        """Create the feature map circuit"""
        return ZZFeatureMap(feature_dimension=self.num_qubits, reps=2)

    def _create_ansatz(self):
        """Create the variational ansatz circuit"""
        return RealAmplitudes(num_qubits=self.num_qubits, reps=self.reps)

    def build_circuit(self):
        """Build the complete quantum circuit"""
        feature_map = self._create_feature_map()
        ansatz = self._create_ansatz()

        # Combine feature map and ansatz
        circuit = QuantumCircuit(self.num_qubits)
        circuit.compose(feature_map, inplace=True)
        circuit.compose(ansatz, inplace=True)

        return circuit

    def fit(self, X_train, y_train, quantum_instance=None):
        """
        Train the quantum classifier

        Args:
            X_train: Training features
            y_train: Training labels
            quantum_instance: Quantum backend (None for simulator)
        """
        logger.info("Starting quantum classifier training...")

        # Normalize features
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Create feature map and ansatz
        feature_map = self._create_feature_map()
        ansatz = self._create_ansatz()

        # Create VQC
        self.vqc = VQC(
            feature_map=feature_map,
            ansatz=ansatz,
            optimizer=self.optimizer,
            sampler=Sampler(),
        )

        # Train the model
        self.vqc.fit(X_train_scaled, y_train)

        logger.info("Training complete!")
        return self

    def predict(self, X_test):
        """
        Make predictions using the trained quantum classifier

        Args:
            X_test: Test features

        Returns:
            predictions: Predicted labels
        """
        if self.vqc is None:
            raise ValueError("Model not trained. Call fit() first.")

        X_test_scaled = self.scaler.transform(X_test)
        predictions = self.vqc.predict(X_test_scaled)

        return predictions

    def score(self, X_test, y_test):
        """
        Calculate accuracy score

        Args:
            X_test: Test features
            y_test: True labels

        Returns:
            accuracy: Classification accuracy
        """
        if self.vqc is None:
            raise ValueError("Model not trained. Call fit() first.")

        X_test_scaled = self.scaler.transform(X_test)
        accuracy = self.vqc.score(X_test_scaled, y_test)

        logger.info(f"Test accuracy: {accuracy:.4f}")
        return accuracy


class QuantumNeuralNetwork:
    """
    Quantum Neural Network using parameterized quantum circuits
    """

    def __init__(self, num_qubits=4, layers=3):
        """
        Initialize quantum neural network

        Args:
            num_qubits: Number of qubits
            layers: Number of layers in the circuit
        """
        self.num_qubits = num_qubits
        self.layers = layers
        self.qnn = None
        self.weights = None

        logger.info(
            f"Initialized QuantumNeuralNetwork with {num_qubits} qubits, {layers} layers"
        )

    def build_circuit(self):
        """Build parameterized quantum circuit"""
        # Input parameters
        inputs = ParameterVector("x", self.num_qubits)

        # Weight parameters
        num_weights = self.layers * self.num_qubits * 3
        weights = ParameterVector("θ", num_weights)

        qc = QuantumCircuit(self.num_qubits)

        # Encode input data
        for i in range(self.num_qubits):
            qc.ry(inputs[i], i)

        # Variational layers
        weight_idx = 0
        for layer in range(self.layers):
            # Rotation layer
            for i in range(self.num_qubits):
                qc.rx(weights[weight_idx], i)
                weight_idx += 1
                qc.ry(weights[weight_idx], i)
                weight_idx += 1
                qc.rz(weights[weight_idx], i)
                weight_idx += 1

            # Entanglement layer
            for i in range(self.num_qubits - 1):
                qc.cx(i, i + 1)
            if self.num_qubits > 2:
                qc.cx(self.num_qubits - 1, 0)

        return qc, inputs, weights

    def create_qnn(self):
        """Create the quantum neural network"""
        circuit, inputs, weights = self.build_circuit()

        # Create QNN
        self.qnn = SamplerQNN(
            circuit=circuit,
            input_params=inputs,
            weight_params=weights,
            sampler=Sampler(),
        )

        # Initialize random weights
        self.weights = np.random.randn(len(weights)) * 0.1

        return self.qnn

    def forward(self, input_data):
        """
        Forward pass through the quantum network

        Args:
            input_data: Input features

        Returns:
            output: Network output
        """
        if self.qnn is None:
            self.create_qnn()

        # Ensure input is 2D
        if len(input_data.shape) == 1:
            input_data = input_data.reshape(1, -1)

        output = self.qnn.forward(input_data, self.weights)
        return output


if __name__ == "__main__":
    # Example usage
    from sklearn.datasets import make_classification

    # Generate synthetic dataset
    X, y = make_classification(
        n_samples=100,
        n_features=4,
        n_informative=3,
        n_redundant=1,
        n_classes=2,
        random_state=42,
    )

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Create and train quantum classifier
    qc = QuantumClassifier(num_features=4, num_qubits=4, reps=2)
    qc.fit(X_train, y_train)

    # Evaluate
    accuracy = qc.score(X_test, y_test)
    print(f"Quantum Classifier Accuracy: {accuracy:.4f}")

    # Test quantum neural network
    qnn = QuantumNeuralNetwork(num_qubits=4, layers=3)
    qnn.create_qnn()

    # Forward pass
    output = qnn.forward(X_test[:1])
    print(f"QNN Output shape: {output.shape}")
