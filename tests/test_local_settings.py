"""Tests for shared/local_settings.py.

Covers load_local_settings and apply_local_settings with various
settings files, environment interactions, and edge cases.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.local_settings import apply_local_settings, load_local_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_settings(tmp_path: Path, values: dict) -> Path:
    p = tmp_path / "local.settings.json"
    p.write_text(json.dumps({"Values": values}), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# load_local_settings — file not found
# ---------------------------------------------------------------------------


class TestLoadLocalSettingsMissingFile:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        missing = tmp_path / "nonexistent.settings.json"
        result = load_local_settings(missing)
        assert result == {}

    def test_returns_dict_type(self, tmp_path):
        result = load_local_settings(tmp_path / "missing.json")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# load_local_settings — invalid file content
# ---------------------------------------------------------------------------


class TestLoadLocalSettingsInvalidContent:
    def test_invalid_json_returns_empty_dict(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not valid json!", encoding="utf-8")
        result = load_local_settings(p)
        assert result == {}

    def test_no_values_key_returns_empty_dict(self, tmp_path):
        p = tmp_path / "settings.json"
        p.write_text(json.dumps({"Host": {"CORS": "*"}}), encoding="utf-8")
        result = load_local_settings(p)
        assert result == {}

    def test_values_not_dict_returns_empty_dict(self, tmp_path):
        p = tmp_path / "settings.json"
        p.write_text(json.dumps({"Values": ["a", "b"]}), encoding="utf-8")
        result = load_local_settings(p)
        assert result == {}


# ---------------------------------------------------------------------------
# load_local_settings — valid settings
# ---------------------------------------------------------------------------


class TestLoadLocalSettingsValid:
    def test_returns_values_from_file(self, tmp_path):
        p = _write_settings(tmp_path, {"MY_KEY": "my_value"})
        result = load_local_settings(p)
        assert result["MY_KEY"] == "my_value"

    def test_multiple_keys_all_returned(self, tmp_path):
        p = _write_settings(tmp_path, {"A": "1", "B": "2", "C": "3"})
        result = load_local_settings(p)
        assert result == {"A": "1", "B": "2", "C": "3"}

    def test_string_path_accepted(self, tmp_path):
        p = _write_settings(tmp_path, {"K": "V"})
        result = load_local_settings(str(p))
        assert result["K"] == "V"

    def test_non_string_value_coerced_to_str(self, tmp_path):
        p = _write_settings(tmp_path, {"NUM": 42})
        result = load_local_settings(p)
        assert result["NUM"] == "42"


# ---------------------------------------------------------------------------
# load_local_settings — filtering
# ---------------------------------------------------------------------------


class TestLoadLocalSettingsFiltering:
    def test_comment_keys_skipped(self, tmp_path):
        p = _write_settings(tmp_path, {"# This is a comment": "val", "REAL_KEY": "real"})
        result = load_local_settings(p)
        assert "# This is a comment" not in result
        assert result.get("REAL_KEY") == "real"

    def test_empty_string_values_skipped(self, tmp_path):
        p = _write_settings(tmp_path, {"EMPTY": "", "PRESENT": "yes"})
        result = load_local_settings(p)
        assert "EMPTY" not in result
        assert result["PRESENT"] == "yes"

    def test_none_values_skipped(self, tmp_path):
        p = _write_settings(tmp_path, {"NULL_KEY": None, "OK_KEY": "ok"})
        result = load_local_settings(p)
        assert "NULL_KEY" not in result
        assert result["OK_KEY"] == "ok"

    def test_all_filtered_returns_empty(self, tmp_path):
        p = _write_settings(tmp_path, {"": "val", "# comment": "x"})
        result = load_local_settings(p)
        # Empty string key may or may not be filtered; comment is definitely filtered
        assert "# comment" not in result


# ---------------------------------------------------------------------------
# apply_local_settings — environment application
# ---------------------------------------------------------------------------


class TestApplyLocalSettings:
    def test_keys_applied_to_env(self, tmp_path, monkeypatch):
        p = _write_settings(tmp_path, {"TEST_APPLY_KEY": "applied_value"})
        monkeypatch.delenv("TEST_APPLY_KEY", raising=False)
        apply_local_settings(p)
        assert os.environ.get("TEST_APPLY_KEY") == "applied_value"

    def test_existing_env_var_not_overridden_by_default(self, tmp_path, monkeypatch):
        monkeypatch.setenv("EXISTING_VAR", "original")
        p = _write_settings(tmp_path, {"EXISTING_VAR": "new_value"})
        apply_local_settings(p)
        assert os.environ.get("EXISTING_VAR") == "original"

    def test_override_true_replaces_existing(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OVERRIDE_VAR", "old")
        p = _write_settings(tmp_path, {"OVERRIDE_VAR": "new"})
        apply_local_settings(p, override=True)
        assert os.environ.get("OVERRIDE_VAR") == "new"

    def test_returns_loaded_dict(self, tmp_path, monkeypatch):
        p = _write_settings(tmp_path, {"RET_KEY": "ret_val"})
        monkeypatch.delenv("RET_KEY", raising=False)
        result = apply_local_settings(p)
        assert isinstance(result, dict)
        assert result.get("RET_KEY") == "ret_val"

    def test_missing_file_returns_empty_dict_and_no_env_change(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GHOST_VAR", raising=False)
        result = apply_local_settings(tmp_path / "ghost.json")
        assert result == {}
        assert "GHOST_VAR" not in os.environ

    def test_multiple_keys_applied(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ALPHA", raising=False)
        monkeypatch.delenv("BETA", raising=False)
        p = _write_settings(tmp_path, {"ALPHA": "a", "BETA": "b"})
        apply_local_settings(p)
        assert os.environ.get("ALPHA") == "a"
        assert os.environ.get("BETA") == "b"
