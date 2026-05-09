"""Tests for generated_tools/data_struct_utils.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generated_tools.data_struct_utils import (coalesce, deep_get, deep_merge,
                                               flatten_dict, rekey_dict,
                                               unflatten_dict, unique_by_key)


class TestDeepGet:
    def test_returns_nested_value(self):
        data = {"user": {"profile": {"name": "Aria"}}}
        assert deep_get(data, "user.profile.name") == "Aria"

    def test_returns_default_for_missing_path(self):
        data = {"user": {"profile": {"name": "Aria"}}}
        assert deep_get(data, "user.profile.age", default=21) == 21

    def test_empty_path_returns_original_data(self):
        data = {"a": 1}
        assert deep_get(data, "") is data

    def test_custom_separator(self):
        data = {"user": {"profile": {"name": "Aria"}}}
        assert deep_get(data, "user/profile/name", sep="/") == "Aria"


class TestFlattenDict:
    def test_flattens_nested_dict(self):
        data = {"user": {"profile": {"name": "Aria"}}, "active": True}
        result = flatten_dict(data)
        assert result == {"user.profile.name": "Aria", "active": True}

    def test_parent_key_prefix(self):
        data = {"x": {"y": 1}}
        result = flatten_dict(data, parent_key="root")
        assert result == {"root.x.y": 1}

    def test_custom_separator(self):
        data = {"a": {"b": 1}}
        result = flatten_dict(data, sep="/")
        assert result == {"a/b": 1}


class TestUnflattenDict:
    def test_unflattens_path_keys(self):
        flat = {"user.profile.name": "Aria", "active": True}
        result = unflatten_dict(flat)
        assert result == {"user": {"profile": {"name": "Aria"}}, "active": True}

    def test_custom_separator(self):
        flat = {"user/profile/name": "Aria"}
        result = unflatten_dict(flat, sep="/")
        assert result == {"user": {"profile": {"name": "Aria"}}}

    def test_roundtrip_with_flatten_dict(self):
        original = {
            "user": {"profile": {"name": "Aria", "age": 21}},
            "flags": {"active": True, "beta": False},
        }
        restored = unflatten_dict(flatten_dict(original))
        assert restored == original


class TestDeepMerge:
    def test_merges_nested_dicts(self):
        base = {"a": {"x": 1}, "b": 2}
        override = {"a": {"y": 3}, "b": 9, "c": 10}
        result = deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 3}, "b": 9, "c": 10}

    def test_override_non_dict_replaces_dict(self):
        base = {"a": {"x": 1}}
        override = {"a": 5}
        result = deep_merge(base, override)
        assert result == {"a": 5}

    def test_inputs_not_mutated(self):
        base = {"a": {"x": 1}}
        override = {"a": {"y": 2}}
        _ = deep_merge(base, override)
        assert base == {"a": {"x": 1}}
        assert override == {"a": {"y": 2}}


class TestUniqueByKey:
    def test_keeps_first_of_duplicate_keys(self):
        records = [
            {"id": 1, "v": "a"},
            {"id": 1, "v": "b"},
            {"id": 2, "v": "c"},
        ]
        result = unique_by_key(records, "id")
        assert result == [{"id": 1, "v": "a"}, {"id": 2, "v": "c"}]

    def test_missing_keys_are_kept_as_distinct_records(self):
        records = [{"v": "a"}, {"v": "b"}, {"id": 1, "v": "c"}]
        result = unique_by_key(records, "id")
        assert result == records

    def test_order_is_preserved(self):
        records = [
            {"id": "b", "v": 1},
            {"id": "a", "v": 2},
            {"id": "b", "v": 3},
            {"id": "c", "v": 4},
        ]
        result = unique_by_key(records, "id")
        assert result == [
            {"id": "b", "v": 1},
            {"id": "a", "v": 2},
            {"id": "c", "v": 4},
        ]


class TestRekeyDict:
    def test_renames_mapped_keys(self):
        data = {"first_name": "Aria", "age": 21}
        mapping = {"first_name": "name"}
        result = rekey_dict(data, mapping)
        assert result == {"name": "Aria", "age": 21}

    def test_keep_unmapped_false_drops_unmapped(self):
        data = {"first_name": "Aria", "age": 21}
        mapping = {"first_name": "name"}
        result = rekey_dict(data, mapping, keep_unmapped=False)
        assert result == {"name": "Aria"}

    def test_empty_mapping_returns_same_when_keep_unmapped_true(self):
        data = {"x": 1}
        result = rekey_dict(data, {})
        assert result == {"x": 1}


class TestCoalesce:
    def test_returns_first_non_none(self):
        assert coalesce(None, None, "ok", "later") == "ok"

    def test_returns_default_when_all_none(self):
        assert coalesce(None, None, default="fallback") == "fallback"

    def test_returns_none_when_all_none_and_no_default(self):
        assert coalesce(None, None) is None

    def test_preserves_falsey_non_none_values(self):
        assert coalesce(None, 0, "x") == 0
        assert coalesce(None, "", "x") == ""
        assert coalesce(None, False, True) is False
