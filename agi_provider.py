"""Compatibility shim for AGI provider imports.

The canonical implementation lives under ``ai-projects/chat-cli/src`` and is
loaded dynamically to keep root-level imports backward compatible.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CANONICAL = (
    Path(__file__).resolve().parent
    / "ai-projects"
    / "chat-cli"
    / "src"
    / "agi_provider.py"
)

_spec = importlib.util.spec_from_file_location("_canonical_agi_provider", _CANONICAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load canonical AGI provider: {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

AGIProvider = _mod.AGIProvider
AGIContext = _mod.AGIContext
ReasoningStep = _mod.ReasoningStep
create_agi_provider = _mod.create_agi_provider
MAX_INPUT_LENGTH = _mod.MAX_INPUT_LENGTH
MAX_HISTORY_SIZE = _mod.MAX_HISTORY_SIZE
MAX_GOALS = _mod.MAX_GOALS
MAX_REASONING_CHAINS = _mod.MAX_REASONING_CHAINS
_sanitize_input = _mod._sanitize_input
_sanitize_for_logging = _mod._sanitize_for_logging

__all__ = [
    "AGIProvider",
    "AGIContext",
    "ReasoningStep",
    "create_agi_provider",
    "MAX_INPUT_LENGTH",
    "MAX_HISTORY_SIZE",
    "MAX_GOALS",
    "MAX_REASONING_CHAINS",
    "_sanitize_input",
    "_sanitize_for_logging",
]
