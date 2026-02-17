"""Performance tests for critical optimizations in aria_web and chat_memory.

Tests validate that keyword matching and DB connection pooling improvements
are working as expected.

Can be run standalone without pytest: python tests/test_performance_critical_fixes.py
"""
import time
import threading
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add repo to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "aria_web"))


def test_keywords_in_cmd_function():
    """Test the optimized _keywords_in_cmd helper function"""
    from aria_web.server import _keywords_in_cmd, _JUMP_KEYWORDS, _DANCE_KEYWORDS
    
    # Test basic matching
    assert _keywords_in_cmd(_JUMP_KEYWORDS, "jump high")
    assert _keywords_in_cmd(_JUMP_KEYWORDS, "leap over")
    assert _keywords_in_cmd(_JUMP_KEYWORDS, "please hop")
    assert not _keywords_in_cmd(_JUMP_KEYWORDS, "walk slowly")
    
    # Test with dance keywords
    assert _keywords_in_cmd(_DANCE_KEYWORDS, "let's dance")
    assert _keywords_in_cmd(_DANCE_KEYWORDS, "spin around")
    assert not _keywords_in_cmd(_DANCE_KEYWORDS, "run fast")
    
    print("✓ test_keywords_in_cmd_function passed")


def test_keyword_sets_are_frozen():
    """Verify keyword sets are frozensets for immutability"""
    from aria_web.server import _JUMP_KEYWORDS, _DANCE_KEYWORDS, _LIMB_KEYWORDS
    
    assert isinstance(_JUMP_KEYWORDS, frozenset)
    assert isinstance(_DANCE_KEYWORDS, frozenset)
    assert isinstance(_LIMB_KEYWORDS, frozenset)
    
    # Frozensets are immutable
    try:
        _JUMP_KEYWORDS.add("new_keyword")
        assert False, "Should have raised AttributeError"
    except AttributeError:
        pass  # Expected
    
    print("✓ test_keyword_sets_are_frozen passed")


def test_determine_position_performance():
    """Test that determine_position_from_context uses optimized patterns"""
    from aria_web.server import determine_position_from_context
    
    # Test that various commands return expected results quickly
    test_commands = [
        ("jump up high", '[aria:position:50:60]'),
        ("dance around", '[aria:position:50:50]'),
        ("wave at me", '[aria:position:30:70]'),
        ("run fast", '[aria:position:85:70]'),
    ]
    
    start = time.time()
    for cmd, expected in test_commands:
        result = determine_position_from_context(cmd)
        assert result == expected, f"Command '{cmd}' returned {result}, expected {expected}"
    elapsed = time.time() - start
    
    # All 4 commands should complete in under 10ms
    assert elapsed < 0.01, f"Position determination too slow: {elapsed*1000:.2f}ms"
    
    print(f"✓ test_determine_position_performance passed ({elapsed*1000:.2f}ms for 4 commands)")


def test_parse_command_performance():
    """Test that generate_tags_fallback performs well with optimized patterns"""
    from aria_web.server import generate_tags_fallback
    
    # Test various command types
    commands = [
        "jump and wave",
        "dance happily",
        "raise left arm",
        "walk to the table and pick up the apple",
        "say hello everyone",
    ]
    
    start = time.time()
    for cmd in commands * 10:  # Run 50 times
        tags = generate_tags_fallback(cmd)
        assert isinstance(tags, list)
    elapsed = time.time() - start
    
    # 50 command parses should complete in under 50ms
    assert elapsed < 0.05, f"Command parsing too slow: {elapsed*1000:.2f}ms for 50 parses"
    
    print(f"✓ test_parse_command_performance passed ({elapsed*1000:.2f}ms for 50 parses)")


@patch('shared.chat_memory.pyodbc')
@patch('shared.chat_memory.os.getenv')
def test_connection_caching(mock_getenv, mock_pyodbc):
    """Test that connections are cached per thread"""
    from shared.chat_memory import _get_conn, _conn_cache, _conn_lock
    
    # Setup mocks
    mock_getenv.return_value = "mock_conn_string"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_pyodbc.connect.return_value = mock_conn
    
    # Clear cache before test
    with _conn_lock:
        _conn_cache.clear()
    
    # First call should create connection
    conn1 = _get_conn()
    assert conn1 is mock_conn
    assert mock_pyodbc.connect.call_count == 1
    
    # Second call should use cached connection (no new connect call)
    conn2 = _get_conn()
    assert conn2 is mock_conn
    assert mock_pyodbc.connect.call_count == 1  # Still 1, no new connection
    
    # Verify cursor.execute was called for connection health check
    assert mock_cursor.execute.called
    
    print("✓ test_connection_caching passed")


@patch('shared.chat_memory.pyodbc')
@patch('shared.chat_memory.os.getenv')
def test_store_embedding_uses_cached_connection(mock_getenv, mock_pyodbc):
    """Test that store_embedding uses cached connection and doesn't close it"""
    from shared.chat_memory import store_embedding, _conn_cache, _conn_lock
    
    # Setup mocks
    mock_getenv.return_value = "mock_conn_string"
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_pyodbc.connect.return_value = mock_conn
    
    # Clear cache
    with _conn_lock:
        _conn_cache.clear()
    
    # Store two embeddings
    embedding = [0.1, 0.2, 0.3]
    result1 = store_embedding("msg1", embedding, "test-model")
    result2 = store_embedding("msg2", embedding, "test-model")
    
    assert result1 is True
    assert result2 is True
    
    # Should only create ONE connection (cached for second call)
    assert mock_pyodbc.connect.call_count == 1
    
    # Connection should NOT be closed (it's cached)
    assert not mock_conn.close.called
    
    print("✓ test_store_embedding_uses_cached_connection passed")


@patch('shared.chat_memory.pyodbc')
@patch('shared.chat_memory.os.getenv')
def test_connection_pooling_speedup(mock_getenv, mock_pyodbc):
    """Measure speedup from connection pooling"""
    from shared.chat_memory import store_embedding, _conn_cache, _conn_lock
    
    # Setup mocks with realistic delays
    mock_getenv.return_value = "mock_conn_string"
    
    def slow_connect(*args, **kwargs):
        # Simulate 50ms connection time
        time.sleep(0.05)
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        return conn
    
    mock_pyodbc.connect.side_effect = slow_connect
    
    # Clear cache
    with _conn_lock:
        _conn_cache.clear()
    
    # Time 10 embedding stores
    embedding = [0.1] * 256
    start = time.time()
    for i in range(10):
        store_embedding(f"msg{i}", embedding, "test")
    elapsed = time.time() - start
    
    # With caching, should only pay 50ms once, not 10 times (500ms)
    # Total should be ~50-100ms instead of 500ms
    assert elapsed < 0.15, f"Connection pooling not effective: {elapsed*1000:.2f}ms"
    assert mock_pyodbc.connect.call_count == 1, "Should only create 1 connection"
    
    print(f"✓ test_connection_pooling_speedup passed (10 operations in {elapsed*1000:.2f}ms)")


def test_keyword_matching_benchmark():
    """Benchmark keyword matching performance"""
    from aria_web.server import _keywords_in_cmd, _JUMP_KEYWORDS
    
    # Manual timing
    start = time.time()
    for _ in range(10000):
        _keywords_in_cmd(_JUMP_KEYWORDS, "jump high")
    elapsed = time.time() - start
    
    # Should complete 10k iterations in under 10ms
    assert elapsed < 0.01, f"Too slow: {elapsed*1000:.2f}ms for 10k iterations"
    
    print(f"✓ test_keyword_matching_benchmark passed (10k iterations in {elapsed*1000:.2f}ms)")


def run_all_tests():
    """Run all tests and report results"""
    print("=" * 70)
    print("Performance Critical Fixes - Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Keyword matching function", test_keywords_in_cmd_function),
        ("Keyword sets immutability", test_keyword_sets_are_frozen),
        ("Position determination performance", test_determine_position_performance),
        ("Command parsing performance", test_parse_command_performance),
        ("Connection caching", test_connection_caching),
        ("Store embedding caching", test_store_embedding_uses_cached_connection),
        ("Connection pooling speedup", test_connection_pooling_speedup),
        ("Keyword matching benchmark", test_keyword_matching_benchmark),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())

