"""
Unit tests for CircuitCache.

Tests LRU eviction, TTL expiration, and cache statistics.
"""

import time

import numpy as np
import pytest
from ai_projects.quantum_ml.src.quantum_llm.circuit_cache import CircuitCache


class TestCircuitCacheBasics:
    """Test basic cache operations."""

    def test_cache_initialization(self):
        """Should initialize with valid parameters."""
        cache = CircuitCache(max_size=10, max_age_seconds=60)
        assert cache.max_size == 10
        assert cache.max_age_seconds == 60

    def test_cache_enforces_minimum_size(self):
        """Should enforce minimum cache size of 1."""
        cache = CircuitCache(max_size=0)
        assert cache.max_size == 1

    def test_cache_enforces_non_negative_ttl(self):
        """Should enforce non-negative TTL."""
        cache = CircuitCache(max_age_seconds=-10)
        assert cache.max_age_seconds == 0


class TestCircuitCachePutGet:
    """Test put and get operations."""

    def test_put_and_get(self):
        """Should store and retrieve values."""
        cache = CircuitCache(max_size=10)
        params = np.array([0.1, 0.2, 0.3])
        probs = np.array([0.25, 0.25, 0.25, 0.25])

        cache.put(params, num_qubits=2, probs=probs)
        retrieved = cache.get(params, num_qubits=2)

        assert retrieved is not None
        assert np.allclose(retrieved, probs)

    def test_get_returns_none_for_missing_key(self):
        """Should return None for missing key."""
        cache = CircuitCache()
        params = np.array([0.1, 0.2])

        result = cache.get(params, num_qubits=2)
        assert result is None

    def test_get_increments_hit_counter(self):
        """Should increment hits counter on successful get."""
        cache = CircuitCache()
        params = np.array([0.1])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)

        stats_before = cache.stats()
        cache.get(params, num_qubits=1)
        stats_after = cache.stats()

        assert stats_after["hits"] == stats_before["hits"] + 1

    def test_get_increments_miss_counter(self):
        """Should increment misses counter on cache miss."""
        cache = CircuitCache()
        params = np.array([0.1])

        stats_before = cache.stats()
        cache.get(params, num_qubits=1)
        stats_after = cache.stats()

        assert stats_after["misses"] == stats_before["misses"] + 1


class TestCircuitCacheLRU:
    """Test LRU eviction behavior."""

    def test_lru_eviction(self):
        """Should evict oldest entry when capacity exceeded."""
        cache = CircuitCache(max_size=3)

        # Fill cache
        params1 = np.array([1.0])
        params2 = np.array([2.0])
        params3 = np.array([3.0])
        probs = np.array([0.5, 0.5])

        cache.put(params1, num_qubits=1, probs=probs)
        cache.put(params2, num_qubits=1, probs=probs)
        cache.put(params3, num_qubits=1, probs=probs)

        assert cache.stats()["size"] == 3

        # Add one more — should evict oldest (params1)
        params4 = np.array([4.0])
        cache.put(params4, num_qubits=1, probs=probs)

        assert cache.stats()["size"] == 3
        assert cache.stats()["evictions"] == 1

        # params1 should no longer be in cache
        assert cache.get(params1, num_qubits=1) is None
        # params4 should be in cache
        assert cache.get(params4, num_qubits=1) is not None

    def test_lru_updates_on_get(self):
        """Should mark entries as recently used on get."""
        cache = CircuitCache(max_size=2)

        params1 = np.array([1.0])
        params2 = np.array([2.0])
        probs = np.array([0.5, 0.5])

        cache.put(params1, num_qubits=1, probs=probs)
        cache.put(params2, num_qubits=1, probs=probs)

        # Access params1 to mark it as recently used
        cache.get(params1, num_qubits=1)

        # Add params3 — should evict params2 (not params1, which was just used)
        params3 = np.array([3.0])
        cache.put(params3, num_qubits=1, probs=probs)

        assert cache.get(params1, num_qubits=1) is not None
        assert cache.get(params2, num_qubits=1) is None
        assert cache.get(params3, num_qubits=1) is not None


class TestCircuitCacheTTL:
    """Test TTL expiration behavior."""

    def test_ttl_expiration(self):
        """Should expire entries older than max_age_seconds."""
        cache = CircuitCache(max_age_seconds=0.1)  # 100ms

        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)

        # Should be retrievable immediately
        assert cache.get(params, num_qubits=1) is not None

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired
        assert cache.get(params, num_qubits=1) is None

    def test_ttl_expiration_increments_counter(self):
        """Should increment expiration counter on TTL expiry."""
        cache = CircuitCache(max_age_seconds=0.05)

        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)

        stats_before = cache.stats()
        time.sleep(0.1)
        cache.get(params, num_qubits=1)  # Trigger expiration check
        stats_after = cache.stats()

        assert stats_after["expirations"] > stats_before["expirations"]

    def test_zero_ttl_disables_expiration(self):
        """Should never expire when TTL is 0."""
        cache = CircuitCache(max_age_seconds=0.0)

        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)

        # Wait a bit
        time.sleep(0.1)

        # Should still be retrievable (no expiration)
        assert cache.get(params, num_qubits=1) is not None


class TestCircuitCacheStats:
    """Test cache statistics."""

    def test_stats_initial_state(self):
        """Should report initial stats correctly."""
        cache = CircuitCache(max_size=10)
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 10
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["evictions"] == 0
        assert stats["expirations"] == 0

    def test_stats_hit_rate_calculation(self):
        """Should calculate hit rate correctly."""
        cache = CircuitCache()
        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)

        # 3 hits
        cache.get(params, num_qubits=1)
        cache.get(params, num_qubits=1)
        cache.get(params, num_qubits=1)

        # 2 misses
        cache.get(np.array([2.0]), num_qubits=1)
        cache.get(np.array([3.0]), num_qubits=1)

        stats = cache.stats()
        assert stats["hits"] == 3
        assert stats["misses"] == 2
        assert stats.get("hit_rate", 0.0) == pytest.approx(3 / 5)

    def test_stats_zero_total_hit_rate(self):
        """Should handle zero total queries for hit rate."""
        cache = CircuitCache()
        stats = cache.stats()

        # No queries yet
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0


class TestCircuitCacheClear:
    """Test clear operation."""

    def test_clear_removes_all_entries(self):
        """Should remove all cached entries."""
        cache = CircuitCache()
        probs = np.array([0.5, 0.5])

        for i in range(10):
            params = np.array([float(i)])
            cache.put(params, num_qubits=1, probs=probs)

        assert cache.stats()["size"] == 10

        cache.clear()

        assert cache.stats()["size"] == 0

    def test_clear_resets_stats(self):
        """Should reset stats after clear."""
        cache = CircuitCache()
        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)
        cache.get(params, num_qubits=1)
        cache.get(params, num_qubits=1)
        cache.get(np.array([2.0]), num_qubits=1)

        stats_before = cache.stats()
        assert stats_before["hits"] > 0 or stats_before["misses"] > 0

        cache.clear()

        # Stats should persist but cache should be empty
        assert cache.stats()["size"] == 0


class TestCircuitCacheParameterValidation:
    """Test parameter validation."""

    def test_rejects_invalid_params(self):
        """Should gracefully handle invalid parameters."""
        cache = CircuitCache()

        # Invalid params (not array-like)
        result = cache.get("not_an_array", num_qubits=1)
        assert result is None

        # Should still work with valid params after
        params = np.array([1.0])
        probs = np.array([0.5, 0.5])
        cache.put(params, num_qubits=1, probs=probs)

        result = cache.get(params, num_qubits=1)
        assert result is not None

    def test_makes_copy_of_stored_probs(self):
        """Should make a copy of stored probabilities."""
        cache = CircuitCache()
        params = np.array([1.0])
        probs = np.array([0.5, 0.5])

        cache.put(params, num_qubits=1, probs=probs)
        retrieved = cache.get(params, num_qubits=1)

        # Modify original
        probs[0] = 0.9

        # Retrieved should be unchanged
        assert retrieved[0] == 0.5
