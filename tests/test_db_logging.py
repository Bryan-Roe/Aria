"""Tests for shared/db_logging.py — fault-tolerant DB logging wrappers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

import shared.db_logging as dbl

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_warned():
    """Reset the module-level _WARNED flag between tests."""
    dbl._WARNED = False


# ---------------------------------------------------------------------------
# _warn_once
# ---------------------------------------------------------------------------


class TestWarnOnce:
    def setup_method(self):
        _clear_warned()

    def test_first_call_sets_warned(self, capsys):
        dbl._warn_once("first warning")
        captured = capsys.readouterr()
        assert "first warning" in captured.out
        assert dbl._WARNED is True

    def test_second_call_suppressed(self, capsys):
        dbl._warn_once("first")
        dbl._warn_once("second")
        captured = capsys.readouterr()
        assert "second" not in captured.out


# ---------------------------------------------------------------------------
# _get_conn (no QAI_DB_CONN configured)
# ---------------------------------------------------------------------------


class TestGetConn:
    def test_returns_none_without_conn_str(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            conn = dbl._get_conn()
        assert conn is None


# ---------------------------------------------------------------------------
# log_chat_message_safe (no DB)
# ---------------------------------------------------------------------------


class TestLogChatMessageSafe:
    def test_skipped_without_db(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            result = dbl.log_chat_message_safe(
                session_id="sess-1",
                provider="local",
                model=None,
                role="user",
                content="Hello",
            )
        assert result["success"] is False
        assert result.get("skipped") is True

    def test_returns_dict(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            result = dbl.log_chat_message_safe(
                session_id=None,
                provider="local",
                model=None,
                role="assistant",
                content="Hi there",
            )
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# log_quantum_run_safe (no DB)
# ---------------------------------------------------------------------------


class TestLogQuantumRunSafe:
    def test_skipped_without_db(self):
        class MockJob:
            name = "test-job"
            mode = "local"
            azure_backend = "aer_simulator"
            n_qubits = 4
            learning_rate = 0.001
            epochs = 2
            batch_size = 16
            azure_shots = None

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("QAI_DB_CONN", None)
            result = dbl.log_quantum_run_safe(
                job=MockJob(),
                result={"status": "succeeded", "duration_sec": 1.5},
                dataset_name="test_dataset",
                log_path="/tmp/test.log",
            )
        assert result["success"] is False
        assert result.get("skipped") is True


# ---------------------------------------------------------------------------
# _parse_quantum_summary
# ---------------------------------------------------------------------------


class TestParseQuantumSummary:
    def test_missing_file_returns_empty(self):
        # Point to a non-existent path via monkeypatching _REPO_ROOT
        with patch.object(dbl, "REPO_ROOT", Path("/nonexistent")):
            result = dbl._parse_quantum_summary()
        assert result == {}

    def test_parses_valid_json(self, tmp_path):
        # Create a summary JSON in expected location
        summary_dir = tmp_path / "ai-projects" / "quantum-ml" / "results"
        summary_dir.mkdir(parents=True)
        summary_file = summary_dir / "custom_training_summary.json"
        summary_data = {
            "metrics": {
                "train_loss_last": 0.15,
                "val_loss_last": 0.18,
                "val_acc_last": 0.92,
                "val_acc_best": 0.95,
            }
        }
        summary_file.write_text(json.dumps(summary_data))

        with patch.object(dbl, "REPO_ROOT", tmp_path):
            result = dbl._parse_quantum_summary()

        assert result["train_loss_last"] == pytest.approx(0.15)
        assert result["val_acc_best"] == pytest.approx(0.95)

    def test_handles_malformed_json(self, tmp_path):
        summary_dir = tmp_path / "ai-projects" / "quantum-ml" / "results"
        summary_dir.mkdir(parents=True)
        (summary_dir / "custom_training_summary.json").write_text("not json!!!")

        with patch.object(dbl, "REPO_ROOT", tmp_path):
            _clear_warned()
            result = dbl._parse_quantum_summary()
        assert result == {}

    def test_handles_missing_metrics_key(self, tmp_path):
        summary_dir = tmp_path / "ai-projects" / "quantum-ml" / "results"
        summary_dir.mkdir(parents=True)
        (summary_dir / "custom_training_summary.json").write_text(
            json.dumps({"other_key": 1})
        )
        with patch.object(dbl, "REPO_ROOT", tmp_path):
            result = dbl._parse_quantum_summary()
        # No 'metrics' key → all values will be None (from .get())
        assert "train_loss_last" in result
        assert result["train_loss_last"] is None
