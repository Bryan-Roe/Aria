"""Core infrastructure tier - always required, minimal dependencies.

Module registry and utilities used by all other modules.
"""

from .module_registry import AIProjectsRegistry

__all__ = ['AIProjectsRegistry']
