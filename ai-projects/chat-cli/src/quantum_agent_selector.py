from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any


class QuantumSolverBackend(str, Enum):
    SIMULATOR = "simulator"
    CLASSICAL = "classical"
    HYBRID = "hybrid"


@dataclass(slots=True)
class QuantumAgentSelectorConfig:
    enabled: bool = False
    backend: QuantumSolverBackend = QuantumSolverBackend.SIMULATOR
    timeout_ms: int = 200
    num_reads: int = 64
    penalty_scale: float = 10.0
    max_cost: float = 0.1
    debug: bool = False

    @classmethod
    def from_env(cls) -> QuantumAgentSelectorConfig:
        raw = (os.getenv("QUANTUM_AGENT_SOLVER_BACKEND", "simulator") or "simulator").strip().lower()
        try:
            backend = QuantumSolverBackend(raw)
        except ValueError:
            backend = QuantumSolverBackend.SIMULATOR
        return cls(
            enabled=(os.getenv("ENABLE_QUANTUM_AGENT_SELECTION", "false").strip().lower() in {"1", "true", "yes"}),
            backend=backend,
            timeout_ms=max(1, int(os.getenv("QUANTUM_SOLVER_TIMEOUT_MS", "200"))),
            num_reads=max(1, int(os.getenv("QUANTUM_AGENT_NUM_READS", "64"))),
            penalty_scale=float(os.getenv("QUANTUM_AGENT_PENALTY_SCALE", "10.0")),
            max_cost=float(os.getenv("MAX_QUANTUM_AGENT_COST", "0.1")),
            debug=(os.getenv("QUANTUM_AGENT_DEBUG", "false").strip().lower() in {"1", "true", "yes"}),
        )


class QuantumAgentSelector:
    def __init__(self, config: QuantumAgentSelectorConfig | None = None) -> None:
        self.config = config or QuantumAgentSelectorConfig.from_env()
        self._metrics: dict[str, Any] = {
            "total_calls": 0,
            "quantum_calls": 0,
            "classical_fallback_calls": 0,
            "timeouts": 0,
            "errors": 0,
            "last_backend": self.config.backend.value,
            "last_latency_ms": 0.0,
            "last_reason": "init",
        }

    def enabled(self) -> bool:
        return self.config.enabled

    def get_metrics(self) -> dict[str, Any]:
        return dict(self._metrics)

    def _encode_qubo(self, ordered_agents: list[str], candidate_scores: dict[str, float], learned_agent: str | None):
        p = self.config.penalty_scale
        q: dict[tuple[int, int], float] = {}
        for i, name in enumerate(ordered_agents):
            score = float(candidate_scores.get(name, 0.0))
            if learned_agent and name == learned_agent:
                score += 0.02
            q[(i, i)] = q.get((i, i), 0.0) + (-score) + (-p)
        n = len(ordered_agents)
        for i in range(n):
            for j in range(i + 1, n):
                q[(i, j)] = q.get((i, j), 0.0) + (2.0 * p)
        return q

    @staticmethod
    def _energy(bits: list[int], q: dict[tuple[int, int], float]) -> float:
        return sum(w * bits[i] * bits[j] for (i, j), w in q.items())

    def _anneal(self, q: dict[tuple[int, int], float], n: int) -> list[int]:
        bits = [0] * n
        bits[random.randrange(0, n)] = 1
        best = bits[:]
        best_e = self._energy(best, q)
        t = 1.0
        for _ in range(max(64, self.config.num_reads * 8)):
            c = bits[:]
            k = random.randrange(0, n)
            c[k] ^= 1
            e0 = self._energy(bits, q)
            e1 = self._energy(c, q)
            if e1 <= e0 or random.random() < pow(2.718281828, -(e1 - e0) / max(t, 1e-6)):
                bits = c
            en = self._energy(bits, q)
            if en < best_e:
                best, best_e = bits[:], en
            t *= 0.995
        return best

    def select(
        self, *, candidate_scores: dict[str, float], learned_agent: str | None = None, timeout_ms: int | None = None
    ):
        self._metrics["total_calls"] += 1
        ordered = sorted([a for a, s in candidate_scores.items() if float(s) > 0.0])
        if not ordered:
            self._metrics["classical_fallback_calls"] += 1
            self._metrics["last_reason"] = "no_candidates"
            return "general", {"mode": "fallback", "reason": "no_candidates"}
        if not self.config.enabled:
            self._metrics["classical_fallback_calls"] += 1
            self._metrics["last_reason"] = "disabled"
            best = max(ordered, key=lambda a: float(candidate_scores.get(a, 0.0)))
            return best, {"mode": "fallback", "reason": "disabled"}

        start = time.time()
        try:
            if self.config.backend == QuantumSolverBackend.CLASSICAL:
                best = max(ordered, key=lambda a: float(candidate_scores.get(a, 0.0)))
                ms = (time.time() - start) * 1000.0
                self._metrics["quantum_calls"] += 1
                self._metrics["last_backend"] = "classical"
                self._metrics["last_latency_ms"] = ms
                self._metrics["last_reason"] = "classical_backend"
                return best, {"mode": "classical_backend", "latency_ms": ms}

            q = self._encode_qubo(ordered, candidate_scores, learned_agent)
            bits = self._anneal(q, len(ordered))
            on = [i for i, b in enumerate(bits) if b == 1]
            chosen = ordered[on[0]] if len(on) == 1 else max(ordered, key=lambda a: float(candidate_scores.get(a, 0.0)))

            ms = (time.time() - start) * 1000.0
            budget = float(timeout_ms if timeout_ms is not None else self.config.timeout_ms)
            if ms > budget:
                self._metrics["timeouts"] += 1
                self._metrics["classical_fallback_calls"] += 1
                self._metrics["last_reason"] = "timeout"
                best = max(ordered, key=lambda a: float(candidate_scores.get(a, 0.0)))
                return best, {"mode": "fallback", "reason": "timeout", "latency_ms": ms}

            self._metrics["quantum_calls"] += 1
            self._metrics["last_backend"] = self.config.backend.value
            self._metrics["last_latency_ms"] = ms
            self._metrics["last_reason"] = "ok"
            return chosen, {"mode": "quantum", "backend": self.config.backend.value, "latency_ms": ms}
        except Exception as exc:
            self._metrics["errors"] += 1
            self._metrics["classical_fallback_calls"] += 1
            self._metrics["last_reason"] = "exception"
            best = max(ordered, key=lambda a: float(candidate_scores.get(a, 0.0)))
            return best, {"mode": "fallback", "reason": "exception", "error": str(exc)}
