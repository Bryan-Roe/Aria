"""
Referral and Affiliate System for Aria monetization
Tracks referrals, calculates commissions, and manages payouts
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import secrets

logger = logging.getLogger(__name__)


class ReferralSystem:
    """Manages referral and affiliate program"""
    
    def __init__(self):
        self.referrals_file = Path("data_out/referrals/referrals.json")
        self.referrals_file.parent.mkdir(parents=True, exist_ok=True)
        self.referrals_data = self._load_referrals()
        
        # Commission rates (percentage of revenue)
        self.commission_rates = {
            "pro": 0.20,  # 20% of $49 = $9.80 per referral
            "enterprise": 0.20,  # 20% of $199 = $39.80 per referral
        }
        
        # Bonus for reaching milestones
        self.milestone_bonuses = {
            5: 50,    # $50 bonus at 5 referrals
            10: 100,  # $100 bonus at 10 referrals
            25: 300,  # $300 bonus at 25 referrals
            50: 750,  # $750 bonus at 50 referrals
            100: 2000  # $2,000 bonus at 100 referrals
        }
    
    def generate_referral_code(self, user_id: str) -> str:
        """Generate unique referral code for user"""
        # Create short, memorable code
        code = f"{user_id[:4].upper()}{secrets.token_hex(3).upper()}"
        
        # Store in user's referral data
        if user_id not in self.referrals_data:
            self.referrals_data[user_id] = {
                "user_id": user_id,
                "referral_code": code,
                "referrals": [],
                "total_commission": 0.0,
                "pending_commission": 0.0,
                "paid_commission": 0.0,
                "created_at": datetime.now().isoformat(),
                "referral_count": 0,
                "milestone_bonuses_earned": []
            }
        else:
            self.referrals_data[user_id]["referral_code"] = code
        
        self._save_referrals()
        return code
    
    def get_referral_code(self, user_id: str) -> Optional[str]:
        """Get user's referral code"""
        if user_id in self.referrals_data:
            return self.referrals_data[user_id].get("referral_code")
        return None
    
    def record_referral(
        self,
        referrer_code: str,
        new_user_id: str,
        tier: str,
        subscription_value: float
    ) -> Dict[str, Any]:
        """
        Record a new referral
        
        Args:
            referrer_code: Referral code used
            new_user_id: ID of new user who signed up
            tier: Subscription tier (pro/enterprise)
            subscription_value: Monthly subscription value
        
        Returns:
            Dict with referral details and commission
        """
        # Find referrer by code
        referrer_id = None
        for user_id, data in self.referrals_data.items():
            if data.get("referral_code") == referrer_code:
                referrer_id = user_id
                break
        
        if not referrer_id:
            logger.error(f"Invalid referral code: {referrer_code}")
            return {"success": False, "error": "Invalid referral code"}
        
        # Calculate commission
        commission_rate = self.commission_rates.get(tier.lower(), 0.15)
        commission = subscription_value * commission_rate
        
        # Create referral record
        referral = {
            "referred_user_id": new_user_id,
            "tier": tier,
            "subscription_value": subscription_value,
            "commission": commission,
            "status": "active",
            "referred_at": datetime.now().isoformat(),
            "last_payment": datetime.now().isoformat()
        }
        
        # Update referrer's data
        referrer_data = self.referrals_data[referrer_id]
        referrer_data["referrals"].append(referral)
        referrer_data["referral_count"] += 1
        referrer_data["pending_commission"] += commission
        referrer_data["total_commission"] += commission
        
        # Check for milestone bonuses
        count = referrer_data["referral_count"]
        if count in self.milestone_bonuses:
            bonus = self.milestone_bonuses[count]
            if count not in referrer_data.get("milestone_bonuses_earned", []):
                referrer_data["pending_commission"] += bonus
                referrer_data["total_commission"] += bonus
                referrer_data.setdefault("milestone_bonuses_earned", []).append(count)
                logger.info(f"Milestone bonus earned: {count} referrals = ${bonus}")
        
        self._save_referrals()
        
        # Send notification
        self._notify_referral(referrer_id, new_user_id, commission)
        
        return {
            "success": True,
            "referrer_id": referrer_id,
            "commission": commission,
            "total_commission": referrer_data["total_commission"],
            "referral_count": count
        }
    
    def get_referral_stats(self, user_id: str) -> Dict[str, Any]:
        """Get referral statistics for user"""
        if user_id not in self.referrals_data:
            return {
                "referral_code": None,
                "referral_count": 0,
                "total_commission": 0.0,
                "pending_commission": 0.0,
                "paid_commission": 0.0,
                "referrals": []
            }
        
        data = self.referrals_data[user_id]
        
        # Calculate active referrals
        active_referrals = [
            r for r in data.get("referrals", [])
            if r["status"] == "active"
        ]
        
        # Next milestone
        next_milestone = None
        current_count = data["referral_count"]
        for milestone in sorted(self.milestone_bonuses.keys()):
            if current_count < milestone:
                next_milestone = {
                    "count": milestone,
                    "bonus": self.milestone_bonuses[milestone],
                    "remaining": milestone - current_count
                }
                break
        
        return {
            "referral_code": data.get("referral_code"),
            "referral_count": data["referral_count"],
            "active_referral_count": len(active_referrals),
            "total_commission": data["total_commission"],
            "pending_commission": data["pending_commission"],
            "paid_commission": data["paid_commission"],
            "referrals": data.get("referrals", []),
            "next_milestone": next_milestone,
            "milestone_bonuses_earned": data.get("milestone_bonuses_earned", [])
        }
    
    def process_payout(self, user_id: str) -> Dict[str, Any]:
        """
        Process payout for user's pending commissions
        
        Args:
            user_id: User ID to process payout for
        
        Returns:
            Dict with payout details
        """
        if user_id not in self.referrals_data:
            return {"success": False, "error": "User not found"}
        
        data = self.referrals_data[user_id]
        pending = data["pending_commission"]
        
        if pending < 25.0:  # Minimum payout threshold
            return {
                "success": False,
                "error": f"Minimum payout is $25. Current: ${pending:.2f}"
            }
        
        # Record payout
        payout = {
            "amount": pending,
            "date": datetime.now().isoformat(),
            "method": "bank_transfer",  # or PayPal, Stripe, etc.
            "status": "processed"
        }
        
        data["paid_commission"] += pending
        data["pending_commission"] = 0.0
        data.setdefault("payouts", []).append(payout)
        
        self._save_referrals()
        
        logger.info(f"Payout processed for {user_id}: ${pending:.2f}")
        
        return {
            "success": True,
            "amount": pending,
            "method": "bank_transfer",
            "processed_at": payout["date"]
        }
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top referrers leaderboard"""
        leaderboard = []
        
        for user_id, data in self.referrals_data.items():
            leaderboard.append({
                "user_id": user_id,
                "referral_count": data["referral_count"],
                "total_commission": data["total_commission"],
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by total commission
        leaderboard.sort(key=lambda x: x["total_commission"], reverse=True)
        
        # Set ranks
        for i, entry in enumerate(leaderboard[:limit]):
            entry["rank"] = i + 1
        
        return leaderboard[:limit]
    
    def cancel_referral(self, referrer_id: str, referred_user_id: str) -> bool:
        """Cancel a referral (e.g., if referred user cancels)"""
        if referrer_id not in self.referrals_data:
            return False
        
        data = self.referrals_data[referrer_id]
        
        for referral in data.get("referrals", []):
            if referral["referred_user_id"] == referred_user_id:
                if referral["status"] == "active":
                    referral["status"] = "cancelled"
                    referral["cancelled_at"] = datetime.now().isoformat()
                    
                    # Deduct commission if not yet paid
                    commission = referral["commission"]
                    if data["pending_commission"] >= commission:
                        data["pending_commission"] -= commission
                    
                    self._save_referrals()
                    logger.info(f"Referral cancelled: {referred_user_id}")
                    return True
        
        return False
    
    def _notify_referral(self, referrer_id: str, new_user_id: str, commission: float):
        """Send referral notification email"""
        try:
            from shared.email_notifications import get_email_system
            
            email_system = get_email_system()
            
            # In production, get actual email from user_id
            referrer_email = f"{referrer_id}@example.com"
            
            subject = f"🎉 New Referral! You earned ${commission:.2f}"
            body_html = f"""
                <h2>New Referral!</h2>
                <p>Congratulations! Someone signed up using your referral code.</p>
                <p><strong>Commission Earned:</strong> ${commission:.2f}</p>
                <p><strong>Referred User:</strong> {new_user_id}</p>
                <p><a href="https://aria-platform.com/referrals.html">View Your Referrals</a></p>
            """
            
            email_system.send_email(referrer_email, subject, body_html)
        
        except Exception as e:
            logger.error(f"Failed to send referral notification: {str(e)}")
    
    def _load_referrals(self) -> Dict[str, Any]:
        """Load referrals from file"""
        if self.referrals_file.exists():
            try:
                with open(self.referrals_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load referrals: {str(e)}")
        
        return {}
    
    def _save_referrals(self):
        """Save referrals to file"""
        try:
            with open(self.referrals_file, 'w') as f:
                json.dump(self.referrals_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save referrals: {str(e)}")


# Global instance
_referral_system: Optional[ReferralSystem] = None


def get_referral_system() -> ReferralSystem:
    """Get global referral system instance"""
    global _referral_system
    if _referral_system is None:
        _referral_system = ReferralSystem()
    return _referral_system
