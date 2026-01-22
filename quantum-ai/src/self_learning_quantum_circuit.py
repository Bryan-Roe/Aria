"""
Self-learning quantum circuit with adaptive depth and entanglement search.
Combines a PennyLane variational circuit with a small classical encoder/head
and automatically tunes entanglement patterns and active layers based on
validation feedback.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pennylane as qml
import torch
import torch.nn as nn
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelfLearningQuantumCircuit(nn.Module):
    """
    Variational quantum circuit that can grow its depth and rotate through
    different entanglement patterns when training stalls.
    """

    def __init__(
        self,
        n_qubits: int = 6,
        max_layers: int = 6,
        start_layers: int = 2,
        entanglement_choices: Optional[Sequence[str]] = None,
        backend: str = "lightning.qubit",
        shots: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.n_qubits = n_qubits
        self.max_layers = max_layers
        self.active_layers = max(1, min(start_layers, max_layers))
        self.entanglement_choices = list(entanglement_choices or ["circular", "full", "ladder", "linear"])
        self.entanglement_index = 0

        self.dev = qml.device(backend, wires=self.n_qubits, shots=shots)
        self.qnode = qml.QNode(self._circuit, self.dev, interface="torch")

        # One parameter set per potential layer; only the first active_layers entries are used.
        self.quantum_weights = nn.Parameter(
            torch.randn(self.max_layers, self.n_qubits, 3) * 0.05
        )

    def _pad_inputs(self, inputs: torch.Tensor) -> torch.Tensor:
        if len(inputs) < self.n_qubits:
            pad = torch.zeros(self.n_qubits - len(inputs), device=inputs.device)
            return torch.cat([inputs, pad])
        if len(inputs) > self.n_qubits:
            return inputs[: self.n_qubits]
        return inputs

    def _entangle(self, pattern: str) -> None:
        if pattern == "linear":
            for i in range(self.n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
        elif pattern == "circular":
            for i in range(self.n_qubits):
                qml.CNOT(wires=[i, (i + 1) % self.n_qubits])
        elif pattern == "full":
            for i in range(self.n_qubits):
                for j in range(i + 1, self.n_qubits):
                    qml.CNOT(wires=[i, j])
        elif pattern == "ladder":
            for i in range(0, self.n_qubits - 1, 2):
                qml.CNOT(wires=[i, i + 1])
            half = self.n_qubits // 2
            for i in range(half):
                if i + half < self.n_qubits:
                    qml.CNOT(wires=[i, i + half])

    def _circuit(self, inputs: torch.Tensor, weights: torch.Tensor) -> List[torch.Tensor]:
        encoded = self._pad_inputs(inputs)

        # Hybrid amplitude/phase encoding
        for wire, value in enumerate(encoded):
            qml.RY(value, wires=wire)
            qml.RZ(value * 0.35, wires=wire)

        entanglement = self.entanglement_choices[self.entanglement_index]

        for layer in range(self.active_layers):
            for wire in range(self.n_qubits):
                qml.RY(weights[layer, wire, 0], wires=wire)
                qml.RZ(weights[layer, wire, 1], wires=wire)
                qml.RX(weights[layer, wire, 2], wires=wire)

            self._entangle(entanglement)

            # Lightweight data re-uploading to help the circuit self-correct
            if layer % 2 == 0:
                for wire, value in enumerate(encoded):
                    qml.RY(value * 0.15, wires=wire)

            qml.Barrier(wires=range(self.n_qubits))

        return [qml.expval(qml.PauliZ(i)) for i in range(self.n_qubits)]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        outputs: List[torch.Tensor] = []
        for sample in x:
            result = self.qnode(sample, self.quantum_weights)
            outputs.append(result if isinstance(result, torch.Tensor) else torch.stack(result))
        return torch.stack(outputs)

    def next_entanglement(self) -> str:
        self.entanglement_index = (self.entanglement_index + 1) % len(self.entanglement_choices)
        return self.entanglement_choices[self.entanglement_index]

    def grow_depth(self) -> int:
        if self.active_layers < self.max_layers:
            self.active_layers += 1
        return self.active_layers

    def status(self) -> Dict[str, str | int]:
        return {
            "entanglement": self.entanglement_choices[self.entanglement_index],
            "active_layers": self.active_layers,
            "max_layers": self.max_layers,
            "n_qubits": self.n_qubits,
        }


class SelfLearningHybridModel(nn.Module):
    """
    Classical encoder + self-learning quantum core + classical prediction head.
    """

    def __init__(
        self,
        input_dim: int,
        quantum_model: SelfLearningQuantumCircuit,
        hidden_dim: int = 32,
        output_dim: int = 1,
    ) -> None:
        super().__init__()
        self.quantum = quantum_model
        self.output_dim = output_dim

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, quantum_model.n_qubits),
            nn.Tanh(),
        )

        self.head = nn.Sequential(
            nn.Linear(quantum_model.n_qubits, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
        )

        self.activation = nn.Sigmoid() if output_dim == 1 else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(x)
        quantum_out = self.quantum(encoded)
        logits = self.head(quantum_out)
        return self.activation(logits)


class SelfLearningTrainer:
    """
    Training helper that watches validation loss and adapts entanglement/depth.
    """

    def __init__(
        self,
        model: SelfLearningHybridModel,
        learning_rate: float = 0.01,
        batch_size: int = 32,
        entanglement_patience: int = 3,
        depth_patience: int = 6,
        min_delta: float = 1e-3,
        device: str = "cpu",
    ) -> None:
        self.model = model.to(device)
        self.device = device
        self.batch_size = batch_size
        self.entanglement_patience = entanglement_patience
        self.depth_patience = depth_patience
        self.min_delta = min_delta

        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.BCELoss() if model.output_dim == 1 else nn.CrossEntropyLoss()

        self.best_val_loss = float("inf")
        self.epochs_since_improve = 0

    def _iterate_minibatches(self, X: torch.Tensor, y: torch.Tensor):
        for start in range(0, len(X), self.batch_size):
            end = start + self.batch_size
            yield X[start:end], y[start:end]

    def _adapt(self, val_loss: float) -> Dict[str, str | int | float]:
        status: Dict[str, str | int | float] = {}
        if val_loss + self.min_delta < self.best_val_loss:
            self.best_val_loss = val_loss
            self.epochs_since_improve = 0
            status["action"] = "improved"
            return status

        self.epochs_since_improve += 1
        status["action"] = "no_improve"
        status["stalled_epochs"] = self.epochs_since_improve

        if self.epochs_since_improve % self.entanglement_patience == 0:
            new_ent = self.model.quantum.next_entanglement()
            status["entanglement"] = new_ent

        if (
            self.epochs_since_improve >= self.depth_patience
            and self.model.quantum.active_layers < self.model.quantum.max_layers
        ):
            new_depth = self.model.quantum.grow_depth()
            status["active_layers"] = new_depth
            self.epochs_since_improve = 0

        return status

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        epochs: int = 25,
    ) -> Dict[str, List[float]]:
        X_train_t = torch.tensor(X_train, dtype=torch.float32, device=self.device)
        X_val_t = torch.tensor(X_val, dtype=torch.float32, device=self.device)

        if isinstance(self.criterion, nn.CrossEntropyLoss):
            y_train_t = torch.tensor(y_train, dtype=torch.long, device=self.device)
            y_val_t = torch.tensor(y_val, dtype=torch.long, device=self.device)
        else:
            y_train_t = torch.tensor(y_train, dtype=torch.float32, device=self.device)
            y_val_t = torch.tensor(y_val, dtype=torch.float32, device=self.device)

        history: Dict[str, List[float]] = {"train_loss": [], "val_loss": [], "val_acc": []}

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0.0
            for batch_X, batch_y in self._iterate_minibatches(X_train_t, y_train_t):
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                if isinstance(self.criterion, nn.CrossEntropyLoss):
                    loss = self.criterion(outputs, batch_y)
                else:
                    loss = self.criterion(outputs, batch_y.unsqueeze(1))
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / max(1, len(X_train) // self.batch_size)
            history["train_loss"].append(avg_loss)

            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_t)
                if isinstance(self.criterion, nn.CrossEntropyLoss):
                    val_loss = self.criterion(val_outputs, y_val_t).item()
                    val_pred = torch.argmax(val_outputs, dim=1)
                    val_acc = (val_pred == y_val_t).float().mean().item()
                else:
                    val_loss = self.criterion(val_outputs, y_val_t.unsqueeze(1)).item()
                    val_pred = (val_outputs > 0.5).float()
                    val_acc = (val_pred == y_val_t.unsqueeze(1)).float().mean().item()

            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            adapt_status = self._adapt(val_loss)
            logger.info(
                "Epoch %d/%d - loss %.4f - val_loss %.4f - val_acc %.4f %s",
                epoch + 1,
                epochs,
                avg_loss,
                val_loss,
                val_acc,
                f"| adapted: {adapt_status}" if adapt_status else "",
            )

        return history


def load_config(config_path: Optional[str] = None) -> Dict:
    cfg_path = config_path or Path(__file__).parent.parent / "config" / "quantum_config.yaml"
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # Minimal self-learning circuit demo on make_moons
    from sklearn.datasets import make_moons
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    torch.manual_seed(42)
    np.random.seed(42)

    X, y = make_moons(n_samples=240, noise=0.15, random_state=42)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.25, random_state=42)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)

    config = load_config()
    backend = config["quantum"]["simulator"]["backend"]
    shots = config["quantum"]["simulator"].get("shots")

    quantum_core = SelfLearningQuantumCircuit(
        n_qubits=6,
        max_layers=6,
        start_layers=2,
        backend=backend,
        shots=shots,
    )

    model = SelfLearningHybridModel(
        input_dim=X_train.shape[1],
        quantum_model=quantum_core,
        hidden_dim=24,
        output_dim=1,
    )

    trainer = SelfLearningTrainer(
        model=model,
        learning_rate=config["ml"]["training"]["learning_rate"],
        batch_size=config["ml"]["training"]["batch_size"],
        entanglement_patience=3,
        depth_patience=6,
        device="cpu",
    )

    hist = trainer.fit(X_train, y_train, X_val, y_val, epochs=20)
    final_status = quantum_core.status()

    print("\nTraining complete.")
    print(f"Final val accuracy: {hist['val_acc'][-1]:.4f}")
    print(f"Architecture: {final_status}")
