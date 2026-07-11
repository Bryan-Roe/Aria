"""Compatibility shim for importing the AutoTrain orchestrator module.

Some tests and legacy scripts import ``autotrain`` from the repository root.
The canonical implementation lives in ``scripts/autotrain.py``.
"""

from __future__ import annotations

import sys
import warnings
from importlib import import_module
from typing import cast

warnings.warn(
    ("Importing 'autotrain' from the repository root is deprecated. Import from 'scripts.autotrain' instead."),
    DeprecationWarning,
    stacklevel=2,
)

_canonical = import_module("scripts.autotrain")

for _name, _value in _canonical.__dict__.items():
    if _name.startswith("__"):
        continue
    globals()[_name] = _value

_canonical_all = getattr(_canonical, "__all__", None)
if isinstance(_canonical_all, (list, tuple)):
    _canonical_all_seq = cast(
        list[object] | tuple[object, ...],
        _canonical_all,
    )
    _exports = [name for name in _canonical_all_seq if isinstance(name, str)]
    globals()["__all__"] = _exports

# Mirror the canonical module so downstream monkeypatches
# affect one object.
sys.modules[__name__] = _canonical
