"""
Unit tests for pure utility functions in scripts/dashboard.py.
Covers: load_json, format_time, print_status_badge.
"""

import importlib.util
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "dashboard_script"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    scripts_dir = str(Path(__file__).parent.parent / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    path = Path(__file__).parent.parent / "scripts" / "dashboard.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()
load_json = mod.load_json
format_time = mod.format_time
print_status_badge = mod.print_status_badge


# ---------------------------------------------------------------------------
# TestLoadJson
# ---------------------------------------------------------------------------


class TestLoadJson:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        result = load_json(tmp_path / "no_such_file.json")
        assert result == {}

    def test_valid_json_loaded(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text(json.dumps({"key": "value", "count": 42}), encoding="utf-8")
        result = load_json(p)
        assert result["key"] == "value"
        assert result["count"] == 42

    def test_corrupt_json_returns_empty_dict(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json", encoding="utf-8")
        result = load_json(p)
        assert result == {}

    def test_empty_json_object_loaded(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text("{}", encoding="utf-8")
        result = load_json(p)
        assert result == {}

    def test_nested_dict_loaded(self, tmp_path):
        p = tmp_path / "nested.json"
        data = {"a": {"b": {"c": 99}}}
        p.write_text(json.dumps(data), encoding="utf-8")
        result = load_json(p)
        assert result["a"]["b"]["c"] == 99

    def test_returns_dict_type(self, tmp_path):
        p = tmp_path / "d.json"
        p.write_text(json.dumps({"x": 1}), encoding="utf-8")
        result = load_json(p)
        assert isinstance(result, dict)

    def test_json_array_returns_empty_dict(self, tmp_path):
        p = tmp_path / "array.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        result = load_json(p)
        assert result == {}


# ---------------------------------------------------------------------------
# TestFormatTime
# ---------------------------------------------------------------------------


class TestFormatTime:
    def test_none_returns_na(self):
        assert format_time(None) == "N/A"

    def test_empty_string_returns_na(self):
        assert format_time("") == "N/A"

    def test_valid_iso_formats_correctly(self):
        result = format_time("2025-06-15T14:30:00")
        assert result == "2025-06-15 14:30:00"

    def test_valid_iso_with_timezone(self):
        result = format_time("2025-06-15T14:30:00+00:00")
        assert "2025-06-15" in result
        assert "14:30:00" in result

    def test_invalid_string_returned_as_is(self):
        result = format_time("not-a-date")
        assert result == "not-a-date"

    def test_output_format_matches_pattern(self):
        result = format_time("2025-01-01T00:00:00")
        parts = result.split(" ")
        assert len(parts) == 2
        assert len(parts[0]) == 10  # YYYY-MM-DD
        assert len(parts[1]) == 8  # HH:MM:SS

    def test_date_only_iso_format(self):
        # Some parsers accept date-only ISO strings
        result = format_time("2025-06-15")
        # Either it parses and formats or returns the original — both OK
        assert "2025" in result


# ---------------------------------------------------------------------------
# TestPrintStatusBadge
# ---------------------------------------------------------------------------


class TestPrintStatusBadge:
    def test_completed_badge(self):
        assert print_status_badge("completed") == "✅"

    def test_running_badge(self):
        assert print_status_badge("running") == "🟢"

    def test_paused_badge(self):
        assert print_status_badge("paused") == "⏸️"

    def test_error_badge(self):
        assert print_status_badge("error") == "❌"

    def test_initializing_badge(self):
        assert print_status_badge("initializing") == "⚙️"

    def test_training_badge(self):
        assert print_status_badge("training") == "🔄"

    def test_unknown_status_returns_question(self):
        assert print_status_badge("unknown_xyz") == "❓"

    def test_empty_string_returns_question(self):
        assert print_status_badge("") == "❓"

    def test_returns_string(self):
        assert isinstance(print_status_badge("completed"), str)

    def test_case_sensitive_no_upper(self):
        # "RUNNING" should not match "running" — returns ❓
        assert print_status_badge("RUNNING") == "❓"
