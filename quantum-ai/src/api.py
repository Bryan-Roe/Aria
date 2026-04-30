"""Public API for the legacy `quantum-ai` module.

This package is a compatibility surface that re-exports the canonical
Quantum Code LLM functionality from `quantum-ai/src/quantum_code_llm.py`.

Use these imports for stable caller contracts:

    from quantum_code_llm import train, generate
    # or
    from api import train, generate
"""

try:
    # Package import (e.g., import quantum_ai.src.api)
    from .quantum_code_llm import (
        QUANTUM_BACKEND,
        CodeTokenizer,
        QuantumCodeLLM,
        QuantumCodeLLMConfig,
        TrainConfig,
        train,
        generate,
        save_checkpoint,
        load_checkpoint,
    )
except ImportError:
    # Top-level import (e.g., sys.path -> quantum-ai/src; import api)
    from quantum_code_llm import (  # type: ignore
        QUANTUM_BACKEND,
        CodeTokenizer,
        QuantumCodeLLM,
        QuantumCodeLLMConfig,
        TrainConfig,
        train,
        generate,
        save_checkpoint,
        load_checkpoint,
    )

__all__ = [
    "QUANTUM_BACKEND",
    "CodeTokenizer",
    "QuantumCodeLLM",
    "QuantumCodeLLMConfig",
    "TrainConfig",
    "train",
    "generate",
    "save_checkpoint",
    "load_checkpoint",
]
