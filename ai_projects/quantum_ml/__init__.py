"""Shim package mapping ai-projects/quantum-ml to ai_projects.quantum_ml.

This module adjusts the package search path so imports like:

    from ai_projects.quantum_ml.src.quantum_llm import QuantumLLMConfig

resolve to files located at: ai-projects/quantum-ml/src/...
"""
from pathlib import Path

# Compute repository root from this file's location (.. -> ai_projects -> repo root)
_repo_root = Path(__file__).resolve().parent.parent.parent
_project_dir = _repo_root / "ai-projects" / "quantum-ml"

# If the project directory exists, prepend it to this package's __path__ so
# Python can locate the `src/` subpackage inside the hyphenated directory.
if _project_dir.exists():
    project_path_str = str(_project_dir)
    if project_path_str not in __path__:
        __path__.insert(0, project_path_str)

__all__ = ["src"]
