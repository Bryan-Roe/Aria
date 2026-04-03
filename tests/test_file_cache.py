"""Test suite for shared/file_cache.py.

Tests cover TTL-based caching, thread-safety, graceful degradation on I/O
errors, and selective/full cache clearing.
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

from shared.file_cache import (DEFAULT_TTL_SECONDS, clear_cache,
                               read_json_cached)

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def clean_cache():
    """Ensure global cache is cleared before and after each test."""
    clear_cache()
    yield
    clear_cache()


class TestReadJsonCached:
    def test_returns_parsed_dict(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"key": "value"}', encoding="utf-8")
        result = read_json_cached(p)
        assert result == {"key": "value"}

    def test_missing_file_returns_none(self, tmp_path):
        result = read_json_cached(tmp_path / "missing.json")
        assert result is None

    def test_invalid_json_returns_none(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        result = read_json_cached(p)
        assert result is None

    def test_second_read_returns_cached_data(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"v": 1}', encoding="utf-8")
        first = read_json_cached(p)
        # Overwrite on disk — cached value should still be returned
        p.write_text('{"v": 999}', encoding="utf-8")
        second = read_json_cached(p)
        assert second == {"v": 1}

    def test_cache_expires_after_ttl(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"v": 1}', encoding="utf-8")
        read_json_cached(p, ttl_seconds=0.1)
        # Update file after TTL expires
        time.sleep(0.15)
        p.write_text('{"v": 2}', encoding="utf-8")
        result = read_json_cached(p, ttl_seconds=0.1)
        assert result == {"v": 2}

    def test_returns_stale_cache_on_io_error(self, tmp_path):
        """When a cached entry exists but the file is deleted, return stale data."""
        p = tmp_path / "data.json"
        p.write_text('{"stale": true}', encoding="utf-8")
        read_json_cached(p, ttl_seconds=0.05)
        # TTL expires and file is deleted
        time.sleep(0.1)
        p.unlink()
        result = read_json_cached(p, ttl_seconds=0.05)
        assert result == {"stale": True}

    def test_accepts_string_path(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"s": 1}', encoding="utf-8")
        result = read_json_cached(str(p))
        assert result == {"s": 1}

    def test_default_ttl_constant_is_positive(self):
        assert DEFAULT_TTL_SECONDS > 0

    def test_thread_safety(self, tmp_path):
        """Multiple threads should not corrupt the cache."""
        p = tmp_path / "data.json"
        p.write_text('{"counter": 0}', encoding="utf-8")

        errors: list[Exception] = []

        def reader():
            for _ in range(20):
                try:
                    result = read_json_cached(p, ttl_seconds=10)
                    assert result is not None
                except Exception as exc:
                    errors.append(exc)

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"


class TestClearCache:
    def test_clear_specific_file(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"v": 1}', encoding="utf-8")
        read_json_cached(p)
        # Overwrite — still cached
        p.write_text('{"v": 2}', encoding="utf-8")
        clear_cache(p)
        # Now it should reload from disk
        result = read_json_cached(p)
        assert result == {"v": 2}

    def test_clear_specific_file_string_path(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"v": 1}', encoding="utf-8")
        read_json_cached(p)
        p.write_text('{"v": 2}', encoding="utf-8")
        clear_cache(str(p))
        result = read_json_cached(p)
        assert result == {"v": 2}

    def test_clear_all(self, tmp_path):
        files = []
        for i in range(3):
            fp = tmp_path / f"data{i}.json"
            fp.write_text(json.dumps({"i": i}), encoding="utf-8")
            read_json_cached(fp)
            # Overwrite each
            fp.write_text(json.dumps({"i": i * 10}), encoding="utf-8")
            files.append(fp)

        clear_cache()  # Clear all

        for i, fp in enumerate(files):
            result = read_json_cached(fp)
            assert result == {"i": i * 10}

    def test_clear_nonexistent_entry_is_silent(self, tmp_path):
        """Clearing a path not in cache should not raise."""
        clear_cache(tmp_path / "never_cached.json")  # Should not raise
