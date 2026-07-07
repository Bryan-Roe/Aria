"""Compatibility shim for importing the AutoTrain orchestrator module.

Some tests and legacy scripts import ``autotrain`` from the repository root.
The canonical implementation lives in ``scripts/autotrain.py``.
"""

from __future__ import annotations

import sys
import warnings
from importlib import import_module

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

# Mirror the canonical module so downstream monkeypatches affect one object.
sys.modules[__name__] = _canonical
