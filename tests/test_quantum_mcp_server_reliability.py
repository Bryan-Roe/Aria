"""Focused reliability tests for quantum/quantum_mcp_server.py."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
import time
import types
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_PATH = REPO_ROOT / "quantum" / "quantum_mcp_server.py"


def _install_dependency_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install lightweight module stubs required to import quantum_mcp_server."""
    # mcp.* stubs
    mcp_mod = types.ModuleType("mcp")
    mcp_server_mod = types.ModuleType("mcp.server")
    mcp_stdio_mod = types.ModuleType("mcp.server.stdio")
    mcp_types_mod = types.ModuleType("mcp.types")

    class DummyServer:
        def __init__(self, *_args, **_kwargs):
            pass

        def list_tools(self):
            def decorator(func):
                return func

            return decorator

        def call_tool(self):
            def decorator(func):
                return func

            return decorator

        async def run(self, *_args, **_kwargs):
            return None

        def create_initialization_options(self):
            return {}

    class DummyTextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text

    class DummyTool:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    mcp_server_mod.Server = DummyServer
    mcp_stdio_mod.stdio_server = object()
    mcp_types_mod.Tool = DummyTool
    mcp_types_mod.TextContent = DummyTextContent

    monkeypatch.setitem(sys.modules, "mcp", mcp_mod)
    monkeypatch.setitem(sys.modules, "mcp.server", mcp_server_mod)
    monkeypatch.setitem(sys.modules, "mcp.server.stdio", mcp_stdio_mod)
    monkeypatch.setitem(sys.modules, "mcp.types", mcp_types_mod)

    # quantum module stubs
    quantum_classifier_mod = types.ModuleType("quantum_classifier")

    class DummyQuantumClassifier:
        def __init__(self, *args, **kwargs):
            pass

    class DummyHybridQuantumClassifier:
        def __init__(self, *args, **kwargs):
            pass

    def dummy_train_quantum_model(*args, **kwargs):
        return {"val_acc": [0.5], "val_loss": [0.5]}

    quantum_classifier_mod.QuantumClassifier = DummyQuantumClassifier
    quantum_classifier_mod.HybridQuantumClassifier = DummyHybridQuantumClassifier
    quantum_classifier_mod.train_quantum_model = dummy_train_quantum_model

    azure_mod = types.ModuleType("azure_quantum_integration")

    class DummyAzureIntegration:
        def __init__(self, config_path: str):
            self.config_path = config_path

        def connect(self):
            return None

    def dummy_create_sample_circuit(_n_qubits: int):
        return object()

    azure_mod.AzureQuantumIntegration = DummyAzureIntegration
    azure_mod.create_sample_circuit = dummy_create_sample_circuit

    monkeypatch.setitem(sys.modules, "quantum_classifier", quantum_classifier_mod)
    monkeypatch.setitem(sys.modules, "azure_quantum_integration", azure_mod)

    # qiskit + torch stubs for top-level imports
    qiskit_mod = types.ModuleType("qiskit")

    class DummyQuantumCircuit:
        pass

    qiskit_mod.QuantumCircuit = DummyQuantumCircuit
    monkeypatch.setitem(sys.modules, "qiskit", qiskit_mod)

    torch_mod = types.ModuleType("torch")
    monkeypatch.setitem(sys.modules, "torch", torch_mod)


def _install_fake_sklearn(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install small sklearn stubs used by _train_classifier_sync."""
    sklearn_mod = types.ModuleType("sklearn")

    datasets_mod = types.ModuleType("sklearn.datasets")

    def _make_dataset():
        data = np.array(
            [
                [0.1, 0.2, 0.3, 0.4],
                [0.4, 0.3, 0.2, 0.1],
                [0.2, 0.1, 0.4, 0.3],
                [0.3, 0.4, 0.1, 0.2],
            ],
            dtype=float,
        )
        target = np.array([0, 1, 0, 1], dtype=int)
        return data, target

    def make_classification(*_args, **_kwargs):
        return _make_dataset()

    class _Bunch:
        def __init__(self, data, target):
            self.data = data
            self.target = target

    def load_iris():
        data, target = _make_dataset()
        return _Bunch(data, target)

    def load_wine():
        data, target = _make_dataset()
        return _Bunch(data, target)

    def load_breast_cancer():
        data, target = _make_dataset()
        return _Bunch(data, target)

    datasets_mod.make_classification = make_classification
    datasets_mod.load_iris = load_iris
    datasets_mod.load_wine = load_wine
    datasets_mod.load_breast_cancer = load_breast_cancer

    model_selection_mod = types.ModuleType("sklearn.model_selection")

    def train_test_split(X, y, test_size=0.2, random_state=42):
        del random_state
        n_train = max(1, int(len(X) * (1 - test_size)))
        n_train = min(n_train, len(X) - 1)
        return X[:n_train], X[n_train:], y[:n_train], y[n_train:]

    model_selection_mod.train_test_split = train_test_split

    preprocessing_mod = types.ModuleType("sklearn.preprocessing")

    class StandardScaler:
        def fit_transform(self, X):
            return X

    preprocessing_mod.StandardScaler = StandardScaler

    monkeypatch.setitem(sys.modules, "sklearn", sklearn_mod)
    monkeypatch.setitem(sys.modules, "sklearn.datasets", datasets_mod)
    monkeypatch.setitem(sys.modules, "sklearn.model_selection", model_selection_mod)
    monkeypatch.setitem(sys.modules, "sklearn.preprocessing", preprocessing_mod)


@pytest.fixture
def quantum_mcp_module(monkeypatch: pytest.MonkeyPatch):
    """Load quantum_mcp_server with stubbed external dependencies."""
    _install_dependency_stubs(monkeypatch)

    module_name = "quantum_mcp_server_testable"
    spec = importlib.util.spec_from_file_location(module_name, MCP_SERVER_PATH)
    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    yield module

    module.io_executor.shutdown(wait=False, cancel_futures=True)
    module.cpu_executor.shutdown(wait=False, cancel_futures=True)
    sys.modules.pop(module_name, None)


@pytest.mark.parametrize(
    "args, env_location, expected",
    [
        ({"location": " westus3 "}, None, "westus3"),
        ({}, "centralus", "centralus"),
        ({}, None, "eastus"),
    ],
)
def test_resolve_azure_location_precedence(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
    args,
    env_location,
    expected,
):
    if env_location is None:
        monkeypatch.delenv("AZURE_QUANTUM_LOCATION", raising=False)
    else:
        monkeypatch.setenv("AZURE_QUANTUM_LOCATION", env_location)

    assert quantum_mcp_module._resolve_azure_location(args) == expected


def test_connect_azure_handler_includes_location_in_config(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("AZURE_QUANTUM_LOCATION", "westus")
    quantum_mcp_module.quantum_state["config_cache"].clear()

    captured: dict[str, dict] = {}

    async def fake_run_executor_with_timeout(_executor, _func, *args, operation):
        assert operation == "connect_azure_quantum"
        captured["config"] = args[0]
        return object()

    monkeypatch.setattr(
        quantum_mcp_module,
        "_run_executor_with_timeout",
        fake_run_executor_with_timeout,
    )

    response = asyncio.run(
        quantum_mcp_module.connect_azure_handler(
            {
                "subscription_id": "sub",
                "resource_group": "rg",
                "workspace_name": "ws",
            }
        )
    )

    assert captured["config"]["azure"]["location"] == "westus"
    assert "Location: westus" in response[0].text


def test_connect_azure_sync_cleans_temp_file_even_on_error(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
):
    captured: dict[str, str] = {}

    class FailingAzureIntegration:
        def __init__(self, config_path: str):
            captured["config_path"] = config_path
            assert Path(config_path).exists()

        def connect(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        quantum_mcp_module,
        "AzureQuantumIntegration",
        FailingAzureIntegration,
    )

    with pytest.raises(RuntimeError, match="boom"):
        quantum_mcp_module._connect_azure_sync({"azure": {"x": "y"}})

    assert "config_path" in captured
    assert not Path(captured["config_path"]).exists()


def test_train_classifier_sync_cleans_temp_file(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
):
    _install_fake_sklearn(monkeypatch)

    captured: dict[str, str] = {}

    class FakeQuantumClassifier:
        def __init__(self, config_path: str):
            captured["qc_config_path"] = config_path
            assert Path(config_path).exists()

    class FakeHybridQuantumClassifier:
        def __init__(self, input_dim: int, quantum_classifier):
            self.input_dim = input_dim
            self.quantum_classifier = quantum_classifier

    def fake_train_quantum_model(
        _model,
        _X_train,
        _y_train,
        _X_val,
        _y_val,
        *,
        config_path: str,
    ):
        captured["train_config_path"] = config_path
        assert Path(config_path).exists()
        return {"val_acc": [0.75], "val_loss": [0.33]}

    monkeypatch.setattr(quantum_mcp_module, "QuantumClassifier", FakeQuantumClassifier)
    monkeypatch.setattr(
        quantum_mcp_module,
        "HybridQuantumClassifier",
        FakeHybridQuantumClassifier,
    )
    monkeypatch.setattr(
        quantum_mcp_module,
        "train_quantum_model",
        fake_train_quantum_model,
    )

    result = quantum_mcp_module._train_classifier_sync(
        "synthetic",
        n_qubits=4,
        n_layers=2,
        epochs=1,
        entanglement="linear",
    )

    assert "Quantum classifier training completed" in result
    assert captured["qc_config_path"] == captured["train_config_path"]
    assert not Path(captured["qc_config_path"]).exists()


def test_run_executor_with_timeout_guard(quantum_mcp_module, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(quantum_mcp_module, "EXECUTOR_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(TimeoutError, match="test-operation timed out"):
        asyncio.run(
            quantum_mcp_module._run_executor_with_timeout(
                quantum_mcp_module.io_executor,
                time.sleep,
                0.1,
                operation="test-operation",
            )
        )


def test_submit_job_requires_confirm_cost_for_paid_qpu(quantum_mcp_module):
    class DummyAzure:
        def submit_circuit(self, *_args, **_kwargs):
            raise AssertionError(
                "submit_circuit should not run without confirm_cost"
            )

    quantum_mcp_module.quantum_state["azure_integration"] = DummyAzure()
    quantum_mcp_module.quantum_state["circuit_cache"].put("cid", object())

    response = asyncio.run(
        quantum_mcp_module.submit_job_handler(
            {
                "circuit_id": "cid",
                "backend_name": "ionq.qpu",
                "shots": 100,
                "confirm_cost": False,
            }
        )
    )

    assert "confirm_cost=true" in response[0].text
    assert "FREE simulators" in response[0].text


def test_submit_job_allows_simulator_without_confirm_cost(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
):
    class DummyJob:
        @staticmethod
        def id() -> str:
            return "job-123"

    class DummyAzure:
        def submit_circuit(self, *_args, **_kwargs):
            return DummyJob()

    quantum_mcp_module.quantum_state["azure_integration"] = DummyAzure()
    quantum_mcp_module.quantum_state["circuit_cache"].put("cid", object())

    async def fake_run_executor_with_timeout(
        _executor,
        func,
        *args,
        operation,
    ):
        assert operation == "submit_quantum_job"
        return func(*args)

    monkeypatch.setattr(
        quantum_mcp_module,
        "_run_executor_with_timeout",
        fake_run_executor_with_timeout,
    )

    response = asyncio.run(
        quantum_mcp_module.submit_job_handler(
            {
                "circuit_id": "cid",
                "backend_name": "ionq.simulator",
                "shots": 100,
            }
        )
    )

    assert "Job ID: job-123" in response[0].text


@pytest.mark.parametrize(
    "raw, expected",
    [
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("no", False),
    ],
)
def test_coerce_bool_parsing(quantum_mcp_module, raw, expected):
    assert quantum_mcp_module._coerce_bool(raw) is expected


def test_submit_job_blocks_paid_qpu_when_confirm_cost_is_false_string(
    quantum_mcp_module,
):
    class DummyAzure:
        def submit_circuit(self, *_args, **_kwargs):
            raise AssertionError(
                "submit_circuit should not run when confirm_cost='false'"
            )

    quantum_mcp_module.quantum_state["azure_integration"] = DummyAzure()
    quantum_mcp_module.quantum_state["circuit_cache"].put("cid", object())

    response = asyncio.run(
        quantum_mcp_module.submit_job_handler(
            {
                "circuit_id": "cid",
                "backend_name": "quantinuum.qpu.h1-1",
                "confirm_cost": "false",
            }
        )
    )

    assert "Refusing paid QPU submission" in response[0].text


def test_submit_job_allows_paid_qpu_when_confirm_cost_true_string(
    quantum_mcp_module,
    monkeypatch: pytest.MonkeyPatch,
):
    class DummyJob:
        @staticmethod
        def id() -> str:
            return "job-paid-ok"

    class DummyAzure:
        def submit_circuit(self, *_args, **_kwargs):
            return DummyJob()

    quantum_mcp_module.quantum_state["azure_integration"] = DummyAzure()
    quantum_mcp_module.quantum_state["circuit_cache"].put("cid", object())

    async def fake_run_executor_with_timeout(
        _executor,
        func,
        *args,
        operation,
    ):
        assert operation == "submit_quantum_job"
        return func(*args)

    monkeypatch.setattr(
        quantum_mcp_module,
        "_run_executor_with_timeout",
        fake_run_executor_with_timeout,
    )

    response = asyncio.run(
        quantum_mcp_module.submit_job_handler(
            {
                "circuit_id": "cid",
                "backend_name": "ionq.qpu",
                "confirm_cost": "true",
            }
        )
    )

    assert "Job ID: job-paid-ok" in response[0].text
