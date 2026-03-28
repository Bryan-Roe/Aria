"""Unit tests for scripts/watch_continuous_automation.py."""
from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest


# ─── module loader ────────────────────────────────────────────────────────────

_MODULE_NAME = "watch_continuous_automation"
_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")


def _load():
    if _MODULE_NAME in sys.modules:
        return sys.modules[_MODULE_NAME]
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    import importlib
    return importlib.import_module(_MODULE_NAME)


# ─── _parse_iso ───────────────────────────────────────────────────────────────

class TestParseIso:
    def setup_method(self):
        self.mod = _load()

    def test_valid_utc_iso(self):
        result = self.mod._parse_iso("2024-01-15T12:00:00+00:00")
        assert result is not None
        assert result.tzinfo is not None

    def test_naive_iso_gets_utc_attached(self):
        result = self.mod._parse_iso("2024-01-15T12:00:00")
        assert result is not None
        assert result.tzinfo == timezone.utc

    def test_invalid_string_returns_none(self):
        assert self.mod._parse_iso("not-a-date") is None

    def test_empty_string_returns_none(self):
        assert self.mod._parse_iso("") is None

    def test_whitespace_is_stripped(self):
        result = self.mod._parse_iso("  2024-01-15T12:00:00  ")
        assert result is not None

    def test_preserves_existing_timezone(self):
        result = self.mod._parse_iso("2024-01-15T12:00:00+05:30")
        assert result is not None
        assert result.tzinfo is not None


# ─── _format_age ──────────────────────────────────────────────────────────────

class TestFormatAge:
    def setup_method(self):
        self.mod = _load()

    def test_none_returns_na(self):
        assert self.mod._format_age(None) == "n/a"

    def test_seconds_ago(self):
        recent = datetime.now(timezone.utc) - timedelta(seconds=30)
        result = self.mod._format_age(recent)
        assert "s" in result
        assert "m" not in result

    def test_minutes_ago(self):
        past = datetime.now(timezone.utc) - timedelta(minutes=5)
        result = self.mod._format_age(past)
        assert "m" in result

    def test_hours_ago(self):
        past = datetime.now(timezone.utc) - timedelta(hours=2, minutes=30)
        result = self.mod._format_age(past)
        assert "h" in result

    def test_days_ago(self):
        past = datetime.now(timezone.utc) - timedelta(days=3, hours=2)
        result = self.mod._format_age(past)
        assert "d" in result

    def test_future_returns_zero(self):
        future = datetime.now(timezone.utc) + timedelta(seconds=60)
        result = self.mod._format_age(future)
        assert result == "0s"


# ─── _tail ────────────────────────────────────────────────────────────────────

class TestTail:
    def setup_method(self):
        self.mod = _load()

    def test_tail_fewer_than_n(self):
        result = self.mod._tail(["a", "b", "c"], 10)
        assert result == ["a", "b", "c"]

    def test_tail_exactly_n(self):
        result = self.mod._tail(["a", "b", "c"], 3)
        assert result == ["a", "b", "c"]

    def test_tail_more_than_n(self):
        result = self.mod._tail(["a", "b", "c", "d", "e"], 3)
        assert result == ["c", "d", "e"]

    def test_tail_zero_returns_empty(self):
        result = self.mod._tail(["a", "b", "c"], 0)
        assert result == []

    def test_tail_empty_input(self):
        result = self.mod._tail([], 5)
        assert result == []

    def test_tail_accepts_generator(self):
        result = self.mod._tail((x for x in ["a", "b", "c", "d"]), 2)
        assert result == ["c", "d"]


# ─── _safe_read_lines ─────────────────────────────────────────────────────────

class TestSafeReadLines:
    def setup_method(self):
        self.mod = _load()

    def test_missing_file_returns_empty(self, tmp_path):
        result = self.mod._safe_read_lines(tmp_path / "nonexistent.log")
        assert result == []

    def test_reads_lines(self, tmp_path):
        f = tmp_path / "test.log"
        f.write_text("line1\nline2\nline3\n", encoding="utf-8")
        result = self.mod._safe_read_lines(f)
        assert result == ["line1", "line2", "line3"]

    def test_truncates_to_max_lines(self, tmp_path):
        f = tmp_path / "big.log"
        f.write_text("\n".join(str(i) for i in range(5000)), encoding="utf-8")
        result = self.mod._safe_read_lines(f, max_lines=100)
        assert len(result) == 100
        # should be the trailing 100 lines
        assert result[0] == "4900"
        assert result[-1] == "4999"

    def test_does_not_truncate_when_under_limit(self, tmp_path):
        f = tmp_path / "small.log"
        lines = [f"line{i}" for i in range(10)]
        f.write_text("\n".join(lines), encoding="utf-8")
        result = self.mod._safe_read_lines(f, max_lines=100)
        assert len(result) == 10


# ─── _analyze_loop_log ────────────────────────────────────────────────────────

class TestAnalyzeLoopLog:
    def setup_method(self):
        self.mod = _load()

    def _start_line(self, ts: str) -> str:
        return f"=== {ts} cycle start ==="

    def _end_line(self, ts: str) -> str:
        return f"=== {ts} cycle end ==="

    def test_empty_log_returns_zeros(self):
        result = self.mod._analyze_loop_log([])
        assert result["cycle_starts"] == 0
        assert result["cycle_ends"] == 0
        assert result["in_progress"] is False
        assert result["last_start"] is None
        assert result["last_end"] is None
        assert result["last_pytest_summary"] is None
        assert result["last_gate_status"] == "unknown"

    def test_single_start_means_in_progress(self):
        ts = "2024-01-15T12:00:00"
        result = self.mod._analyze_loop_log([self._start_line(ts)])
        assert result["cycle_starts"] == 1
        assert result["cycle_ends"] == 0
        assert result["in_progress"] is True

    def test_completed_cycle_not_in_progress(self):
        s = "2024-01-15T12:00:00"
        e = "2024-01-15T12:01:00"
        lines = [self._start_line(s), self._end_line(e)]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_starts"] == 1
        assert result["cycle_ends"] == 1
        assert result["in_progress"] is False

    def test_two_cycles_second_in_progress(self):
        lines = [
            self._start_line("2024-01-15T12:00:00"),
            self._end_line("2024-01-15T12:01:00"),
            self._start_line("2024-01-15T12:05:00"),
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_starts"] == 2
        assert result["cycle_ends"] == 1
        assert result["in_progress"] is True

    def test_two_completed_cycles_not_in_progress(self):
        lines = [
            self._start_line("2024-01-15T12:00:00"),
            self._end_line("2024-01-15T12:01:00"),
            self._start_line("2024-01-15T12:05:00"),
            self._end_line("2024-01-15T12:06:00"),
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["in_progress"] is False

    def test_duplicate_start_markers_same_timestamp_deduped(self):
        ts = "2024-01-15T12:00:00"
        lines = [self._start_line(ts), self._start_line(
            ts), self._start_line(ts)]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_starts"] == 1
        assert result["duplicate_start_markers"] == 2

    def test_duplicate_end_markers_same_timestamp_deduped(self):
        ts = "2024-01-15T12:01:00"
        lines = [self._end_line(ts), self._end_line(ts)]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_ends"] == 1
        assert result["duplicate_end_markers"] == 1

    def test_no_duplicates_when_distinct_timestamps(self):
        lines = [
            self._start_line("2024-01-15T12:00:00"),
            self._start_line("2024-01-15T12:05:00"),
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_starts"] == 2
        assert result["duplicate_start_markers"] == 0

    def test_gate_passed_detected(self):
        lines = ["some output [integration_contract_gate] passed blah"]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_gate_status"] == "passed"

    def test_gate_failed_detected(self):
        lines = ["[integration_contract_gate] failed"]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_gate_status"] == "failed"

    def test_gate_status_updates_to_latest(self):
        lines = [
            "[integration_contract_gate] passed",
            "[integration_contract_gate] failed",
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_gate_status"] == "failed"

    def test_pytest_summary_extracted(self):
        lines = ["1243 passed, 5 skipped"]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_pytest_summary"] == "1243 passed, 5 skipped"

    def test_pytest_summary_without_skipped(self):
        lines = ["42 passed"]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_pytest_summary"] == "42 passed"

    def test_last_start_is_datetime(self):
        ts = "2024-01-15T12:00:00"
        result = self.mod._analyze_loop_log([self._start_line(ts)])
        assert isinstance(result["last_start"], datetime)

    def test_last_end_is_datetime(self):
        ts = "2024-01-15T12:01:00"
        result = self.mod._analyze_loop_log([self._end_line(ts)])
        assert isinstance(result["last_end"], datetime)

    def test_last_start_is_most_recent(self):
        lines = [
            self._start_line("2024-01-15T12:00:00"),
            self._start_line("2024-01-15T12:05:00"),
            self._start_line("2024-01-15T12:03:00"),
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["last_start"] == self.mod._parse_iso(
            "2024-01-15T12:05:00")

    def test_mixed_log_full_scenario(self):
        lines = [
            self._start_line("2024-01-15T12:00:00"),
            "some output line",
            "[integration_contract_gate] passed",
            "1000 passed, 2 skipped",
            self._end_line("2024-01-15T12:01:30"),
            self._start_line("2024-01-15T12:10:00"),
            "[integration_contract_gate] failed",
        ]
        result = self.mod._analyze_loop_log(lines)
        assert result["cycle_starts"] == 2
        assert result["cycle_ends"] == 1
        assert result["in_progress"] is True
        assert result["last_gate_status"] == "failed"
        assert result["last_pytest_summary"] == "1000 passed, 2 skipped"


# ─── _read_pid / _pid_running ─────────────────────────────────────────────────

class TestReadPid:
    def setup_method(self):
        self.mod = _load()

    def test_missing_file_returns_none(self, tmp_path):
        result = self.mod._read_pid(tmp_path / "missing.pid")
        assert result is None

    def test_valid_pid_file(self, tmp_path):
        f = tmp_path / "loop.pid"
        f.write_text("12345\n", encoding="utf-8")
        assert self.mod._read_pid(f) == 12345

    def test_non_integer_returns_none(self, tmp_path):
        f = tmp_path / "bad.pid"
        f.write_text("not-a-pid\n", encoding="utf-8")
        assert self.mod._read_pid(f) is None

    def test_empty_file_returns_none(self, tmp_path):
        f = tmp_path / "empty.pid"
        f.write_text("", encoding="utf-8")
        assert self.mod._read_pid(f) is None


class TestPidRunning:
    def setup_method(self):
        self.mod = _load()

    def test_none_pid_returns_false(self):
        assert self.mod._pid_running(None) is False

    def test_current_process_is_running(self):
        assert self.mod._pid_running(os.getpid()) is True

    def test_dead_pid_returns_false(self):
        # PID 0 is never a valid user process
        # Use a large PID unlikely to exist
        assert self.mod._pid_running(999999999) is False
