"""
Quantum embedding transformer with classical fallback.

QuantumEmbeddingTransformer takes a classical embedding vector, applies
amplitude-encoding + variational circuit transformation, and returns a
transformed embedding of the same dimensionality.

When no quantum backend is installed, a numpy-only simulation is used.
"""

from __future__ import annotations

import logging

import numpy as np

from .quantum_sampler import _active_backend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Classical (numpy) fallback
# ---------------------------------------------------------------------------


def _classical_amplitude_transform(
    embedding: np.ndarray,
    params: np.ndarray,
    num_qubits: int,
) -> np.ndarray:
    """
    Simulate amplitude encoding + rotation via numpy linear algebra.

    The embedding is encoded as quantum amplitudes, a rotation matrix is
    constructed from params, and the result is re-projected back to the
    original dimensionality.
    """
    dim = len(embedding)

    # Amplitude-encode: normalize to unit vector
    norm = np.linalg.norm(embedding)
    if norm < 1e-12:
        return embedding.copy()
    state = embedding / norm

    # Construct pairwise real rotations (Givens-like 2x2 rotations) that preserve norm.
    # Resize params to supply one angle per rotation pair.
    angles = np.resize(params, (dim + 1) // 2) * np.pi

    transformed = state.copy().astype(float)
    # Apply 2x2 rotations across adjacent element pairs
    for i in range(0, dim - 1, 2):
        theta = angles[i // 2]
        c = np.cos(theta)
        s = np.sin(theta)
        a = transformed[i]
        b = transformed[i + 1]
        transformed[i] = c * a - s * b
        transformed[i + 1] = s * a + c * b

    # If dim is odd, the last element is left unchanged; rotations preserve norm
    return transformed * norm


# ---------------------------------------------------------------------------
# PennyLane embedding
# ---------------------------------------------------------------------------


def _pennylane_amplitude_transform(
    embedding: np.ndarray,
    params: np.ndarray,
    num_qubits: int,
    num_layers: int,
) -> np.ndarray:
    """Amplitude-encode + variational transform via PennyLane."""
    try:
        import pennylane as qml  # type: ignore  # noqa: PLC0415
    except ImportError:
        logger.warning("PennyLane not available, using classical fallback")
        return _classical_amplitude_transform(embedding, params, num_qubits)

    dim = len(embedding)
    pad_to = 2**num_qubits
    state_in = np.resize(embedding, pad_to).astype(complex)
    norm = np.linalg.norm(state_in)
    if norm < 1e-12:
        return embedding.copy()
    state_in /= norm

    dev = qml.device("default.qubit", wires=num_qubits, shots=None)

    @qml.qnode(dev)
    def circuit(state_vec, params):
        qml.AmplitudeEmbedding(state_vec, wires=range(num_qubits), normalize=True)
        for layer in range(num_layers):
            for q in range(num_qubits):
                idx = (layer * num_qubits + q) % len(params)
                qml.RY(params[idx], wires=q)
                qml.RZ(params[(idx + 1) % len(params)], wires=q)
            for q in range(num_qubits - 1):
                qml.CNOT(wires=[q, q + 1])
        return qml.state()

    out_state = np.array(circuit(state_in, params), dtype=complex)
    # Project back: take real amplitudes and resize to original dim
    transformed = np.real(out_state)
    result = np.resize(transformed, dim) * norm
    return result


# ---------------------------------------------------------------------------
# Qiskit embedding (statevector simulation)
# ---------------------------------------------------------------------------


def _qiskit_amplitude_transform(
    embedding: np.ndarray,
    params: np.ndarray,
    num_qubits: int,
    num_layers: int,
) -> np.ndarray:
    """Amplitude-encode + variational transform via Qiskit statevector sim."""
    try:
        from qiskit import QuantumCircuit, transpile  # type: ignore  # noqa: PLC0415
        from qiskit.circuit import ParameterVector  # type: ignore  # noqa: PLC0415
        from qiskit_aer import AerSimulator  # type: ignore  # noqa: PLC0415
    except ImportError:
        logger.warning("Qiskit/AerSimulator not available, using classical fallback")
        return _classical_amplitude_transform(embedding, params, num_qubits)

    dim = len(embedding)
    pad_to = 2**num_qubits
    state_in = np.zeros(pad_to, dtype=complex)
    state_in[: min(dim, pad_to)] = embedding[: min(dim, pad_to)]
    norm = np.linalg.norm(state_in)
    if norm < 1e-12:
        return embedding.copy()
    state_in /= norm

    n = num_qubits
    total_params = num_layers * n * 2
    pv = ParameterVector("θ", total_params)
    qc = QuantumCircuit(n)
    qc.initialize(state_in.tolist(), range(n))

    idx = 0
    for _layer in range(num_layers):
        for q in range(n):
            qc.ry(pv[idx % total_params], q)
            idx += 1
            qc.rz(pv[idx % total_params], q)
            idx += 1
        for q in range(n - 1):
            qc.cx(q, q + 1)

    param_dict = {pv[i]: float(params[i % len(params)]) for i in range(total_params)}
    bound = qc.assign_parameters(param_dict)

    sim = AerSimulator(method="statevector")
    job = sim.run(transpile(bound, sim))
    sv = job.result().get_statevector()
    out = np.array(sv, dtype=complex)
    result = np.resize(np.real(out), dim) * norm
    return result


# ---------------------------------------------------------------------------
# Public QuantumEmbeddingTransformer
# ---------------------------------------------------------------------------


class QuantumEmbeddingTransformer:
    """
    Transforms a classical embedding vector using quantum amplitude encoding
    followed by a variational circuit.

    The output embedding has the same dimensionality as the input.

    Parameters
    ----------
    backend : str
        One of "auto", "pennylane", "qiskit", "classical".
    num_qubits : int
        Number of qubits (default 4).  Controls the internal Hilbert-space
        dimension (2**num_qubits).  Embeddings are padded or truncated to fit.
    num_layers : int
        Number of variational layers (default 2).
    seed : int, optional
        Random seed for parameter initialization and reproducibility.
    """

    def __init__(
        self,
        backend: str = "auto",
        num_qubits: int = 4,
        num_layers: int = 2,
        seed: int | None = None,
    ) -> None:
        self.effective_backend = _active_backend(backend)
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self._rng = np.random.default_rng(seed)
        # Randomly initialized variational parameters
        n_params = num_qubits * num_layers * 2
        self._params = self._rng.uniform(-np.pi, np.pi, size=n_params)
        logger.info(
            "QuantumEmbeddingTransformer initialized: backend=%s, qubits=%d, layers=%d",
            self.effective_backend,
            num_qubits,
            num_layers,
        )

    def transform(self, embedding: np.ndarray) -> np.ndarray:
        """
        Apply the quantum amplitude encoding + variational transformation.

        Parameters
        ----------
        embedding : np.ndarray
            1-D array of floats representing a classical embedding.

        Returns
        -------
        np.ndarray
            Transformed embedding with the same shape as the input.
        """
        if embedding.ndim != 1:
            raise ValueError(f"Expected 1-D embedding, got shape {embedding.shape}")
        embedding = embedding.astype(float)

        if self.effective_backend == "pennylane":
            return _pennylane_amplitude_transform(embedding, self._params, self.num_qubits, self.num_layers)
        if self.effective_backend == "qiskit":
            return _qiskit_amplitude_transform(embedding, self._params, self.num_qubits, self.num_layers)
        return _classical_amplitude_transform(embedding, self._params, self.num_qubits)

    def update_params(self, params: np.ndarray) -> None:
        """Override the variational parameters (e.g. after training)."""
        self._params = np.array(params, dtype=float)
