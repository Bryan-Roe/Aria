"""Tests for quantum/src/quantum_quick_start.py — local simulation only."""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
QUANTUM_SRC = REPO_ROOT / "quantum" / "src"

if str(QUANTUM_SRC) not in sys.path:
    sys.path.insert(0, str(QUANTUM_SRC))

_qs = importlib.import_module("quantum_quick_start")
build_parser = _qs.build_parser
main = _qs.main
run_aer_bell_state = _qs.run_aer_bell_state
run_aer_ghz = _qs.run_aer_ghz
train_local_classifier = _qs.train_local_classifier

# ---------------------------------------------------------------------------
# Aer circuit tests
# ---------------------------------------------------------------------------


class TestAerBellState:
    def test_returns_counts(self):
        result = run_aer_bell_state(shots=100)
        assert result["success"] is True
        assert result["circuit"] == "bell_state"
        assert isinstance(result["counts"], dict)
        total = sum(result["counts"].values())
        assert total == 100

    def test_entanglement_correlation(self):
        """Only |00> and |11> should appear (modulo noise)."""
        result = run_aer_bell_state(shots=500)
        for state in result["counts"]:
            assert state in ("00", "11"), f"unexpected state {state}"


class TestAerGHZ:
    def test_3_qubit(self):
        result = run_aer_ghz(n_qubits=3, shots=200)
        assert result["n_qubits"] == 3
        assert result["success"] is True

    def test_boundary_2(self):
        result = run_aer_ghz(n_qubits=2, shots=100)
        assert result["success"]

    def test_rejects_too_many_qubits(self):
        with pytest.raises(ValueError, match="between 2 and 10"):
            run_aer_ghz(n_qubits=11)

    def test_rejects_too_few_qubits(self):
        with pytest.raises(ValueError, match="between 2 and 10"):
            run_aer_ghz(n_qubits=1)


# ---------------------------------------------------------------------------
# Classifier training (very small to keep CI fast)
# ---------------------------------------------------------------------------

class TestTrainLocalClassifier:
    @pytest.mark.slow
    def test_banknote_trains(self):
        """Full training loop on banknote, 1 epoch, 4 qubits."""
        result = train_local_classifier(
            dataset="banknote",
            n_qubits=4,
            n_layers=1,
            epochs=1,
            batch_size=32,
            learning_rate=0.01,
        )
        assert "final_val_acc" in result
        assert 0.0 <= result["final_val_acc"] <= 1.0
        assert result["elapsed_seconds"] > 0

    @pytest.mark.slow
    def test_heart_trains(self):
        result = train_local_classifier(
            dataset="heart",
            n_qubits=4,
            n_layers=1,
            epochs=1,
            batch_size=32,
        )
        assert "history" in result
        assert len(result["history"]["train_loss"]) == 1


# ---------------------------------------------------------------------------
# CLI / main()
# ---------------------------------------------------------------------------

class TestCLI:
    def test_parser_defaults(self):
        p = build_parser()
        args = p.parse_args([])
        assert args.dataset == "banknote"
        assert args.n_qubits == 4
        assert args.dry_run is False

    def test_parser_dry_run(self):
        p = build_parser()
        args = p.parse_args(["--dry-run", "--no-save"])
        assert args.dry_run is True
        assert args.no_save is True

    def test_main_dry_run(self):
        """Dry-run should succeed (Aer circuits only, no classifier)."""
        result = main(["--dry-run", "--no-save"])
        assert result["mode"] == "dry-run"
        assert "bell_state" in result
        assert "ghz_state" in result
        assert "classifier" not in result

    @pytest.mark.slow
    def test_main_full(self, tmp_path):
        """Full run with results saved to a temp dir."""
        with patch("quantum_quick_start.DATA_OUT", tmp_path):
            result = main(
                [
                    "--epochs",
                    "1",
                    "--batch-size",
                    "32",
                    "--dataset",
                    "banknote",
                ]
            )
        assert result["mode"] == "full"
        assert "classifier" in result
        # Check a JSON was written
        jsons = list(tmp_path.glob("*.json"))
        assert len(jsons) == 1
        data = json.loads(jsons[0].read_text())
        assert "classifier" in data
