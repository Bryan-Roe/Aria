"""
Stripe webhook handler for Aria monetization
Processes Stripe payment events and updates subscriptions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Handles Stripe webhook events"""

    def __init__(self):
        self.webhook_log = Path("data_out/webhooks/stripe_events.json")
        self.webhook_log.parent.mkdir(parents=True, exist_ok=True)
        self.processed_events = set()

    def handle_webhook(
        self, payload: str, signature: str, webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming Stripe webhook

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            webhook_secret: Webhook signing secret

        Returns:
            Response dict with status and message
        """
        try:
            # In production, verify signature with Stripe
            # import stripe
            # event = stripe.Webhook.construct_event(
            #     payload, signature, webhook_secret
            # )

            # For demo, parse JSON directly
            event = json.loads(payload)

            # Check for duplicate events
            event_id = event.get("id")
            if event_id in self.processed_events:
                logger.info(f"Duplicate event {event_id}, skipping")
                return {"status": "success", "message": "Duplicate event"}

            # Log the event
            self._log_event(event)

            # Route to appropriate handler
            event_type = event.get("type")
            handler = self._get_event_handler(event_type)

            if handler:
                result = handler(event)
                self.processed_events.add(event_id)
                return {"status": "success", "result": result}
            else:
                logger.warning(f"No handler for event type: {event_type}")
                return {"status": "ignored", "message": f"No handler for {event_type}"}

        except Exception as e:
            logger.error(f"Webhook handling failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _get_event_handler(self, event_type: str):
        """Get handler function for event type"""
        handlers = {
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.payment_succeeded": self._handle_payment_succeeded,
            "invoice.payment_failed": self._handle_payment_failed,
            "charge.succeeded": self._handle_charge_succeeded,
            "charge.failed": self._handle_charge_failed,
            "customer.created": self._handle_customer_created,
            "customer.updated": self._handle_customer_updated,
        }
        return handlers.get(event_type)

    def _handle_subscription_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.created event"""
        subscription = event["data"]["object"]

        # Extract subscription details
        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status")
        plan_id = subscription.get("plan", {}).get("id")
        amount = subscription.get("plan", {}).get("amount", 0) / 100

        logger.info(
            f"Subscription created: {subscription_id} for customer {customer_id}"
        )

        # Update subscription in database
        from shared.subscription_manager import get_subscription_manager

        manager = get_subscription_manager()

        # Map Stripe plan to tier
        tier = self._map_plan_to_tier(plan_id, amount)

        # Create/update subscription
        manager.upgrade_subscription(
            user_id=customer_id,
            tier=tier,
            duration_days=30,
            payment_method="stripe",
            stripe_subscription_id=subscription_id,
        )

        # Send notification
        from shared.email_notifications import get_email_system

        email_system = get_email_system()
        email_system.notify_subscription_activated(
            user_email=self._get_customer_email(customer_id),
            tier=tier.value.upper(),
            price=amount,
        )

        return {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "tier": tier.value,
            "status": status,
        }

    def _handle_subscription_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.updated event"""
        subscription = event["data"]["object"]

        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")
        status = subscription.get("status")

        logger.info(f"Subscription updated: {subscription_id}, status: {status}")

        # Handle status changes
        if status == "canceled":
            return self._handle_subscription_deleted(event)
        elif status == "past_due":
            # Send payment reminder
            from shared.email_notifications import get_email_system

            email_system = get_email_system()
            email_system.notify_payment_failed(
                user_email=self._get_customer_email(customer_id),
                amount=subscription.get("plan", {}).get("amount", 0) / 100,
                reason="Payment past due",
            )

        return {"subscription_id": subscription_id, "status": status}

    def _handle_subscription_deleted(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.deleted event"""
        subscription = event["data"]["object"]

        customer_id = subscription.get("customer")
        subscription_id = subscription.get("id")

        logger.info(f"Subscription deleted: {subscription_id}")

        # Downgrade to free tier
        from shared.subscription_manager import get_subscription_manager

        manager = get_subscription_manager()

        # Get user_id from customer_id mapping
        # In production, maintain a customer_id -> user_id mapping
        user_id = customer_id

        # Cancel subscription (keeps access until period end)
        subscription_obj = manager.get_subscription(user_id)
        if subscription_obj:
            subscription_obj.is_active = False
            manager._save_subscriptions()

        return {
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "action": "cancelled",
        }

    def _handle_payment_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_succeeded event"""
        invoice = event["data"]["object"]

        customer_id = invoice.get("customer")
        invoice_id = invoice.get("id")
        amount = invoice.get("amount_paid", 0) / 100

        logger.info(f"Payment succeeded: {invoice_id}, amount: ${amount}")

        # Send receipt
        from shared.email_notifications import get_email_system

        email_system = get_email_system()
        email_system.notify_payment_succeeded(
            user_email=self._get_customer_email(customer_id),
            amount=amount,
            invoice_id=invoice_id,
        )

        return {"invoice_id": invoice_id, "amount": amount, "status": "paid"}

    def _handle_payment_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed event"""
        invoice = event["data"]["object"]

        customer_id = invoice.get("customer")
        invoice_id = invoice.get("id")
        amount = invoice.get("amount_due", 0) / 100

        logger.info(f"Payment failed: {invoice_id}, amount: ${amount}")

        # Send notification
        from shared.email_notifications import get_email_system

        email_system = get_email_system()
        email_system.notify_payment_failed(
            user_email=self._get_customer_email(customer_id),
            amount=amount,
            reason="Payment declined",
        )

        return {"invoice_id": invoice_id, "amount": amount, "status": "failed"}

    def _handle_charge_succeeded(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.succeeded event"""
        charge = event["data"]["object"]

        charge_id = charge.get("id")
        amount = charge.get("amount", 0) / 100

        logger.info(f"Charge succeeded: {charge_id}, amount: ${amount}")

        return {"charge_id": charge_id, "amount": amount, "status": "succeeded"}

    def _handle_charge_failed(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.failed event"""
        charge = event["data"]["object"]

        charge_id = charge.get("id")
        amount = charge.get("amount", 0) / 100
        failure_message = charge.get("failure_message", "Unknown error")

        logger.info(f"Charge failed: {charge_id}, reason: {failure_message}")

        return {
            "charge_id": charge_id,
            "amount": amount,
            "status": "failed",
            "reason": failure_message,
        }

    def _handle_customer_created(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.created event"""
        customer = event["data"]["object"]

        customer_id = customer.get("id")
        email = customer.get("email")

        logger.info(f"Customer created: {customer_id}, email: {email}")

        return {"customer_id": customer_id, "email": email}

    def _handle_customer_updated(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle customer.updated event"""
        customer = event["data"]["object"]

        customer_id = customer.get("id")

        logger.info(f"Customer updated: {customer_id}")

        return {"customer_id": customer_id}

    def _map_plan_to_tier(self, plan_id: str, amount: float):
        """Map Stripe plan to subscription tier"""
        from shared.subscription_manager import SubscriptionTier

        # Map based on amount
        if amount >= 199:
            return SubscriptionTier.ENTERPRISE
        elif amount >= 49:
            return SubscriptionTier.PRO
        else:
            return SubscriptionTier.FREE

    def _get_customer_email(self, customer_id: str) -> str:
        """Get customer email from Stripe customer ID"""
        # In production, query Stripe API or database
        # For demo, return placeholder
        return f"{customer_id}@example.com"

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Log webhook event to file"""
        try:
            # Load existing log
            log_data = []
            if self.webhook_log.exists():
                with open(self.webhook_log, "r") as f:
                    log_data = json.load(f)

            # Append new event
            log_data.append(
                {
                    "event_id": event.get("id"),
                    "type": event.get("type"),
                    "created": event.get("created"),
                    "processed_at": datetime.now().isoformat(),
                    "data": event.get("data", {}),
                }
            )

            # Keep only last 500 events
            if len(log_data) > 500:
                log_data = log_data[-500:]

            # Save log
            with open(self.webhook_log, "w") as f:
                json.dump(log_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to log webhook event: {str(e)}")


# Global instance
_webhook_handler: Optional[StripeWebhookHandler] = None


def get_webhook_handler() -> StripeWebhookHandler:
    """Get global webhook handler instance"""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = StripeWebhookHandler()
    return _webhook_handler
