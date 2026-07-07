"""Notification adapter for sending structured webhook events."""

from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

_ALLOWED_SCHEMES = {"http", "https"}


class NotificationAdapter:
    def __init__(
        self,
        webhook_url: str | None = None,
        timeout: int = 10,
    ) -> None:
        if webhook_url is not None:
            parsed = urlparse(webhook_url)
            if parsed.scheme not in _ALLOWED_SCHEMES:
                raise ValueError(f"Webhook URL scheme '{parsed.scheme}' is not allowed; use http or https.")
        self.webhook_url = webhook_url
        self.timeout = timeout

    def notify(
        self,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = {"message": message, "metadata": metadata or {}}
        if not self.webhook_url:
            return {"status": "skipped", "payload": payload}

        request = Request(  # noqa: S310 - scheme validated in __init__
            self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:  # noqa: S310
                body = response.read().decode("utf-8")
        except (OSError, TimeoutError, URLError) as exc:
            return {
                "status": "failed",
                "payload": payload,
                "error": str(exc),
            }
        try:
            parsed_body: Any = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed_body = body
        return {
            "status": "sent",
            "code": getattr(response, "status", 200),
            "response": parsed_body,
        }
