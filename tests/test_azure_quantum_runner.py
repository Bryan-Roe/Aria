import sys
from importlib import import_module
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
QUANTUM_DIR = REPO_ROOT / "ai-projects" / "quantum-ml"
if str(QUANTUM_DIR) not in sys.path:
    sys.path.insert(0, str(QUANTUM_DIR))


def _load_module():
    return import_module("test_azure_quantum")


@pytest.mark.unit
def test_choose_backend_skip_hardware_overrides_requested_qpu():
    module = _load_module()

    backend, allow_hardware_comparison = module.choose_backend(
        backends=["ionq.simulator", "ionq.qpu"],
        requested_backend="ionq.qpu",
        non_interactive=False,
        skip_hardware=True,
    )

    assert backend == "ionq.simulator"
    assert allow_hardware_comparison is False


@pytest.mark.unit
def test_choose_backend_requested_simulator_disables_hardware_comparison():
    module = _load_module()

    backend, allow_hardware_comparison = module.choose_backend(
        backends=["ionq.simulator", "quantinuum.sim.h1-1sc", "ionq.qpu"],
        requested_backend="quantinuum.sim.h1-1sc",
        non_interactive=False,
        skip_hardware=False,
    )

    assert backend == "quantinuum.sim.h1-1sc"
    assert allow_hardware_comparison is False
