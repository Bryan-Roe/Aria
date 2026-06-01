"""Notification adapter for sending structured webhook events."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen


class NotificationAdapter:
    def __init__(self, webhook_url: Optional[str] = None, timeout: int = 10) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout

    def notify(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"message": message, "metadata": metadata or {}}
        if not self.webhook_url:
            return {"status": "skipped", "payload": payload}

        request = Request(
            self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        try:
            parsed_body: Any = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed_body = body
        return {"status": "sent", "code": getattr(response, "status", 200), "response": parsed_body}
