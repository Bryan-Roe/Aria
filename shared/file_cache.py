"""Simple TTL-based file caching for repeated JSON reads.

Reduces I/O overhead for files that are read frequently but change infrequently.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from threading import Lock

# Cache structure: {path: (data, timestamp)}
_file_cache: Dict[str, Tuple[Any, float]] = {}
_cache_lock = Lock()

# Default TTL: 60 seconds
DEFAULT_TTL_SECONDS = 60


def read_json_cached(file_path: str | Path, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> Optional[Dict[str, Any]]:
    """Read JSON file with TTL-based caching.
    
    Args:
        file_path: Path to JSON file
        ttl_seconds: Time-to-live for cache in seconds (default: 60)
        
    Returns:
        Parsed JSON data as dict, or None if file doesn't exist or parse error
        
    Thread-safe: Uses lock to protect cache dictionary
    """
    path_str = str(file_path)
    now = time.time()
    
    with _cache_lock:
        # Check cache first
        if path_str in _file_cache:
            cached_data, cached_time = _file_cache[path_str]
            if now - cached_time < ttl_seconds:
                return cached_data
        
        # Cache miss or expired - read from file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _file_cache[path_str] = (data, now)
            return data
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            # On error, return stale cache if available (graceful degradation)
            if path_str in _file_cache:
                cached_data, _ = _file_cache[path_str]
                return cached_data
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
