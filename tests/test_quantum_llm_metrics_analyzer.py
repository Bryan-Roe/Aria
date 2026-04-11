"""Unit tests for scripts/quantum_llm_metrics_analyzer.py."""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "quantum_llm_metrics_analyzer"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = Path(__file__).parent.parent / "scripts" / "quantum_llm_metrics_analyzer.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


qa = _load()


# ---------------------------------------------------------------------------
# load_status
# ---------------------------------------------------------------------------


class TestLoadStatus:
    def test_missing_file_returns_none(self, tmp_path: Path):
        assert qa.load_status(tmp_path / "nonexistent.json") is None

    def test_valid_json_returned(self, tmp_path: Path):
        f = tmp_path / "status.json"
        f.write_text('{"status": "running", "epochs_completed": 5}')
        result = qa.load_status(f)
        assert result == {"status": "running", "epochs_completed": 5}

    def test_corrupt_json_returns_none(self, tmp_path: Path):
        f = tmp_path / "bad.json"
        f.write_text("{ NOT VALID JSON }")
        assert qa.load_status(f) is None

    def test_empty_object_returned(self, tmp_path: Path):
        f = tmp_path / "empty.json"
        f.write_text("{}")
        assert qa.load_status(f) == {}

    def test_returns_dict(self, tmp_path: Path):
        f = tmp_path / "s.json"
        f.write_text('{"x": 1}')
        assert isinstance(qa.load_status(f), dict)


# ---------------------------------------------------------------------------
# extract_metrics
# ---------------------------------------------------------------------------


class TestExtractMetrics:
    def test_all_fields_present(self):
        status = {
            "last_updated": "2024-01-01T00:00:00",
            "status": "completed",
            "epochs_completed": 10,
            "best_loss": 0.05,
            "final_loss": 0.07,
            "inference_ready": True,
            "checkpoint_exists": True,
        }
        result = qa.extract_metrics(status)
        assert result["timestamp"] == "2024-01-01T00:00:00"
        assert result["status"] == "completed"
        assert result["epochs_completed"] == 10
        assert result["best_loss"] == 0.05
        assert result["final_loss"] == 0.07
        assert result["inference_ready"] is True
        assert result["checkpoint_exists"] is True

    def test_defaults_for_missing_fields(self):
        result = qa.extract_metrics({})
        assert result["epochs_completed"] == 0
        assert result["inference_ready"] is False
        assert result["checkpoint_exists"] is False
        assert result["best_loss"] is None
        assert result["final_loss"] is None
        assert result["timestamp"] is None
        assert result["status"] is None

    def test_partial_status(self):
        result = qa.extract_metrics({"status": "running", "epochs_completed": 3})
        assert result["status"] == "running"
        assert result["epochs_completed"] == 3
        assert result["best_loss"] is None

    def test_returns_dict(self):
        assert isinstance(qa.extract_metrics({}), dict)

    def test_exact_keys(self):
        result = qa.extract_metrics({})
        expected = {
            "timestamp",
            "status",
            "epochs_completed",
            "best_loss",
            "final_loss",
            "inference_ready",
            "checkpoint_exists",
        }
        assert set(result.keys()) == expected


# ---------------------------------------------------------------------------
# analyze_metrics
# ---------------------------------------------------------------------------


class TestAnalyzeMetrics:
    def test_empty_list_returns_empty_dict(self):
        assert qa.analyze_metrics([]) == {}

    def test_total_snapshots(self):
        metrics = [{"best_loss": 0.1}, {"best_loss": 0.2}, {"best_loss": 0.3}]
        result = qa.analyze_metrics(metrics)
        assert result["total_snapshots"] == 3

    def test_inference_ready_count(self):
        metrics = [
            {"inference_ready": True},
            {"inference_ready": False},
            {"inference_ready": True},
        ]
        result = qa.analyze_metrics(metrics)
        assert result["inference_ready_count"] == 2

    def test_checkpoint_count(self):
        metrics = [
            {"checkpoint_exists": True},
            {"checkpoint_exists": False},
        ]
        result = qa.analyze_metrics(metrics)
        assert result["checkpoint_count"] == 1

    def test_best_loss_stats(self):
        metrics = [
            {"best_loss": 0.1},
            {"best_loss": 0.3},
            {"best_loss": 0.2},
        ]
        result = qa.analyze_metrics(metrics)
        assert "best_loss" in result
        bl = result["best_loss"]
        assert bl["min"] == pytest.approx(0.1)
        assert bl["max"] == pytest.approx(0.3)
        assert bl["mean"] == pytest.approx(0.2)
        assert bl["count"] == 3

    def test_best_loss_stdev_with_multiple_values(self):
        metrics = [{"best_loss": 0.1}, {"best_loss": 0.3}]
        result = qa.analyze_metrics(metrics)
        assert "stdev" in result["best_loss"]

    def test_best_loss_no_stdev_single_value(self):
        metrics = [{"best_loss": 0.1}]
        result = qa.analyze_metrics(metrics)
        assert "stdev" not in result["best_loss"]

    def test_final_loss_stats(self):
        metrics = [{"final_loss": 0.4}, {"final_loss": 0.2}]
        result = qa.analyze_metrics(metrics)
        assert "final_loss" in result
        fl = result["final_loss"]
        assert fl["min"] == pytest.approx(0.2)
        assert fl["max"] == pytest.approx(0.4)

    def test_epoch_stats(self):
        metrics = [
            {"epochs_completed": 5},
            {"epochs_completed": 10},
            {"epochs_completed": 15},
        ]
        result = qa.analyze_metrics(metrics)
        assert "epochs" in result
        ep = result["epochs"]
        assert ep["max"] == 15
        assert ep["current"] == 15  # last item
        assert ep["mean"] == pytest.approx(10.0)

    def test_trend_detected_with_two_final_losses(self):
        metrics = [{"final_loss": 0.8}, {"final_loss": 0.4}]
        result = qa.analyze_metrics(metrics)
        assert "trend" in result
        tr = result["trend"]
        assert tr["first_loss"] == pytest.approx(0.8)
        assert tr["latest_loss"] == pytest.approx(0.4)
        assert tr["improvement"] == pytest.approx(0.4)
        assert tr["improvement_percentage"] == pytest.approx(50.0)

    def test_trend_negative_improvement(self):
        metrics = [{"final_loss": 0.3}, {"final_loss": 0.6}]
        result = qa.analyze_metrics(metrics)
        tr = result["trend"]
        assert tr["improvement"] < 0

    def test_no_trend_with_single_final_loss(self):
        metrics = [{"final_loss": 0.5}]
        result = qa.analyze_metrics(metrics)
        assert "trend" not in result

    def test_none_values_excluded_from_loss_stats(self):
        metrics = [{"best_loss": None}, {"best_loss": 0.2}]
        result = qa.analyze_metrics(metrics)
        assert result["best_loss"]["count"] == 1
        assert result["best_loss"]["min"] == pytest.approx(0.2)

    def test_zero_epochs_excluded_from_epoch_stats(self):
        # epochs_completed=0 is falsy, excluded from analysis
        metrics = [{"epochs_completed": 0}, {"epochs_completed": 5}]
        result = qa.analyze_metrics(metrics)
        assert result["epochs"]["max"] == 5

    def test_returns_dict(self):
        assert isinstance(qa.analyze_metrics([{"best_loss": 0.1}]), dict)


# ---------------------------------------------------------------------------
# format_analysis_report
# ---------------------------------------------------------------------------


class TestFormatAnalysisReport:
    def _make_full_analysis(self):
        return {
            "total_snapshots": 3,
            "inference_ready_count": 2,
            "checkpoint_count": 1,
            "best_loss": {
                "min": 0.05,
                "max": 0.15,
                "mean": 0.10,
                "count": 3,
                "stdev": 0.05,
            },
            "final_loss": {
                "min": 0.06,
                "max": 0.18,
                "mean": 0.12,
                "count": 3,
                "stdev": 0.06,
            },
            "epochs": {"current": 30, "max": 30, "mean": 20.0},
            "trend": {
                "first_loss": 0.18,
                "latest_loss": 0.06,
                "improvement": 0.12,
                "improvement_percentage": 66.67,
            },
        }

    def test_returns_string(self):
        assert isinstance(qa.format_analysis_report({}), str)

    def test_contains_header(self):
        result = qa.format_analysis_report({})
        assert "Quantum LLM" in result

    def test_contains_snapshot_count(self):
        result = qa.format_analysis_report(self._make_full_analysis())
        assert "3" in result

    def test_contains_best_loss_values(self):
        result = qa.format_analysis_report(self._make_full_analysis())
        assert "0.050000" in result

    def test_contains_final_loss_section(self):
        result = qa.format_analysis_report(self._make_full_analysis())
        assert "Final Loss" in result

    def test_contains_epoch_section(self):
        result = qa.format_analysis_report(self._make_full_analysis())
        assert "Epoch" in result

    def test_contains_trend_section(self):
        result = qa.format_analysis_report(self._make_full_analysis())
        assert "Trend" in result or "trend" in result.lower()

    def test_improvement_shows_checkmark(self):
        analysis = self._make_full_analysis()
        result = qa.format_analysis_report(analysis)
        assert "✓" in result

    def test_negative_improvement_shows_x(self):
        analysis = self._make_full_analysis()
        analysis["trend"]["improvement"] = -0.05
        result = qa.format_analysis_report(analysis)
        assert "✗" in result

    def test_empty_analysis_no_crash(self):
        result = qa.format_analysis_report({})
        assert len(result) > 0
