"""
Subscription and monetization management for Aria platform.
Handles subscription tiers, usage tracking, and feature gating.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Subscription tier levels"""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Feature(Enum):
    """Platform features that can be gated"""

    BASIC_CHAT = "basic_chat"
    ARIA_CHARACTER = "aria_character"
    QUANTUM_COMPUTING = "quantum_computing"
    ADVANCED_TRAINING = "advanced_training"
    WEBSITE_MAKER = "website_maker"
    API_ACCESS = "api_access"
    PRIORITY_SUPPORT = "priority_support"
    CUSTOM_MODELS = "custom_models"
    UNLIMITED_REQUESTS = "unlimited_requests"
    COMMERCIAL_LICENSE = "commercial_license"


# Subscription tier pricing (monthly in USD)
TIER_PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.PRO: 49,
    SubscriptionTier.ENTERPRISE: 199,
}

# Feature access matrix
TIER_FEATURES = {
    SubscriptionTier.FREE: {
        Feature.BASIC_CHAT: True,
        Feature.ARIA_CHARACTER: True,
        Feature.QUANTUM_COMPUTING: False,
        Feature.ADVANCED_TRAINING: False,
        Feature.WEBSITE_MAKER: False,
        Feature.API_ACCESS: False,
        Feature.PRIORITY_SUPPORT: False,
        Feature.CUSTOM_MODELS: False,
        Feature.UNLIMITED_REQUESTS: False,
        Feature.COMMERCIAL_LICENSE: False,
    },
    SubscriptionTier.PRO: {
        Feature.BASIC_CHAT: True,
        Feature.ARIA_CHARACTER: True,
        Feature.QUANTUM_COMPUTING: True,
        Feature.ADVANCED_TRAINING: True,
        Feature.WEBSITE_MAKER: True,
        Feature.API_ACCESS: True,
        Feature.PRIORITY_SUPPORT: False,
        Feature.CUSTOM_MODELS: False,
        Feature.UNLIMITED_REQUESTS: False,
        Feature.COMMERCIAL_LICENSE: True,
    },
    SubscriptionTier.ENTERPRISE: {
        Feature.BASIC_CHAT: True,
        Feature.ARIA_CHARACTER: True,
        Feature.QUANTUM_COMPUTING: True,
        Feature.ADVANCED_TRAINING: True,
        Feature.WEBSITE_MAKER: True,
        Feature.API_ACCESS: True,
        Feature.PRIORITY_SUPPORT: True,
        Feature.CUSTOM_MODELS: True,
        Feature.UNLIMITED_REQUESTS: True,
        Feature.COMMERCIAL_LICENSE: True,
    },
}

# Usage limits per tier (monthly)
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "chat_messages": 100,
        "quantum_jobs": 0,
        "training_hours": 0,
        "api_requests": 0,
        "websites_created": 0,
    },
    SubscriptionTier.PRO: {
        "chat_messages": 10000,
        "quantum_jobs": 50,
        "training_hours": 20,
        "api_requests": 10000,
        "websites_created": 10,
    },
    SubscriptionTier.ENTERPRISE: {
        "chat_messages": -1,  # unlimited
        "quantum_jobs": -1,
        "training_hours": -1,
        "api_requests": -1,
        "websites_created": -1,
    },
}


class Subscription:
    """Represents a user subscription"""

    def __init__(
        self,
        user_id: str,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        payment_method: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
    ):
        self.user_id = user_id
        self._tier = tier  # Use private attribute
        self.start_date = start_date or datetime.now()
        self.end_date = end_date
        self.payment_method = payment_method
        self.stripe_subscription_id = stripe_subscription_id
        self.usage = {
            "chat_messages": 0,
            "quantum_jobs": 0,
            "training_hours": 0,
            "api_requests": 0,
            "websites_created": 0,
        }
        self.usage_reset_date = datetime.now() + timedelta(days=30)
        # Cache tier limits to avoid repeated dictionary lookups
        self._tier_limits = TIER_LIMITS.get(self._tier, {})
        if not self._tier_limits:
            logger.warning(f"Unknown tier {self._tier} - using empty limits")

    @property
    def tier(self) -> SubscriptionTier:
        """Get subscription tier"""
        return self._tier

    @tier.setter
    def tier(self, value: SubscriptionTier):
        """Set subscription tier and update cached limits"""
        self._tier = value
        # Update cached tier limits whenever tier changes
        self._tier_limits = TIER_LIMITS.get(value, {})
        if not self._tier_limits:
            logger.warning(f"Unknown tier {value} - using empty limits")

    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        if self.tier == SubscriptionTier.FREE:
            return True
        if self.end_date is None:
            return True
        return datetime.now() < self.end_date

    def has_feature(self, feature: Feature) -> bool:
        """Check if subscription has access to a feature"""
        if not self.is_active():
            return False
        return TIER_FEATURES.get(self.tier, {}).get(feature, False)

    def check_limit(self, resource: str, amount: int = 1) -> bool:
        """Check if usage is within limits - optimized with cached tier limits"""
        if not self.is_active():
            return False

        # Reset usage if period expired
        if datetime.now() > self.usage_reset_date:
            self.reset_usage()

        # Use cached tier limits
        limit = self._tier_limits.get(resource, 0)
        if limit == -1:  # unlimited
            return True

        current_usage = self.usage.get(resource, 0)
        return (current_usage + amount) <= limit

    def increment_usage(self, resource: str, amount: int = 1) -> bool:
        """Increment usage counter if within limits"""
        if self.check_limit(resource, amount):
            self.usage[resource] = self.usage.get(resource, 0) + amount
            return True
        return False

    def reset_usage(self):
        """Reset monthly usage counters"""
        self.usage = {
            "chat_messages": 0,
            "quantum_jobs": 0,
            "training_hours": 0,
            "api_requests": 0,
            "websites_created": 0,
        }
        self.usage_reset_date = datetime.now() + timedelta(days=30)

    def get_usage_percentage(self, resource: str) -> float:
        """Get usage as percentage of limit - optimized with cached tier limits"""
        # Use cached tier limits
        limit = self._tier_limits.get(resource, 0)
        if limit == -1:
            return 0.0  # unlimited
        if limit == 0:
            return 100.0
        current = self.usage.get(resource, 0)
        return (current / limit) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription to dictionary"""
        return {
            "user_id": self.user_id,
            "tier": self.tier.value,
            "tier_name": self.tier.name,
            "price": TIER_PRICING[self.tier],
            "is_active": self.is_active(),
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "payment_method": self.payment_method,
            "stripe_subscription_id": self.stripe_subscription_id,
            "usage": self.usage,
            "usage_reset_date": self.usage_reset_date.isoformat(),
            "limits": TIER_LIMITS[self.tier],
            "features": {f.value: self.has_feature(f) for f in Feature},
        }


class SubscriptionManager:
    """Manages subscriptions and feature access"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data_out/subscriptions")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.subscriptions: Dict[str, Subscription] = {}
        self._load_subscriptions()

    def _load_subscriptions(self):
        """Load subscriptions from storage"""
        try:
            subscription_file = self.storage_path / "subscriptions.json"
            if subscription_file.exists():
                with open(subscription_file, "r") as f:
                    data = json.load(f)
                    for user_id, sub_data in data.items():
                        tier = SubscriptionTier(sub_data.get("tier", "free"))
                        sub = Subscription(
                            user_id=user_id,
                            tier=tier,
                            start_date=(
                                datetime.fromisoformat(sub_data["start_date"])
                                if sub_data.get("start_date")
                                else None
                            ),
                            end_date=(
                                datetime.fromisoformat(sub_data["end_date"])
                                if sub_data.get("end_date")
                                else None
                            ),
                            payment_method=sub_data.get("payment_method"),
                            stripe_subscription_id=sub_data.get(
                                "stripe_subscription_id"
                            ),
                        )
                        sub.usage = sub_data.get("usage", sub.usage)
                        if sub_data.get("usage_reset_date"):
                            sub.usage_reset_date = datetime.fromisoformat(
                                sub_data["usage_reset_date"]
                            )
                        self.subscriptions[user_id] = sub
        except Exception as e:
            logger.error(f"Failed to load subscriptions: {e}")

    def _save_subscriptions(self):
        """Save subscriptions to storage"""
        try:
            subscription_file = self.storage_path / "subscriptions.json"
            data = {
                user_id: sub.to_dict() for user_id, sub in self.subscriptions.items()
            }
            with open(subscription_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save subscriptions: {e}")

    def get_subscription(self, user_id: str) -> Subscription:
        """Get or create subscription for user"""
        if user_id not in self.subscriptions:
            self.subscriptions[user_id] = Subscription(user_id)
            self._save_subscriptions()
        return self.subscriptions[user_id]

    def upgrade_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        duration_days: int = 30,
        payment_method: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
    ) -> Subscription:
        """Upgrade user subscription"""
        sub = self.get_subscription(user_id)
        sub.tier = tier  # Property setter automatically updates _tier_limits
        sub.start_date = datetime.now()
        sub.end_date = datetime.now() + timedelta(days=duration_days)
        sub.payment_method = payment_method
        sub.stripe_subscription_id = stripe_subscription_id
        self._save_subscriptions()
        logger.info(f"Upgraded {user_id} to {tier.value}")
        return sub

    def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user subscription (downgrade to free at end of period)"""
        if user_id in self.subscriptions:
            sub = self.subscriptions[user_id]
            # Set to expire but don't immediate downgrade (grace period)
            logger.info(f"Cancelled subscription for {user_id}, expires {sub.end_date}")
            self._save_subscriptions()
            return True
        return False

    def check_access(self, user_id: str, feature: Feature) -> bool:
        """Check if user has access to a feature"""
        sub = self.get_subscription(user_id)
        return sub.has_feature(feature)

    def track_usage(self, user_id: str, resource: str, amount: int = 1) -> bool:
        """Track resource usage, returns False if limit exceeded"""
        sub = self.get_subscription(user_id)
        result = sub.increment_usage(resource, amount)
        if result:
            self._save_subscriptions()
        return result

    def get_revenue_stats(self) -> Dict[str, Any]:
        """Calculate revenue statistics"""
        stats = {
            "total_subscribers": len(self.subscriptions),
            "active_subscribers": 0,
            "by_tier": {tier.value: 0 for tier in SubscriptionTier},
            "monthly_recurring_revenue": 0,
            "annual_recurring_revenue": 0,
        }

        for sub in self.subscriptions.values():
            if sub.is_active():
                stats["active_subscribers"] += 1
                stats["by_tier"][sub.tier.value] += 1
                price = TIER_PRICING[sub.tier]
                stats["monthly_recurring_revenue"] += price

        stats["annual_recurring_revenue"] = stats["monthly_recurring_revenue"] * 12

        return stats

    def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        """Get all subscriptions as dictionaries"""
        return [sub.to_dict() for sub in self.subscriptions.values()]


# Global instance
_subscription_manager: Optional[SubscriptionManager] = None


def get_subscription_manager() -> SubscriptionManager:
    """Get global subscription manager instance"""
    global _subscription_manager
    if _subscription_manager is None:
        _subscription_manager = SubscriptionManager()
    return _subscription_manager
