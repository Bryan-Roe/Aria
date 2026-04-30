"""Compatibility shim for importing the AutoTrain orchestrator module.

Some tests and legacy scripts import ``autotrain`` from the repository root.
The canonical implementation lives in ``scripts/autotrain.py``.
"""

from scripts.autotrain import *  # noqa: F401,F403
