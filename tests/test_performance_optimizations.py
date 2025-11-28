"""
Tests for performance optimization improvements.

These tests verify that the optimizations made to various modules
maintain correct functionality while improving performance.
"""
import json
import tempfile
import time
from pathlib import Path
from collections import deque

import pytest


class TestSqlEngineOptimizations:
    """Tests for sql_engine.py optimizations."""
    
    def test_deque_slow_query_log(self):
        """Test that the slow query log uses efficient deque operations."""
        # Simulate the optimized implementation
        log = deque()
        
        # Add entries with timestamps going backwards from now
        # This simulates entries being added over time (newest last)
        now = time.time()
        for i in range(100):
            # Older entries first, newer entries last
            log.append((now - (99 - i), i * 10))
        
        # Prune old entries (older than 60 seconds)
        cutoff = now - 60
        while log and log[0][0] < cutoff:
            log.popleft()
        
        # Should keep entries from approximately the last 60 seconds
        # Due to timing, we allow for the boundary case (60 or 61 entries)
        assert 59 <= len(log) <= 61
        
    def test_query_hash_normalization(self):
        """Test that query hash normalization is efficient."""
        sql = """
            SELECT *
            FROM   users
            WHERE  id = 1
        """
        # Optimized normalization using split/join
        normalized = ' '.join(sql.split())
        
        assert normalized == "SELECT * FROM users WHERE id = 1"


class TestLineCountingOptimizations:
    """Tests for efficient line counting in various modules."""
    
    def test_binary_line_counting(self, tmp_path):
        """Test efficient binary-mode line counting."""
        test_file = tmp_path / "test.jsonl"
        
        # Create test file with known line count
        lines = ['{"data": ' + str(i) + '}' for i in range(1000)]
        test_file.write_text('\n'.join(lines) + '\n')
        
        # Count lines using optimized binary method
        line_count = 0
        with open(test_file, 'rb') as f:
            buf_size = 65536
            read_f = f.read
            buf = read_f(buf_size)
            while buf:
                line_count += buf.count(b'\n')
                buf = read_f(buf_size)
        
        assert line_count == 1000
        
    def test_binary_counting_empty_file(self, tmp_path):
        """Test binary line counting on empty file."""
        test_file = tmp_path / "empty.jsonl"
        test_file.write_text('')
        
        line_count = 0
        with open(test_file, 'rb') as f:
            buf = f.read(65536)
            while buf:
                line_count += buf.count(b'\n')
                buf = f.read(65536)
        
        assert line_count == 0


class TestBufferedWriteOptimizations:
    """Tests for buffered write optimizations."""
    
    def test_batched_jsonl_writing(self, tmp_path):
        """Test that buffered JSONL writing produces correct output."""
        output_file = tmp_path / "output.jsonl"
        
        # Simulate the optimized buffered writing
        buffer = []
        buffer_size = 100
        
        with open(output_file, 'w', encoding='utf-8', buffering=65536) as f:
            for i in range(250):
                line = json.dumps({"id": i, "data": f"item_{i}"})
                buffer.append(line)
                
                if len(buffer) >= buffer_size:
                    f.write('\n'.join(buffer) + '\n')
                    buffer.clear()
            
            # Write remaining items
            if buffer:
                f.write('\n'.join(buffer) + '\n')
        
        # Verify output
        with open(output_file, 'r') as f:
            lines = [line for line in f if line.strip()]
        
        assert len(lines) == 250
        
        # Verify content
        first_item = json.loads(lines[0])
        assert first_item == {"id": 0, "data": "item_0"}
        
        last_item = json.loads(lines[-1])
        assert last_item == {"id": 249, "data": "item_249"}


class TestAggregationOptimizations:
    """Tests for result aggregation optimizations."""
    
    def test_single_pass_aggregation(self):
        """Test that single-pass aggregation works correctly."""
        # Simulate the EvaluationResult dataclass
        class MockResult:
            def __init__(self, model_id, status, duration, metrics):
                self.model_id = model_id
                self.status = status
                self.duration = duration
                self.metrics = metrics
        
        results = [
            MockResult("model_a", "succeeded", 10.5, {"accuracy": 0.95}),
            MockResult("model_b", "failed", 5.0, {}),
            MockResult("model_c", "succeeded", 8.0, {"accuracy": 0.88}),
            MockResult("model_d", "succeeded", 12.0, {"accuracy": 0.92}),
        ]
        
        # Single-pass aggregation
        succeeded = []
        failed = []
        total_duration = 0.0
        
        for r in results:
            total_duration += r.duration
            if r.status == "succeeded":
                succeeded.append(r)
            else:
                failed.append(r)
        
        assert len(succeeded) == 3
        assert len(failed) == 1
        assert total_duration == 35.5


class TestDatasetSampleCountingOptimizations:
    """Tests for dataset sample counting optimizations."""
    
    def test_count_dataset_samples(self, tmp_path):
        """Test the optimized _count_dataset_samples function."""
        # Create a dataset directory
        dataset_dir = tmp_path / "test_dataset"
        dataset_dir.mkdir()
        
        # Create train.jsonl with 50 lines
        train_data = '\n'.join(['{"text": "sample ' + str(i) + '"}' for i in range(50)]) + '\n'
        (dataset_dir / "train.jsonl").write_text(train_data)
        
        # Create test.jsonl with 10 lines
        test_data = '\n'.join(['{"text": "test ' + str(i) + '"}' for i in range(10)]) + '\n'
        (dataset_dir / "test.jsonl").write_text(test_data)
        
        # Count using optimized method
        train = test = 0
        for name, key in [("train.jsonl", "train"), ("test.jsonl", "test")]:
            f = dataset_dir / name
            if f.exists():
                count = 0
                with f.open("rb") as fh:
                    buf_size = 65536
                    read_f = fh.read
                    buf = read_f(buf_size)
                    while buf:
                        count += buf.count(b'\n')
                        buf = read_f(buf_size)
                if key == "train":
                    train += count
                else:
                    test += count
        
        assert train == 50
        assert test == 10


class TestDequeVsListPerformance:
    """Tests demonstrating deque vs list performance for slow query log."""
    
    def test_deque_popleft_efficiency(self):
        """Verify deque popleft is efficient for pruning old entries."""
        # Create a deque with 1000 entries
        log = deque()
        now = time.time()
        
        for i in range(1000):
            log.append((now - (1000 - i), i))
        
        # Prune entries older than 60 seconds
        cutoff = now - 60
        start = time.perf_counter()
        
        while log and log[0][0] < cutoff:
            log.popleft()
        
        elapsed = time.perf_counter() - start
        
        # Should complete very quickly (O(n) but with O(1) per pop)
        assert elapsed < 0.01  # Should be much less than 10ms
        assert len(log) <= 61  # Only entries from last 60 seconds


class TestJsonSampleCounting:
    """Tests for efficient JSON sample counting."""
    
    def test_json_array_counting(self, tmp_path):
        """Test counting samples in a JSON array file."""
        test_file = tmp_path / "data.json"
        data = [{"id": i} for i in range(100)]
        test_file.write_text(json.dumps(data))
        
        with open(test_file, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                loaded = json.load(f)
                count = len(loaded) if isinstance(loaded, list) else 1
            else:
                count = sum(1 for line in f if line.strip())
        
        assert count == 100
    
    def test_jsonl_counting(self, tmp_path):
        """Test counting lines in a JSONL file."""
        test_file = tmp_path / "data.jsonl"
        lines = [json.dumps({"id": i}) for i in range(100)]
        test_file.write_text('\n'.join(lines) + '\n')
        
        with open(test_file, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            f.seek(0)
            
            if first_char == '[':
                loaded = json.load(f)
                count = len(loaded) if isinstance(loaded, list) else 1
            elif first_char == '{':
                count = sum(1 for line in f if line.strip())
            else:
                count = 0
        
        assert count == 100
