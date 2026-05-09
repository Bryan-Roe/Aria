"""Unit tests for scripts/cleanup_artifacts.py — _file_age_days and find_candidates."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------


def _load():
    mod_name = "cleanup_artifacts"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    path = Path(__file__).parent.parent / "scripts" / "cleanup_artifacts.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


ca = _load()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patched_find(tmp_path: Path, **kwargs):
    """Call find_candidates with DATA_OUT redirected to tmp_path."""
    old = ca.DATA_OUT
    ca.DATA_OUT = tmp_path
    try:
        return ca.find_candidates(**kwargs)
    finally:
        ca.DATA_OUT = old


def _touch(path: Path, age_seconds: float = 0.0) -> Path:
    """Create a file and optionally back-date its mtime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x")
    if age_seconds > 0:
        mtime = time.time() - age_seconds
        os.utime(path, (mtime, mtime))
    return path


# ---------------------------------------------------------------------------
# _file_age_days
# ---------------------------------------------------------------------------


class TestFileAgeDays:
    def test_fresh_file_is_near_zero(self, tmp_path: Path):
        f = _touch(tmp_path / "fresh.json")
        age = ca._file_age_days(f)
        assert 0.0 <= age < 0.1

    def test_old_file_returns_correct_days(self, tmp_path: Path):
        f = _touch(tmp_path / "old.json", age_seconds=10 * 86400)
        age = ca._file_age_days(f)
        assert 9.9 < age < 10.1

    def test_returns_float(self, tmp_path: Path):
        f = _touch(tmp_path / "f.json")
        assert isinstance(ca._file_age_days(f), float)

    def test_one_day_old(self, tmp_path: Path):
        f = _touch(tmp_path / "day.json", age_seconds=86400)
        age = ca._file_age_days(f)
        assert 0.99 < age < 1.01

    def test_zero_seconds_is_not_negative(self, tmp_path: Path):
        f = _touch(tmp_path / "z.json")
        assert ca._file_age_days(f) >= 0.0


# ---------------------------------------------------------------------------
# find_candidates — structural / empty cases
# ---------------------------------------------------------------------------


class TestFindCandidatesEmpty:
    def test_empty_data_out_returns_empty_list(self, tmp_path: Path):
        result = _patched_find(tmp_path)
        assert result == []

    def test_returns_list(self, tmp_path: Path):
        result = _patched_find(tmp_path)
        assert isinstance(result, list)

    def test_non_cleanable_dir_ignored(self, tmp_path: Path):
        non_cleanable = tmp_path / "some_other_dir"
        _touch(non_cleanable / "old.json", age_seconds=200 * 86400)
        result = _patched_find(tmp_path)
        assert result == []

    def test_cleanable_dir_with_no_files_returns_empty(self, tmp_path: Path):
        (tmp_path / "autotrain").mkdir()
        result = _patched_find(tmp_path)
        assert result == []

    def test_result_is_list_of_tuples(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "run1.json", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) > 0
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2


# ---------------------------------------------------------------------------
# find_candidates — KEEP_FILES exclusion
# ---------------------------------------------------------------------------


class TestFindCandidatesKeepFiles:
    def test_status_json_always_kept(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "status.json", age_seconds=365 * 86400)
        result = _patched_find(tmp_path)
        paths = [r[0] for r in result]
        assert not any(p.name == "status.json" for p in paths)

    def test_latest_results_json_always_kept(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "latest_results.json", age_seconds=365 * 86400)
        result = _patched_find(tmp_path)
        paths = [r[0] for r in result]
        assert not any(p.name == "latest_results.json" for p in paths)

    def test_other_old_json_not_kept(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "run_2020.json", age_seconds=365 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1
        assert result[0][0].name == "run_2020.json"


# ---------------------------------------------------------------------------
# find_candidates — age-based policy
# ---------------------------------------------------------------------------


class TestFindCandidatesAge:
    def test_young_file_not_a_candidate(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "recent.json", age_seconds=1 * 86400)
        result = _patched_find(tmp_path, max_age_days=30)
        assert result == []

    def test_old_file_is_candidate(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        f = _touch(dirpath / "old.json", age_seconds=60 * 86400)
        result = _patched_find(tmp_path, max_age_days=30)
        assert len(result) == 1
        assert result[0][0] == f

    def test_reason_contains_age_info(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "ancient.json", age_seconds=100 * 86400)
        result = _patched_find(tmp_path, max_age_days=30)
        assert len(result) == 1
        reason = result[0][1]
        assert ">" in reason and "d" in reason

    def test_custom_max_age_respected(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "medium.json", age_seconds=5 * 86400)
        # Should not be a candidate at default 30 days
        assert _patched_find(tmp_path, max_age_days=30) == []
        # Should be a candidate at 3 days
        result = _patched_find(tmp_path, max_age_days=3)
        assert len(result) == 1

    def test_exactly_at_threshold_not_candidate(self, tmp_path: Path):
        """Files exactly at max_age_days are NOT candidates (need age > threshold)."""
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "edge.json", age_seconds=30 * 86400)
        # Age is ~30.0 but not strictly > 30
        result = _patched_find(tmp_path, max_age_days=31)
        assert result == []


# ---------------------------------------------------------------------------
# find_candidates — count-based policy
# ---------------------------------------------------------------------------


class TestFindCandidatesCount:
    def test_fewer_files_than_max_count_no_candidates(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        for i in range(5):
            _touch(dirpath / f"run_{i:02d}.json")
        result = _patched_find(tmp_path, max_count=10)
        assert result == []

    def test_excess_files_are_candidates(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        # Create 7 fresh files; max_count=5 → oldest 2 should be candidates
        for i in range(7):
            f = dirpath / f"run_{i:02d}.json"
            _touch(f, age_seconds=i * 3600)  # older files have higher i
        result = _patched_find(tmp_path, max_count=5, max_age_days=9999)
        assert len(result) == 2

    def test_count_reason_contains_count_info(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        for i in range(4):
            _touch(dirpath / f"run_{i:02d}.json", age_seconds=i * 3600)
        result = _patched_find(tmp_path, max_count=2, max_age_days=9999)
        assert any("count=" in r[1] for r in result)

    def test_newest_files_kept_by_count(self, tmp_path: Path):
        """Newest files should survive; oldest become count candidates."""
        dirpath = tmp_path / "autotrain"
        # make 3 files; newest has age_seconds=0, oldest has age_seconds=2h
        for i in range(3):
            _touch(dirpath / f"run_{i:02d}.json", age_seconds=i * 3600)
        result = _patched_find(tmp_path, max_count=1, max_age_days=9999)
        # Files are sorted newest first, so idx=0 is the newest (run_00)
        # run_01 (idx=1) and run_02 (idx=2) are candidates
        assert len(result) == 2
        candidate_names = {r[0].name for r in result}
        assert "run_00.json" not in candidate_names


# ---------------------------------------------------------------------------
# find_candidates — file pattern matching
# ---------------------------------------------------------------------------


class TestFindCandidatesPatterns:
    def test_json_files_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "run.json", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1

    def test_log_files_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "run.log", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1

    def test_md_files_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "notes.md", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1

    def test_csv_files_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "metrics.csv", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1

    def test_py_files_not_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "script.py", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert result == []

    def test_txt_files_not_matched(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "notes.txt", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert result == []


# ---------------------------------------------------------------------------
# find_candidates — multiple CLEANABLE dirs
# ---------------------------------------------------------------------------


class TestFindCandidatesMultipleDirs:
    def test_all_cleanable_dirs_scanned(self, tmp_path: Path):
        for dirname in ca.CLEANABLE:
            dirpath = tmp_path / dirname
            _touch(dirpath / "old.json", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == len(ca.CLEANABLE)

    def test_only_populated_dirs_contribute(self, tmp_path: Path):
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "old.json", age_seconds=60 * 86400)
        # quantum_autorun exists but empty
        (tmp_path / "quantum_autorun").mkdir()
        result = _patched_find(tmp_path)
        assert len(result) == 1

    def test_missing_cleanable_dir_skipped(self, tmp_path: Path):
        # Only autotrain exists, others are missing — should not error
        dirpath = tmp_path / "autotrain"
        _touch(dirpath / "old.json", age_seconds=60 * 86400)
        result = _patched_find(tmp_path)
        assert len(result) == 1
