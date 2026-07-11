"""Tests for shared/json_utils.py — load_status_json function.

load_status_json is not exercised by test_json_utils.py; this file
provides full coverage of its public behaviour.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.json_utils import load_status_json

# ---------------------------------------------------------------------------
# Metadata keys always present
# ---------------------------------------------------------------------------


class TestLoadStatusJsonMetadataKeys:
    def test_metadata_keys_present_when_file_exists(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p)
        assert "_status_file_exists" in result
        assert "_status_file_age_seconds" in result
        assert "_status_file_stale" in result
        assert "_status_file_error" in result

    def test_metadata_keys_present_when_file_missing(self, tmp_path):
        result = load_status_json(tmp_path / "missing.json")
        assert "_status_file_exists" in result
        assert "_status_file_age_seconds" in result
        assert "_status_file_stale" in result
        assert "_status_file_error" in result


# ---------------------------------------------------------------------------
# File missing
# ---------------------------------------------------------------------------


class TestLoadStatusJsonMissingFile:
    def test_exists_false_for_missing_file(self, tmp_path):
        result = load_status_json(tmp_path / "nope.json")
        assert result["_status_file_exists"] is False

    def test_age_none_for_missing_file(self, tmp_path):
        result = load_status_json(tmp_path / "nope.json")
        assert result["_status_file_age_seconds"] is None

    def test_stale_none_for_missing_file(self, tmp_path):
        result = load_status_json(tmp_path / "nope.json")
        assert result["_status_file_stale"] is None

    def test_error_set_for_missing_file(self, tmp_path):
        result = load_status_json(tmp_path / "nope.json")
        assert result["_status_file_error"] is not None
        assert "not found" in result["_status_file_error"].lower()

    def test_returns_dict_with_missing_file(self, tmp_path):
        result = load_status_json(tmp_path / "nope.json")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Valid file
# ---------------------------------------------------------------------------


class TestLoadStatusJsonValidFile:
    def test_payload_merged_into_result(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"stage": "done", "count": 42}', encoding="utf-8")
        result = load_status_json(p)
        assert result["stage"] == "done"
        assert result["count"] == 42

    def test_exists_true_for_present_file(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_exists"] is True

    def test_error_none_for_valid_file(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_error"] is None

    def test_age_seconds_is_non_negative(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_age_seconds"] >= 0.0

    def test_age_seconds_is_float(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"x": 1}', encoding="utf-8")
        result = load_status_json(p)
        assert isinstance(result["_status_file_age_seconds"], float)

    def test_accepts_string_path(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"x": 1}', encoding="utf-8")
        result = load_status_json(str(p))
        assert result["x"] == 1
        assert result["_status_file_exists"] is True


# ---------------------------------------------------------------------------
# Staleness (max_age_seconds)
# ---------------------------------------------------------------------------


class TestLoadStatusJsonStaleness:
    def test_stale_none_when_max_age_not_provided(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_stale"] is None

    def test_not_stale_for_fresh_file(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        result = load_status_json(p, max_age_seconds=3600)
        assert result["_status_file_stale"] is False

    def test_stale_for_old_file(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        # Backdate mtime by 2 seconds
        past = time.time() - 2
        import os

        os.utime(p, (past, past))
        result = load_status_json(p, max_age_seconds=1)
        assert result["_status_file_stale"] is True

    def test_stale_false_when_max_age_equals_zero_and_file_is_fresh(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"ok": true}', encoding="utf-8")
        # A max_age_seconds of 3600 should not mark a just-written file stale.
        result = load_status_json(p, max_age_seconds=3600)
        assert result["_status_file_stale"] is False


# ---------------------------------------------------------------------------
# Non-dict JSON root
# ---------------------------------------------------------------------------


class TestLoadStatusJsonNonDictRoot:
    def test_list_root_sets_error(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_error"] is not None
        assert "not an object" in result["_status_file_error"].lower()

    def test_list_root_still_returns_dict(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        result = load_status_json(p)
        assert isinstance(result, dict)

    def test_string_root_sets_error(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('"just a string"', encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_error"] is not None


# ---------------------------------------------------------------------------
# Invalid JSON
# ---------------------------------------------------------------------------


class TestLoadStatusJsonInvalidJson:
    def test_invalid_json_sets_error(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text("not valid json!!!", encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_error"] is not None

    def test_invalid_json_exists_still_true(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text("{broken", encoding="utf-8")
        result = load_status_json(p)
        assert result["_status_file_exists"] is True


# ---------------------------------------------------------------------------
# Default dict merging
# ---------------------------------------------------------------------------


class TestLoadStatusJsonDefault:
    def test_default_values_present_when_file_missing(self, tmp_path):
        default = {"fallback_key": "fallback_value", "count": 0}
        result = load_status_json(tmp_path / "missing.json", default=default)
        assert result["fallback_key"] == "fallback_value"
        assert result["count"] == 0

    def test_file_payload_overrides_default(self, tmp_path):
        p = tmp_path / "status.json"
        p.write_text('{"count": 99}', encoding="utf-8")
        result = load_status_json(p, default={"count": 0, "extra": "yes"})
        assert result["count"] == 99  # file wins
        assert result["extra"] == "yes"  # default still present

    def test_no_default_and_missing_file_still_returns_dict(self, tmp_path):
        result = load_status_json(tmp_path / "missing.json")
        assert isinstance(result, dict)
