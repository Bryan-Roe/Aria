"""Public API for quantum-ml module.

This module defines the stable interface for quantum ML workflows.
All imports from quantum-ml should come through this module.
"""

# Re-export main quantum APIs
try:
    from .quantum_llm_integrated import QuantumLLMPipeline
except ImportError:
    QuantumLLMPipeline = None

try:
    from .quantum_classifier import QuantumClassifier
except ImportError:
    QuantumClassifier = None

try:
    from .azure_quantum_integration import AzureQuantumClient
except ImportError:
    AzureQuantumClient = None

try:
    from .automate_quantum_job import submit_quantum_job, poll_quantum_job
except ImportError:
    submit_quantum_job = None
    poll_quantum_job = None


__all__ = [
    'QuantumLLMPipeline',
    'QuantumClassifier',
    'AzureQuantumClient',
    'submit_quantum_job',
    'poll_quantum_job',
]
