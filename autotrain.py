"""Compatibility shim for importing the AutoTrain orchestrator module.

Some tests and legacy scripts import ``autotrain`` from the repository root.
The canonical implementation lives in ``scripts/autotrain.py``.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "Importing 'autotrain' from the repository root is deprecated. "
    "Import from 'scripts.autotrain' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from scripts.autotrain import *  # noqa: F401,F403
from scripts.autotrain import __all__  # noqa: F401,E402
