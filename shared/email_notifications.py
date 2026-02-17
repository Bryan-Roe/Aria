"""
Email notification system for Aria monetization
Handles subscription events, usage alerts, and billing notifications
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# Pre-compile regex patterns for performance
_RE_HTML_TAGS = re.compile(r'<[^<]+?>')
_RE_WHITESPACE = re.compile(r'\s+')


class EmailTemplate(Enum):
    """Email template types"""
    WELCOME = "welcome"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    USAGE_WARNING_80 = "usage_warning_80"
    USAGE_WARNING_90 = "usage_warning_90"
    USAGE_LIMIT_REACHED = "usage_limit_reached"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    INVOICE_GENERATED = "invoice_generated"
    TRIAL_ENDING = "trial_ending"
    UPGRADE_REMINDER = "upgrade_reminder"


class EmailNotificationSystem:
    """Handles email notifications for subscription events"""
    
    def __init__(self, smtp_host: Optional[str] = None, smtp_port: int = 587):
        self.smtp_host = smtp_host or "localhost"
        self.smtp_port = smtp_port
        self.from_email = "noreply@aria-platform.com"
        self.template_dir = Path("templates/emails")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Store sent emails for testing/demo
        self.sent_emails: List[Dict[str, Any]] = []
        self.notification_log = Path("data_out/notifications/email_log.json")
        self.notification_log.parent.mkdir(parents=True, exist_ok=True)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send an email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML email body
            body_text: Plain text email body (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            email_data = {
                "to": to_email,
                "from": self.from_email,
                "subject": subject,
                "body_html": body_html,
                "body_text": body_text or self._strip_html(body_html),
                "timestamp": datetime.now().isoformat(),
                "status": "sent"
            }
            
            # In production, use actual SMTP library
            # import smtplib
            # from email.mime.multipart import MIMEMultipart
            # from email.mime.text import MIMEText
            # ... send via SMTP
            
            # For demo/testing, log the email
            self.sent_emails.append(email_data)
            self._log_notification(email_data)
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_template_email(
        self,
        to_email: str,
        template: EmailTemplate,
        context: Dict[str, Any]
    ) -> bool:
        """
        Send an email using a template
        
        Args:
            to_email: Recipient email address
            template: Email template to use
            context: Template context variables
        
        Returns:
            True if sent successfully
        """
        template_data = self._get_template(template)
        subject = self._render_template(template_data["subject"], context)
        body_html = self._render_template(template_data["body_html"], context)
        body_text = self._render_template(template_data["body_text"], context)
        
        return self.send_email(to_email, subject, body_html, body_text)
    
    def notify_subscription_activated(
        self,
        user_email: str,
        tier: str,
        price: float
    ) -> bool:
        """Notify user that subscription is activated"""
        context = {
            "tier": tier,
            "price": price,
            "date": datetime.now().strftime("%B %d, %Y"),
            "dashboard_url": "https://aria-platform.com/my-subscription.html"
        }
        return self.send_template_email(
            user_email,
            EmailTemplate.SUBSCRIPTION_ACTIVATED,
            context
        )
    
    def notify_usage_warning(
        self,
        user_email: str,
        resource: str,
        percentage: float,
        current: int,
        limit: int
    ) -> bool:
        """Notify user about approaching usage limits"""
        template = (
            EmailTemplate.USAGE_WARNING_90 if percentage >= 90
            else EmailTemplate.USAGE_WARNING_80
        )
        
        context = {
            "resource": resource,
            "percentage": int(percentage),
            "current": current,
            "limit": limit,
            "remaining": limit - current,
            "upgrade_url": "https://aria-platform.com/pricing.html"
        }
        
        return self.send_template_email(user_email, template, context)
    
    def notify_usage_limit_reached(
        self,
        user_email: str,
        resource: str,
        limit: int
    ) -> bool:
        """Notify user that usage limit has been reached"""
        context = {
            "resource": resource,
            "limit": limit,
            "upgrade_url": "https://aria-platform.com/pricing.html",
            "reset_date": self._get_next_reset_date()
        }
        
        return self.send_template_email(
            user_email,
            EmailTemplate.USAGE_LIMIT_REACHED,
            context
        )
    
    def notify_payment_succeeded(
        self,
        user_email: str,
        amount: float,
        invoice_id: str
    ) -> bool:
        """Notify user of successful payment"""
        context = {
            "amount": amount,
            "invoice_id": invoice_id,
            "date": datetime.now().strftime("%B %d, %Y"),
            "invoice_url": f"https://aria-platform.com/invoices/{invoice_id}"
        }
        
        return self.send_template_email(
            user_email,
            EmailTemplate.PAYMENT_SUCCEEDED,
            context
        )
    
    def notify_payment_failed(
        self,
        user_email: str,
        amount: float,
        reason: str
    ) -> bool:
        """Notify user of failed payment"""
        context = {
            "amount": amount,
            "reason": reason,
            "date": datetime.now().strftime("%B %d, %Y"),
            "billing_url": "https://aria-platform.com/account.html"
        }
        
        return self.send_template_email(
            user_email,
            EmailTemplate.PAYMENT_FAILED,
            context
        )
    
    def _get_template(self, template: EmailTemplate) -> Dict[str, str]:
        """Get email template data"""
        templates = {
            EmailTemplate.SUBSCRIPTION_ACTIVATED: {
                "subject": "Welcome to Aria {tier} Plan! 🎉",
                "body_html": """
                    <h2>Welcome to Aria {tier}!</h2>
                    <p>Your subscription has been activated successfully.</p>
                    <p><strong>Plan:</strong> {tier}<br>
                    <strong>Price:</strong> ${price}/month<br>
                    <strong>Date:</strong> {date}</p>
                    <p><a href="{dashboard_url}">View Your Subscription Dashboard</a></p>
                    <p>Thank you for choosing Aria!</p>
                """,
                "body_text": """
                    Welcome to Aria {tier}!
                    
                    Your subscription has been activated successfully.
                    
                    Plan: {tier}
                    Price: ${price}/month
                    Date: {date}
                    
                    View your dashboard: {dashboard_url}
                    
                    Thank you for choosing Aria!
                """
            },
            EmailTemplate.USAGE_WARNING_80: {
                "subject": "⚠️ Usage Alert: {percentage}% of {resource} limit used",
                "body_html": """
                    <h2>Usage Alert</h2>
                    <p>You've used <strong>{percentage}%</strong> of your {resource} limit.</p>
                    <p>Current usage: {current} / {limit}<br>
                    Remaining: {remaining}</p>
                    <p>Consider <a href="{upgrade_url}">upgrading your plan</a> for higher limits.</p>
                """,
                "body_text": """
                    Usage Alert
                    
                    You've used {percentage}% of your {resource} limit.
                    
                    Current usage: {current} / {limit}
                    Remaining: {remaining}
                    
                    Consider upgrading: {upgrade_url}
                """
            },
            EmailTemplate.USAGE_WARNING_90: {
                "subject": "🚨 Urgent: {percentage}% of {resource} limit used",
                "body_html": """
                    <h2>Urgent Usage Alert</h2>
                    <p>You've used <strong>{percentage}%</strong> of your {resource} limit!</p>
                    <p>Current usage: {current} / {limit}<br>
                    Remaining: {remaining}</p>
                    <p><strong>Action needed:</strong> <a href="{upgrade_url}">Upgrade now</a> to avoid service interruption.</p>
                """,
                "body_text": """
                    Urgent Usage Alert
                    
                    You've used {percentage}% of your {resource} limit!
                    
                    Current usage: {current} / {limit}
                    Remaining: {remaining}
                    
                    Action needed: Upgrade now to avoid service interruption.
                    {upgrade_url}
                """
            },
            EmailTemplate.USAGE_LIMIT_REACHED: {
                "subject": "🛑 {resource} limit reached",
                "body_html": """
                    <h2>Usage Limit Reached</h2>
                    <p>You've reached your {resource} limit of {limit}.</p>
                    <p>Your limit will reset on {reset_date}.</p>
                    <p>To continue using this feature, <a href="{upgrade_url}">upgrade your plan</a> now.</p>
                """,
                "body_text": """
                    Usage Limit Reached
                    
                    You've reached your {resource} limit of {limit}.
                    
                    Your limit will reset on {reset_date}.
                    
                    To continue, upgrade your plan: {upgrade_url}
                """
            },
            EmailTemplate.PAYMENT_SUCCEEDED: {
                "subject": "✅ Payment Received - Invoice #{invoice_id}",
                "body_html": """
                    <h2>Payment Successful</h2>
                    <p>We've received your payment of <strong>${amount}</strong>.</p>
                    <p>Invoice: #{invoice_id}<br>
                    Date: {date}</p>
                    <p><a href="{invoice_url}">View Invoice</a></p>
                    <p>Thank you for your business!</p>
                """,
                "body_text": """
                    Payment Successful
                    
                    We've received your payment of ${amount}.
                    
                    Invoice: #{invoice_id}
                    Date: {date}
                    
                    View invoice: {invoice_url}
                    
                    Thank you for your business!
                """
            },
            EmailTemplate.PAYMENT_FAILED: {
                "subject": "❌ Payment Failed - Action Required",
                "body_html": """
                    <h2>Payment Failed</h2>
                    <p>We were unable to process your payment of <strong>${amount}</strong>.</p>
                    <p>Reason: {reason}<br>
                    Date: {date}</p>
                    <p>Please <a href="{billing_url}">update your payment method</a> to avoid service interruption.</p>
                """,
                "body_text": """
                    Payment Failed - Action Required
                    
                    We were unable to process your payment of ${amount}.
                    
                    Reason: {reason}
                    Date: {date}
                    
                    Please update your payment method: {billing_url}
                """
            }
        }
        
        return templates.get(template, {
            "subject": "Notification from Aria",
            "body_html": "<p>Notification</p>",
            "body_text": "Notification"
        })
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Simple template rendering"""
        result = template
        for key, value in context.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
    
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags for plain text version"""
        text = _RE_HTML_TAGS.sub('', html)
        text = _RE_WHITESPACE.sub(' ', text)
        return text.strip()
    
    def _get_next_reset_date(self) -> str:
        """Get next monthly reset date"""
        from datetime import timedelta
        next_month = datetime.now() + timedelta(days=30)
        return next_month.strftime("%B %d, %Y")
    
    def _log_notification(self, email_data: Dict[str, Any]) -> None:
        """Log notification to file"""
        try:
            # Load existing log
            log_data = []
            if self.notification_log.exists():
                with open(self.notification_log, 'r') as f:
                    log_data = json.load(f)
            
            # Append new notification
            log_data.append(email_data)
            
            # Keep only last 1000 notifications
            if len(log_data) > 1000:
                log_data = log_data[-1000:]
            
            # Save log
            with open(self.notification_log, 'w') as f:
                json.dump(log_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")
    
    def get_sent_emails(self, user_email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sent emails (for testing/demo)"""
        if user_email:
            return [e for e in self.sent_emails if e["to"] == user_email]
        return self.sent_emails


# Global instance
_email_system: Optional[EmailNotificationSystem] = None


def get_email_system() -> EmailNotificationSystem:
    """Get global email notification system instance"""
    global _email_system
    if _email_system is None:
        _email_system = EmailNotificationSystem()
    return _email_system
