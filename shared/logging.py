"""Shared structured logging helpers."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for cross-service logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(level: int | None = None) -> None:
    """Configure root logger once with JSON output."""
    root = logging.getLogger()
    if any(isinstance(handler.formatter, JsonFormatter) for handler in root.handlers):
        return

    resolved_level = level
    if resolved_level is None:
        resolved_level = logging.DEBUG if os.getenv("QAI_DEBUG", "").lower() in {"1", "true", "yes"} else logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]
    root.setLevel(resolved_level)
