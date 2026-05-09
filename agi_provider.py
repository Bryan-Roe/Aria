"""Compatibility shim for legacy `import agi_provider`.

The canonical implementation lives under `ai-projects/chat-cli/src/agi_provider.py`.
This shim dynamically loads the canonical module and re-exports its public API to
keep root-level imports backward compatible.

Improvements:
- Clear, early error messages when the canonical file is missing/unreadable.
- Safer import mechanics (no clobbering existing sys.modules entries).
- Better typing and explicit re-exports.
- Avoid leaking internal attributes (only export what exists).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_CANONICAL = (
    Path(__file__).resolve().parent
    / "ai-projects"
    / "chat-cli"
    / "src"
    / "agi_provider.py"
)

_MODULE_NAME = "_canonical_agi_provider"


def _load_canonical_module(path: Path) -> ModuleType:
    if not path.exists():
        raise ImportError(
            f"Canonical AGI provider not found at: {path}. "
            "Expected repository layout: ai-projects/chat-cli/src/agi_provider.py"
        )
    if not path.is_file():
        raise ImportError(f"Canonical AGI provider path is not a file: {path}")

    spec = importlib.util.spec_from_file_location(_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create import spec for canonical AGI provider: {path}")

    module = importlib.util.module_from_spec(spec)

    # Avoid overwriting an existing module entry if something else registered it.
    existing = sys.modules.get(_MODULE_NAME)
    if existing is None:
        sys.modules[_MODULE_NAME] = module

    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover
        sys.modules.pop(_MODULE_NAME, None)
        raise ImportError(f"Failed to import canonical AGI provider from {path}: {exc}") from exc

    return module


_mod = _load_canonical_module(_CANONICAL)


def _export(name: str) -> Any:
    try:
        return getattr(_mod, name)
    except AttributeError as exc:
        raise ImportError(
            f"Canonical AGI provider is missing expected export '{name}' "
            f"from {_CANONICAL}"
        ) from exc


AGIProvider = _export("AGIProvider")
AGIContext = _export("AGIContext")
ReasoningStep = _export("ReasoningStep")
create_agi_provider = _export("create_agi_provider")

MAX_INPUT_LENGTH = _export("MAX_INPUT_LENGTH")
MAX_HISTORY_SIZE = _export("MAX_HISTORY_SIZE")
MAX_GOALS = _export("MAX_GOALS")
MAX_REASONING_CHAINS = _export("MAX_REASONING_CHAINS")

_sanitize_input = _export("_sanitize_input")
_sanitize_for_logging = _export("_sanitize_for_logging")
_infer_aria_movement_tag = _export("_infer_aria_movement_tag")
_AGENT_REGISTRY = _export("_AGENT_REGISTRY")

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
    "_infer_aria_movement_tag",
    "_AGENT_REGISTRY",
]
