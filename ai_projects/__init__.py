"""Compatibility shim exposing ai-projects as the ai_projects package.

This package provides subpackages (e.g., quantum_ml) that map to the
corresponding directories under ai-projects/ so imports like

    from ai_projects.quantum_ml.src.quantum_llm import ...

continue to work even though the filesystem uses hyphens.

Automatically created by Copilot CLI.
"""

__all__ = ["quantum_ml"]
