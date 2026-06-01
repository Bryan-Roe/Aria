import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "ai-projects" / "quantum-ml" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _load_module():
    return import_module("azure_quantum_integration")


class _PropBackend:
    """Backend whose ``name`` is a plain attribute/property (string)."""

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name


class _MethodBackend:
    """Backend whose ``name`` is a callable method (older SDK style)."""

    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


def _make_integration(module, provider_name="ionq"):
    """Build an integration instance without invoking __init__."""
    inst = module.AzureQuantumIntegration.__new__(
        module.AzureQuantumIntegration
    )
    inst.provider = MagicMock()
    inst.quantum_config = {"provider": provider_name}
    return inst


@pytest.mark.unit
def test_submit_batch_rejects_job_name_count_mismatch():
    module = _load_module()
    azure = MagicMock()
    manager = module.QuantumJobManager(azure)
    circuits = [
        module.create_sample_circuit(2),
        module.create_sample_circuit(2),
    ]

    with pytest.raises(ValueError, match="job_names"):
        manager.submit_batch(circuits, job_names=["only-one-name"])

    azure.submit_circuit.assert_not_called()


@pytest.mark.unit
def test_backend_name_handles_property_and_method_styles():
    """_backend_name must tolerate both SDK name shapes."""
    module = _load_module()
    assert module._backend_name(_PropBackend("ionq.simulator")) == (
        "ionq.simulator"
    )
    assert module._backend_name(_MethodBackend("ionq.qpu")) == "ionq.qpu"


@pytest.mark.unit
def test_get_backend_prefers_simulator_even_when_qpu_listed_first():
    """Default selection must avoid unintended QPU costs."""
    module = _load_module()
    inst = _make_integration(module, provider_name="ionq")
    inst.provider.backends.return_value = [
        _PropBackend("ionq.qpu"),
        _PropBackend("ionq.simulator"),
    ]

    inst.get_backend()

    inst.provider.get_backend.assert_called_once_with("ionq.simulator")


@pytest.mark.unit
def test_get_backend_falls_back_to_qpu_when_no_simulator_available():
    """Fall back to QPU when no simulator backend is available."""
    module = _load_module()
    inst = _make_integration(module, provider_name="ionq")
    inst.provider.backends.return_value = [_PropBackend("ionq.qpu")]

    inst.get_backend()

    inst.provider.get_backend.assert_called_once_with("ionq.qpu")


@pytest.mark.unit
def test_get_backend_honors_explicit_backend_name():
    """Explicit backend names must pass through verbatim."""
    module = _load_module()
    inst = _make_integration(module, provider_name="quantinuum")

    inst.get_backend("quantinuum.qpu.h1-1")

    inst.provider.get_backend.assert_called_once_with("quantinuum.qpu.h1-1")
    inst.provider.backends.assert_not_called()


@pytest.mark.unit
def test_backend_name_supports_method_and_property_forms():
    module = _load_module()

    class MethodBackend:
        def name(self):
            return "method.backend"

    class PropertyBackend:
        name = "property.backend"

    assert module._backend_name(MethodBackend()) == "method.backend"
    assert module._backend_name(PropertyBackend()) == "property.backend"


@pytest.mark.unit
def test_submit_circuit_uses_default_shots_when_none():
    module = _load_module()
    azure = module.AzureQuantumIntegration.__new__(
        module.AzureQuantumIntegration
    )
    azure.quantum_config = {
        "hardware": {"shots": 123, "optimization_level": 2}
    }
    backend = MagicMock()
    backend.run.return_value = MagicMock(id=lambda: "job-1")
    azure.get_backend = MagicMock(return_value=backend)

    circuit = module.create_sample_circuit(2)

    with patch.object(
        module, "transpile", return_value="transpiled"
    ) as transpile_mock:
        result = module.AzureQuantumIntegration.submit_circuit(
            azure,
            circuit,
            backend_name="ionq.simulator",
            shots=None,
            job_name="sample-job",
        )

    transpile_mock.assert_called_once()
    backend.run.assert_called_once_with("transpiled", shots=123)
    assert result is backend.run.return_value
