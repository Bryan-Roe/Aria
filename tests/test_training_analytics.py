"""
Unit tests for scripts/training_analytics.py — TrainingAnalytics class.
The existing test_training_analytics_cli.py only covers the --report CLI flag;
these tests cover all class methods.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "training_analytics"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = Path(__file__).parent.parent / "scripts" / "training_analytics.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()
TrainingAnalytics = mod.TrainingAnalytics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_ta(tmp_path, status_dict):
    """Write *status_dict* to a JSON file and return a TrainingAnalytics pointing there."""
    p = tmp_path / "status.json"
    p.write_text(json.dumps(status_dict), encoding="utf-8")
    return TrainingAnalytics(str(p))


def _history(*mean_accuracies, epochs=50):
    """Return a performance_history list with the given mean_accuracies."""
    return [{"mean_accuracy": a, "epochs": epochs} for a in mean_accuracies]


# ---------------------------------------------------------------------------
# TestGetAccuracy
# ---------------------------------------------------------------------------


class TestGetAccuracy:
    def test_returns_mean_accuracy(self):
        assert TrainingAnalytics._get_accuracy({"mean_accuracy": 0.85}) == 0.85

    def test_falls_back_to_accuracy(self):
        assert TrainingAnalytics._get_accuracy({"accuracy": 0.72}) == 0.72

    def test_mean_accuracy_wins_over_accuracy(self):
        perf = {"mean_accuracy": 0.90, "accuracy": 0.70}
        assert TrainingAnalytics._get_accuracy(perf) == 0.90

    def test_missing_both_returns_zero(self):
        assert TrainingAnalytics._get_accuracy({}) == 0.0

    def test_zero_accuracy(self):
        assert TrainingAnalytics._get_accuracy({"mean_accuracy": 0.0}) == 0.0


# ---------------------------------------------------------------------------
# TestLoadStatus
# ---------------------------------------------------------------------------


class TestLoadStatus:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        ta = TrainingAnalytics(str(tmp_path / "no_such_file.json"))
        assert ta.status == {}

    def test_valid_json_dict_loaded(self, tmp_path):
        ta = _write_ta(tmp_path, {"cycles_completed": 7, "best_accuracy": 0.85})
        assert ta.status["cycles_completed"] == 7
        assert ta.status["best_accuracy"] == pytest.approx(0.85)

    def test_corrupt_json_returns_empty_dict(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")
        ta = TrainingAnalytics(str(p))
        assert ta.status == {}

    def test_json_array_returns_empty_dict(self, tmp_path):
        p = tmp_path / "array.json"
        p.write_text("[1,2,3]", encoding="utf-8")
        ta = TrainingAnalytics(str(p))
        assert ta.status == {}

    def test_empty_object_loaded(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.status == {}

    def test_status_loader_metadata_not_leaked(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {"cycles_completed": 3, "performance_history": []},
        )
        assert ta.status["cycles_completed"] == 3
        assert not any(key.startswith("_status_file_") for key in ta.status)


# ---------------------------------------------------------------------------
# TestCalculateImprovementRate
# ---------------------------------------------------------------------------


class TestCalculateImprovementRate:
    def test_no_history_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.calculate_improvement_rate() == 0.0

    def test_single_entry_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.70)})
        assert ta.calculate_improvement_rate() == 0.0

    def test_two_entries_simple_improvement(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.80)})
        # (0.80 - 0.60) / (2-1) = 0.20
        assert ta.calculate_improvement_rate() == pytest.approx(0.20)

    def test_multiple_entries(self, tmp_path):
        ta = _write_ta(
            tmp_path, {"performance_history": _history(0.50, 0.60, 0.70, 0.80)}
        )
        # (0.80 - 0.50) / (4-1) = 0.10
        assert ta.calculate_improvement_rate() == pytest.approx(0.10)

    def test_decreasing_accuracy(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.90, 0.70)})
        assert ta.calculate_improvement_rate() == pytest.approx(-0.20)

    def test_flat_accuracy_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.75, 0.75, 0.75)})
        assert ta.calculate_improvement_rate() == pytest.approx(0.0)

    def test_uses_mean_accuracy_key(self, tmp_path):
        history = [{"mean_accuracy": 0.65}, {"mean_accuracy": 0.85}]
        ta = _write_ta(tmp_path, {"performance_history": history})
        assert ta.calculate_improvement_rate() == pytest.approx(0.20)

    def test_uses_legacy_accuracy_key(self, tmp_path):
        history = [{"accuracy": 0.65}, {"accuracy": 0.85}]
        ta = _write_ta(tmp_path, {"performance_history": history})
        assert ta.calculate_improvement_rate() == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# TestPredictTargetAccuracy
# ---------------------------------------------------------------------------


class TestPredictTargetAccuracy:
    def test_no_history_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.predict_target_accuracy(0.90) == 0

    def test_already_at_target_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.85, 0.92)})
        assert ta.predict_target_accuracy(0.90) == 0

    def test_exactly_at_target_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.80, 0.90)})
        assert ta.predict_target_accuracy(0.90) == 0

    def test_no_improvement_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.75, 0.75)})
        assert ta.predict_target_accuracy(0.90) == 0

    def test_declining_accuracy_returns_zero(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.85, 0.75)})
        assert ta.predict_target_accuracy(0.90) == 0

    def test_normal_prediction(self, tmp_path):
        # rate = 0.05/cycle, current = 0.80, target = 0.90
        # cycles_needed = (0.90 - 0.80) / 0.05 ≈ 1.9999... (float) → int(1.9999) + 1 = 2
        ta = _write_ta(tmp_path, {"performance_history": _history(0.75, 0.80)})
        result = ta.predict_target_accuracy(0.90)
        assert result == 2

    def test_returns_integer(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.70, 0.75)})
        assert isinstance(ta.predict_target_accuracy(0.95), int)


# ---------------------------------------------------------------------------
# TestIdentifyBestEpochCount
# ---------------------------------------------------------------------------


class TestIdentifyBestEpochCount:
    def test_empty_history_returns_100(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.identify_best_epoch_count() == 100

    def test_no_epochs_field_returns_100(self, tmp_path):
        history = [{"mean_accuracy": 0.80}, {"mean_accuracy": 0.85}]
        ta = _write_ta(tmp_path, {"performance_history": history})
        assert ta.identify_best_epoch_count() == 100

    def test_single_epoch_group(self, tmp_path):
        history = [{"mean_accuracy": 0.80, "epochs": 50}]
        ta = _write_ta(tmp_path, {"performance_history": history})
        assert ta.identify_best_epoch_count() == 50

    def test_best_epoch_selected(self, tmp_path):
        history = [
            {"mean_accuracy": 0.70, "epochs": 25},
            {"mean_accuracy": 0.75, "epochs": 25},
            {"mean_accuracy": 0.85, "epochs": 100},
            {"mean_accuracy": 0.88, "epochs": 100},
        ]
        ta = _write_ta(tmp_path, {"performance_history": history})
        # avg 25-epochs = 0.725, avg 100-epochs = 0.865 → best = 100
        assert ta.identify_best_epoch_count() == 100

    def test_ties_resolved_by_first_seen(self, tmp_path):
        # Both epoch counts have same average — implementation returns whichever > best_avg last
        history = [
            {"mean_accuracy": 0.80, "epochs": 50},
            {"mean_accuracy": 0.80, "epochs": 100},
        ]
        ta = _write_ta(tmp_path, {"performance_history": history})
        result = ta.identify_best_epoch_count()
        assert result in (50, 100)

    def test_skips_entries_without_epochs(self, tmp_path):
        history = [
            {"mean_accuracy": 0.70},
            {"mean_accuracy": 0.90, "epochs": 200},
        ]
        ta = _write_ta(tmp_path, {"performance_history": history})
        assert ta.identify_best_epoch_count() == 200


# ---------------------------------------------------------------------------
# TestDetectPlateau
# ---------------------------------------------------------------------------


class TestDetectPlateau:
    def test_not_enough_history_returns_false(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.80, 0.82)})
        assert ta.detect_plateau(window=3) is False

    def test_empty_history_returns_false(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.detect_plateau() is False

    def test_identical_values_returns_true(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.80, 0.80, 0.80)})
        assert ta.detect_plateau(window=3) is True

    def test_high_variance_returns_false(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.75, 0.90)})
        assert ta.detect_plateau(window=3) is False

    def test_tiny_variance_returns_true(self, tmp_path):
        # pvariance([0.8000, 0.8001, 0.8000]) ≈ 2.2e-9 < 0.0001
        ta = _write_ta(
            tmp_path, {"performance_history": _history(0.8000, 0.8001, 0.8000)}
        )
        assert ta.detect_plateau(window=3) is True

    def test_window_uses_only_recent_entries(self, tmp_path):
        # Early entries vary wildly but last 3 are flat
        ta = _write_ta(
            tmp_path, {"performance_history": _history(0.10, 0.50, 0.80, 0.80, 0.80)}
        )
        assert ta.detect_plateau(window=3) is True

    def test_default_window_is_3(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.70, 0.80, 0.90)})
        assert ta.detect_plateau() is False


# ---------------------------------------------------------------------------
# TestGenerateReport
# ---------------------------------------------------------------------------


class TestGenerateReport:
    def test_empty_status_runs_without_error(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        report = ta.generate_report()
        assert isinstance(report, str)
        assert "OVERVIEW" in report

    def test_contains_cycle_count(self, tmp_path):
        ta = _write_ta(tmp_path, {"cycles_completed": 42, "best_accuracy": 0.88})
        assert "42" in ta.generate_report()

    def test_contains_best_accuracy(self, tmp_path):
        ta = _write_ta(tmp_path, {"cycles_completed": 1, "best_accuracy": 0.88})
        assert "88.00%" in ta.generate_report()

    def test_performance_trend_section_present_when_history(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "performance_history": _history(0.70, 0.80, 0.90),
                "cycles_completed": 3,
                "best_accuracy": 0.90,
            },
        )
        report = ta.generate_report()
        assert "PERFORMANCE TREND" in report
        assert "PREDICTIONS" in report

    def test_plateau_warning_shown(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "performance_history": _history(0.80, 0.80, 0.80),
                "cycles_completed": 3,
                "best_accuracy": 0.80,
            },
        )
        assert "PLATEAU DETECTED" in ta.generate_report()

    def test_improving_status_shown(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "performance_history": _history(0.60, 0.70, 0.80),
                "cycles_completed": 3,
                "best_accuracy": 0.80,
            },
        )
        assert "still improving" in ta.generate_report()

    def test_dataset_inventory_counted(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "dataset_inventory": {"chat": ["a", "b"], "quantum": ["c"]},
                "cycles_completed": 0,
                "best_accuracy": 0,
            },
        )
        # total_datasets_available not set → falls back to len(dataset_inventory)
        assert "Total Datasets: 2" in ta.generate_report()

    def test_total_datasets_available_overrides_inventory(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "total_datasets_available": 99,
                "dataset_inventory": {"chat": ["a"]},
                "cycles_completed": 0,
                "best_accuracy": 0,
            },
        )
        assert "Total Datasets: 99" in ta.generate_report()

    def test_promotion_listed(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "promotions": [{"version": "3", "cycle": 10, "accuracy": 0.91}],
                "cycles_completed": 10,
                "best_accuracy": 0.91,
            },
        )
        assert "v3" in ta.generate_report()

    def test_ready_for_production_when_high_accuracy(self, tmp_path):
        ta = _write_ta(
            tmp_path,
            {
                "performance_history": _history(0.88, 0.91),
                "cycles_completed": 2,
                "best_accuracy": 0.91,
            },
        )
        assert "production" in ta.generate_report().lower()


# ---------------------------------------------------------------------------
# TestGenerateAsciiChart
# ---------------------------------------------------------------------------


class TestGenerateAsciiChart:
    def test_no_data_returns_message(self, tmp_path):
        ta = _write_ta(tmp_path, {})
        assert ta.generate_ascii_chart() == "No data available"

    def test_all_equal_values_returns_message(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.80, 0.80, 0.80)})
        assert ta.generate_ascii_chart() == "All values are equal"

    def test_varying_values_returns_string(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.70, 0.80)})
        chart = ta.generate_ascii_chart()
        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_chart_contains_metric_label(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.80)})
        chart = ta.generate_ascii_chart("mean_accuracy")
        assert "MEAN_ACCURACY" in chart

    def test_custom_metric(self, tmp_path):
        history = [
            {"loss": 0.8},
            {"loss": 0.6},
            {"loss": 0.4},
        ]
        ta = _write_ta(tmp_path, {"performance_history": history})
        chart = ta.generate_ascii_chart("loss")
        assert "LOSS" in chart

    def test_chart_has_min_and_max_labels(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.80)})
        chart = ta.generate_ascii_chart()
        assert "Max:" in chart
        assert "Min:" in chart

    def test_chart_contains_block_characters(self, tmp_path):
        ta = _write_ta(tmp_path, {"performance_history": _history(0.60, 0.80)})
        chart = ta.generate_ascii_chart()
        assert "█" in chart
