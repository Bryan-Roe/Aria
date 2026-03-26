"""Performance tests for keyword set optimizations in apps/aria/server.py

The `apps/aria` directory is added to sys.path by tests/conftest.py, so
`from server import ...` works here at module level without any manual path setup.
"""
import time

import pytest

from server import (
    DANCE_KEYWORDS,
    JUMP_KEYWORDS,
    WAVE_KEYWORDS,
    _contains_any_keyword,
    determine_position_from_context,
)


class TestKeywordSetPerformance:
    """Test that keyword set optimizations work correctly and are faster."""

    def test_contains_any_keyword_basic(self):
        """Test basic functionality of keyword checking."""
        assert _contains_any_keyword("jump high", JUMP_KEYWORDS)
        assert _contains_any_keyword("leap forward", JUMP_KEYWORDS)
        assert not _contains_any_keyword("walk slowly", JUMP_KEYWORDS)

        assert _contains_any_keyword("dance now", DANCE_KEYWORDS)
        assert _contains_any_keyword("spin around", DANCE_KEYWORDS)
        assert not _contains_any_keyword("sit down", DANCE_KEYWORDS)

    def test_determine_position_with_keywords(self):
        """Test that position determination works with new keyword sets."""
        # Jump keywords
        pos = determine_position_from_context("jump high")
        assert "position:50:60" in pos

        # Dance keywords
        pos = determine_position_from_context("dance around")
        assert "position:50:50" in pos

        # Wave keywords
        pos = determine_position_from_context("wave hello")
        assert "position:30:70" in pos

    def test_keyword_set_performance(self):
        """Benchmark: keyword sets should be faster than list any()."""
        commands = [
            "jump high and leap",
            "dance and spin",
            "wave hello",
            "run fast",
            "walk slowly",
            "sit down and rest",
        ] * 100  # 600 iterations

        # Test with optimized keyword sets
        start = time.perf_counter()
        for cmd in commands:
            result = _contains_any_keyword(cmd, JUMP_KEYWORDS)
            result = _contains_any_keyword(cmd, DANCE_KEYWORDS)
            result = _contains_any_keyword(cmd, WAVE_KEYWORDS)
        optimized_time = time.perf_counter() - start

        # Test with old-style any() approach (simulated)
        def old_style_check(text, keywords_list):
            return any(k in text for k in keywords_list)

        start = time.perf_counter()
        for cmd in commands:
            result = old_style_check(cmd, list(JUMP_KEYWORDS))
            result = old_style_check(cmd, list(DANCE_KEYWORDS))
            result = old_style_check(cmd, list(WAVE_KEYWORDS))
        old_time = time.perf_counter() - start

        # Optimized should be at least as fast (usually faster)
        # We allow some variance due to system load
        print(f"\nOptimized time: {optimized_time:.4f}s")
        print(f"Old style time: {old_time:.4f}s")
        print(f"Speedup: {old_time / optimized_time:.2f}x")

        # Should be faster or similar (within 10% tolerance)
        assert optimized_time <= old_time * 1.1, \
            f"Optimized version slower: {optimized_time:.4f}s vs {old_time:.4f}s"


class TestConnectionPooling:
    """Test connection pooling in chat_memory."""

    def test_connection_pool_import(self):
        """Verify connection pooling functions exist."""
        try:
            from shared.chat_memory import _get_conn, _return_conn, _connection_pool
            assert callable(_get_conn)
            assert callable(_return_conn)
            assert isinstance(_connection_pool, list)
        except ImportError as e:
            pytest.skip(f"chat_memory module not available: {e}")

    def test_connection_pool_basic(self):
        """Test that connection pooling works correctly."""
        pytest.importorskip("pyodbc")

        from shared.chat_memory import _get_conn, _return_conn, _connection_pool

        # Clear pool
        _connection_pool.clear()

        # Get a connection (will fail without DB, but that's ok)
        conn = _get_conn()

        if conn is None:
            # No database configured - this is expected in CI
            pytest.skip("No database connection available")

        # Return it to pool
        _return_conn(conn)

        # Pool should have 1 connection now
        assert len(_connection_pool) == 1

        # Get again - should reuse from pool
        conn2 = _get_conn()
        assert conn2 is not None

        # Pool should be empty after reuse
        assert len(_connection_pool) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
