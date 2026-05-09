"""Utilities for defensive imports with graceful fallbacks.

This module provides helpers to reduce boilerplate when importing optional
dependencies that may not be available in all runtime environments.
"""

import logging
from typing import Any, Callable, Dict, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


def safe_import(
    module_path: str,
    *,
    import_names: Optional[Tuple[str, ...]] = None,
    fallback_factory: Optional[Callable[[str], Any]] = None,
    log_failure: bool = True,
) -> Any:
    """Safely import a module or specific names, with optional fallbacks.

    Args:
        module_path: Full module path (e.g., 'shared.sql_engine')
        import_names: Optional tuple of specific names to import from the module
                     (e.g., ('sql_health', 'engine_stats')). If None, returns the module.
        fallback_factory: Optional callable that receives the import name and returns
                         a fallback function/object. Called once per import_name on failure.
        log_failure: Whether to log import failures (default: True)

    Returns:
        - If import_names is None: the imported module, or None on failure
        - If import_names is provided: dict mapping names to imported values or fallbacks

    Examples:
        # Import entire module
        sql_engine = safe_import('shared.sql_engine')

        # Import specific functions with fallbacks
        funcs = safe_import(
            'shared.sql_engine',
            import_names=('sql_health', 'engine_stats'),
            fallback_factory=lambda name: lambda: {"enabled": False, "error": f"{name}_import_failed"}
        )
        sql_health = funcs['sql_health']
        engine_stats = funcs['engine_stats']
    """
    try:
        # Import the module
        parts = module_path.split(".")
        module = __import__(module_path, fromlist=parts[-1:] if len(parts) > 1 else [])

        if import_names is None:
            # Return the whole module
            return module

        # Extract specific names
        result: Dict[str, Any] = {}
        for name in import_names:
            if hasattr(module, name):
                result[name] = getattr(module, name)
            elif fallback_factory:
                result[name] = fallback_factory(name)
            else:
                result[name] = None

        return result

    except Exception as e:
        if log_failure:
            _LOGGER.info(f"[safe_import] Failed to import {module_path}: {e}")

        if import_names is None:
            # No specific names requested, return None
            return None

        # Build fallback dict
        result: Dict[str, Any] = {}
        for name in import_names:
            if fallback_factory:
                result[name] = fallback_factory(name)
            else:
                result[name] = None

        return result


def create_stub_function(
    name: str, error_key: str = "error"
) -> Callable[..., Dict[str, Any]]:
    """Create a stub function that returns a dict indicating unavailability.

    Args:
        name: The function name (used in error message)
        error_key: Key name for the error field (default: 'error')

    Returns:
        A function that accepts any args/kwargs and returns an error dict

    Example:
        sql_health = create_stub_function('sql_health')
        # sql_health() returns {"enabled": False, "error": "sql_health_unavailable"}
    """

    def stub(*args, **kwargs) -> Dict[str, Any]:
        return {"enabled": False, error_key: f"{name}_unavailable"}

    stub.__name__ = name
    return stub
