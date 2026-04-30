"""Compatibility wrapper for Qiskit environment validation.

The canonical script lives in:
  ai-projects/quantum-ml/scripts/validate_qiskit_env.py

This wrapper preserves legacy path expectations used by tests and tooling.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CANONICAL = (
    Path(__file__).resolve().parents[2]
    / "ai-projects"
    / "quantum-ml"
    / "scripts"
    / "validate_qiskit_env.py"
)

if not _CANONICAL.exists():
    raise FileNotFoundError(f"Canonical validator not found: {_CANONICAL}")

_spec = importlib.util.spec_from_file_location(
    "_validate_qiskit_env_canonical", _CANONICAL
)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load spec for {_CANONICAL}")

_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# Re-export callable surface used by tests and scripts.
find_distributions = _mod.find_distributions
classify = _mod.classify
detect_conflict = _mod.detect_conflict
main = _mod.main


if __name__ == "__main__":
    main()
