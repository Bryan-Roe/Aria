"""Tests for LM Studio availability cache thread safety.

This module tests that the _lmstudio_cache dictionary is properly protected
with threading.RLock to prevent race conditions in concurrent Azure Functions
environments.
"""

import sys
import threading
import time
from pathlib import Path
from unittest import mock

import chat_providers

# Add workspace root to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "ai-projects" / "chat-cli" / "src"))


class TestLMStudioCacheThreadSafety:
    """Test thread-safe LM Studio availability caching."""

    def setup_method(self):
        """Reset cache before each test."""
        with chat_providers._lmstudio_cache_lock:
            chat_providers._lmstudio_cache["available"] = None
            chat_providers._lmstudio_cache["checked_at"] = 0.0
            chat_providers._lmstudio_cache["url"] = None

    def test_cache_returns_cached_value_within_ttl(self):
        """Cached value should be returned within TTL."""
        url = "http://127.0.0.1:1234/v1"

        # First call - cache miss, will try HTTP (which will fail)
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("connection refused")
        ):
            result1 = chat_providers._check_lmstudio_available(url)

        assert result1 is False

        # Second call - should use cache, not make HTTP request
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            result2 = chat_providers._check_lmstudio_available(url)

        assert result2 is False
        mock_urlopen.assert_not_called()

    def test_cache_refreshes_after_ttl(self):
        """Cache should be refreshed after TTL expires."""
        url = "http://127.0.0.1:1234/v1"

        # First call - cache miss
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("connection refused")
        ):
            result1 = chat_providers._check_lmstudio_available(url)

        assert result1 is False

        # Manually expire the cache
        with chat_providers._lmstudio_cache_lock:
            chat_providers._lmstudio_cache["checked_at"] = (
                time.time() - chat_providers._LMSTUDIO_CACHE_TTL - 1
            )

        # Second call - should make new HTTP request
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            result2 = chat_providers._check_lmstudio_available(url)

        mock_urlopen.assert_called_once()

    def test_cache_invalidates_on_url_change(self):
        """Cache should be invalidated when URL changes."""
        url1 = "http://127.0.0.1:1234/v1"
        url2 = "http://127.0.0.1:5678/v1"

        # First call with url1
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("connection refused")
        ):
            result1 = chat_providers._check_lmstudio_available(url1)

        assert result1 is False

        # Second call with different url - should make new HTTP request
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("connection refused")
            result2 = chat_providers._check_lmstudio_available(url2)

        mock_urlopen.assert_called_once()

    def test_successful_connection_is_cached(self):
        """Successful LM Studio connection should be cached."""
        url = "http://127.0.0.1:1234/v1"

        # First call - successful
        mock_response = mock.MagicMock()
        with mock.patch("urllib.request.urlopen", return_value=mock_response):
            result1 = chat_providers._check_lmstudio_available(url)

        assert result1 is True

        # Second call - should use cache
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            result2 = chat_providers._check_lmstudio_available(url)

        assert result2 is True
        mock_urlopen.assert_not_called()

    def test_concurrent_access_is_thread_safe(self):
        """Multiple threads accessing cache concurrently should not cause race conditions."""
        url = "http://127.0.0.1:1234/v1"
        results = []
        errors = []
        call_count = [0]

        def mock_urlopen(*args, **kwargs):
            # Add small delay to increase chance of race condition if not thread-safe
            time.sleep(0.01)
            call_count[0] += 1
            raise Exception("connection refused")

        def check_available():
            try:
                result = chat_providers._check_lmstudio_available(url)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Run many threads concurrently
        threads = []
        with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
            for _ in range(20):
                t = threading.Thread(target=check_available)
                threads.append(t)

            for t in threads:
                t.start()

            for t in threads:
                t.join()

        # All results should be consistent (False since we're mocking connection refused)
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20
        assert all(r is False for r in results)

        # Due to thread timing, the first thread should perform the HTTP call,
        # subsequent threads might either wait or also make calls before cache is set.
        # What's important is no exceptions occurred and all results are consistent.

    def test_lock_is_rlock(self):
        """Verify that the lock is an RLock (reentrant) for flexibility."""
        assert type(chat_providers._lmstudio_cache_lock).__name__ == "RLock"

    def test_cache_ttl_value(self):
        """Verify TTL constant is set to reasonable value."""
        assert chat_providers._LMSTUDIO_CACHE_TTL == 30
