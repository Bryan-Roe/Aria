"""
Quantum-inspired provider router with classical fallback.

QuantumRouter selects among multiple LLM providers based on prompt features
(length, language, latency budget) using a QAOA-style / Grover-inspired
routine.  When no quantum backend is installed a classical heuristic is used.

Provider abstraction is compatible with the existing chat provider interface
in ``ai-projects/chat-cli/src/chat_providers.py`` and ``shared/``.
"""

from __future__ import annotations

import logging
import math
import warnings
from typing import Dict, List, Optional, Tuple

import numpy as np

from .quantum_sampler import _active_backend

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def _extract_prompt_features(
    prompt: str,
    latency_budget_ms: float = 5000.0,
) -> np.ndarray:
    """
    Extract a small numeric feature vector from a prompt string.

    Features (normalized to [0, 1]):
      0. prompt length (chars / max_chars)
      1. word count (words / 500)
      2. question mark presence
      3. code block presence
      4. latency budget (budget_ms / 10_000)

    Returns
    -------
    np.ndarray shape (5,)
    """
    length = min(len(prompt) / 8000.0, 1.0)
    words = min(len(prompt.split()) / 500.0, 1.0)
    has_question = float("?" in prompt)
    has_code = float("```" in prompt or "    " in prompt)
    budget = min(latency_budget_ms / 10_000.0, 1.0)
    return np.array([length, words, has_question, has_code, budget], dtype=float)


# ---------------------------------------------------------------------------
# Classical scoring / routing
# ---------------------------------------------------------------------------


def _classical_score_providers(
    features: np.ndarray,
    providers: List[str],
    params: np.ndarray,
) -> np.ndarray:
    """
    Score each provider using a simple parameterized linear model.

    Returns an array of scores (higher is better).
    """
    n = len(providers)
    scores = np.zeros(n, dtype=float)
    for i in range(n):
        # Each provider gets a weight vector of size len(features)
        weights = params[i * len(features) : (i + 1) * len(features)]
        if len(weights) < len(features):
            weights = np.resize(weights, len(features))
        scores[i] = float(np.dot(weights, features))
    return scores


# ---------------------------------------------------------------------------
# QAOA-style scoring (PennyLane)
# ---------------------------------------------------------------------------


def _pennylane_qaoa_scores(
    features: np.ndarray,
    providers: List[str],
    params: np.ndarray,
    num_qubits: int,
) -> np.ndarray:
    """Score providers using a QAOA-inspired variational circuit via PennyLane."""
    import pennylane as qml  # noqa: PLC0415

    n_providers = len(providers)
    scores = np.zeros(n_providers, dtype=float)

    dev = qml.device("default.qubit", wires=num_qubits, shots=None)

    for i, _provider in enumerate(providers):
        @qml.qnode(dev)
        def circuit(features, params, i=i):  # capture i
            # Encode features as rotation angles
            for q in range(min(len(features), num_qubits)):
                qml.RY(features[q] * np.pi, wires=q)
            # QAOA-style mixing layers
            n_layers = max(1, len(params) // (2 * num_qubits))
            for layer in range(n_layers):
                for q in range(num_qubits):
                    idx = (layer * num_qubits + q) % len(params)
                    qml.RZ(params[idx], wires=q)
                for q in range(num_qubits - 1):
                    qml.CNOT(wires=[q, q + 1])
            # Provider-specific expectation
            wire = i % num_qubits
            return qml.expval(qml.PauliZ(wires=wire))

        scores[i] = float(circuit(features, params))

    return scores


# ---------------------------------------------------------------------------
# Public QuantumRouter
# ---------------------------------------------------------------------------


class QuantumRouter:
    """
    Routes prompts to the best LLM provider using quantum-circuit scoring.

    Parameters
    ----------
    providers : list of str
        Ordered list of provider names (e.g. ``["azure", "openai", "local"]``).
    backend : str
        One of "auto", "pennylane", "qiskit", "classical".
    num_qubits : int
        Number of qubits for the routing circuit (default 4).
    seed : int, optional
        Random seed for parameter initialization.
    """

    def __init__(
        self,
        providers: Optional[List[str]] = None,
        backend: str = "auto",
        num_qubits: int = 4,
        seed: Optional[int] = None,
    ) -> None:
        self.providers = list(providers or ["azure", "openai", "lmstudio", "local"])
        self.effective_backend = _active_backend(backend)
        self.num_qubits = num_qubits
        self._rng = np.random.default_rng(seed)
        # Random initial params; feature dim is 5
        n_params = len(self.providers) * 5
        self._params = self._rng.uniform(-np.pi, np.pi, size=n_params)
        logger.info(
            "QuantumRouter initialized: backend=%s, providers=%s",
            self.effective_backend,
            self.providers,
        )

    def route(
        self,
        prompt: str,
        latency_budget_ms: float = 5000.0,
        exclude: Optional[List[str]] = None,
    ) -> str:
        """
        Select the best provider for the given prompt.

        Parameters
        ----------
        prompt : str
            The user's prompt text.
        latency_budget_ms : float
            Desired maximum latency in milliseconds.
        exclude : list of str, optional
            Provider names to exclude from routing.

        Returns
        -------
        str
            Selected provider name.
        """
        candidates = [p for p in self.providers if p not in (exclude or [])]
        if not candidates:
            return self.providers[0] if self.providers else "local"
        if len(candidates) == 1:
            return candidates[0]

        features = _extract_prompt_features(prompt, latency_budget_ms)

        try:
            if self.effective_backend == "pennylane":
                scores = _pennylane_qaoa_scores(
                    features, candidates, self._params, self.num_qubits
                )
            else:
                scores = _classical_score_providers(features, candidates, self._params)
        except Exception as exc:  # noqa: BLE001
            logger.warning("QuantumRouter scoring failed (%s), using first provider", exc)
            return candidates[0]

        best_idx = int(np.argmax(scores))
        chosen = candidates[best_idx]
        logger.debug(
            "QuantumRouter chose '%s' (scores=%s) for prompt length=%d",
            chosen,
            scores.round(3).tolist(),
            len(prompt),
        )
        return chosen

    def route_with_scores(
        self,
        prompt: str,
        latency_budget_ms: float = 5000.0,
    ) -> Tuple[str, Dict[str, float]]:
        """
        Like ``route`` but also returns the per-provider score dict.

        Returns
        -------
        tuple of (chosen_provider, {provider: score, ...})
        """
        features = _extract_prompt_features(prompt, latency_budget_ms)

        try:
            if self.effective_backend == "pennylane":
                scores_arr = _pennylane_qaoa_scores(
                    features, self.providers, self._params, self.num_qubits
                )
            else:
                scores_arr = _classical_score_providers(
                    features, self.providers, self._params
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("QuantumRouter scoring failed (%s)", exc)
            scores_arr = np.zeros(len(self.providers))

        scores = {p: float(s) for p, s in zip(self.providers, scores_arr)}
        chosen = max(scores, key=lambda k: scores[k])
        return chosen, scores
