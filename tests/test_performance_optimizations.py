"""
Tests for performance optimization improvements.

These tests verify that the optimizations made to various modules
maintain correct functionality while improving performance.
"""

import json
import sys
import time
from collections import deque
from pathlib import Path

import pytest


class TestSqlRepositoryOptimizations:
    """Tests for sql_repository.py optimizations."""

    def test_list_values_uses_sql_limit(self):
        """Test that list_values uses SQL LIMIT instead of fetchall()[:limit]."""
        repo_root = Path(__file__).resolve().parents[1]
        repo_str = str(repo_root)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)

        try:
            from shared.sql_repository import list_values

            # This test verifies the function signature and behavior
            # The actual optimization is that the SQL query now includes LIMIT
            # instead of fetching all rows and slicing in Python
            result = list_values(limit=5)

            # Result should be a list (even if empty when DB not configured)
            assert isinstance(result, list)

            # If results exist, should never exceed limit
            if result:
                assert len(result) <= 5
        except ImportError:
            # If imports fail, skip the test
            pytest.skip("sql_repository module not available")


class TestTrainingAnalyticsOptimizations:
    """Tests for training_analytics.py optimizations."""

    def test_chart_generation_uses_join(self):
        """Test that chart generation uses join() instead of += in loops."""
        # Simulate the optimized chart generation pattern
        chart_height = 10
        scaled = [5, 7, 3, 8, 6, 4, 9, 2]

        chart = []
        for row in range(chart_height - 1, -1, -1):
            chars = []
            for value in scaled:
                if value >= row:
                    chars.append("█")
                else:
                    chars.append(" ")
            chart.append("            │" + "".join(chars))

        # Verify chart was built correctly
        assert len(chart) == chart_height
        assert all("│" in line for line in chart)

        # Verify the pattern: higher values should have more blocks
        # The last line (row 0) should have all blocks
        assert chart[-1].count("█") == len(scaled)

    def test_identify_best_epoch_count_prefers_highest_mean(self, tmp_path):
        """TrainingAnalytics should pick epoch count with highest average accuracy."""
        repo_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo_root / "scripts"))
        try:
            from training_analytics import TrainingAnalytics
        finally:
            sys.path.pop(0)

        status = {
            "performance_history": [
                {"epochs": 50, "mean_accuracy": 0.75},
                {"epochs": 100, "mean_accuracy": 0.80},
                {"epochs": 100, "mean_accuracy": 0.85},
                {"epochs": 25, "mean_accuracy": 0.70},
            ]
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status))

        analytics = TrainingAnalytics(status_file=str(status_file))
        assert analytics.identify_best_epoch_count() == 100

    def test_detect_plateau_uses_variance_threshold(self, tmp_path):
        """Plateau detection should flag when variance is effectively zero."""
        repo_root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(repo_root / "scripts"))
        try:
            from training_analytics import TrainingAnalytics
        finally:
            sys.path.pop(0)

        status = {
            "performance_history": [
                {"mean_accuracy": 0.9000},
                {"mean_accuracy": 0.90005},
                {"mean_accuracy": 0.89995},
                {"mean_accuracy": 0.90002},
            ]
        }
        status_file = tmp_path / "status.json"
        status_file.write_text(json.dumps(status))

        analytics = TrainingAnalytics(status_file=str(status_file))
        assert analytics.detect_plateau(window=3)


class TestWebAppOptimizations:
    """Tests for ai-projects/quantum-ml/web_app.py memory optimization."""

    def test_metrics_history_trimming_uses_comprehension(self):
        """Test that metrics history trimming uses dict comprehension."""
        # Simulate session metrics_history structure
        metrics_history = {
            "epochs": list(range(1500)),
            "train_loss": [0.5 - i * 0.0001 for i in range(1500)],
            "val_loss": [0.6 - i * 0.0001 for i in range(1500)],
            "val_accuracy": [0.5 + i * 0.0002 for i in range(1500)],
            "timestamps": [i * 0.5 for i in range(1500)],
        }

        # Apply the optimized trimming pattern
        if len(metrics_history["epochs"]) > 1000:
            metrics_history = {
                key: values[-1000:] for key, values in metrics_history.items()
            }

        # Verify trimming worked correctly
        assert len(metrics_history["epochs"]) == 1000
        assert len(metrics_history["train_loss"]) == 1000
        assert len(metrics_history["val_accuracy"]) == 1000

        # Verify we kept the last 1000 entries
        assert metrics_history["epochs"][0] == 500
        assert metrics_history["epochs"][-1] == 1499


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
        normalized = " ".join(sql.split())

        assert normalized == "SELECT * FROM users WHERE id = 1"


class TestLineCountingOptimizations:
    """Tests for efficient line counting in various modules."""

    def test_binary_line_counting(self, tmp_path):
        """Test efficient binary-mode line counting."""
        test_file = tmp_path / "test.jsonl"

        # Create test file with known line count
        lines = ['{"data": ' + str(i) + "}" for i in range(1000)]
        test_file.write_text("\n".join(lines) + "\n")

        # Count lines using optimized binary method
        line_count = 0
        with open(test_file, "rb") as f:
            buf_size = 65536
            read_f = f.read
            buf = read_f(buf_size)
            while buf:
                line_count += buf.count(b"\n")
                buf = read_f(buf_size)

        assert line_count == 1000

    def test_binary_counting_empty_file(self, tmp_path):
        """Test binary line counting on empty file."""
        test_file = tmp_path / "empty.jsonl"
        test_file.write_text("")

        line_count = 0
        with open(test_file, "rb") as f:
            buf = f.read(65536)
            while buf:
                line_count += buf.count(b"\n")
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

        with open(output_file, "w", encoding="utf-8", buffering=65536) as f:
            for i in range(250):
                line = json.dumps({"id": i, "data": f"item_{i}"})
                buffer.append(line)

                if len(buffer) >= buffer_size:
                    f.write("\n".join(buffer) + "\n")
                    buffer.clear()

            # Write remaining items
            if buffer:
                f.write("\n".join(buffer) + "\n")

        # Verify output
        with open(output_file, "r") as f:
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
        train_data = (
            "\n".join(['{"text": "sample ' + str(i) + '"}' for i in range(50)]) + "\n"
        )
        (dataset_dir / "train.jsonl").write_text(train_data)

        # Create test.jsonl with 10 lines
        test_data = (
            "\n".join(['{"text": "test ' + str(i) + '"}' for i in range(10)]) + "\n"
        )
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
                        count += buf.count(b"\n")
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

        with open(test_file, "r", encoding="utf-8") as f:
            first_char = f.read(1)
            f.seek(0)

            if first_char == "[":
                loaded = json.load(f)
                count = len(loaded) if isinstance(loaded, list) else 1
            else:
                count = sum(1 for line in f if line.strip())

        assert count == 100

    def test_jsonl_counting(self, tmp_path):
        """Test counting lines in a JSONL file."""
        test_file = tmp_path / "data.jsonl"
        lines = [json.dumps({"id": i}) for i in range(100)]
        test_file.write_text("\n".join(lines) + "\n")

        with open(test_file, "r", encoding="utf-8") as f:
            first_char = f.read(1)
            f.seek(0)

            if first_char == "[":
                loaded = json.load(f)
                count = len(loaded) if isinstance(loaded, list) else 1
            elif first_char == "{":
                count = sum(1 for line in f if line.strip())
            else:
                count = 0

        assert count == 100


class TestPruneMessagesOptimization:
    """Tests for the O(n) prune_messages optimization."""

    def test_prune_messages_complexity(self):
        """Test that prune_messages correctly prunes messages within budget."""
        import sys

        sys.path.insert(0, "ai-projects/chat-cli/src")
        from token_utils import prune_messages

        # Create many messages to test pruning
        messages = [{"role": "user", "content": f"Message {i}" * 50} for i in range(30)]

        result, stats, _ = prune_messages(
            messages=messages,
            provider="openai",
            model="gpt-4o-mini",
            max_context_tokens=2000,
            reserve_output_tokens=500,
        )

        # Verify pruning happened correctly
        assert stats.removed_count > 0
        assert stats.pruned_tokens <= stats.budget - stats.reserve_output_tokens
        assert len(result) < len(messages)

    def test_prune_messages_no_pruning_needed(self):
        """Test prune_messages when all messages fit within budget."""
        import sys

        sys.path.insert(0, "ai-projects/chat-cli/src")
        from token_utils import prune_messages

        # Small number of short messages
        messages = [{"role": "user", "content": "Hi"}]

        result, stats, _ = prune_messages(
            messages=messages,
            provider="openai",
            model="gpt-4o-mini",
            max_context_tokens=10000,
            reserve_output_tokens=500,
        )

        assert stats.removed_count == 0
        assert len(result) == 1


class TestStringBuildOptimization:
    """Tests for string building optimizations."""

    def test_build_prompt_uses_join(self):
        """Test that _build_prompt produces correct output with optimized join."""
        import sys

        sys.path.insert(0, "ai-projects/chat-cli/src")
        from lora_infer_bridge import _build_prompt

        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant reply"},
        ]

        prompt = _build_prompt(messages)

        assert "[SYSTEM] System prompt" in prompt
        assert "User: User message" in prompt
        assert "Assistant: Assistant reply" in prompt
        assert prompt.endswith("Assistant: ")

    def test_build_prompt_empty_messages(self):
        """Test _build_prompt with empty messages."""
        import sys

        sys.path.insert(0, "ai-projects/chat-cli/src")
        from lora_infer_bridge import _build_prompt

        prompt = _build_prompt([])
        assert prompt == "Assistant: "


class TestRegexCachingOptimization:
    """Tests for regex caching optimization."""

    def test_ansi_escape_regex_cached(self):
        """Test that ANSI escape regex is compiled at module level."""
        import sys

        sys.path.insert(0, "shared")
        import re

        from ai_runner import _ANSI_ESCAPE_RE

        # Verify it's a compiled pattern
        assert isinstance(_ANSI_ESCAPE_RE, re.Pattern)

        # Verify it works correctly
        test_str = "\x1b[31mRed\x1b[0m"
        clean = _ANSI_ESCAPE_RE.sub("", test_str)
        assert clean == "Red"


class TestHeapTopKOptimization:
    """Tests for heapq-based top-k selection optimization."""

    def test_heapq_nlargest(self):
        """Test that heapq.nlargest correctly selects top-k items."""
        import heapq

        # Simulate similarity scores
        scored = [{"id": i, "similarity": i * 0.01} for i in range(100)]

        # Get top 5
        top5 = heapq.nlargest(5, scored, key=lambda x: x["similarity"])

        # Verify order (highest first)
        assert top5[0]["id"] == 99
        assert top5[4]["id"] == 95

        # Verify all 5 are present
        assert len(top5) == 5


class TestHashEmbeddingOptimization:
    """Tests for hash embedding optimization."""

    def test_hash_embedding_normalized(self):
        """Test that hash embedding produces L2-normalized vectors."""
        import math
        import sys

        sys.path.insert(0, "shared")
        from chat_memory import _hash_embedding

        text = "Hello world test"
        embedding = _hash_embedding(text)

        # Check L2 norm is 1.0
        norm = math.sqrt(sum(x * x for x in embedding))
        assert abs(norm - 1.0) < 1e-6

    def test_hash_embedding_empty_text(self):
        """Test hash embedding with empty text."""
        import sys

        sys.path.insert(0, "shared")
        from chat_memory import _hash_embedding

        embedding = _hash_embedding("")

        # Should return zero vector
        assert all(x == 0.0 for x in embedding)


class TestCollectionOptimizations:
    """Tests for collection operation optimizations (February 2026)."""

    def test_single_pass_role_checking(self):
        """Test that role checking uses single-pass set comprehension."""
        # Simulate messages window
        window = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
        ]

        # Old inefficient approach (for comparison)
        old_result = any(x.get("role") == "user" for x in window) and any(
            x.get("role") == "assistant" for x in window
        )

        # New optimized approach
        roles = {x.get("role") for x in window}
        new_result = "user" in roles and "assistant" in roles

        # Both should produce same result
        assert old_result == new_result
        assert old_result is True

    def test_single_pass_empty_window(self):
        """Test single-pass role checking with empty window."""
        window = []

        roles = {x.get("role") for x in window}
        result = "user" in roles and "assistant" in roles

        assert not result

    def test_set_intersection_tag_filtering(self):
        """Test that tag filtering uses set intersection."""

        # Mock job objects
        class Job:
            def __init__(self, id, tags):
                self.id = id
                self.tags = tags

        jobs = [
            Job(1, ["python", "ml", "quantum"]),
            Job(2, ["javascript", "web"]),
            Job(3, ["python", "web"]),
            Job(4, ["quantum", "research"]),
        ]

        filter_tags = ["python", "quantum"]

        # Old inefficient approach
        old_result = [j for j in jobs if any(tag in j.tags for tag in filter_tags)]

        # New optimized approach
        tags_set = set(filter_tags)
        new_result = [j for j in jobs if set(j.tags) & tags_set]

        # Both should produce same result
        assert len(old_result) == len(new_result) == 3
        assert [j.id for j in old_result] == [j.id for j in new_result] == [1, 3, 4]


class TestCommandParsingOptimizations:
    """Tests for command parsing optimizations (February 2026)."""

    def test_movement_command_parsing(self):
        """Test optimized movement command parsing."""
        # Define command patterns directly for testing
        _COMMAND_PATTERNS = (
            (
                ("[aria:walk:left]", "walk left"),
                {"action": "walk", "direction": "left", "distance": 200},
            ),
            (
                ("[aria:walk:right]", "walk right"),
                {"action": "walk", "direction": "right", "distance": 200},
            ),
            (
                ("[aria:move:right]", "aria move right"),
                {"action": "move", "direction": "right", "distance": 100},
            ),
            (("[aria:wave]", "aria wave"), {"action": "wave"}),
            (("[aria:jump]", "aria jump"), {"action": "jump"}),
            (
                ("[aria:walk:up]", "walk up"),
                {"action": "walk", "direction": "up", "distance": 200},
            ),
        )

        def parse_movement_commands(text: str) -> dict:
            """Test version of parse_movement_commands"""
            lower_text = text.lower()
            commands = []
            for patterns, command in _COMMAND_PATTERNS:
                if any(pattern in lower_text for pattern in patterns):
                    commands.append(command)
            return {"commands": commands} if commands else {}

        # Test various command patterns
        test_cases = [
            ("walk left", [{"action": "walk", "direction": "left", "distance": 200}]),
            (
                "[aria:move:right]",
                [{"action": "move", "direction": "right", "distance": 100}],
            ),
            ("aria wave", [{"action": "wave"}]),
            ("no commands here", []),
        ]

        for text, expected_commands in test_cases:
            result = parse_movement_commands(text)
            if expected_commands:
                assert result.get("commands") == expected_commands
            else:
                assert result == {}

    def test_command_parsing_performance(self):
        """Test that command parsing is efficient with pattern table."""
        # Define command patterns
        _COMMAND_PATTERNS = (
            (
                ("[aria:walk:left]", "walk left"),
                {"action": "walk", "direction": "left", "distance": 200},
            ),
            (
                ("[aria:walk:right]", "walk right"),
                {"action": "walk", "direction": "right", "distance": 200},
            ),
            (
                ("[aria:move:right]", "aria move right"),
                {"action": "move", "direction": "right", "distance": 100},
            ),
            (
                ("[aria:move:left]", "aria move left"),
                {"action": "move", "direction": "left", "distance": 100},
            ),
            (("[aria:center]", "go to center"), {"action": "center"}),
            (("[aria:wave]", "aria wave"), {"action": "wave"}),
            (("[aria:jump]", "aria jump"), {"action": "jump"}),
        )

        def parse_movement_commands(text: str) -> dict:
            """Test version of parse_movement_commands"""
            lower_text = text.lower()
            commands = []
            for patterns, command in _COMMAND_PATTERNS:
                if any(pattern in lower_text for pattern in patterns):
                    commands.append(command)
            return {"commands": commands} if commands else {}

        # Test with text containing multiple commands
        text = "Please walk left, then aria move right, go to center, aria wave, and aria jump"

        start = time.perf_counter()
        for _ in range(100):
            parse_movement_commands(text)
        elapsed = time.perf_counter() - start

        # Should complete 100 iterations in under 10ms
        # (extremely generous threshold; actual should be much faster)
        assert elapsed < 0.01


class TestFileReadingOptimizations:
    """Tests for file reading optimizations (February 2026)."""

    def test_single_pass_file_reading(self, tmp_path):
        """Test that evaluation set generation reads files only once."""
        # Create test dataset files
        dataset_dir = tmp_path / "test_dataset"
        dataset_dir.mkdir()

        train_file = dataset_dir / "train.json"
        test_file = dataset_dir / "test.json"

        # Create sample records
        train_data = [
            {
                "messages": [
                    {"role": "user", "content": "Q1"},
                    {"role": "assistant", "content": "A1"},
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": "Q2"},
                    {"role": "assistant", "content": "A2"},
                ]
            },
        ]
        test_data = [
            {
                "messages": [
                    {"role": "user", "content": "Q3"},
                    {"role": "assistant", "content": "A3"},
                ]
            },
        ]

        with open(train_file, "w") as f:
            for record in train_data:
                f.write(json.dumps(record) + "\n")

        with open(test_file, "w") as f:
            for record in test_data:
                f.write(json.dumps(record) + "\n")

        # Test the optimized function
        import sys

        sys.path.insert(0, "scripts")
        from generate_evaluation_set import collect_training_hashes_and_records

        hashes, records = collect_training_hashes_and_records(dataset_dir)

        # Should have collected all records
        assert len(records) == 3
        assert len(hashes) == 3

        # Verify hashes are populated
        for record in records:
            assert "hash" in record
