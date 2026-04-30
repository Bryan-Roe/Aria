"""Comprehensive tests for shared/referral_system.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from shared.referral_system import ReferralSystem, get_referral_system


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def referral_system(tmp_path):
    """Return a ReferralSystem using tmp_path for storage isolation."""
    rs = ReferralSystem.__new__(ReferralSystem)
    rs.referrals_file = tmp_path / "referrals.json"
    rs.referrals_data = {}
    rs.commission_rates = {"pro": 0.20, "enterprise": 0.20}
    rs.milestone_bonuses = {5: 50, 10: 100, 25: 300, 50: 750, 100: 2000}
    return rs


# ---------------------------------------------------------------------------
# generate_referral_code
# ---------------------------------------------------------------------------


class TestGenerateReferralCode:
    def test_returns_string(self, referral_system):
        code = referral_system.generate_referral_code("user1")
        assert isinstance(code, str)

    def test_code_format(self, referral_system):
        code = referral_system.generate_referral_code("user1")
        # Format: first 4 chars of user_id upper + 6 hex chars
        assert code[:4] == "USER"

    def test_stores_new_user_data(self, referral_system):
        referral_system.generate_referral_code("user1")
        assert "user1" in referral_system.referrals_data

    def test_initial_data_structure(self, referral_system):
        referral_system.generate_referral_code("user1")
        data = referral_system.referrals_data["user1"]
        assert data["referral_count"] == 0
        assert data["total_commission"] == pytest.approx(0.0)
        assert data["pending_commission"] == pytest.approx(0.0)
        assert data["paid_commission"] == pytest.approx(0.0)
        assert data["referrals"] == []

    def test_updates_code_for_existing_user(self, referral_system):
        code1 = referral_system.generate_referral_code("user1")
        code2 = referral_system.generate_referral_code("user1")
        assert referral_system.referrals_data["user1"]["referral_code"] == code2

    def test_saves_referrals(self, referral_system):
        referral_system.generate_referral_code("user1")
        assert referral_system.referrals_file.exists()

    def test_different_users_different_codes(self, referral_system):
        code1 = referral_system.generate_referral_code("user1")
        code2 = referral_system.generate_referral_code("user2")
        # The hex suffix is randomly generated; codes should be distinct
        assert code1 != code2


# ---------------------------------------------------------------------------
# get_referral_code
# ---------------------------------------------------------------------------


class TestGetReferralCode:
    def test_returns_none_for_unknown_user(self, referral_system):
        assert referral_system.get_referral_code("unknown") is None

    def test_returns_code_for_known_user(self, referral_system):
        code = referral_system.generate_referral_code("user1")
        assert referral_system.get_referral_code("user1") == code


# ---------------------------------------------------------------------------
# record_referral
# ---------------------------------------------------------------------------


class TestRecordReferral:
    def test_invalid_referral_code_returns_error(self, referral_system):
        result = referral_system.record_referral("INVALID", "new_user", "pro", 49.0)
        assert result["success"] is False
        assert "Invalid referral code" in result["error"]

    def test_successful_referral(self, referral_system):
        code = referral_system.generate_referral_code("referrer1")
        result = referral_system.record_referral(code, "new_user", "pro", 49.0)
        assert result["success"] is True
        assert result["referrer_id"] == "referrer1"

    def test_commission_calculated_correctly(self, referral_system):
        code = referral_system.generate_referral_code("referrer1")
        result = referral_system.record_referral(code, "new_user", "pro", 49.0)
        expected = 49.0 * 0.20
        assert result["commission"] == pytest.approx(expected)

    def test_enterprise_commission(self, referral_system):
        code = referral_system.generate_referral_code("referrer1")
        result = referral_system.record_referral(code, "new_user", "enterprise", 199.0)
        expected = 199.0 * 0.20
        assert result["commission"] == pytest.approx(expected)

    def test_referral_count_increments(self, referral_system):
        code = referral_system.generate_referral_code("referrer1")
        referral_system.record_referral(code, "user_a", "pro", 49.0)
        referral_system.record_referral(code, "user_b", "pro", 49.0)
        data = referral_system.referrals_data["referrer1"]
        assert data["referral_count"] == 2

    def test_pending_commission_accumulates(self, referral_system):
        code = referral_system.generate_referral_code("referrer1")
        referral_system.record_referral(code, "user_a", "pro", 49.0)
        referral_system.record_referral(code, "user_b", "pro", 49.0)
        data = referral_system.referrals_data["referrer1"]
        assert data["pending_commission"] == pytest.approx(2 * 49.0 * 0.20)

    def test_milestone_bonus_at_5_referrals(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        data = referral_system.referrals_data["ref1"]
        data["referral_count"] = 4  # next one hits milestone 5
        for i in range(5):
            referral_system.record_referral(code, f"user_{i}", "pro", 49.0)

        assert 5 in referral_system.referrals_data["ref1"]["milestone_bonuses_earned"]

    def test_milestone_bonus_only_awarded_once(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        data = referral_system.referrals_data["ref1"]
        data["referral_count"] = 4
        data["milestone_bonuses_earned"] = [5]  # already awarded

        before = data["pending_commission"]
        referral_system.record_referral(code, "user_x", "pro", 49.0)
        # Bonus should not be added again
        after = referral_system.referrals_data["ref1"]["pending_commission"]
        diff = after - before
        assert diff == pytest.approx(49.0 * 0.20)  # only commission, no bonus

    def test_unknown_tier_uses_default_rate(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        result = referral_system.record_referral(code, "user_x", "unknown_tier", 100.0)
        assert result["success"] is True
        # Default rate is 0.15
        assert result["commission"] == pytest.approx(100.0 * 0.15)

    def test_referral_notification_called(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        with patch.object(referral_system, "_notify_referral") as mock_notify:
            referral_system.record_referral(code, "new_user", "pro", 49.0)
        mock_notify.assert_called_once()

    def test_referral_notification_failure_does_not_crash(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        # Patch get_email_system to raise so the exception is caught inside _notify_referral
        with patch("shared.referral_system.get_referral_system", side_effect=Exception("import error")):
            with patch("shared.email_notifications.get_email_system", side_effect=Exception("SMTP down")):
                # Should not raise — _notify_referral catches all exceptions
                result = referral_system.record_referral(code, "new_user", "pro", 49.0)
        assert result["success"] is True


# ---------------------------------------------------------------------------
# get_referral_stats
# ---------------------------------------------------------------------------


class TestGetReferralStats:
    def test_stats_for_unknown_user(self, referral_system):
        stats = referral_system.get_referral_stats("ghost")
        assert stats["referral_count"] == 0
        assert stats["total_commission"] == pytest.approx(0.0)
        assert stats["referral_code"] is None

    def test_stats_for_user_with_no_referrals(self, referral_system):
        referral_system.generate_referral_code("user1")
        stats = referral_system.get_referral_stats("user1")
        assert stats["referral_count"] == 0

    def test_stats_show_next_milestone(self, referral_system):
        referral_system.generate_referral_code("user1")
        stats = referral_system.get_referral_stats("user1")
        assert stats["next_milestone"] is not None
        assert stats["next_milestone"]["count"] == 5

    def test_stats_next_milestone_none_after_max(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["referral_count"] = 100
        stats = referral_system.get_referral_stats("user1")
        assert stats["next_milestone"] is None

    def test_active_referral_count(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        referral_system.record_referral(code, "u1", "pro", 49.0)
        # Manually add a cancelled referral
        referral_system.referrals_data["ref1"]["referrals"].append(
            {"referred_user_id": "u2", "status": "cancelled", "commission": 9.8}
        )
        stats = referral_system.get_referral_stats("ref1")
        assert stats["active_referral_count"] == 1


# ---------------------------------------------------------------------------
# process_payout
# ---------------------------------------------------------------------------


class TestProcessPayout:
    def test_unknown_user_returns_error(self, referral_system):
        result = referral_system.process_payout("ghost")
        assert result["success"] is False

    def test_below_minimum_returns_error(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 10.0
        result = referral_system.process_payout("user1")
        assert result["success"] is False
        assert "Minimum payout" in result["error"]

    def test_successful_payout(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 50.0
        result = referral_system.process_payout("user1")
        assert result["success"] is True
        assert result["amount"] == pytest.approx(50.0)

    def test_payout_clears_pending(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 50.0
        referral_system.process_payout("user1")
        assert referral_system.referrals_data["user1"]["pending_commission"] == pytest.approx(0.0)

    def test_payout_adds_to_paid(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 50.0
        referral_system.referrals_data["user1"]["paid_commission"] = 25.0
        referral_system.process_payout("user1")
        assert referral_system.referrals_data["user1"]["paid_commission"] == pytest.approx(75.0)

    def test_payout_records_in_payouts_list(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 50.0
        referral_system.process_payout("user1")
        assert len(referral_system.referrals_data["user1"]["payouts"]) == 1

    def test_exact_minimum_threshold(self, referral_system):
        referral_system.generate_referral_code("user1")
        referral_system.referrals_data["user1"]["pending_commission"] = 25.0
        result = referral_system.process_payout("user1")
        assert result["success"] is True


# ---------------------------------------------------------------------------
# get_leaderboard
# ---------------------------------------------------------------------------


class TestGetLeaderboard:
    def test_empty_leaderboard(self, referral_system):
        lb = referral_system.get_leaderboard()
        assert lb == []

    def test_leaderboard_sorted_by_commission(self, referral_system):
        referral_system.referrals_data = {
            "u1": {"referral_count": 3, "total_commission": 30.0},
            "u2": {"referral_count": 5, "total_commission": 100.0},
            "u3": {"referral_count": 1, "total_commission": 10.0},
        }
        lb = referral_system.get_leaderboard()
        assert lb[0]["user_id"] == "u2"
        assert lb[1]["user_id"] == "u1"
        assert lb[2]["user_id"] == "u3"

    def test_leaderboard_ranks_assigned(self, referral_system):
        referral_system.referrals_data = {
            "u1": {"referral_count": 1, "total_commission": 10.0},
            "u2": {"referral_count": 2, "total_commission": 20.0},
        }
        lb = referral_system.get_leaderboard()
        assert lb[0]["rank"] == 1
        assert lb[1]["rank"] == 2

    def test_leaderboard_respects_limit(self, referral_system):
        for i in range(15):
            referral_system.referrals_data[f"u{i}"] = {
                "referral_count": i,
                "total_commission": float(i),
            }
        lb = referral_system.get_leaderboard(limit=5)
        assert len(lb) == 5


# ---------------------------------------------------------------------------
# cancel_referral
# ---------------------------------------------------------------------------


class TestCancelReferral:
    def test_cancel_unknown_referrer(self, referral_system):
        assert referral_system.cancel_referral("ghost", "user1") is False

    def test_cancel_nonexistent_referred_user(self, referral_system):
        referral_system.generate_referral_code("ref1")
        assert referral_system.cancel_referral("ref1", "ghost") is False

    def test_cancel_active_referral(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        referral_system.record_referral(code, "user1", "pro", 49.0)
        result = referral_system.cancel_referral("ref1", "user1")
        assert result is True
        referral = referral_system.referrals_data["ref1"]["referrals"][0]
        assert referral["status"] == "cancelled"

    def test_cancel_reduces_pending_commission(self, referral_system):
        code = referral_system.generate_referral_code("ref1")
        referral_system.record_referral(code, "user1", "pro", 49.0)
        commission = 49.0 * 0.20
        before = referral_system.referrals_data["ref1"]["pending_commission"]
        referral_system.cancel_referral("ref1", "user1")
        after = referral_system.referrals_data["ref1"]["pending_commission"]
        assert after == pytest.approx(before - commission)

    def test_cancel_already_cancelled_referral(self, referral_system):
        referral_system.generate_referral_code("ref1")
        referral_system.referrals_data["ref1"]["referrals"] = [
            {"referred_user_id": "user1", "status": "cancelled", "commission": 9.8}
        ]
        result = referral_system.cancel_referral("ref1", "user1")
        assert result is False


# ---------------------------------------------------------------------------
# _load_referrals / _save_referrals
# ---------------------------------------------------------------------------


class TestLoadSaveReferrals:
    def test_loads_existing_file(self, tmp_path):
        data = {"user1": {"referral_code": "TEST12", "referral_count": 1, "total_commission": 10.0}}
        rs = ReferralSystem.__new__(ReferralSystem)
        rs.referrals_file = tmp_path / "referrals.json"
        rs.referrals_file.write_text(json.dumps(data))
        loaded = rs._load_referrals()
        assert loaded == data

    def test_returns_empty_dict_when_file_missing(self, tmp_path):
        rs = ReferralSystem.__new__(ReferralSystem)
        rs.referrals_file = tmp_path / "no_file.json"
        loaded = rs._load_referrals()
        assert loaded == {}

    def test_returns_empty_dict_on_corrupt_file(self, tmp_path):
        rs = ReferralSystem.__new__(ReferralSystem)
        rs.referrals_file = tmp_path / "referrals.json"
        rs.referrals_file.write_text("not json")
        loaded = rs._load_referrals()
        assert loaded == {}

    def test_save_creates_file(self, tmp_path):
        rs = ReferralSystem.__new__(ReferralSystem)
        rs.referrals_file = tmp_path / "referrals.json"
        rs.referrals_data = {"u1": {"referral_count": 0}}
        rs._save_referrals()
        assert rs.referrals_file.exists()

    def test_save_and_reload_roundtrip(self, tmp_path):
        rs = ReferralSystem.__new__(ReferralSystem)
        rs.referrals_file = tmp_path / "referrals.json"
        rs.referrals_data = {"u1": {"referral_code": "U1AB1C", "referral_count": 3}}
        rs._save_referrals()
        loaded = rs._load_referrals()
        assert loaded["u1"]["referral_count"] == 3


# ---------------------------------------------------------------------------
# get_referral_system (singleton)
# ---------------------------------------------------------------------------


class TestGetReferralSystem:
    def test_returns_referral_system_instance(self):
        import shared.referral_system as rs_module

        rs_module._referral_system = None
        with patch.object(ReferralSystem, "__init__", lambda self: None):
            with patch.object(ReferralSystem, "_load_referrals", return_value={}):
                # Just check type
                pass

        # Use the real factory
        rs_module._referral_system = None
        try:
            system = get_referral_system()
            assert isinstance(system, ReferralSystem)
        finally:
            rs_module._referral_system = None

    def test_singleton_behavior(self):
        import shared.referral_system as rs_module

        rs_module._referral_system = None
        try:
            s1 = get_referral_system()
            s2 = get_referral_system()
            assert s1 is s2
        finally:
            rs_module._referral_system = None
