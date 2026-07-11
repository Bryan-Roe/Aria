"""Tests for shared/stripe_webhooks.py.

Covers handle_webhook routing, duplicate detection, invalid payloads,
simple event handlers that do not require external singletons, and the
module-level get_webhook_handler() singleton.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.stripe_webhooks import StripeWebhookHandler, get_webhook_handler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(tmp_path: Path) -> StripeWebhookHandler:
    """Build a handler whose log file sits inside tmp_path to avoid side effects."""
    handler = StripeWebhookHandler.__new__(StripeWebhookHandler)
    handler.webhook_log = tmp_path / "stripe_events.json"
    handler.webhook_log.parent.mkdir(parents=True, exist_ok=True)
    handler.processed_events = set()
    return handler


def _payload(**kwargs) -> str:
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# handle_webhook — invalid JSON
# ---------------------------------------------------------------------------


class TestHandleWebhookInvalidPayload:
    def test_invalid_json_returns_error_status(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h.handle_webhook("not valid json", signature="sig123")
        assert result["status"] == "error"

    def test_invalid_json_message_is_string(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h.handle_webhook("{broken", signature="")
        assert isinstance(result["message"], str)


# ---------------------------------------------------------------------------
# handle_webhook — unknown event type
# ---------------------------------------------------------------------------


class TestHandleWebhookUnknownEventType:
    def test_unknown_type_returns_ignored(self, tmp_path):
        h = _make_handler(tmp_path)
        payload = _payload(id="evt_1", type="unknown.event", data={})
        result = h.handle_webhook(payload, signature="")
        assert result["status"] == "ignored"

    def test_ignored_message_mentions_event_type(self, tmp_path):
        h = _make_handler(tmp_path)
        payload = _payload(id="evt_2", type="mystery.type", data={})
        result = h.handle_webhook(payload, signature="")
        assert "mystery.type" in result["message"]

    def test_none_type_returns_ignored(self, tmp_path):
        h = _make_handler(tmp_path)
        payload = json.dumps({"id": "evt_no_type", "data": {}})
        result = h.handle_webhook(payload, signature="")
        assert result["status"] == "ignored"


# ---------------------------------------------------------------------------
# handle_webhook — duplicate events
# ---------------------------------------------------------------------------


class TestHandleWebhookDuplicate:
    def test_duplicate_event_id_returns_success(self, tmp_path):
        h = _make_handler(tmp_path)
        h.processed_events.add("evt_dup")
        payload = _payload(id="evt_dup", type="charge.succeeded", data={"object": {"id": "ch_1", "amount": 1000}})
        result = h.handle_webhook(payload, signature="")
        assert result["status"] == "success"
        assert "Duplicate" in result.get("message", "")

    def test_duplicate_not_added_again(self, tmp_path):
        h = _make_handler(tmp_path)
        h.processed_events.add("evt_known")
        size_before = len(h.processed_events)
        payload = _payload(id="evt_known", type="charge.succeeded", data={"object": {}})
        h.handle_webhook(payload, signature="")
        assert len(h.processed_events) == size_before


# ---------------------------------------------------------------------------
# _get_event_handler
# ---------------------------------------------------------------------------


class TestGetEventHandler:
    def test_known_event_types_return_callable(self, tmp_path):
        h = _make_handler(tmp_path)
        known_types = [
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "invoice.payment_succeeded",
            "invoice.payment_failed",
            "charge.succeeded",
            "charge.failed",
            "customer.created",
            "customer.updated",
        ]
        for event_type in known_types:
            handler_fn = h._get_event_handler(event_type)
            assert callable(handler_fn), f"Expected callable for {event_type}"

    def test_unknown_event_type_returns_none(self, tmp_path):
        h = _make_handler(tmp_path)
        assert h._get_event_handler("some.unknown.event") is None

    def test_empty_string_returns_none(self, tmp_path):
        h = _make_handler(tmp_path)
        assert h._get_event_handler("") is None


# ---------------------------------------------------------------------------
# _handle_charge_succeeded
# ---------------------------------------------------------------------------


class TestHandleChargeSucceeded:
    def _event(self, charge_id: str = "ch_1", amount: int = 5000):
        return {"data": {"object": {"id": charge_id, "amount": amount}}}

    def test_returns_charge_id(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_succeeded(self._event("ch_abc"))
        assert result["charge_id"] == "ch_abc"

    def test_amount_converted_to_dollars(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_succeeded(self._event(amount=9999))
        assert abs(result["amount"] - 99.99) < 0.001

    def test_status_is_succeeded(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_succeeded(self._event())
        assert result["status"] == "succeeded"


# ---------------------------------------------------------------------------
# _handle_charge_failed
# ---------------------------------------------------------------------------


class TestHandleChargeFailed:
    def _event(self, charge_id: str = "ch_fail", amount: int = 2000, reason: str = "card declined"):
        return {"data": {"object": {"id": charge_id, "amount": amount, "failure_message": reason}}}

    def test_returns_charge_id(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_failed(self._event(charge_id="ch_bad"))
        assert result["charge_id"] == "ch_bad"

    def test_status_is_failed(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_failed(self._event())
        assert result["status"] == "failed"

    def test_reason_included(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_charge_failed(self._event(reason="insufficient funds"))
        assert result["reason"] == "insufficient funds"

    def test_missing_failure_message_uses_default(self, tmp_path):
        h = _make_handler(tmp_path)
        event = {"data": {"object": {"id": "ch_x", "amount": 0}}}
        result = h._handle_charge_failed(event)
        assert isinstance(result["reason"], str)


# ---------------------------------------------------------------------------
# _handle_customer_created
# ---------------------------------------------------------------------------


class TestHandleCustomerCreated:
    def _event(self, customer_id: str = "cus_1", email: str = "a@b.com"):
        return {"data": {"object": {"id": customer_id, "email": email}}}

    def test_returns_customer_id(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_customer_created(self._event(customer_id="cus_abc"))
        assert result["customer_id"] == "cus_abc"

    def test_returns_email(self, tmp_path):
        h = _make_handler(tmp_path)
        result = h._handle_customer_created(self._event(email="user@example.com"))
        assert result["email"] == "user@example.com"


# ---------------------------------------------------------------------------
# _handle_customer_updated
# ---------------------------------------------------------------------------


class TestHandleCustomerUpdated:
    def test_returns_customer_id(self, tmp_path):
        h = _make_handler(tmp_path)
        event = {"data": {"object": {"id": "cus_upd"}}}
        result = h._handle_customer_updated(event)
        assert result["customer_id"] == "cus_upd"


# ---------------------------------------------------------------------------
# _get_customer_email
# ---------------------------------------------------------------------------


class TestGetCustomerEmail:
    def test_returns_string(self, tmp_path):
        h = _make_handler(tmp_path)
        email = h._get_customer_email("cus_xyz")
        assert isinstance(email, str)

    def test_customer_id_in_email(self, tmp_path):
        h = _make_handler(tmp_path)
        email = h._get_customer_email("cus_123")
        assert "cus_123" in email


# ---------------------------------------------------------------------------
# _log_event
# ---------------------------------------------------------------------------


class TestLogEvent:
    def test_creates_log_file(self, tmp_path):
        h = _make_handler(tmp_path)
        h._log_event({"id": "evt_log1", "type": "charge.succeeded", "created": 1000, "data": {}})
        assert h.webhook_log.exists()

    def test_log_file_contains_event_id(self, tmp_path):
        h = _make_handler(tmp_path)
        h._log_event({"id": "evt_log2", "type": "charge.succeeded", "created": 1001, "data": {}})
        log_data = json.loads(h.webhook_log.read_text(encoding="utf-8"))
        assert any(e["event_id"] == "evt_log2" for e in log_data)

    def test_appends_multiple_events(self, tmp_path):
        h = _make_handler(tmp_path)
        for i in range(3):
            h._log_event({"id": f"evt_{i}", "type": "t", "created": i, "data": {}})
        log_data = json.loads(h.webhook_log.read_text(encoding="utf-8"))
        assert len(log_data) == 3

    def test_does_not_raise_on_write_failure(self, tmp_path):
        h = _make_handler(tmp_path)
        # Make log file a directory so writing fails gracefully
        h.webhook_log.mkdir(parents=True, exist_ok=True)
        # Should not raise
        h._log_event({"id": "evt_err", "type": "t", "created": 0, "data": {}})


# ---------------------------------------------------------------------------
# get_webhook_handler — singleton
# ---------------------------------------------------------------------------


class TestGetWebhookHandler:
    def test_returns_stripe_webhook_handler_instance(self, tmp_path, monkeypatch):
        import shared.stripe_webhooks as swh

        monkeypatch.setattr(swh, "_webhook_handler", None)
        handler = get_webhook_handler()
        assert isinstance(handler, StripeWebhookHandler)

    def test_returns_same_instance_on_repeated_calls(self, tmp_path, monkeypatch):
        import shared.stripe_webhooks as swh

        monkeypatch.setattr(swh, "_webhook_handler", None)
        h1 = get_webhook_handler()
        h2 = get_webhook_handler()
        assert h1 is h2
