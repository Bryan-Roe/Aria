"""
Unit tests for scripts/monitor_autonomous_training.py — TrainingMonitor class.
"""

import importlib.util
import json
import sys
from io import StringIO
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "monitor_autonomous_training"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = Path(__file__).parent.parent / "scripts" / \
        "monitor_autonomous_training.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()
TrainingMonitor = mod.TrainingMonitor
Colors = mod.Colors

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _monitor(tmp_path, status=None, heartbeat=None, log_lines=None):
    """Create a TrainingMonitor pointed at temp files, optionally pre-populated."""
    sf = tmp_path / "status.json"
    lf = tmp_path / "training.log"
    hf = tmp_path / "autonomous_training_heartbeat.json"

    if status is not None:
        sf.write_text(json.dumps(status), encoding="utf-8")
    if heartbeat is not None:
        hf.write_text(json.dumps(heartbeat), encoding="utf-8")
    if log_lines is not None:
        lf.write_text("\n".join(log_lines), encoding="utf-8")

    m = TrainingMonitor(str(sf), str(lf))
    # Override heartbeat path to match tmp_path
    m.heartbeat_file = hf
    return m


# ---------------------------------------------------------------------------
# TestColors
# ---------------------------------------------------------------------------

class TestColors:
    def test_has_escape_codes(self):
        assert "\033[" in Colors.HEADER
        assert "\033[" in Colors.OKGREEN
        assert "\033[" in Colors.FAIL
        assert "\033[" in Colors.ENDC

    def test_end_code_resets(self):
        assert Colors.ENDC == "\033[0m"

    def test_bold_code(self):
        assert Colors.BOLD == "\033[1m"

    def test_all_attributes_present(self):
        for attr in ("HEADER", "OKBLUE", "OKCYAN", "OKGREEN",
                     "WARNING", "FAIL", "ENDC", "BOLD", "UNDERLINE"):
            assert hasattr(Colors, attr), f"Missing Colors.{attr}"


# ---------------------------------------------------------------------------
# TestFormatDuration
# ---------------------------------------------------------------------------

class TestFormatDuration:
    def test_under_60_seconds(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(30.0) == "30.0s"

    def test_zero_seconds(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(0.0) == "0.0s"

    def test_59_seconds(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(59.9) == "59.9s"

    def test_exactly_60_seconds_is_minutes(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(60.0) == "1.0m"

    def test_90_seconds(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(90.0) == "1.5m"

    def test_3599_seconds_is_minutes(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(3599.0).endswith("m")

    def test_exactly_1_hour(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(3600.0) == "1.0h"

    def test_2_hours(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(7200.0) == "2.0h"

    def test_fractional_hours(self, tmp_path):
        m = _monitor(tmp_path)
        assert m.format_duration(5400.0) == "1.5h"


# ---------------------------------------------------------------------------
# TestFormatPercentage
# ---------------------------------------------------------------------------

class TestFormatPercentage:
    def _strip_colors(self, s: str) -> str:
        """Strip ANSI color codes."""
        import re
        return re.sub(r'\033\[[0-9;]+m', '', s)

    def test_high_accuracy_green(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.92)
        assert Colors.OKGREEN in result
        assert "92.00%" in self._strip_colors(result)

    def test_ninety_percent_green(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.90)
        assert Colors.OKGREEN in result

    def test_medium_accuracy_cyan(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.80)
        assert Colors.OKCYAN in result
        assert "80.00%" in self._strip_colors(result)

    def test_seventy_five_percent_cyan(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.75)
        assert Colors.OKCYAN in result

    def test_moderate_accuracy_warning(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.65)
        assert Colors.WARNING in result
        assert "65.00%" in self._strip_colors(result)

    def test_sixty_percent_warning(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.60)
        assert Colors.WARNING in result

    def test_low_accuracy_fail(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.50)
        assert Colors.FAIL in result
        assert "50.00%" in self._strip_colors(result)

    def test_zero_accuracy_fail(self, tmp_path):
        m = _monitor(tmp_path)
        result = m.format_percentage(0.0)
        assert Colors.FAIL in result

    def test_result_contains_percent_sign(self, tmp_path):
        m = _monitor(tmp_path)
        result = self._strip_colors(m.format_percentage(0.70))
        assert "%" in result


# ---------------------------------------------------------------------------
# TestLoadStatus
# ---------------------------------------------------------------------------

class TestLoadStatus:
    def test_missing_file_returns_none(self, tmp_path):
        m = _monitor(tmp_path)  # no status written
        assert m.load_status() is None

    def test_valid_status_loaded(self, tmp_path):
        data = {"cycles_completed": 5, "best_accuracy": 0.85}
        m = _monitor(tmp_path, status=data)
        result = m.load_status()
        assert result is not None
        assert result["cycles_completed"] == 5

    def test_corrupt_json_returns_error_dict(self, tmp_path):
        sf = tmp_path / "status.json"
        sf.write_text("{corrupt", encoding="utf-8")
        m = TrainingMonitor(str(sf), str(tmp_path / "log.log"))
        result = m.load_status()
        assert isinstance(result, dict)
        assert "error" in result

    def test_empty_status_loaded(self, tmp_path):
        m = _monitor(tmp_path, status={})
        result = m.load_status()
        assert result == {}


# ---------------------------------------------------------------------------
# TestLoadHeartbeat
# ---------------------------------------------------------------------------

class TestLoadHeartbeat:
    def test_missing_file_returns_none(self, tmp_path):
        m = _monitor(tmp_path)  # no heartbeat written
        assert m.load_heartbeat() is None

    def test_valid_heartbeat_loaded(self, tmp_path):
        hb_data = {"state": "running", "pid": 1234,
                   "timestamp": "2024-01-01T12:00:00"}
        m = _monitor(tmp_path, heartbeat=hb_data)
        result = m.load_heartbeat()
        assert result is not None
        assert result["state"] == "running"
        assert result["pid"] == 1234

    def test_corrupt_heartbeat_returns_none(self, tmp_path):
        m = _monitor(tmp_path)
        m.heartbeat_file.write_text("{bad json", encoding="utf-8")
        assert m.load_heartbeat() is None


# ---------------------------------------------------------------------------
# TestGetRecentLogs
# ---------------------------------------------------------------------------

class TestGetRecentLogs:
    def test_missing_file_returns_empty_list(self, tmp_path):
        m = _monitor(tmp_path)  # no log file
        assert m.get_recent_logs() == []

    def test_returns_log_lines(self, tmp_path):
        lines = ["INFO: cycle 1 started",
                 "INFO: cycle 1 done", "ERROR: something failed"]
        m = _monitor(tmp_path, log_lines=lines)
        result = m.get_recent_logs(10)
        assert len(result) == 3
        assert any("cycle 1 started" in ln for ln in result)

    def test_respects_lines_limit(self, tmp_path):
        many_lines = [f"line {i}" for i in range(50)]
        m = _monitor(tmp_path, log_lines=many_lines)
        result = m.get_recent_logs(lines=10)
        assert len(result) == 10

    def test_returns_most_recent_when_truncated(self, tmp_path):
        many_lines = [f"line {i}" for i in range(20)]
        m = _monitor(tmp_path, log_lines=many_lines)
        result = m.get_recent_logs(lines=5)
        assert len(result) == 5
        # The last 5 lines should be line 15..19 (strip trailing newline for comparison)
        stripped = [ln.rstrip("\n") for ln in result]
        assert stripped == [f"line {i}" for i in range(15, 20)]

    def test_empty_file_returns_empty_list(self, tmp_path):
        m = _monitor(tmp_path, log_lines=[])
        assert m.get_recent_logs() == []

    def test_single_line(self, tmp_path):
        m = _monitor(tmp_path, log_lines=["single entry"])
        result = m.get_recent_logs()
        assert len(result) == 1


# ---------------------------------------------------------------------------
# TestPrintAlerts (verifies logic by capturing stdout)
# ---------------------------------------------------------------------------

class TestPrintAlerts:
    def _capture(self, m, status):
        import io
        buf = io.StringIO()
        orig = sys.stdout
        sys.stdout = buf
        try:
            m.print_alerts(status)
        finally:
            sys.stdout = orig
        return buf.getvalue()

    def test_no_alerts_for_clean_status(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "training",
            "total_datasets_available": 500,
        }
        output = self._capture(m, status)
        assert "ALERTS" not in output

    def test_error_phase_triggers_alert(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "error",
            "error": "Disk full",
            "total_datasets_available": 500,
        }
        output = self._capture(m, status)
        assert "Disk full" in output

    def test_stopped_phase_triggers_warning(self, tmp_path):
        m = _monitor(tmp_path)
        status = {"current_phase": "stopped", "total_datasets_available": 500}
        output = self._capture(m, status)
        assert "stopped" in output.lower()

    def test_performance_degradation_triggers_warning(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "training",
            "total_datasets_available": 500,
            "performance_history": [
                {"mean_accuracy": 0.85},
                {"mean_accuracy": 0.70},  # >0.05 drop
            ],
        }
        output = self._capture(m, status)
        assert "degradation" in output.lower() or "85.00%" in output or "70.00%" in output

    def test_low_dataset_count_triggers_warning(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "training",
            "total_datasets_available": 50,  # < 100
        }
        output = self._capture(m, status)
        assert "Low dataset" in output or "50" in output

    def test_no_degradation_below_threshold(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "training",
            "total_datasets_available": 500,
            "performance_history": [
                {"mean_accuracy": 0.85},
                {"mean_accuracy": 0.82},  # only 0.03 drop — below 0.05 threshold
            ],
        }
        output = self._capture(m, status)
        # Should NOT trigger degradation alert
        assert "degradation" not in output.lower()

    def test_inventory_counted_when_total_absent(self, tmp_path):
        m = _monitor(tmp_path)
        status = {
            "current_phase": "training",
            # total = 50 < 100
            "dataset_inventory": {"chat": 20, "quantum": 30},
        }
        output = self._capture(m, status)
        assert "Low dataset" in output or "50" in output
