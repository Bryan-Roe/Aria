"""Compatibility shim for legacy ``import agi_provider``.

The canonical implementation lives at
``ai-projects/chat-cli/src/agi_provider.py``. This module loads that file and
re-exports its public API so existing root-level imports continue to work.

The shim is intentionally small, defensive, and side-effect aware:
- validates the canonical file path early with actionable ImportError messages
- caches the loaded canonical module to avoid repeated execution
- preserves an existing compatible module already present in ``sys.modules``
- re-exports only symbols that are explicitly expected to exist
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final, cast

_CANONICAL_PATH: Final[Path] = (
    Path(__file__).resolve().parent
    / "ai-projects"
    / "chat-cli"
    / "src"
    / "agi_provider.py"
)

_MODULE_NAME: Final[str] = "_aria_canonical_agi_provider"

_EXPECTED_EXPORTS: Final[tuple[str, ...]] = (
    "AGIProvider",
    "AGIContext",
    "ReasoningStep",
    "create_agi_provider",
    "MemoryInterface",
    "EnvironmentInterface",
    "MAX_INPUT_LENGTH",
    "MAX_HISTORY_SIZE",
    "MAX_GOALS",
    "MAX_REASONING_CHAINS",
    "_sanitize_input",
    "_sanitize_for_logging",
    "_infer_aria_movement_tag",
    "_AGENT_REGISTRY",
)


def _validate_canonical_path(path: Path) -> None:
    if not path.exists():
        raise ImportError(
            "Canonical AGI provider not found at "
            f"{path!s}. Expected repository layout: "
            "ai-projects/chat-cli/src/agi_provider.py"
        )
    if not path.is_file():
        raise ImportError(f"Canonical AGI provider path is not a file: {path!s}")


def _load_canonical_module(path: Path) -> ModuleType:
    _validate_canonical_path(path)

    existing = sys.modules.get(_MODULE_NAME)
    if existing is not None:
        existing_file = getattr(existing, "__file__", None)
        if existing_file and Path(existing_file).resolve() == path.resolve():
            return existing

    spec = importlib.util.spec_from_file_location(_MODULE_NAME, path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Unable to create import spec for canonical AGI provider: {path!s}"
        )

    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(_MODULE_NAME)
    sys.modules[_MODULE_NAME] = module

    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover
        if previous is not None:
            sys.modules[_MODULE_NAME] = previous
        else:
            sys.modules.pop(_MODULE_NAME, None)
        raise ImportError(
            f"Failed to import canonical AGI provider from {path!s}: "
            f"{exc.__class__.__name__}: {exc}"
        ) from exc

    return module


def _export(module: ModuleType, name: str) -> Any:
    try:
        return getattr(module, name)
    except AttributeError as exc:
        raise ImportError(
            f"Canonical AGI provider is missing expected export {name!r} "
            f"from {_CANONICAL_PATH!s}"
        ) from exc


_mod = _load_canonical_module(_CANONICAL_PATH)

AGIProvider = _export(_mod, "AGIProvider")
AGIContext = _export(_mod, "AGIContext")
ReasoningStep = _export(_mod, "ReasoningStep")
create_agi_provider = _export(_mod, "create_agi_provider")
MemoryInterface = _export(_mod, "MemoryInterface")
EnvironmentInterface = _export(_mod, "EnvironmentInterface")

MAX_INPUT_LENGTH = cast(int, _export(_mod, "MAX_INPUT_LENGTH"))
MAX_HISTORY_SIZE = cast(int, _export(_mod, "MAX_HISTORY_SIZE"))
MAX_GOALS = cast(int, _export(_mod, "MAX_GOALS"))
MAX_REASONING_CHAINS = cast(int, _export(_mod, "MAX_REASONING_CHAINS"))

_sanitize_input = _export(_mod, "_sanitize_input")
_sanitize_for_logging = _export(_mod, "_sanitize_for_logging")
_infer_aria_movement_tag = _export(_mod, "_infer_aria_movement_tag")
_AGENT_REGISTRY = _export(_mod, "_AGENT_REGISTRY")

__all__ = list(_EXPECTED_EXPORTS)
