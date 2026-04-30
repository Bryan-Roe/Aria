"""Comprehensive tests for shared/subscription_manager.py."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from shared.subscription_manager import (
    TIER_FEATURES,
    TIER_LIMITS,
    TIER_PRICING,
    Feature,
    Subscription,
    SubscriptionManager,
    SubscriptionTier,
    get_subscription_manager,
)


# ---------------------------------------------------------------------------
# SubscriptionTier enum
# ---------------------------------------------------------------------------


class TestSubscriptionTierEnum:
    def test_all_tiers_defined(self):
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.PRO.value == "pro"
        assert SubscriptionTier.ENTERPRISE.value == "enterprise"

    def test_tier_pricing_defined_for_all(self):
        for tier in SubscriptionTier:
            assert tier in TIER_PRICING

    def test_tier_limits_defined_for_all(self):
        for tier in SubscriptionTier:
            assert tier in TIER_LIMITS

    def test_tier_features_defined_for_all(self):
        for tier in SubscriptionTier:
            assert tier in TIER_FEATURES


# ---------------------------------------------------------------------------
# Feature enum
# ---------------------------------------------------------------------------


class TestFeatureEnum:
    def test_basic_chat_defined(self):
        assert Feature.BASIC_CHAT.value == "basic_chat"

    def test_all_features_in_tier_matrix(self):
        for tier in SubscriptionTier:
            for feature in Feature:
                assert feature in TIER_FEATURES[tier]


# ---------------------------------------------------------------------------
# Subscription — construction
# ---------------------------------------------------------------------------


class TestSubscriptionConstruction:
    def test_defaults_to_free_tier(self):
        sub = Subscription("u1")
        assert sub.tier == SubscriptionTier.FREE
        assert sub.user_id == "u1"

    def test_custom_tier(self):
        sub = Subscription("u2", tier=SubscriptionTier.PRO)
        assert sub.tier == SubscriptionTier.PRO

    def test_initial_usage_zeroed(self):
        sub = Subscription("u3")
        for v in sub.usage.values():
            assert v == 0

    def test_start_date_defaults_to_now(self):
        before = datetime.now()
        sub = Subscription("u4")
        after = datetime.now()
        assert before <= sub.start_date <= after

    def test_custom_start_end_date(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        sub = Subscription("u5", start_date=start, end_date=end)
        assert sub.start_date == start
        assert sub.end_date == end

    def test_stripe_subscription_id(self):
        sub = Subscription("u6", stripe_subscription_id="sub_abc123")
        assert sub.stripe_subscription_id == "sub_abc123"


# ---------------------------------------------------------------------------
# Subscription.tier property / setter
# ---------------------------------------------------------------------------


class TestSubscriptionTierProperty:
    def test_tier_setter_updates_cached_limits(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub._tier_limits == TIER_LIMITS[SubscriptionTier.FREE]
        sub.tier = SubscriptionTier.PRO
        assert sub._tier_limits == TIER_LIMITS[SubscriptionTier.PRO]

    def test_tier_getter_returns_current(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.tier = SubscriptionTier.ENTERPRISE
        assert sub.tier == SubscriptionTier.ENTERPRISE


# ---------------------------------------------------------------------------
# Subscription.is_active
# ---------------------------------------------------------------------------


class TestSubscriptionIsActive:
    def test_free_always_active(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.is_active() is True

    def test_free_with_past_end_date_still_active(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE, end_date=datetime(2000, 1, 1))
        assert sub.is_active() is True

    def test_pro_active_without_end_date(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        assert sub.is_active() is True

    def test_pro_active_with_future_end_date(self):
        sub = Subscription(
            "u1",
            tier=SubscriptionTier.PRO,
            end_date=datetime.now() + timedelta(days=30),
        )
        assert sub.is_active() is True

    def test_pro_inactive_with_past_end_date(self):
        sub = Subscription(
            "u1",
            tier=SubscriptionTier.PRO,
            end_date=datetime.now() - timedelta(seconds=1),
        )
        assert sub.is_active() is False


# ---------------------------------------------------------------------------
# Subscription.has_feature
# ---------------------------------------------------------------------------


class TestSubscriptionHasFeature:
    def test_free_has_basic_chat(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.has_feature(Feature.BASIC_CHAT) is True

    def test_free_lacks_quantum(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.has_feature(Feature.QUANTUM_COMPUTING) is False

    def test_pro_has_quantum(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        assert sub.has_feature(Feature.QUANTUM_COMPUTING) is True

    def test_enterprise_has_all_features(self):
        sub = Subscription("u1", tier=SubscriptionTier.ENTERPRISE)
        for feature in Feature:
            assert sub.has_feature(feature) is True

    def test_inactive_sub_has_no_features(self):
        sub = Subscription(
            "u1",
            tier=SubscriptionTier.PRO,
            end_date=datetime.now() - timedelta(days=1),
        )
        assert sub.has_feature(Feature.QUANTUM_COMPUTING) is False


# ---------------------------------------------------------------------------
# Subscription.check_limit
# ---------------------------------------------------------------------------


class TestSubscriptionCheckLimit:
    def test_free_chat_within_limit(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.check_limit("chat_messages", 1) is True

    def test_free_chat_at_limit_boundary(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 99
        assert sub.check_limit("chat_messages", 1) is True

    def test_free_chat_exceeds_limit(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 100
        assert sub.check_limit("chat_messages", 1) is False

    def test_free_quantum_always_false(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.check_limit("quantum_jobs", 1) is False

    def test_enterprise_unlimited(self):
        sub = Subscription("u1", tier=SubscriptionTier.ENTERPRISE)
        sub.usage["chat_messages"] = 999999
        assert sub.check_limit("chat_messages", 1) is True

    def test_inactive_sub_check_limit_false(self):
        sub = Subscription(
            "u1",
            tier=SubscriptionTier.PRO,
            end_date=datetime.now() - timedelta(days=1),
        )
        assert sub.check_limit("chat_messages", 1) is False

    def test_check_limit_resets_if_period_expired(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 100
        # Expire the reset date in the past
        sub.usage_reset_date = datetime.now() - timedelta(seconds=1)
        # After reset, usage goes back to 0
        assert sub.check_limit("chat_messages", 1) is True

    def test_unknown_resource_defaults_to_zero_limit(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.check_limit("unknown_resource", 1) is False


# ---------------------------------------------------------------------------
# Subscription.increment_usage
# ---------------------------------------------------------------------------


class TestSubscriptionIncrementUsage:
    def test_increment_within_limit(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        result = sub.increment_usage("chat_messages")
        assert result is True
        assert sub.usage["chat_messages"] == 1

    def test_increment_exceeds_limit_returns_false(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 100
        result = sub.increment_usage("chat_messages")
        assert result is False
        assert sub.usage["chat_messages"] == 100

    def test_increment_by_custom_amount(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        sub.increment_usage("chat_messages", 5)
        assert sub.usage["chat_messages"] == 5

    def test_enterprise_unlimited_increment(self):
        sub = Subscription("u1", tier=SubscriptionTier.ENTERPRISE)
        for _ in range(100):
            assert sub.increment_usage("chat_messages") is True
        assert sub.usage["chat_messages"] == 100


# ---------------------------------------------------------------------------
# Subscription.reset_usage
# ---------------------------------------------------------------------------


class TestSubscriptionResetUsage:
    def test_reset_clears_all_counters(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        sub.usage["chat_messages"] = 500
        sub.usage["quantum_jobs"] = 10
        sub.reset_usage()
        for v in sub.usage.values():
            assert v == 0

    def test_reset_extends_reset_date(self):
        sub = Subscription("u1")
        old_reset = sub.usage_reset_date
        sub.reset_usage()
        assert sub.usage_reset_date > old_reset


# ---------------------------------------------------------------------------
# Subscription.get_usage_percentage
# ---------------------------------------------------------------------------


class TestSubscriptionGetUsagePercentage:
    def test_zero_usage(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.get_usage_percentage("chat_messages") == pytest.approx(0.0)

    def test_fifty_percent(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 50
        assert sub.get_usage_percentage("chat_messages") == pytest.approx(50.0)

    def test_hundred_percent(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        sub.usage["chat_messages"] = 100
        assert sub.get_usage_percentage("chat_messages") == pytest.approx(100.0)

    def test_unlimited_returns_zero(self):
        sub = Subscription("u1", tier=SubscriptionTier.ENTERPRISE)
        sub.usage["chat_messages"] = 99999
        assert sub.get_usage_percentage("chat_messages") == pytest.approx(0.0)

    def test_zero_limit_returns_100(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        assert sub.get_usage_percentage("quantum_jobs") == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Subscription.to_dict
# ---------------------------------------------------------------------------


class TestSubscriptionToDict:
    def test_required_keys_present(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        d = sub.to_dict()
        required = [
            "user_id", "tier", "tier_name", "price", "is_active",
            "start_date", "end_date", "usage", "limits", "features",
        ]
        for key in required:
            assert key in d, f"Missing key: {key}"

    def test_tier_value_correct(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        d = sub.to_dict()
        assert d["tier"] == "pro"
        assert d["tier_name"] == "PRO"

    def test_price_correct(self):
        sub = Subscription("u1", tier=SubscriptionTier.PRO)
        d = sub.to_dict()
        assert d["price"] == TIER_PRICING[SubscriptionTier.PRO]

    def test_features_dict_has_all_features(self):
        sub = Subscription("u1", tier=SubscriptionTier.FREE)
        d = sub.to_dict()
        for feature in Feature:
            assert feature.value in d["features"]

    def test_no_end_date_when_none(self):
        sub = Subscription("u1")
        d = sub.to_dict()
        assert d["end_date"] is None


# ---------------------------------------------------------------------------
# SubscriptionManager
# ---------------------------------------------------------------------------


class TestSubscriptionManager:
    def test_get_subscription_creates_new_for_unknown_user(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        sub = mgr.get_subscription("new_user")
        assert sub.user_id == "new_user"
        assert sub.tier == SubscriptionTier.FREE

    def test_get_subscription_returns_same_instance(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        sub1 = mgr.get_subscription("u1")
        sub2 = mgr.get_subscription("u1")
        assert sub1 is sub2

    def test_upgrade_subscription(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.get_subscription("u1")
        sub = mgr.upgrade_subscription("u1", SubscriptionTier.PRO)
        assert sub.tier == SubscriptionTier.PRO

    def test_upgrade_sets_end_date(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        before = datetime.now()
        sub = mgr.upgrade_subscription("u1", SubscriptionTier.PRO, duration_days=30)
        after = datetime.now()
        assert sub.end_date > before
        assert sub.end_date <= after + timedelta(days=30, seconds=1)

    def test_upgrade_with_payment_info(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        sub = mgr.upgrade_subscription(
            "u1",
            SubscriptionTier.PRO,
            payment_method="card_xxx",
            stripe_subscription_id="sub_yyy",
        )
        assert sub.payment_method == "card_xxx"
        assert sub.stripe_subscription_id == "sub_yyy"

    def test_cancel_subscription_existing_user(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.get_subscription("u1")
        result = mgr.cancel_subscription("u1")
        assert result is True

    def test_cancel_subscription_nonexistent_user(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        result = mgr.cancel_subscription("ghost")
        assert result is False

    def test_check_access(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.get_subscription("u1")
        assert mgr.check_access("u1", Feature.BASIC_CHAT) is True
        assert mgr.check_access("u1", Feature.QUANTUM_COMPUTING) is False

    def test_track_usage_within_limit(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.get_subscription("u1")
        assert mgr.track_usage("u1", "chat_messages") is True

    def test_track_usage_exceeds_limit(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        sub = mgr.get_subscription("u1")
        sub.usage["chat_messages"] = 100
        assert mgr.track_usage("u1", "chat_messages") is False

    def test_get_revenue_stats_empty(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        stats = mgr.get_revenue_stats()
        assert stats["total_subscribers"] == 0
        assert stats["monthly_recurring_revenue"] == 0

    def test_get_revenue_stats_with_subscribers(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.upgrade_subscription("u1", SubscriptionTier.PRO)
        mgr.upgrade_subscription("u2", SubscriptionTier.ENTERPRISE)
        stats = mgr.get_revenue_stats()
        assert stats["total_subscribers"] == 2
        expected_mrr = TIER_PRICING[SubscriptionTier.PRO] + TIER_PRICING[SubscriptionTier.ENTERPRISE]
        assert stats["monthly_recurring_revenue"] == expected_mrr
        assert stats["annual_recurring_revenue"] == expected_mrr * 12

    def test_get_all_subscriptions(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.get_subscription("u1")
        mgr.get_subscription("u2")
        all_subs = mgr.get_all_subscriptions()
        assert len(all_subs) == 2

    def test_save_and_load_subscriptions(self, tmp_path):
        mgr = SubscriptionManager(storage_path=tmp_path)
        mgr.upgrade_subscription("u1", SubscriptionTier.PRO, payment_method="card")
        # Create a new manager from same path — should reload
        mgr2 = SubscriptionManager(storage_path=tmp_path)
        sub = mgr2.get_subscription("u1")
        assert sub.tier == SubscriptionTier.PRO

    def test_load_handles_corrupt_file(self, tmp_path):
        sub_file = tmp_path / "subscriptions.json"
        sub_file.write_text("not valid json")
        mgr = SubscriptionManager(storage_path=tmp_path)
        # Should not crash, just have empty subscriptions
        assert mgr.subscriptions == {}

    def test_load_from_file_with_usage_and_reset_date(self, tmp_path):
        sub_file = tmp_path / "subscriptions.json"
        data = {
            "u1": {
                "user_id": "u1",
                "tier": "pro",
                "start_date": "2024-01-01T00:00:00",
                "end_date": "2025-01-01T00:00:00",
                "payment_method": None,
                "stripe_subscription_id": None,
                "usage": {"chat_messages": 42, "quantum_jobs": 0, "training_hours": 0,
                          "api_requests": 0, "websites_created": 0},
                "usage_reset_date": "2024-02-01T00:00:00",
                "limits": {},
                "features": {},
                "tier_name": "PRO",
                "price": 49,
                "is_active": True,
            }
        }
        sub_file.write_text(json.dumps(data))
        mgr = SubscriptionManager(storage_path=tmp_path)
        sub = mgr.get_subscription("u1")
        assert sub.tier == SubscriptionTier.PRO
        assert sub.usage["chat_messages"] == 42


# ---------------------------------------------------------------------------
# get_subscription_manager (singleton)
# ---------------------------------------------------------------------------


class TestGetSubscriptionManager:
    def test_returns_subscription_manager_instance(self):
        import shared.subscription_manager as sm_module

        sm_module._subscription_manager = None
        mgr = get_subscription_manager()
        assert isinstance(mgr, SubscriptionManager)

    def test_singleton_behavior(self):
        import shared.subscription_manager as sm_module

        sm_module._subscription_manager = None
        mgr1 = get_subscription_manager()
        mgr2 = get_subscription_manager()
        assert mgr1 is mgr2

    def teardown_method(self):
        import shared.subscription_manager as sm_module

        sm_module._subscription_manager = None
