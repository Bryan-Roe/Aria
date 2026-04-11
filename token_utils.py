"""Compatibility shim for token utilities.

Re-exports the canonical token utility implementation from
``ai-projects/chat-cli/src/token_utils.py``.
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
    / "token_utils.py"
)

_spec = importlib.util.spec_from_file_location(
    "_canonical_token_utils_root", _CANONICAL
)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load canonical token utils: {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

for _name, _value in _mod.__dict__.items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value

if hasattr(_mod, "__all__"):
    __all__ = list(_mod.__all__)  # type: ignore[attr-defined]
else:
    __all__ = [k for k in globals() if not k.startswith("__")]
