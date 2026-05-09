"""Simple TTL-based file caching for repeated JSON reads.

Reduces I/O overhead for files that are read frequently but change infrequently.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional, Tuple

# Cache structure: {path: (data, timestamp)}
_file_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = Lock()

# Default TTL: 60 seconds
DEFAULT_TTL_SECONDS = 60


def read_json_cached(
    file_path: str | Path,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> Optional[Dict[str, Any]]:
    """Read JSON file with TTL-based caching.

    Args:
        file_path: Path to JSON file
        ttl_seconds: Time-to-live for cache in seconds (supports fractional values; default: 60)

    Returns:
        Parsed JSON data as dict, or None if file doesn't exist or parse error

    Thread-safe: Uses lock to protect cache dictionary
    """
    path_str = str(file_path)
    now = time.time()

    with _cache_lock:
        # Check cache first
        cached_entry = _file_cache.get(path_str)
        if cached_entry is not None:
            cached_data, cached_time = cached_entry
            if now - cached_time < ttl_seconds:
                return cached_data
            # Capture stale snapshot so we can still return it if file read fails.
            stale_data = cached_data
        else:
            stale_data = None

        # Cache miss or expired - read from file
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            _file_cache[path_str] = (data, now)
            return data
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            # On error, return stale cache snapshot if available (graceful degradation)
            if stale_data is not None:
                return stale_data
            return None


def clear_cache(file_path: Optional[str | Path] = None) -> None:
    """Clear cache for specific file or entire cache.

    Args:
        file_path: Specific file to clear, or None to clear all
    """
    with _cache_lock:
        if file_path is None:
            _file_cache.clear()
        else:
            _file_cache.pop(str(file_path), None)
