"""Generated utility functions for comparing records and collections.

This module is intentionally pure (no filesystem/network side effects)
and safe for reuse in API and CLI layers.
"""

from typing import Any, Iterable


def compare_records(
    before: dict[str, Any], after: dict[str, Any], fields: Iterable[str] | None = None
) -> dict[str, Any]:
    """Compare two records and return added, removed, changed, and unchanged fields.

    Args:
        before: Original record.
        after: Updated record.
        fields: Optional field subset to compare.

    Returns:
        Dictionary with keys: added, removed, changed, unchanged.
    """
    if fields is None:
        field_names = sorted(set(before.keys()) | set(after.keys()))
    else:
        field_names = list(fields)

    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    changed: dict[str, dict[str, Any]] = {}
    unchanged: dict[str, Any] = {}

    for field in field_names:
        in_before = field in before
        in_after = field in after

        if not in_before and in_after:
            added[field] = after[field]
        elif in_before and not in_after:
            removed[field] = before[field]
        else:
            before_value = before.get(field)
            after_value = after.get(field)
            if before_value == after_value:
                unchanged[field] = after_value
            else:
                changed[field] = {"before": before_value, "after": after_value}

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }


def diff_record_sets(
    records_a: Iterable[dict[str, Any]],
    records_b: Iterable[dict[str, Any]],
    key: str,
) -> dict[str, list[Any]]:
    """Compare two record sets by primary key.

    Records with missing keys are ignored.

    Returns:
        Dict with keys:
        - only_in_a: keys present only in records_a
        - only_in_b: keys present only in records_b
        - changed: list of per-record diffs
        - unchanged: keys whose records are equal
    """
    index_a: dict[Any, dict[str, Any]] = {}
    for record in records_a:
        if key in record:
            index_a[record[key]] = record

    index_b: dict[Any, dict[str, Any]] = {}
    for record in records_b:
        if key in record:
            index_b[record[key]] = record

    keys_a = set(index_a.keys())
    keys_b = set(index_b.keys())

    only_in_a = sorted(keys_a - keys_b)
    only_in_b = sorted(keys_b - keys_a)
    shared = sorted(keys_a & keys_b)

    changed: list[dict[str, Any]] = []
    unchanged: list[Any] = []
    for item_key in shared:
        diff = compare_records(index_a[item_key], index_b[item_key])
        if diff["added"] or diff["removed"] or diff["changed"]:
            changed.append({"key": item_key, "diff": diff})
        else:
            unchanged.append(item_key)

    return {
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "changed": changed,
        "unchanged": unchanged,
    }


def jaccard_similarity(values_a: Iterable[Any], values_b: Iterable[Any]) -> float:
    """Compute Jaccard similarity between two iterables.

    Returns 1.0 when both collections are empty.
    """
    set_a = set(values_a)
    set_b = set(values_b)
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 1.0
    return len(set_a & set_b) / len(union)


def changed_fields(diff: dict[str, Any]) -> list[str]:
    """Return changed field names from compare_records() output."""
    names: list[str] = []
    for field in diff.get("added", {}):
        names.append(field)
    for field in diff.get("removed", {}):
        names.append(field)
    for field in diff.get("changed", {}):
        names.append(field)
    return sorted(names)
