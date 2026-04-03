"""Test suite for shared/performance_utils.py.

Tests cover tail_file, tail_file_smart, stream_jsonl, batch_process,
find_json_in_output, FileCache, timeit decorator, and memoize_with_ttl.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import time

from shared.performance_utils import (FileCache, batch_process,
                                      find_json_in_output, memoize_with_ttl,
                                      stream_jsonl, tail_file, tail_file_smart,
                                      timeit)

# ---------------------------------------------------------------------------
# tail_file
# ---------------------------------------------------------------------------


class TestTailFile:
    def test_returns_last_n_lines(self, tmp_path):
        p = tmp_path / "file.log"
        p.write_text("\n".join(str(i) for i in range(20)), encoding="utf-8")
        result = tail_file(p, max_lines=5)
        assert len(result) == 5
        # Last 5 lines are 15-19
        assert result[-1].strip() == "19"

    def test_returns_all_if_fewer_than_max(self, tmp_path):
        p = tmp_path / "small.log"
        p.write_text("a\nb\nc\n", encoding="utf-8")
        result = tail_file(p, max_lines=100)
        assert len(result) == 3

    def test_missing_file_returns_empty(self, tmp_path):
        result = tail_file(tmp_path / "missing.log")
        assert result == []

    def test_default_max_lines(self, tmp_path):
        p = tmp_path / "file.log"
        p.write_text("\n".join(str(i) for i in range(100)), encoding="utf-8")
        result = tail_file(p)  # default max_lines=20
        assert len(result) == 20

    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "empty.log"
        p.write_text("", encoding="utf-8")
        result = tail_file(p)
        assert result == []


# ---------------------------------------------------------------------------
# tail_file_smart
# ---------------------------------------------------------------------------


class TestTailFileSmart:
    def test_small_file(self, tmp_path):
        p = tmp_path / "small.log"
        lines = [f"line {i}\n" for i in range(10)]
        p.write_text("".join(lines), encoding="utf-8")
        result = tail_file_smart(p, max_lines=5)
        assert len(result) == 5
        assert result[-1].strip() == "line 9"

    def test_large_file_tail(self, tmp_path):
        p = tmp_path / "big.log"
        # Write enough to exceed the small_file_threshold
        lines = [f"line {i}" for i in range(1000)]
        p.write_text("\n".join(lines), encoding="utf-8")
        result = tail_file_smart(p, max_lines=5, small_file_threshold=100)
        assert len(result) == 5
        assert result[-1].strip() == "line 999"

    def test_missing_file_returns_empty(self, tmp_path):
        result = tail_file_smart(tmp_path / "nope.log")
        assert result == []

    def test_matches_tail_file_for_small_files(self, tmp_path):
        p = tmp_path / "cmp.log"
        p.write_text("\n".join(str(i) for i in range(30)), encoding="utf-8")
        regular = tail_file(p, max_lines=10)
        smart = tail_file_smart(p, max_lines=10)
        # Both should return the same last 10 lines (stripping whitespace)
        assert [l.strip() for l in regular] == [l.strip() for l in smart]


# ---------------------------------------------------------------------------
# stream_jsonl
# ---------------------------------------------------------------------------


class TestStreamJsonl:
    def test_yields_all_records(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text(
            '{"id": 1}\n{"id": 2}\n{"id": 3}\n',
            encoding="utf-8",
        )
        results = list(stream_jsonl(p))
        assert len(results) == 3
        assert results[0] == {"id": 1}

    def test_skips_empty_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\n\n{"id": 2}\n', encoding="utf-8")
        results = list(stream_jsonl(p))
        assert len(results) == 2

    def test_skips_invalid_json_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\nnot json\n{"id": 3}\n', encoding="utf-8")
        results = list(stream_jsonl(p))
        assert len(results) == 2

    def test_filter_fn(self, tmp_path):
        p = tmp_path / "data.jsonl"
        records = [{"id": i, "valid": i % 2 == 0} for i in range(6)]
        p.write_text("\n".join(json.dumps(r) for r in records), encoding="utf-8")
        results = list(stream_jsonl(p, filter_fn=lambda r: bool(r.get("valid"))))
        assert all(r["valid"] for r in results)
        assert len(results) == 3  # ids 0, 2, 4

    def test_missing_file_yields_nothing(self, tmp_path):
        results = list(stream_jsonl(tmp_path / "missing.jsonl"))
        assert results == []

    def test_is_lazy_iterator(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\n{"id": 2}\n', encoding="utf-8")
        gen = stream_jsonl(p)
        # Should be a generator / iterator, not a list
        import types

        assert isinstance(gen, types.GeneratorType)


# ---------------------------------------------------------------------------
# batch_process
# ---------------------------------------------------------------------------


class TestBatchProcess:
    def test_processes_all_items(self):
        processed = []
        batch_process(list(range(10)), batch_size=3, process_fn=processed.extend)
        assert sorted(processed) == list(range(10))

    def test_batch_size_respected(self):
        batch_sizes = []
        batch_process(
            list(range(10)),
            batch_size=3,
            process_fn=lambda b: batch_sizes.append(len(b)),
        )
        # 10 items in batches of 3 → [3, 3, 3, 1]
        assert batch_sizes == [3, 3, 3, 1]

    def test_empty_items(self):
        called = []
        batch_process([], batch_size=5, process_fn=lambda b: called.append(b))
        assert called == []

    def test_batch_size_larger_than_list(self):
        processed = []
        batch_process([1, 2], batch_size=100, process_fn=processed.extend)
        assert processed == [1, 2]


# ---------------------------------------------------------------------------
# find_json_in_output
# ---------------------------------------------------------------------------


class TestFindJsonInOutput:
    def test_finds_json_at_end(self):
        output = 'Starting...\nProcessing...\n{"result": 42}\nDone.'
        result = find_json_in_output(output)
        assert result == {"result": 42}

    def test_finds_json_with_key(self):
        output = '{"metrics": {"acc": 0.9}}\n{"other": 1}'
        result = find_json_in_output(output, key="metrics")
        assert result is not None
        assert "metrics" in result

    def test_returns_none_if_no_json(self):
        output = "No JSON here.\nJust plain text."
        result = find_json_in_output(output)
        assert result is None

    def test_returns_none_if_key_not_present(self):
        output = '{"a": 1}\nSome text'
        result = find_json_in_output(output, key="missing_key")
        assert result is None

    def test_ignores_invalid_json_chunks(self):
        output = 'Start\n{not valid json}\n{"valid": true}'
        result = find_json_in_output(output)
        assert result == {"valid": True}

    def test_search_from_beginning(self):
        output = '{"first": 1}\n{"second": 2}'
        result = find_json_in_output(output, search_from_end=False)
        # Should find the first JSON when searching from start
        assert result is not None
        assert "first" in result or "second" in result

    def test_empty_output_returns_none(self):
        result = find_json_in_output("")
        assert result is None


# ---------------------------------------------------------------------------
# FileCache
# ---------------------------------------------------------------------------


class TestFileCache:
    def test_read_returns_file_content(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("hello world", encoding="utf-8")
        cache = FileCache()
        assert cache.read(p) == "hello world"

    def test_second_read_from_cache(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("original", encoding="utf-8")
        cache = FileCache()
        cache.read(p)
        p.write_text("changed", encoding="utf-8")
        # Should return cached original
        assert cache.read(p) == "original"

    def test_read_bytes(self, tmp_path):
        p = tmp_path / "file.bin"
        p.write_bytes(b"\x00\x01\x02")
        cache = FileCache()
        assert cache.read_bytes(p) == b"\x00\x01\x02"

    def test_invalidate_forces_reload(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("v1", encoding="utf-8")
        cache = FileCache()
        cache.read(p)
        p.write_text("v2", encoding="utf-8")
        cache.invalidate(p)
        assert cache.read(p) == "v2"

    def test_clear_empties_cache(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("cached", encoding="utf-8")
        cache = FileCache()
        cache.read(p)
        p.write_text("fresh", encoding="utf-8")
        cache.clear()
        assert cache.read(p) == "fresh"

    def test_stats(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("data", encoding="utf-8")
        cache = FileCache(max_size_mb=1)
        stats_before = cache.stats()
        assert stats_before["entries"] == 0
        cache.read(p)
        stats_after = cache.stats()
        assert stats_after["entries"] == 1
        assert stats_after["current_size_mb"] > 0

    def test_size_limit_respected(self, tmp_path):
        """Files that would exceed max size are not cached."""
        p = tmp_path / "big.txt"
        # Write 2 KB
        p.write_bytes(b"x" * 2048)
        cache = FileCache(max_size_mb=0.001)  # 1 KB limit
        cache.read_bytes(p)
        # File should NOT be in cache because it's too big
        assert cache.stats()["entries"] == 0

    def test_invalidate_nonexistent_is_silent(self):
        cache = FileCache()
        cache.invalidate(Path("not/in/cache.txt"))  # Should not raise

    def test_size_tracking_after_invalidate(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("hello", encoding="utf-8")
        cache = FileCache()
        cache.read(p)
        size_before = cache.current_size
        assert size_before > 0
        cache.invalidate(p)
        assert cache.current_size == 0


# ---------------------------------------------------------------------------
# timeit decorator
# ---------------------------------------------------------------------------


class TestTimeit:
    def test_returns_correct_result(self, capsys):
        @timeit
        def add(a, b):
            return a + b

        result = add(3, 4)
        assert result == 7

    def test_prints_timing_info(self, capsys):
        @timeit
        def noop():
            pass

        noop()
        captured = capsys.readouterr()
        assert "noop" in captured.out
        assert "s" in captured.out

    def test_preserves_function_name(self):
        @timeit
        def my_func():
            pass

        assert my_func.__name__ == "my_func"


# ---------------------------------------------------------------------------
# memoize_with_ttl
# ---------------------------------------------------------------------------


class TestMemoizeWithTtl:
    def test_caches_result(self):
        call_count = [0]

        @memoize_with_ttl(ttl_seconds=10)
        def compute(x):
            call_count[0] += 1
            return x * 2

        assert compute(5) == 10
        assert compute(5) == 10
        assert call_count[0] == 1  # Only called once

    def test_expires_after_ttl(self):
        call_count = [0]

        @memoize_with_ttl(ttl_seconds=0.1)
        def compute():
            call_count[0] += 1
            return 42

        compute()
        time.sleep(0.15)
        compute()
        assert call_count[0] == 2  # Called again after expiry

    def test_different_args_cached_separately(self):
        call_count = [0]

        @memoize_with_ttl(ttl_seconds=10)
        def compute(x):
            call_count[0] += 1
            return x * 3

        compute(1)
        compute(2)
        assert call_count[0] == 2

    def test_cache_clear(self):
        call_count = [0]

        @memoize_with_ttl(ttl_seconds=10)
        def compute():
            call_count[0] += 1
            return "value"

        compute()
        compute.cache_clear()
        compute()
        assert call_count[0] == 2

    def test_cache_info(self):
        @memoize_with_ttl(ttl_seconds=30)
        def compute():
            return 1

        compute()
        info = compute.cache_info()
        assert info["size"] == 1
        assert info["ttl"] == 30

    def test_preserves_function_name(self):
        @memoize_with_ttl()
        def my_cached_fn():
            pass

        assert my_cached_fn.__name__ == "my_cached_fn"
