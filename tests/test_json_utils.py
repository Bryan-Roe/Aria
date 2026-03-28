"""Test suite for shared/json_utils.py.

Tests cover load_json, save_json, load_jsonl, save_jsonl, and merge_json_files.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.json_utils import (
    load_json,
    load_jsonl,
    merge_json_files,
    save_json,
    save_jsonl,
)

import json
import tempfile

import pytest


# ---------------------------------------------------------------------------
# load_json
# ---------------------------------------------------------------------------

class TestLoadJson:
    def test_load_valid_dict(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"key": "value", "num": 42}', encoding="utf-8")
        result = load_json(p)
        assert result == {"key": "value", "num": 42}

    def test_load_valid_list(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('[1, 2, 3]', encoding="utf-8")
        result = load_json(p)
        assert result == [1, 2, 3]

    def test_load_accepts_string_path(self, tmp_path):
        p = tmp_path / "data.json"
        p.write_text('{"x": 1}', encoding="utf-8")
        result = load_json(str(p))
        assert result == {"x": 1}

    def test_missing_file_raises_without_default(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "missing.json")

    def test_missing_file_returns_default(self, tmp_path):
        result = load_json(tmp_path / "missing.json",
                           default={"fallback": True})
        assert result == {"fallback": True}

    def test_invalid_json_raises_without_default(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_json(p)

    def test_invalid_json_returns_default(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not json", encoding="utf-8")
        result = load_json(p, default=[])
        assert result == []

    def test_default_none_still_raises(self, tmp_path):
        """Passing default=None should not suppress exceptions."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "missing.json", default=None)

    def test_unicode_content(self, tmp_path):
        p = tmp_path / "unicode.json"
        p.write_text('{"emoji": "🎉", "cjk": "日本語"}', encoding="utf-8")
        result = load_json(p)
        assert result["emoji"] == "🎉"
        assert result["cjk"] == "日本語"


# ---------------------------------------------------------------------------
# save_json
# ---------------------------------------------------------------------------

class TestSaveJson:
    def test_save_dict(self, tmp_path):
        p = tmp_path / "out.json"
        save_json({"a": 1, "b": [2, 3]}, p)
        assert p.exists()
        loaded = json.loads(p.read_text(encoding="utf-8"))
        assert loaded == {"a": 1, "b": [2, 3]}

    def test_default_indent_is_2(self, tmp_path):
        p = tmp_path / "out.json"
        save_json({"key": "value"}, p)
        content = p.read_text(encoding="utf-8")
        # With indent=2 the content should have whitespace
        assert "\n" in content

    def test_create_parents_by_default(self, tmp_path):
        p = tmp_path / "deeply" / "nested" / "out.json"
        save_json({"ok": True}, p)
        assert p.exists()

    def test_create_parents_false_raises_if_no_dir(self, tmp_path):
        p = tmp_path / "subdir" / "out.json"
        with pytest.raises(FileNotFoundError):
            save_json({"ok": True}, p, create_parents=False)

    def test_roundtrip_with_unicode(self, tmp_path):
        p = tmp_path / "u.json"
        original = {"text": "café ☕"}
        save_json(original, p)
        result = load_json(p)
        assert result == original

    def test_ensure_ascii_false_preserves_unicode(self, tmp_path):
        p = tmp_path / "u.json"
        save_json({"text": "日本語"}, p, ensure_ascii=False)
        raw = p.read_text(encoding="utf-8")
        assert "日本語" in raw

    def test_accepts_string_path(self, tmp_path):
        p = str(tmp_path / "out.json")
        save_json({"x": 42}, p)
        assert Path(p).exists()


# ---------------------------------------------------------------------------
# load_jsonl
# ---------------------------------------------------------------------------

class TestLoadJsonl:
    def test_load_basic(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\n{"id": 2}\n{"id": 3}\n', encoding="utf-8")
        result = load_jsonl(p)
        assert len(result) == 3
        assert result[0] == {"id": 1}
        assert result[2] == {"id": 3}

    def test_skip_empty_lines_by_default(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\n\n{"id": 2}\n', encoding="utf-8")
        result = load_jsonl(p)
        assert len(result) == 2

    def test_max_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text("\n".join(json.dumps({"i": i})
                     for i in range(10)) + "\n", encoding="utf-8")
        result = load_jsonl(p, max_lines=3)
        assert len(result) == 3
        assert result[-1] == {"i": 2}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_jsonl(tmp_path / "missing.jsonl")

    def test_invalid_json_line_raises(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"id": 1}\nnot json\n{"id": 3}\n', encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_jsonl(p)

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        result = load_jsonl(p)
        assert result == []


# ---------------------------------------------------------------------------
# save_jsonl
# ---------------------------------------------------------------------------

class TestSaveJsonl:
    def test_save_basic(self, tmp_path):
        p = tmp_path / "out.jsonl"
        data = [{"id": 1}, {"id": 2}]
        save_jsonl(data, p)
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": 1}
        assert json.loads(lines[1]) == {"id": 2}

    def test_each_line_is_valid_json(self, tmp_path):
        p = tmp_path / "out.jsonl"
        data = [{"a": i, "b": str(i)} for i in range(5)]
        save_jsonl(data, p)
        for line in p.read_text(encoding="utf-8").strip().splitlines():
            obj = json.loads(line)
            assert "a" in obj

    def test_create_parents_by_default(self, tmp_path):
        p = tmp_path / "sub" / "out.jsonl"
        save_jsonl([{"x": 1}], p)
        assert p.exists()

    def test_roundtrip(self, tmp_path):
        p = tmp_path / "rt.jsonl"
        original = [{"messages": [{"role": "user", "content": "Hi"}]}]
        save_jsonl(original, p)
        result = load_jsonl(p)
        assert result == original

    def test_unicode_content(self, tmp_path):
        p = tmp_path / "u.jsonl"
        save_jsonl([{"text": "日本語 🎌"}], p)
        loaded = load_jsonl(p)
        assert loaded[0]["text"] == "日本語 🎌"

    def test_empty_list(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        save_jsonl([], p)
        assert p.read_text(encoding="utf-8") == ""


# ---------------------------------------------------------------------------
# merge_json_files
# ---------------------------------------------------------------------------

class TestMergeJsonFiles:
    def test_extend_strategy_merges_lists(self, tmp_path):
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "merged.json"
        save_json([1, 2], a)
        save_json([3, 4], b)
        merge_json_files([a, b], out)
        result = load_json(out)
        assert result == [1, 2, 3, 4]

    def test_extend_strategy_wraps_non_list_in_list(self, tmp_path):
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "merged.json"
        save_json({"x": 1}, a)
        save_json({"y": 2}, b)
        merge_json_files([a, b], out)
        result = load_json(out)
        # Each non-list value is appended as-is
        assert {"x": 1} in result
        assert {"y": 2} in result

    def test_update_strategy_merges_dicts(self, tmp_path):
        a = tmp_path / "a.json"
        b = tmp_path / "b.json"
        out = tmp_path / "merged.json"
        save_json({"base": 1, "override": "old"}, a)
        save_json({"override": "new", "extra": 2}, b)
        merge_json_files([a, b], out, merge_strategy="update")
        result = load_json(out)
        assert result["base"] == 1
        assert result["override"] == "new"
        assert result["extra"] == 2

    def test_update_strategy_non_dict_raises(self, tmp_path):
        a = tmp_path / "a.json"
        out = tmp_path / "merged.json"
        save_json([1, 2, 3], a)
        with pytest.raises(ValueError, match="Expected dict"):
            merge_json_files([a], out, merge_strategy="update")

    def test_unknown_strategy_raises(self, tmp_path):
        a = tmp_path / "a.json"
        out = tmp_path / "merged.json"
        save_json([], a)
        with pytest.raises(ValueError, match="Unknown merge strategy"):
            merge_json_files([a], out, merge_strategy="invalid")

    def test_creates_parent_dirs(self, tmp_path):
        a = tmp_path / "a.json"
        save_json([1], a)
        out = tmp_path / "deep" / "dir" / "merged.json"
        merge_json_files([a], out)
        assert out.exists()
