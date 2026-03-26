"""Unit tests for scripts/resource_monitor.py."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path


# ─── module loader ────────────────────────────────────────────────────────────

def _load():
    path = Path(__file__).parent.parent / "scripts" / "resource_monitor.py"
    spec = importlib.util.spec_from_file_location("resource_monitor", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── _level ───────────────────────────────────────────────────────────────────

class TestLevel:
    def setup_method(self):
        self.mod = _load()

    def test_ok_below_warn_threshold(self):
        assert self.mod._level("cpu_percent", 50.0) == "ok"

    def test_warn_at_threshold(self):
        # cpu warn=75
        assert self.mod._level("cpu_percent", 75.0) == "warn"

    def test_warn_between_thresholds(self):
        assert self.mod._level("cpu_percent", 80.0) == "warn"

    def test_crit_at_threshold(self):
        # cpu crit=90
        assert self.mod._level("cpu_percent", 90.0) == "crit"

    def test_crit_above_threshold(self):
        assert self.mod._level("cpu_percent", 99.0) == "crit"

    def test_unknown_metric_returns_ok(self):
        assert self.mod._level("nonexistent_metric", 50.0) == "ok"

    def test_mem_thresholds(self):
        # mem warn=80, crit=95
        assert self.mod._level("mem_percent", 79.9) == "ok"
        assert self.mod._level("mem_percent", 80.0) == "warn"
        assert self.mod._level("mem_percent", 95.0) == "crit"

    def test_disk_thresholds(self):
        # disk warn=80, crit=90
        assert self.mod._level("disk_percent", 85.0) == "warn"
        assert self.mod._level("disk_percent", 91.0) == "crit"

    def test_gpu_mem_thresholds(self):
        assert self.mod._level("gpu_mem_percent", 79.0) == "ok"
        assert self.mod._level("gpu_mem_percent", 80.0) == "warn"
        assert self.mod._level("gpu_mem_percent", 95.0) == "crit"

    def test_zero_returns_ok(self):
        assert self.mod._level("cpu_percent", 0.0) == "ok"


# ─── _badge ───────────────────────────────────────────────────────────────────

class TestBadge:
    def setup_method(self):
        self.mod = _load()

    def test_ok_badge(self):
        assert self.mod._badge("ok") == "✅"

    def test_warn_badge(self):
        b = self.mod._badge("warn")
        assert "⚠" in b

    def test_crit_badge(self):
        assert self.mod._badge("crit") == "🔴"

    def test_unknown_level_returns_question_mark(self):
        assert self.mod._badge("unknown") == "❓"


# ─── _bar ─────────────────────────────────────────────────────────────────────

class TestBar:
    def setup_method(self):
        self.mod = _load()

    def test_zero_percent_bar(self):
        result = self.mod._bar(0.0, width=10)
        assert result.startswith("[")
        assert "░" * 10 in result
        assert "0.0%" in result

    def test_hundred_percent_bar(self):
        result = self.mod._bar(100.0, width=10)
        assert "█" * 10 in result
        assert "100.0%" in result

    def test_fifty_percent_bar(self):
        result = self.mod._bar(50.0, width=20)
        # 50% of 20 = 10 filled, 10 empty
        assert result.count("█") == 10
        assert result.count("░") == 10

    def test_bar_total_length(self):
        # "[" + width chars + "] " + pct string
        result = self.mod._bar(75.0, width=20)
        inner = result[1:21]  # strip "[" and count 20 chars
        assert len(inner) == 20

    def test_custom_width(self):
        result = self.mod._bar(100.0, width=5)
        assert result.count("█") == 5


# ─── collect_snapshot ─────────────────────────────────────────────────────────

class TestCollectSnapshot:
    def setup_method(self):
        self.mod = _load()

    def test_returns_dict(self):
        snap = self.mod.collect_snapshot()
        assert isinstance(snap, dict)

    def test_has_required_keys(self):
        snap = self.mod.collect_snapshot()
        assert "timestamp" in snap
        assert "cpu_mem" in snap
        assert "disks" in snap
        assert "gpus" in snap

    def test_timestamp_is_iso_string(self):
        snap = self.mod.collect_snapshot()
        ts = snap["timestamp"]
        assert isinstance(ts, str)
        assert "T" in ts or len(ts) >= 10

    def test_cpu_mem_is_dict(self):
        snap = self.mod.collect_snapshot()
        assert isinstance(snap["cpu_mem"], dict)

    def test_disks_is_list(self):
        snap = self.mod.collect_snapshot()
        assert isinstance(snap["disks"], list)

    def test_gpus_is_list(self):
        snap = self.mod.collect_snapshot()
        assert isinstance(snap["gpus"], list)

    def test_snapshot_is_json_serializable(self):
        snap = self.mod.collect_snapshot()
        serialized = json.dumps(snap)
        assert isinstance(serialized, str)


# ─── thresholds constant ──────────────────────────────────────────────────────

class TestThresholds:
    def setup_method(self):
        self.mod = _load()

    def test_all_expected_keys_present(self):
        keys = {"cpu_percent", "mem_percent", "disk_percent",
                "gpu_mem_percent", "gpu_util"}
        assert keys == set(self.mod.THRESHOLDS.keys())

    def test_warn_less_than_crit_for_all(self):
        for k, v in self.mod.THRESHOLDS.items():
            assert v["warn"] < v["crit"], f"{k}: warn >= crit"

    def test_all_values_positive(self):
        for k, v in self.mod.THRESHOLDS.items():
            assert v["warn"] > 0, f"{k}: warn not positive"
            assert v["crit"] > 0, f"{k}: crit not positive"
