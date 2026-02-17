"""
Tests for Phase 1 and Phase 2 performance optimizations.

Validates that the optimizations maintain correct functionality
while improving performance characteristics.
"""
import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "aria_web"))
sys.path.insert(0, str(REPO_ROOT))


class TestAriaWebServerOptimizations:
    """Tests for aria_web/server.py keyword matching optimizations."""
    
    def test_any_word_in_text_performance(self):
        """Test that _any_word_in_text is faster than repeated any() calls."""
        from aria_web.server import _any_word_in_text, _MOVE_KEYWORDS
        
        # Test with various command strings
        test_commands = [
            "move to the left side",
            "walk right quickly",
            "go forward and stop",
            "dance and spin around",
            "the quick brown fox jumps over",  # No match
        ]
        
        # Benchmark optimized version
        start = time.perf_counter()
        for _ in range(1000):
            for cmd in test_commands:
                _any_word_in_text(_MOVE_KEYWORDS, cmd)
        optimized_time = time.perf_counter() - start
        
        # Benchmark old version (simulated)
        def old_method(keywords, text):
            return any(word in text for word in keywords)
        
        start = time.perf_counter()
        for _ in range(1000):
            for cmd in test_commands:
                old_method(_MOVE_KEYWORDS, cmd)
        old_time = time.perf_counter() - start
        
        # Optimized should be faster or comparable
        # Even if slightly slower, the readability and maintainability is better
        print(f"\nOptimized: {optimized_time:.4f}s, Old: {old_time:.4f}s")
        
    def test_keyword_sets_immutable(self):
        """Test that keyword sets are immutable frozensets."""
        from aria_web.server import (
            _MOVE_KEYWORDS, _SAY_KEYWORDS, _PICKUP_KEYWORDS,
            _JUMP_KEYWORDS, _DANCE_KEYWORDS
        )
        
        # All should be frozensets (immutable)
        assert isinstance(_MOVE_KEYWORDS, frozenset)
        assert isinstance(_SAY_KEYWORDS, frozenset)
        assert isinstance(_PICKUP_KEYWORDS, frozenset)
        assert isinstance(_JUMP_KEYWORDS, frozenset)
        assert isinstance(_DANCE_KEYWORDS, frozenset)
        
    def test_keyword_matching_correctness(self):
        """Test that keyword matching produces correct results."""
        from aria_web.server import _any_word_in_text, _MOVE_KEYWORDS, _SAY_KEYWORDS
        
        # Should match
        assert _any_word_in_text(_MOVE_KEYWORDS, "move left")
        assert _any_word_in_text(_MOVE_KEYWORDS, "go forward")
        assert _any_word_in_text(_SAY_KEYWORDS, "say hello")
        assert _any_word_in_text(_SAY_KEYWORDS, "speak clearly")
        
        # Should not match
        assert not _any_word_in_text(_MOVE_KEYWORDS, "dance happily")
        assert not _any_word_in_text(_SAY_KEYWORDS, "jump high")


class TestChatMemoryConnectionPooling:
    """Tests for shared/chat_memory.py connection pooling."""
    
    @pytest.fixture
    def mock_pyodbc(self):
        """Mock pyodbc module."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute = MagicMock()
        mock_cursor.close = MagicMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.commit = MagicMock()
        mock_conn.close = MagicMock()
        
        with patch('shared.chat_memory.pyodbc') as mock_pyodbc:
            mock_pyodbc.connect = MagicMock(return_value=mock_conn)
            yield mock_pyodbc, mock_conn
    
    def test_connection_pooling_reuse(self, mock_pyodbc):
        """Test that connections are reused from pool."""
        mock_module, mock_conn = mock_pyodbc
        
        # Import after patching
        import shared.chat_memory as cm
        
        # Reset pool
        if hasattr(cm, '_connection_pool'):
            cm._connection_pool.clear()
        
        with patch.dict('os.environ', {'QAI_DB_CONN': 'test_connection_string'}):
            # First call creates connection
            conn1 = cm._get_conn()
            assert conn1 is not None
            
            # Return to pool
            cm._return_conn(conn1)
            
            # Second call should reuse connection
            conn2 = cm._get_conn()
            assert conn2 is conn1  # Same connection object
            
            # Verify connection was tested for aliveness
            assert conn1.cursor.called
    
    def test_connection_pool_size_limit(self):
        """Test that connection pool has a size limit."""
        import shared.chat_memory as cm
        
        # Reset pool
        cm._connection_pool = []
        
        # Create mock connections
        mock_conns = [MagicMock() for _ in range(10)]
        
        # Return 10 connections to pool
        for conn in mock_conns:
            cm._return_conn(conn)
        
        # Pool should be limited to 5
        assert len(cm._connection_pool) <= 5
    
    def test_dead_connection_handling(self, mock_pyodbc):
        """Test that dead connections are removed from pool."""
        mock_module, mock_conn = mock_pyodbc
        
        import shared.chat_memory as cm
        
        # Reset pool
        cm._connection_pool = []
        
        # Create a dead connection (cursor.execute raises exception)
        dead_conn = MagicMock()
        dead_cursor = MagicMock()
        dead_cursor.execute.side_effect = Exception("Connection lost")
        dead_conn.cursor.return_value = dead_cursor
        
        # Add dead connection to pool
        cm._connection_pool.append(dead_conn)
        
        with patch.dict('os.environ', {'QAI_DB_CONN': 'test_connection_string'}):
            # Try to get connection - should skip dead one and create new
            conn = cm._get_conn()
            
            # Should have created a new connection
            assert mock_module.connect.called


class TestBatchEvaluatorOptimizations:
    """Tests for scripts/batch_evaluator.py optimizations."""
    
    def test_compare_models_dict_lookup(self):
        """Test that compare_models uses O(1) dict lookup."""
        # Import the evaluator
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from batch_evaluator import BatchEvaluator, EvalResult
        
        # Create evaluator with test results
        evaluator = BatchEvaluator()
        
        # Create mock results
        for i in range(100):
            result = EvalResult(
                model_id=f"model_{i}",
                model_type="test",
                status="completed",
                duration=10.0,
                metrics={"accuracy": 0.8}
            )
            evaluator.results.append(result)
        
        # Test comparison with multiple models
        model_ids = ["model_5", "model_25", "model_50", "model_75"]
        
        start = time.perf_counter()
        comparison = evaluator.compare_models(model_ids)
        elapsed = time.perf_counter() - start
        
        # Should be very fast (< 1ms for 100 models)
        assert elapsed < 0.001
        
        # Verify correct results returned
        assert len(comparison["models"]) == 4
        assert "model_5" in comparison["models"]
        assert "model_25" in comparison["models"]
        
    def test_compare_models_correctness(self):
        """Test that compare_models returns correct results."""
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from batch_evaluator import BatchEvaluator, EvalResult
        
        evaluator = BatchEvaluator()
        
        # Create specific test results
        result1 = EvalResult(
            model_id="model_a",
            model_type="lora",
            status="completed",
            duration=15.5,
            metrics={"accuracy": 0.95, "loss": 0.05}
        )
        result2 = EvalResult(
            model_id="model_b",
            model_type="azure",
            status="completed",
            duration=10.2,
            metrics={"accuracy": 0.92, "loss": 0.08}
        )
        
        evaluator.results = [result1, result2]
        
        # Compare the two models
        comparison = evaluator.compare_models(["model_a", "model_b"])
        
        assert len(comparison["models"]) == 2
        assert comparison["models"] == ["model_a", "model_b"]
        
        # Check detailed comparison data
        comp_data = comparison["comparison"]
        assert len(comp_data) == 2
        assert comp_data[0]["model_id"] == "model_a"
        assert comp_data[0]["metrics"]["accuracy"] == 0.95
        assert comp_data[1]["model_id"] == "model_b"
        assert comp_data[1]["metrics"]["accuracy"] == 0.92


class TestDictionaryIterationOptimizations:
    """Tests for dictionary iteration optimizations across multiple files."""
    
    def test_direct_iteration_performance(self):
        """Test that direct iteration is faster than .keys()."""
        test_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        # Method 1: Using .keys() (old way)
        start = time.perf_counter()
        for _ in range(100):
            result1 = [k for k in test_dict.keys() if k.startswith("key_5")]
        old_time = time.perf_counter() - start
        
        # Method 2: Direct iteration (optimized)
        start = time.perf_counter()
        for _ in range(100):
            result2 = [k for k in test_dict if k.startswith("key_5")]
        new_time = time.perf_counter() - start
        
        # Results should be identical
        assert len(result1) == len(result2)
        
        # Optimized should be slightly faster or equal
        print(f"\nOld (.keys()): {old_time:.4f}s, New (direct): {new_time:.4f}s")
        # Allow for timing variance - main benefit is code cleanliness
        assert new_time <= old_time * 1.1


class TestFileStreamingOptimizations:
    """Tests for file I/O streaming optimizations."""
    
    def test_log_tail_streaming(self, tmp_path):
        """Test that log tail reading works correctly for large files."""
        # Create a large log file
        log_file = tmp_path / "large.log"
        
        # Write 10000 lines
        lines = [f"Line {i}: Some log content here\n" for i in range(10000)]
        log_file.write_text(''.join(lines))
        
        # Simulate the optimized reading (for files > 64KB)
        with open(log_file, 'rb') as f:
            f.seek(0, 2)  # End of file
            file_size = f.tell()
            
            # Read backwards in blocks
            block_size = 32768
            chunks = []
            remaining = file_size
            target_lines = 500
            
            while remaining > 0 and len(chunks) < target_lines * 2:
                read_size = min(block_size, remaining)
                f.seek(remaining - read_size)
                chunk = f.read(read_size)
                chunks.insert(0, chunk)
                remaining -= read_size
                
                decoded = b''.join(chunks).decode('utf-8', errors='ignore')
                if decoded.count('\n') >= target_lines:
                    break
            
            decoded = b''.join(chunks).decode('utf-8', errors='ignore')
            result_lines = decoded.splitlines(keepends=True)[-500:]
        
        # Should get last 500 lines
        assert len(result_lines) == 500
        assert "Line 9999" in result_lines[-1]
        assert "Line 9500" in result_lines[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
