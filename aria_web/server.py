"""Compatibility wrapper for legacy `aria_web/server.py` path.

Delegates to the canonical implementation at `apps/aria/server.py` and exposes
legacy helper/constant names expected by older tests and scripts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_CANONICAL = Path(__file__).resolve().parents[1] / "apps" / "aria" / "server.py"

_spec = importlib.util.spec_from_file_location("_canonical_aria_server", _CANONICAL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load canonical aria server: {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)

# Re-export canonical symbols first.
for _name, _value in _mod.__dict__.items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value


# Legacy helper aliases expected by tests.
def _any_word_in_text(words, text: str) -> bool:
    for word in words:
        if word in text:
            return True
    return False


def _keywords_in_cmd(words, text: str) -> bool:
    for word in words:
        if word in text:
            return True
    return False


_MOVE_KEYWORDS = _mod.MOVE_KEYWORDS
_SAY_KEYWORDS = _mod.SAY_KEYWORDS
_PICKUP_KEYWORDS = _mod.PICKUP_KEYWORDS
_JUMP_KEYWORDS = _mod.JUMP_KEYWORDS
_DANCE_KEYWORDS = _mod.DANCE_KEYWORDS
_LIMB_KEYWORDS = frozenset(
    set(_mod.LEFT_ARM_KEYWORDS)
    | set(_mod.RIGHT_ARM_KEYWORDS)
    | set(_mod.LEFT_LEG_KEYWORDS)
    | set(_mod.RIGHT_LEG_KEYWORDS)
)

__all__ = [k for k in globals() if not k.startswith("__")]


if __name__ == "__main__":
    _mod.main()
