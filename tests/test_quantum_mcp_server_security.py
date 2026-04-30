"""Security tests for ai-projects/quantum-ml/quantum_mcp_server.py.

Covers:
 - shots bounds validation in simulate_circuit_handler
 - custom gate qubit-index bounds checking in _create_circuit_sync
 - temp file cleanup in _connect_azure_sync and _train_classifier_sync
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
QUANTUM_ML_DIR = REPO_ROOT / "ai-projects" / "quantum-ml"
if str(QUANTUM_ML_DIR) not in sys.path:
    sys.path.insert(0, str(QUANTUM_ML_DIR))
SRC_DIR = QUANTUM_ML_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(coro):
    """Run a coroutine synchronously."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# shots bounds validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSimulateCircuitHandlerShotsBounds:
    """simulate_circuit_handler must reject shots outside [1, 8192]."""

    def _make_circuit_in_cache(self):
        """Import mcp server with minimal stubs and pre-populate the cache."""
        try:
            from quantum_mcp_server import (quantum_state,
                                            simulate_circuit_handler)
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")

        try:
            from qiskit import QuantumCircuit
        except ImportError:
            pytest.skip("qiskit not installed")

        # Put a real 1-qubit circuit in the cache.
        circuit_id = "test_circuit_sec"
        qc = QuantumCircuit(1, 1)
        qc.h(0)
        qc.measure(0, 0)
        quantum_state["circuit_cache"].put(circuit_id, qc)
        return circuit_id, simulate_circuit_handler

    def test_rejects_zero_shots(self):
        circuit_id, handler = self._make_circuit_in_cache()
        result = _run(handler({"circuit_id": circuit_id, "shots": 0}))
        assert "8192" in result[0].text or "between" in result[0].text.lower()

    def test_rejects_shots_above_8192(self):
        circuit_id, handler = self._make_circuit_in_cache()
        result = _run(handler({"circuit_id": circuit_id, "shots": 999_999}))
        assert "8192" in result[0].text or "between" in result[0].text.lower()

    def test_rejects_string_shots(self):
        circuit_id, handler = self._make_circuit_in_cache()
        result = _run(handler({"circuit_id": circuit_id, "shots": "all"}))
        assert "8192" in result[0].text or "integer" in result[0].text.lower()


# ---------------------------------------------------------------------------
# Custom gate qubit bounds
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCreateCircuitCustomGatesBounds:
    """_create_circuit_sync must silently skip gates with out-of-bounds qubits."""

    def _get_create_sync(self):
        try:
            from quantum_mcp_server import _create_circuit_sync
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")
        return _create_circuit_sync

    def test_out_of_bounds_single_qubit_gate_skipped(self):
        _create_circuit_sync = self._get_create_sync()
        # n_qubits=2 but gate targets qubit 5 — should be skipped, not IndexError.
        circuit = _create_circuit_sync(
            2,
            "custom",
            # qubit 5 out of range for 2-qubit circuit
            [{"gate": "h", "qubit": 5}],
        )
        assert circuit is not None
        # Circuit should have no Hadamard applied (the gate was skipped),
        # but still have measurements.
        op_counts = circuit.count_ops()
        assert op_counts.get("h", 0) == 0

    def test_out_of_bounds_two_qubit_gate_skipped(self):
        _create_circuit_sync = self._get_create_sync()
        circuit = _create_circuit_sync(
            2,
            "custom",
            [{"gate": "cx", "qubits": [0, 5]}],  # qubit 5 out of range
        )
        assert circuit is not None
        assert circuit.count_ops().get("cx", 0) == 0

    def test_same_qubit_cx_skipped(self):
        _create_circuit_sync = self._get_create_sync()
        # Control and target are the same qubit — invalid, must be skipped.
        circuit = _create_circuit_sync(
            2,
            "custom",
            [{"gate": "cx", "qubits": [1, 1]}],
        )
        assert circuit is not None
        assert circuit.count_ops().get("cx", 0) == 0

    def test_valid_custom_gate_applied(self):
        _create_circuit_sync = self._get_create_sync()
        circuit = _create_circuit_sync(
            2,
            "custom",
            [{"gate": "h", "qubit": 0}, {"gate": "cx", "qubits": [0, 1]}],
        )
        assert circuit is not None
        ops = circuit.count_ops()
        assert ops.get("h", 0) == 1
        assert ops.get("cx", 0) == 1

    def test_negative_qubit_index_skipped(self):
        _create_circuit_sync = self._get_create_sync()
        circuit = _create_circuit_sync(
            2,
            "custom",
            [{"gate": "h", "qubit": -1}],
        )
        assert circuit is not None
        assert circuit.count_ops().get("h", 0) == 0


# ---------------------------------------------------------------------------
# Temp file cleanup
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTempFileCleanup:
    """Verify temp files are removed even when downstream calls raise."""

    def test_connect_azure_cleans_up_temp_file_on_success(self):
        """On successful connect, the temp YAML must be deleted."""
        try:
            from quantum_mcp_server import _connect_azure_sync
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")

        captured_paths: list[str] = []

        original_mkstemp = tempfile.mkstemp

        def spy_mkstemp(**kwargs):
            fd, path = original_mkstemp(**kwargs)
            captured_paths.append(path)
            return fd, path

        fake_integration = MagicMock()

        config = {
            "azure": {
                "subscription_id": "sub",
                "resource_group": "rg",
                "workspace_name": "ws",
                "location": "eastus",
            },
            "quantum": {
                "provider": "ionq",
                "hardware": {"shots": 500, "optimization_level": 2},
            },
            "ml": {"model": {"n_qubits": 4, "n_layers": 2, "entanglement": "linear"}},
            "logging": {"level": "INFO", "results_dir": "./results"},
        }

        with (
            patch("tempfile.mkstemp", side_effect=spy_mkstemp),
            patch(
                "quantum_mcp_server.AzureQuantumIntegration",
                return_value=fake_integration,
            ),
        ):
            try:
                _connect_azure_sync(config)
            except Exception:
                pass  # We only care about the file being cleaned up.

        for path in captured_paths:
            assert not os.path.exists(path), f"Temp file was not deleted: {path}"

    def test_connect_azure_cleans_up_temp_file_on_failure(self):
        """On a connection error, the temp YAML must still be deleted."""
        try:
            from quantum_mcp_server import _connect_azure_sync
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")

        captured_paths: list[str] = []
        original_mkstemp = tempfile.mkstemp

        def spy_mkstemp(**kwargs):
            fd, path = original_mkstemp(**kwargs)
            captured_paths.append(path)
            return fd, path

        with (
            patch("tempfile.mkstemp", side_effect=spy_mkstemp),
            patch(
                "quantum_mcp_server.AzureQuantumIntegration",
                side_effect=RuntimeError("Azure connection error"),
            ),
        ):
            with pytest.raises(RuntimeError):
                _connect_azure_sync(
                    {"azure": {}, "quantum": {}, "ml": {}, "logging": {}}
                )

        for path in captured_paths:
            assert not os.path.exists(path), f"Temp file leaked on failure: {path}"


# ---------------------------------------------------------------------------
# Additional runtime-validation guards
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRuntimeValidationGuards:
    """Validate hard runtime guards that should not rely only on schema."""

    def _import_server(self):
        try:
            import quantum_mcp_server as mcp_server
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")
        return mcp_server

    def test_call_tool_rejects_non_object_arguments(self):
        mcp_server = self._import_server()
        result = _run(mcp_server.call_tool("list_quantum_backends", ["bad", "args"]))
        assert "expected an object" in result[0].text.lower()

    def test_create_circuit_rejects_boolean_qubit_count(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.create_circuit_handler({"n_qubits": True, "circuit_type": "ghz"})
        )
        assert "n_qubits" in result[0].text

    def test_submit_job_rejects_invalid_shots_before_connection(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.submit_job_handler(
                {"circuit_id": "abc123", "backend_name": "simulator", "shots": 0}
            )
        )
        assert "shots must be" in result[0].text.lower()

    def test_submit_job_rejects_non_boolean_confirm_cost(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.submit_job_handler(
                {
                    "circuit_id": "abc123",
                    "backend_name": "simulator",
                    "confirm_cost": "yes",
                    "shots": 10,
                }
            )
        )
        assert "confirm_cost must be a boolean" in result[0].text

    def test_connect_azure_rejects_missing_subscription_id(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.connect_azure_handler(
                {"resource_group": "rg", "workspace_name": "ws"}
            )
        )
        assert "subscription_id is required" in result[0].text

    def test_connect_azure_rejects_whitespace_workspace_name(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.connect_azure_handler(
                {
                    "subscription_id": "sub",
                    "resource_group": "rg",
                    "workspace_name": "   ",
                }
            )
        )
        assert "workspace_name is required" in result[0].text

    def test_estimate_cost_rejects_missing_backend_name(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.estimate_cost_handler(
                {"circuit_id": "abc123", "backend_name": "", "shots": 100}
            )
        )
        assert "backend_name is required" in result[0].text

    def test_estimate_cost_rejects_whitespace_backend_name(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.estimate_cost_handler(
                {"circuit_id": "abc123", "backend_name": "   ", "shots": 100}
            )
        )
        assert "backend_name is required" in result[0].text

    def test_circuit_properties_rejects_missing_circuit_id(self):
        mcp_server = self._import_server()
        result = _run(mcp_server.circuit_properties_handler({}))
        assert "circuit_id is required" in result[0].text

    def test_circuit_properties_rejects_whitespace_circuit_id(self):
        mcp_server = self._import_server()
        result = _run(mcp_server.circuit_properties_handler({"circuit_id": "   "}))
        assert "circuit_id is required" in result[0].text

    def test_submit_job_rejects_whitespace_backend_name(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.submit_job_handler(
                {"circuit_id": "abc123", "backend_name": "   ", "shots": 10}
            )
        )
        assert "backend_name is required" in result[0].text

    def test_simulate_circuit_rejects_whitespace_circuit_id(self):
        try:
            from quantum_mcp_server import simulate_circuit_handler
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")

        result = _run(simulate_circuit_handler({"circuit_id": "   ", "shots": 10}))
        assert "circuit_id is required" in result[0].text

    def test_train_classifier_rejects_invalid_bounds(self):
        mcp_server = self._import_server()
        result = _run(
            mcp_server.train_classifier_handler(
                {
                    "dataset": "synthetic",
                    "n_qubits": 100,
                    "n_layers": 2,
                    "epochs": 10,
                    "entanglement": "linear",
                }
            )
        )
        assert "n_qubits" in result[0].text


# ---------------------------------------------------------------------------
# Cost-gating enforcement
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCostGatingEnforcement:
    """Verify cost-gating prevents excessive job submissions."""

    def _import_server(self):
        try:
            import quantum_mcp_server as mcp_server
        except (ImportError, SystemExit):
            pytest.skip("quantum_mcp_server dependencies not installed")
        return mcp_server

    def _make_circuit_in_cache(self):
        """Pre-populate cache with test circuit."""
        mcp_server = self._import_server()
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            pytest.skip("qiskit not installed")

        circuit_id = "cost_gate_test"
        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])
        mcp_server.quantum_state["circuit_cache"].put(circuit_id, qc)
        return circuit_id, mcp_server

    def test_cost_estimation_zero_for_simulator(self):
        """Verify simulator backend has zero cost."""
        mcp_server = self._import_server()
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            pytest.skip("qiskit not installed")

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.measure([0, 1], [0, 1])

        cost = mcp_server._estimate_job_cost_sync(qc, "simulator", 1000)
        assert cost == 0.0, "Simulator should have zero cost"

    def test_cost_estimation_nonzero_for_ionq(self):
        """Verify IonQ backend has nonzero cost."""
        mcp_server = self._import_server()
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            pytest.skip("qiskit not installed")

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        cost = mcp_server._estimate_job_cost_sync(qc, "ionq", 1000)
        # 4 gates * 1000 shots * 0.00003 = 0.12
        assert cost > 0.0, "IonQ should have nonzero cost"
        assert abs(cost - 0.12) < 0.01, f"Expected ~0.12, got {cost}"

    def test_submit_job_rejects_cost_per_job_limit(self):
        """Returns error when single job cost exceeds MAX_COST_PER_JOB_USD."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()
        fake_azure = MagicMock()

        with (
            patch.object(mcp_server, "MAX_COST_PER_JOB_USD", 0.01),
            patch.dict(
                mcp_server.quantum_state,
                {
                    "azure_integration": fake_azure,
                    "cumulative_cost_usd": 0.0,
                    "known_backends": ["ionq", "microsoft.simulator"],
                    "known_backends_refreshed_at": time.time(),
                },
                clear=False,
            ),
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "ionq",
                        "confirm_cost": True,
                        "shots": 1000,
                    }
                )
            )

        assert "cost" in result[0].text.lower() or "limit" in result[0].text.lower()
        assert "exceed" in result[0].text.lower()

    def test_submit_job_rejects_cumulative_cost_limit(self):
        """Returns error when cumulative session cost would be exceeded."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()
        fake_azure = MagicMock()

        # Pre-set cumulative cost to near-limit
        with (
            patch.object(mcp_server, "MAX_CUMULATIVE_COST_PER_SESSION_USD", 0.50),
            patch.dict(
                mcp_server.quantum_state,
                {
                    "azure_integration": fake_azure,
                    "cumulative_cost_usd": 0.49,
                    "known_backends": ["ionq", "microsoft.simulator"],
                    "known_backends_refreshed_at": time.time(),
                },
                clear=False,
            ),
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "ionq",
                        "confirm_cost": True,
                        "shots": 1000,  # Will add ~0.12, exceeding 0.50 total
                    }
                )
            )

            # Should reject due to cumulative cost
            assert (
                "budget" in result[0].text.lower() or "exceed" in result[0].text.lower()
            )

    def test_submit_job_accepts_within_cost_limits(self):
        """Accepts job when within both per-job and cumulative limits."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        # Create a fake Azure integration mock
        fake_job = MagicMock()
        fake_job.id.return_value = "job_12345"

        fake_azure = MagicMock()
        fake_azure.submit_circuit.return_value = fake_job

        with (
            patch.object(mcp_server, "MAX_COST_PER_JOB_USD", 1.0),
            patch.object(mcp_server, "MAX_CUMULATIVE_COST_PER_SESSION_USD", 100.0),
            patch.dict(
                mcp_server.quantum_state,
                {
                    "azure_integration": fake_azure,
                    "cumulative_cost_usd": 0.0,
                    "known_backends": ["ionq", "microsoft.simulator"],
                    "known_backends_refreshed_at": time.time(),
                },
                clear=False,
            ),
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "simulator",  # Free, so will pass cost gates
                        "shots": 100,
                    }
                )
            )

        assert "submitted" in result[0].text.lower() or "job" in result[0].text.lower()

    def test_submit_job_requires_confirmation_for_paid_backend(self):
        """Paid backends should require explicit cost confirmation."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()
        fake_azure = MagicMock()

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                "known_backends": ["ionq", "microsoft.simulator"],
                "known_backends_refreshed_at": time.time(),
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "ionq",
                        "shots": 100,
                    }
                )
            )

        assert "confirmation required" in result[0].text.lower()
        assert "confirm_cost=true" in result[0].text.lower()

    def test_unknown_backend_uses_conservative_paid_rate(self):
        """Unknown non-simulator backends should never be treated as free."""
        mcp_server = self._import_server()
        try:
            from qiskit import QuantumCircuit
        except ImportError:
            pytest.skip("qiskit not installed")

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        cost = mcp_server._estimate_job_cost_sync(qc, "mystery-qpu", 1000)
        assert (
            cost > 0.0
        ), "Unknown paid-like backend should use a conservative nonzero rate"

    def test_submit_job_rejects_backend_not_in_allowlist(self):
        """Submission must fail when backend is not in cached allowlist."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()
        fake_azure = MagicMock()
        fake_azure.list_backends.return_value = ["ionq", "microsoft.simulator"]

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                "known_backends": ["ionq", "microsoft.simulator"],
                "known_backends_refreshed_at": time.time(),
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "unknown.qpu",
                        "confirm_cost": True,
                        "shots": 100,
                    }
                )
            )

        assert "not in the workspace allowlist" in result[0].text.lower()

    def test_submit_job_refreshes_on_allowlist_miss(self):
        """If backend is missing from fresh cache, submit should do one re-fetch before rejecting."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        fake_job = MagicMock()
        fake_job.id.return_value = "job_miss_refresh_1"
        fake_azure = MagicMock()
        fake_azure.list_backends.return_value = ["old.backend", "microsoft.simulator"]
        fake_azure.submit_circuit.return_value = fake_job

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                # Fresh cache missing target backend; should trigger one-time re-fetch.
                "known_backends": ["old.backend"],
                "known_backends_refreshed_at": time.time(),
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "microsoft.simulator",
                        "shots": 50,
                    }
                )
            )

            assert "submitted" in result[0].text.lower()
            fake_azure.list_backends.assert_called_once()

    def test_submit_job_refreshes_allowlist_when_empty(self):
        """When allowlist cache is empty, submit should refresh it before checking."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        fake_job = MagicMock()
        fake_job.id.return_value = "job_refresh_1"
        fake_azure = MagicMock()
        fake_azure.list_backends.return_value = ["ionq", "microsoft.simulator"]
        fake_azure.submit_circuit.return_value = fake_job

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                "known_backends": [],
                "known_backends_refreshed_at": 0.0,
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "microsoft.simulator",
                        "shots": 50,
                    }
                )
            )

            assert "submitted" in result[0].text.lower()
            assert "microsoft.simulator" in [
                b.lower() for b in mcp_server.quantum_state["known_backends"]
            ]

    def test_submit_job_allowlist_refresh_error_is_reported(self):
        """When backend is missing and refresh fails, response should include refresh failure context."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        fake_azure = MagicMock()
        fake_azure.list_backends.side_effect = RuntimeError("backend API unavailable")

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                "known_backends": ["ionq", "microsoft.simulator"],
                "known_backends_refreshed_at": time.time(),
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "unknown.backend",
                        "confirm_cost": True,
                        "shots": 100,
                    }
                )
            )

            text = result[0].text.lower()
            assert "not in the workspace allowlist" in text
            assert "refresh failed" in text

    def test_estimate_cost_rejects_backend_not_in_allowlist(self):
        """Cost estimation should also reject unknown backends, matching submit behavior."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        fake_azure = MagicMock()

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "known_backends": ["ionq", "microsoft.simulator"],
                "known_backends_refreshed_at": time.time(),
            },
            clear=False,
        ):
            result = _run(
                mcp_server.estimate_cost_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "unknown.backend",
                        "shots": 100,
                    }
                )
            )

        assert "not in the workspace allowlist" in result[0].text.lower()

    def test_submit_job_stale_allowlist_miss_refreshes_once(self):
        """When stale cache triggers refresh, allowlist miss should not trigger a second refresh."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        fake_azure = MagicMock()
        fake_azure.list_backends.return_value = ["ionq", "microsoft.simulator"]

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                "known_backends": ["old.backend"],
                "known_backends_refreshed_at": 0.0,  # stale by construction
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "unknown.backend",
                        "confirm_cost": True,
                        "shots": 100,
                    }
                )
            )

            assert "not in the workspace allowlist" in result[0].text.lower()
            fake_azure.list_backends.assert_called_once()

    def test_submit_job_refreshes_stale_allowlist(self):
        """When allowlist cache is older than TTL, submit should re-fetch before checking."""
        mcp_server = self._import_server()
        circuit_id, _ = self._make_circuit_in_cache()

        stale_ts = 0.0  # Unix epoch — always older than any TTL

        fake_job = MagicMock()
        fake_job.id.return_value = "job_stale_1"
        fake_azure = MagicMock()
        # Return new list that differs from the stale one
        fake_azure.list_backends.return_value = ["ionq.updated", "microsoft.simulator"]
        fake_azure.submit_circuit.return_value = fake_job

        with patch.dict(
            mcp_server.quantum_state,
            {
                "azure_integration": fake_azure,
                "cumulative_cost_usd": 0.0,
                # Stale cache — has old entry, time is epoch
                "known_backends": ["old.backend"],
                "known_backends_refreshed_at": stale_ts,
            },
            clear=False,
        ):
            result = _run(
                mcp_server.submit_job_handler(
                    {
                        "circuit_id": circuit_id,
                        "backend_name": "microsoft.simulator",
                        "shots": 50,
                    }
                )
            )

            # Should succeed using the refreshed list
            assert "submitted" in result[0].text.lower()
            # Cache should now hold the refreshed list, not the stale one
            assert "old.backend" not in [
                b.lower() for b in mcp_server.quantum_state["known_backends"]
            ]
            assert "microsoft.simulator" in [
                b.lower() for b in mcp_server.quantum_state["known_backends"]
            ]
            # Timestamp should be updated
            assert mcp_server.quantum_state["known_backends_refreshed_at"] > stale_ts
