"""Comprehensive tests for shared/email_notifications.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from shared.email_notifications import (
    EmailNotificationSystem,
    EmailTemplate,
    get_email_system,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def email_system(tmp_path):
    """EmailNotificationSystem with isolated tmp dirs."""
    system = EmailNotificationSystem.__new__(EmailNotificationSystem)
    system.smtp_host = "localhost"
    system.smtp_port = 587
    system.from_email = "noreply@aria-platform.com"
    system.template_dir = tmp_path / "templates" / "emails"
    system.template_dir.mkdir(parents=True)
    system.sent_emails = []
    system.notification_log = tmp_path / "notifications" / "email_log.json"
    system.notification_log.parent.mkdir(parents=True)
    return system


# ---------------------------------------------------------------------------
# EmailTemplate enum
# ---------------------------------------------------------------------------


class TestEmailTemplateEnum:
    def test_all_templates_defined(self):
        expected = [
            "WELCOME", "SUBSCRIPTION_ACTIVATED", "SUBSCRIPTION_CANCELLED",
            "SUBSCRIPTION_EXPIRED", "USAGE_WARNING_80", "USAGE_WARNING_90",
            "USAGE_LIMIT_REACHED", "PAYMENT_SUCCEEDED", "PAYMENT_FAILED",
            "INVOICE_GENERATED", "TRIAL_ENDING", "UPGRADE_REMINDER",
        ]
        names = [t.name for t in EmailTemplate]
        for e in expected:
            assert e in names


# ---------------------------------------------------------------------------
# EmailNotificationSystem.send_email
# ---------------------------------------------------------------------------


class TestSendEmail:
    def test_send_email_returns_true(self, email_system):
        result = email_system.send_email(
            "user@example.com", "Test Subject", "<p>Hello</p>"
        )
        assert result is True

    def test_email_added_to_sent_emails(self, email_system):
        email_system.send_email("user@example.com", "Sub", "<p>Body</p>")
        assert len(email_system.sent_emails) == 1

    def test_sent_email_structure(self, email_system):
        email_system.send_email("user@example.com", "Subject", "<p>Body</p>", "Plain text")
        record = email_system.sent_emails[0]
        assert record["to"] == "user@example.com"
        assert record["from"] == "noreply@aria-platform.com"
        assert record["subject"] == "Subject"
        assert record["status"] == "sent"

    def test_body_text_auto_generated_from_html(self, email_system):
        email_system.send_email("u@e.com", "Sub", "<h1>Hello</h1><p>World</p>")
        record = email_system.sent_emails[0]
        assert "<" not in record["body_text"]
        assert "Hello" in record["body_text"]

    def test_body_text_used_when_provided(self, email_system):
        email_system.send_email("u@e.com", "Sub", "<p>HTML</p>", "Plain text override")
        record = email_system.sent_emails[0]
        assert record["body_text"] == "Plain text override"

    def test_notification_logged_to_file(self, email_system):
        email_system.send_email("u@e.com", "Sub", "<p>Body</p>")
        assert email_system.notification_log.exists()
        data = json.loads(email_system.notification_log.read_text())
        assert len(data) == 1

    def test_multiple_emails_logged(self, email_system):
        email_system.send_email("a@e.com", "Sub1", "<p>1</p>")
        email_system.send_email("b@e.com", "Sub2", "<p>2</p>")
        data = json.loads(email_system.notification_log.read_text())
        assert len(data) == 2

    def test_log_truncated_at_1000(self, email_system):
        # Pre-fill log with 999 items
        existing = [{"to": f"u{i}@e.com", "subject": f"s{i}"} for i in range(999)]
        email_system.notification_log.write_text(json.dumps(existing))
        email_system.send_email("new@e.com", "new", "<p>x</p>")
        data = json.loads(email_system.notification_log.read_text())
        assert len(data) == 1000

    def test_log_over_1000_is_truncated(self, email_system):
        existing = [{"to": f"u{i}@e.com", "subject": f"s{i}"} for i in range(1000)]
        email_system.notification_log.write_text(json.dumps(existing))
        email_system.send_email("new@e.com", "new", "<p>x</p>")
        data = json.loads(email_system.notification_log.read_text())
        assert len(data) == 1000


# ---------------------------------------------------------------------------
# EmailNotificationSystem.send_template_email
# ---------------------------------------------------------------------------


class TestSendTemplateEmail:
    def test_subscription_activated_template(self, email_system):
        result = email_system.send_template_email(
            "u@e.com",
            EmailTemplate.SUBSCRIPTION_ACTIVATED,
            {"tier": "PRO", "price": 49, "date": "January 1, 2025",
             "dashboard_url": "https://example.com"},
        )
        assert result is True
        record = email_system.sent_emails[0]
        assert "PRO" in record["subject"]

    def test_usage_warning_80_template(self, email_system):
        result = email_system.send_template_email(
            "u@e.com",
            EmailTemplate.USAGE_WARNING_80,
            {"resource": "chat_messages", "percentage": 80,
             "current": 80, "limit": 100, "remaining": 20,
             "upgrade_url": "https://example.com/pricing"},
        )
        assert result is True

    def test_unknown_template_uses_fallback(self, email_system):
        # WELCOME template has no explicit definition → uses fallback
        result = email_system.send_template_email(
            "u@e.com",
            EmailTemplate.WELCOME,
            {},
        )
        assert result is True
        assert "Notification" in email_system.sent_emails[0]["subject"]


# ---------------------------------------------------------------------------
# EmailNotificationSystem.notify_subscription_activated
# ---------------------------------------------------------------------------


class TestNotifySubscriptionActivated:
    def test_sends_email(self, email_system):
        result = email_system.notify_subscription_activated("u@e.com", "PRO", 49.0)
        assert result is True
        assert len(email_system.sent_emails) == 1

    def test_subject_contains_tier(self, email_system):
        email_system.notify_subscription_activated("u@e.com", "PRO", 49.0)
        subject = email_system.sent_emails[0]["subject"]
        assert "PRO" in subject


# ---------------------------------------------------------------------------
# EmailNotificationSystem.notify_usage_warning
# ---------------------------------------------------------------------------


class TestNotifyUsageWarning:
    def test_warning_80_percent(self, email_system):
        result = email_system.notify_usage_warning("u@e.com", "chat_messages", 80.0, 80, 100)
        assert result is True

    def test_warning_90_percent_uses_urgent_template(self, email_system):
        result = email_system.notify_usage_warning("u@e.com", "chat_messages", 90.0, 90, 100)
        assert result is True
        subject = email_system.sent_emails[0]["subject"]
        assert "Urgent" in subject

    def test_warning_below_90_uses_regular_template(self, email_system):
        email_system.notify_usage_warning("u@e.com", "chat_messages", 85.0, 85, 100)
        subject = email_system.sent_emails[0]["subject"]
        assert "Urgent" not in subject


# ---------------------------------------------------------------------------
# EmailNotificationSystem.notify_usage_limit_reached
# ---------------------------------------------------------------------------


class TestNotifyUsageLimitReached:
    def test_sends_email(self, email_system):
        result = email_system.notify_usage_limit_reached("u@e.com", "chat_messages", 100)
        assert result is True

    def test_email_body_contains_limit(self, email_system):
        email_system.notify_usage_limit_reached("u@e.com", "quantum_jobs", 50)
        body = email_system.sent_emails[0]["body_html"]
        assert "50" in body


# ---------------------------------------------------------------------------
# EmailNotificationSystem.notify_payment_succeeded
# ---------------------------------------------------------------------------


class TestNotifyPaymentSucceeded:
    def test_sends_email(self, email_system):
        result = email_system.notify_payment_succeeded("u@e.com", 49.0, "inv_123")
        assert result is True

    def test_email_subject_contains_invoice_id(self, email_system):
        email_system.notify_payment_succeeded("u@e.com", 49.0, "inv_123")
        subject = email_system.sent_emails[0]["subject"]
        assert "inv_123" in subject

    def test_email_body_contains_amount(self, email_system):
        email_system.notify_payment_succeeded("u@e.com", 49.0, "inv_123")
        body = email_system.sent_emails[0]["body_html"]
        assert "49" in body


# ---------------------------------------------------------------------------
# EmailNotificationSystem.notify_payment_failed
# ---------------------------------------------------------------------------


class TestNotifyPaymentFailed:
    def test_sends_email(self, email_system):
        result = email_system.notify_payment_failed("u@e.com", 49.0, "Card declined")
        assert result is True

    def test_email_body_contains_reason(self, email_system):
        email_system.notify_payment_failed("u@e.com", 49.0, "Insufficient funds")
        body = email_system.sent_emails[0]["body_html"]
        assert "Insufficient funds" in body


# ---------------------------------------------------------------------------
# EmailNotificationSystem._strip_html
# ---------------------------------------------------------------------------


class TestStripHtml:
    def test_strips_simple_tags(self, email_system):
        result = email_system._strip_html("<p>Hello</p>")
        assert result == "Hello"

    def test_strips_nested_tags(self, email_system):
        result = email_system._strip_html("<h1><strong>Title</strong></h1>")
        assert result == "Title"

    def test_collapses_whitespace(self, email_system):
        result = email_system._strip_html("<p>Hello   World</p>")
        assert "  " not in result

    def test_empty_string(self, email_system):
        result = email_system._strip_html("")
        assert result == ""


# ---------------------------------------------------------------------------
# EmailNotificationSystem._render_template
# ---------------------------------------------------------------------------


class TestRenderTemplate:
    def test_substitutes_context_variables(self, email_system):
        tmpl = "Hello {name}, you have {count} messages."
        result = email_system._render_template(tmpl, {"name": "Alice", "count": 5})
        assert result == "Hello Alice, you have 5 messages."

    def test_unmatched_keys_left_as_is(self, email_system):
        tmpl = "Hello {name}."
        result = email_system._render_template(tmpl, {})
        assert result == "Hello {name}."

    def test_numeric_context_values(self, email_system):
        tmpl = "Price: ${amount}"
        result = email_system._render_template(tmpl, {"amount": 49})
        assert "49" in result


# ---------------------------------------------------------------------------
# EmailNotificationSystem._get_next_reset_date
# ---------------------------------------------------------------------------


class TestGetNextResetDate:
    def test_returns_string(self, email_system):
        result = email_system._get_next_reset_date()
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# EmailNotificationSystem.get_sent_emails
# ---------------------------------------------------------------------------


class TestGetSentEmails:
    def test_returns_all_sent_emails(self, email_system):
        email_system.send_email("a@e.com", "s1", "<p>1</p>")
        email_system.send_email("b@e.com", "s2", "<p>2</p>")
        assert len(email_system.get_sent_emails()) == 2

    def test_filters_by_user_email(self, email_system):
        email_system.send_email("a@e.com", "s1", "<p>1</p>")
        email_system.send_email("b@e.com", "s2", "<p>2</p>")
        results = email_system.get_sent_emails("a@e.com")
        assert len(results) == 1
        assert results[0]["to"] == "a@e.com"

    def test_empty_list_when_no_emails_sent(self, email_system):
        assert email_system.get_sent_emails() == []


# ---------------------------------------------------------------------------
# get_email_system (singleton)
# ---------------------------------------------------------------------------


class TestGetEmailSystem:
    def test_returns_email_system_instance(self):
        import shared.email_notifications as en_module

        en_module._email_system = None
        try:
            system = get_email_system()
            assert isinstance(system, EmailNotificationSystem)
        finally:
            en_module._email_system = None

    def test_singleton_behavior(self):
        import shared.email_notifications as en_module

        en_module._email_system = None
        try:
            s1 = get_email_system()
            s2 = get_email_system()
            assert s1 is s2
        finally:
            en_module._email_system = None
