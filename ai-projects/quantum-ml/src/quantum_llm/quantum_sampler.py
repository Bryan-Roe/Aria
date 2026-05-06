"""
Quantum-circuit-based token sampling with classical fallback.

QuantumSampler uses a parameterized variational circuit (RY/RZ + CNOT
entanglement layers) whose measurement probabilities re-weight an LLM's
top-k logit distribution.  When no quantum backend is available it falls
back to a numpy-only simulation.
"""

from __future__ import annotations

import logging
import warnings
from typing import Optional, Sequence

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------
_PENNYLANE_AVAILABLE = False
_QISKIT_AVAILABLE = False

try:
    import pennylane as qml  # type: ignore

    _PENNYLANE_AVAILABLE = True
except ImportError:
    pass

try:
    from qiskit import QuantumCircuit  # type: ignore
    from qiskit.circuit import ParameterVector  # type: ignore

    _QISKIT_AVAILABLE = True
except ImportError:
    pass


def _active_backend(requested: str) -> str:
    """Resolve the effective backend string."""
    if requested == "auto":
        if _PENNYLANE_AVAILABLE:
            return "pennylane"
        if _QISKIT_AVAILABLE:
            return "qiskit"
        return "classical"
    if requested == "pennylane" and not _PENNYLANE_AVAILABLE:
        warnings.warn("PennyLane not available, falling back to classical", stacklevel=3)
        return "classical"
    if requested == "qiskit" and not _QISKIT_AVAILABLE:
        warnings.warn("Qiskit not available, falling back to classical", stacklevel=3)
        return "classical"
    return requested


# ---------------------------------------------------------------------------
# Classical (numpy) fallback sampler
# ---------------------------------------------------------------------------


def _classical_variational_probs(
    params: np.ndarray,
    num_qubits: int,
    shots: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Simulate a variational circuit classically using numpy.

    Returns a probability distribution over 2**num_qubits outcomes.
    The state is built via matrix multiplication of Ry/Rz + CNOT tensors,
    keeping the simulation exact (not shot-based) for reproducibility.
    """
    dim = 2**num_qubits
    state = np.zeros(dim, dtype=complex)
    state[0] = 1.0  # |0...0>

    # Build a simple rotation-based unitary: each param rotates qubit i
    n_params = len(params)
    for i, theta in enumerate(params[:num_qubits]):
        q = i % num_qubits
        # Apply single-qubit Ry rotation to qubit q using tensor product
        ry = np.array(
            [[np.cos(theta / 2), -np.sin(theta / 2)],
             [np.sin(theta / 2),  np.cos(theta / 2)]],
            dtype=complex,
        )
        # Embed into full Hilbert space
        op = np.eye(1, dtype=complex)
        for j in range(num_qubits):
            op = np.kron(op, ry if j == q else np.eye(2, dtype=complex))
        state = op @ state

    # Apply CNOT entanglement (correct 2-qubit gate embedding)
    for q in range(num_qubits - 1):
        # CNOT between qubits q and q+1 — build full operator via tensor products
        # Format: I ⊗ ... ⊗ I ⊗ CNOT(q,q+1) ⊗ I ⊗ ... ⊗ I
        cnot2 = np.eye(4, dtype=complex)
        cnot2[[2, 3]] = cnot2[[3, 2]]

        # Build operator: I for qubits < q, CNOT2 for q and q+1, I for qubits > q+1
        before_dims = q          # number of qubits before the CNOT pair
        after_dims = num_qubits - q - 2  # number of qubits after the CNOT pair

        op = np.eye(1, dtype=complex)
        for _ in range(before_dims):
            op = np.kron(op, np.eye(2, dtype=complex))
        op = np.kron(op, cnot2)
        for _ in range(after_dims):
            op = np.kron(op, np.eye(2, dtype=complex))

        if op.shape == (dim, dim):
            state = op @ state

    probs = np.abs(state) ** 2
    probs = probs / probs.sum()  # renormalize
    return probs


# ---------------------------------------------------------------------------
# PennyLane sampler
# ---------------------------------------------------------------------------


def _pennylane_variational_probs(
    params: np.ndarray,
    num_qubits: int,
    shots: int,
    num_layers: int,
) -> np.ndarray:
    """Run a PennyLane variational circuit and return measurement probabilities."""
    import pennylane as qml  # noqa: PLC0415

    dev = qml.device("default.qubit", wires=num_qubits, shots=None)

    @qml.qnode(dev)
    def circuit(params):
        # Encode params as RY rotations
        n = num_qubits
        for layer in range(num_layers):
            for q in range(n):
                idx = layer * n + q
                theta = params[idx % len(params)]
                qml.RY(theta, wires=q)
                qml.RZ(params[(idx + 1) % len(params)], wires=q)
            # Entanglement
            for q in range(n - 1):
                qml.CNOT(wires=[q, q + 1])
        return qml.probs(wires=list(range(n)))

    probs = np.array(circuit(params), dtype=float)
    probs = probs / probs.sum()
    return probs


# ---------------------------------------------------------------------------
# Qiskit sampler
# ---------------------------------------------------------------------------


def _qiskit_variational_probs(
    params: np.ndarray,
    num_qubits: int,
    shots: int,
    num_layers: int,
) -> np.ndarray:
    """Run a Qiskit variational circuit and return shot-based probabilities."""
    from qiskit import QuantumCircuit, transpile  # noqa: PLC0415
    from qiskit.circuit import ParameterVector  # noqa: PLC0415
    from qiskit_aer import AerSimulator  # type: ignore  # noqa: PLC0415

    n = num_qubits
    n_params_per_layer = 2 * n
    total_params = num_layers * n_params_per_layer
    pv = ParameterVector("θ", total_params)

    qc = QuantumCircuit(n, n)
    idx = 0
    for _layer in range(num_layers):
        for q in range(n):
            qc.ry(pv[idx % total_params], q)
            idx += 1
            qc.rz(pv[idx % total_params], q)
            idx += 1
        for q in range(n - 1):
            qc.cx(q, q + 1)
    qc.measure(range(n), range(n))

    # Bind parameters
    param_dict = {pv[i]: float(params[i % len(params)]) for i in range(total_params)}
    bound = qc.assign_parameters(param_dict)

    sim = AerSimulator()
    job = sim.run(transpile(bound, sim), shots=shots)
    counts = job.result().get_counts()

    dim = 2**n
    probs = np.zeros(dim, dtype=float)
    for bitstring, count in counts.items():
        idx = int(bitstring, 2)
        if idx < dim:
            probs[idx] = count
    total = probs.sum()
    if total > 0:
        probs /= total
    else:
        probs = np.ones(dim) / dim
    return probs


# ---------------------------------------------------------------------------
# Public QuantumSampler class
# ---------------------------------------------------------------------------


class QuantumSampler:
    """
    Applies quantum-circuit measurement probabilities to re-weight an LLM's
    top-k logit distribution.

    Parameters
    ----------
    backend : str
        One of "auto", "pennylane", "qiskit", "classical".
    num_qubits : int
        Number of qubits in the variational circuit (default 4).
    shots : int
        Number of measurement shots for shot-based backends (default 512).
    num_layers : int
        Number of variational layers (default 2).
    seed : int, optional
        Random seed for reproducibility.
    """

    def __init__(
        self,
        backend: str = "auto",
        num_qubits: int = 4,
        shots: int = 512,
        num_layers: int = 2,
        seed: Optional[int] = None,
    ) -> None:
        self.effective_backend = _active_backend(backend)
        self.num_qubits = num_qubits
        self.shots = shots
        self.num_layers = num_layers
        self._rng = np.random.default_rng(seed)
        logger.info(
            "QuantumSampler initialized: backend=%s, qubits=%d, shots=%d",
            self.effective_backend,
            num_qubits,
            shots,
        )

    # ------------------------------------------------------------------
    # Core sampling
    # ------------------------------------------------------------------

    def _get_circuit_probs(self, params: np.ndarray) -> np.ndarray:
        """Run the variational circuit and return probabilities over 2**n outcomes."""
        if self.effective_backend == "pennylane":
            return _pennylane_variational_probs(
                params, self.num_qubits, self.shots, self.num_layers
            )
        if self.effective_backend == "qiskit":
            return _qiskit_variational_probs(
                params, self.num_qubits, self.shots, self.num_layers
            )
        # Classical fallback
        return _classical_variational_probs(
            params, self.num_qubits, self.shots, self._rng
        )

    def sample(
        self,
        logits: Sequence[float],
        blend_factor: float = 0.3,
        seed: Optional[int] = None,
    ) -> int:
        """
        Sample a token index from the re-weighted logit distribution.

        Parameters
        ----------
        logits : Sequence[float]
            LLM logit scores for top-k candidates.
        blend_factor : float
            Weight for quantum distribution (0 = pure classical, 1 = pure quantum).
        seed : int, optional
            Override the sampler's internal RNG seed for this call.

        Returns
        -------
        int
            Sampled index into ``logits``.
        """
        logits_arr = np.array(logits, dtype=float)
        k = len(logits_arr)

        if k == 0:
            return 0

        # Classical softmax distribution
        logits_arr -= logits_arr.max()  # numerical stability
        classical_probs = np.exp(logits_arr)
        classical_probs /= classical_probs.sum()

        # Generate random circuit params from logit values (deterministic mapping)
        n_params = self.num_qubits * self.num_layers * 2
        params = np.pi * (logits_arr[:n_params] if k >= n_params else np.resize(logits_arr, n_params))
        circuit_probs = self._get_circuit_probs(params)

        # Map circuit probs (over 2**num_qubits outcomes) onto k candidates
        dim = len(circuit_probs)
        if dim >= k:
            quantum_probs = circuit_probs[:k]
        else:
            # Repeat/tile to fill k candidates
            quantum_probs = np.resize(circuit_probs, k)
        quantum_probs = quantum_probs / quantum_probs.sum()

        # Blend
        blended = (1.0 - blend_factor) * classical_probs + blend_factor * quantum_probs
        blended /= blended.sum()

        rng = np.random.default_rng(seed) if seed is not None else self._rng
        return int(rng.choice(k, p=blended))
