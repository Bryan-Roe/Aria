"""
Circuit cache for quantum LLM — reduces recomputation of identical circuits.

Uses LRU eviction + TTL expiration to avoid memory growth while maintaining
hit rates for frequently-used parameter combinations.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class CircuitCache:
    """
    Least-Recently-Used cache with time-to-live (TTL) expiration.

    Stores probability distributions keyed by hashed parameters.
    Evicts oldest entries when capacity is exceeded; expires entries
    older than max_age_seconds.
    """

    def __init__(
        self,
        max_size: int = 256,
        max_age_seconds: float = 3600.0,
    ) -> None:
        """
        Initialize the cache.

        Parameters
        ----------
        max_size : int
            Maximum entries before LRU eviction.
        max_age_seconds : float
            Maximum age for entries before TTL expiration.
        """
        self.max_size = max(1, int(max_size))
        self.max_age_seconds = max(0, float(max_age_seconds))
        self._cache: OrderedDict[str, tuple[np.ndarray, float]] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _hash_params(self, params: np.ndarray, num_qubits: int) -> str:
        """Generate a cache key for parameters."""
        try:
            # Accept array-like inputs (lists, tuples) and coerce to numeric numpy array.
            # Non-numeric or malformed inputs will raise and be treated as invalid.
            arr = np.asarray(params, dtype=np.float64)
        except Exception as e:
            raise TypeError("params must be array-like of numeric values") from e

        param_bytes = arr.tobytes()
        qubits_str = str(num_qubits).encode()
        key_bytes = param_bytes + qubits_str
        return hashlib.sha256(key_bytes).hexdigest()[:16]

    def get(
        self,
        params: np.ndarray,
        num_qubits: int,
    ) -> np.ndarray | None:
        """
        Retrieve cached probability distribution.

        Returns None if not found, expired, or params are invalid.
        """
        try:
            key = self._hash_params(params, num_qubits)
        except (TypeError, ValueError):
            return None

        if key not in self._cache:
            self._stats["misses"] += 1
            return None

        probs, timestamp = self._cache[key]

        # Check TTL (non-positive TTL means no expiration)
        age_seconds = time.monotonic() - timestamp
        if self.max_age_seconds > 0 and age_seconds > self.max_age_seconds:
            del self._cache[key]
            self._stats["expirations"] += 1
            self._stats["misses"] += 1
            return None

        # Mark as recently used
        self._cache.move_to_end(key)
        self._stats["hits"] += 1
        return probs.copy()

    def put(
        self,
        params: np.ndarray,
        num_qubits: int,
        probs: np.ndarray,
    ) -> None:
        """
        Cache a probability distribution.

        Evicts oldest entry if capacity exceeded.
        """
        try:
            key = self._hash_params(params, num_qubits)
            # Normalize and copy
            probs_copy = np.asarray(probs, dtype=np.float64).copy()
            if probs_copy.size == 0:
                return
        except (TypeError, ValueError):
            return

        # If key exists, remove it (will be re-added at end)
        if key in self._cache:
            del self._cache[key]

        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

        # Add entry
        self._cache[key] = (probs_copy, time.monotonic())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def stats(self) -> dict[str, Any]:
        """Return cache performance statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "evictions": self._stats["evictions"],
            "expirations": self._stats["expirations"],
        }
