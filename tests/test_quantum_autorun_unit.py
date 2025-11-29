"""Unit tests for Quantum AutoRun orchestrator components."""
import json
from pathlib import Path
from unittest.mock import patch

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from quantum_autorun import (  # type: ignore
    QJob,
    read_yaml,
    load_jobs,
    build_command,
    validate_job,
)


class TestQJobDataclass:
    def test_minimal_job(self):
        j = QJob(name="test")
        assert j.name == "test"
        assert j.mode == "train_custom_dataset"
        assert j.enabled is True
        assert j.preset is None
        assert j.csv is None
        assert j.extra_args == []
        assert j.azure_backend is None
        assert j.azure_confirm_cost is False

    def test_full_job(self):
        j = QJob(
            name="full",
            preset="heart",
            n_qubits=4,
            epochs=1,
            batch_size=16,
            learning_rate=0.001,
            test_size=0.2,
            extra_args=["--verbose"],
        )
        assert j.preset == "heart"
        assert j.n_qubits == 4
        assert j.epochs == 1
        assert j.batch_size == 16
        assert j.learning_rate == 0.001
        assert j.test_size == 0.2
        assert j.extra_args == ["--verbose"]

    def test_azure_job(self):
        j = QJob(
            name="azure_test",
            mode="azure_hardware",
            azure_backend="ionq.simulator",
            azure_shots=100,
            n_qubits=3,
            azure_confirm_cost=False,
        )
        assert j.mode == "azure_hardware"
        assert j.azure_backend == "ionq.simulator"
        assert j.azure_shots == 100
        assert j.azure_confirm_cost is False


class TestYAMLParsing:
    def test_read_yaml(self, tmp_path):
        cfg = tmp_path / "qa.yaml"
        cfg.write_text("jobs: []\n", encoding="utf-8")
        data = read_yaml(cfg)
        assert data == {"jobs": []}

    def test_load_jobs(self, tmp_path):
        cfg = tmp_path / "quantum_autorun.yaml"
        cfg.write_text(
            """
jobs:
  - name: a
    preset: heart
  - name: b
    csv: datasets/quantum/banknote.csv
    label_col: class
    drop_cols: "col1,col2"
    epochs: 1
    batch_size: 8
""",
            encoding="utf-8",
        )
        jobs = load_jobs(cfg)
        assert len(jobs) == 2
        assert jobs[0].preset == "heart"
        assert jobs[1].csv.endswith("banknote.csv")
        assert jobs[1].label_col == "class"
        assert jobs[1].drop_cols == "col1,col2"
        assert jobs[1].epochs == 1
        assert jobs[1].batch_size == 8


class TestCommandBuilder:
    def test_command_with_preset(self):
        j = QJob(name="t", preset="heart", epochs=1, n_qubits=4)
        cmd = build_command(j)
        assert len(cmd) >= 2
        assert cmd[0].endswith("python.exe") or cmd[0].endswith("python")
        assert "train_custom_dataset.py" in cmd[1]
        assert "--preset" in cmd
        assert "heart" in cmd
        assert "--epochs" in cmd
        assert "1" in cmd

    def test_command_with_csv_and_fields(self):
        j = QJob(name="t", csv="datasets/quantum/banknote.csv", label_col="class", drop_cols="c1,c2")
        cmd = build_command(j)
        # '--csv' flag present and path argument contains the filename
        assert "--csv" in cmd
        assert any(arg.endswith("banknote.csv") for arg in cmd)
        assert "--label-col" in cmd and "class" in cmd
        assert "--drop-cols" in cmd and "c1,c2" in cmd

    def test_azure_command_simulator(self):
        j = QJob(
            name="azure_sim",
            mode="azure_hardware",
            azure_backend="ionq.simulator",
            azure_shots=100,
            n_qubits=3,
        )
        cmd = build_command(j)
        assert "deploy_to_azure_quantum.py" in cmd[1]
        assert "--backend" in cmd and "ionq.simulator" in cmd
        assert "--shots" in cmd and "100" in cmd
        assert "--n-qubits" in cmd and "3" in cmd

    def test_azure_command_qpu(self):
        j = QJob(
            name="azure_qpu",
            mode="azure_hardware",
            azure_backend="ionq.qpu",
            azure_shots=50,
            azure_confirm_cost=True,
            extra_args=["--circuit-file", "test.qasm"],
        )
        cmd = build_command(j)
        assert "deploy_to_azure_quantum.py" in cmd[1]
        assert "--backend" in cmd and "ionq.qpu" in cmd
        assert "--shots" in cmd and "50" in cmd
        assert "--circuit-file" in cmd and "test.qasm" in cmd


class TestValidation:
    @patch("quantum_autorun.TRAIN_SCRIPT", Path("/fake/train_custom_dataset.py"))
    def test_missing_train_script(self):
        from quantum_autorun import validate_job  # type: ignore

        j = QJob(name="t", preset="heart")
        res = validate_job(j)
        assert res["status"] == "missing"
        assert any("train_custom_dataset.py" in m for m in res.get("missing", []))

    def test_invalid_preset(self):
        j = QJob(name="t", preset="not_a_preset")
        res = validate_job(j)
        assert res["status"] == "missing"
        assert any("Unknown preset" in m for m in res.get("missing", []))

    def test_missing_csv_path(self, tmp_path):
        j = QJob(name="t", csv=str(tmp_path / "nope.csv"))
        res = validate_job(j)
        # Should report missing file
        assert res["status"] == "missing" or "missing" in res

    @patch("quantum_autorun.AZURE_SUBMIT_SCRIPT", Path("/fake/deploy_to_azure_quantum.py"))
    def test_missing_azure_script(self):
        from quantum_autorun import validate_job  # type: ignore

        j = QJob(name="t", mode="azure_hardware", azure_backend="ionq.simulator")
        res = validate_job(j)
        assert res["status"] == "missing"
        assert any("deploy_to_azure_quantum.py" in m for m in res.get("missing", []))

    def test_azure_qpu_without_cost_confirm(self):
        j = QJob(
            name="t",
            mode="azure_hardware",
            azure_backend="ionq.qpu",
            azure_confirm_cost=False,
        )
        res = validate_job(j)
        # Should fail validation due to missing cost confirmation
        assert res["status"] == "missing"
        assert any("azure_confirm_cost" in m for m in res.get("missing", []))

    def test_azure_simulator_no_cost_confirm_needed(self):
        j = QJob(
            name="t",
            mode="azure_hardware",
            azure_backend="ionq.simulator",
            azure_confirm_cost=False,
        )
        # Simulator should pass even without cost confirmation
        # (will fail on missing script in real test, but logic is correct)
        res = validate_job(j)
        # Either validated or missing script, but not cost error
        if res["status"] == "missing":
            assert not any("azure_confirm_cost" in m for m in res.get("missing", []))


class TestStatusJSON:
    def test_collect_status_structure(self, tmp_path):
        from quantum_autorun import collect_status  # type: ignore

        results = [
            {"name": "a", "status": "validated"},
            {"name": "b", "status": "validated"},
        ]
        with patch("quantum_autorun.DATA_OUT", Path(tmp_path)):
            status = collect_status(results)
        assert "generated_at" in status
        assert "jobs" in status and len(status["jobs"]) == 2
