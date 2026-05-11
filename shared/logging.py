"""Structured logging utilities for the Aria platform.

Provides a structured JSON log formatter and a helper to configure the root
logger once per process.  Existing handler configurations are not replaced;
this module augments them.

Usage::

    from shared.logging import configure_logging, get_logger

    configure_logging(level="DEBUG", structured=True)
    log = get_logger(__name__)
    log.info("hello", extra={"request_id": "abc123"})
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

__all__ = ["configure_logging", "get_logger", "JsonFormatter"]

# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------

_BUILTIN_KEYS = frozenset(
    {
        "args",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record on a single line.

    Extra fields passed via ``extra={}`` are included verbatim in the output
    dict.  Built-in LogRecord attributes are excluded from the extras section.
    """

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        else:
            record.exc_text = None

        doc: Dict[str, Any] = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
            )
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }

        if record.exc_text:
            doc["exception"] = record.exc_text

        # Attach caller location at DEBUG level to avoid noise at INFO+
        if record.levelno <= logging.DEBUG:
            doc["location"] = f"{record.pathname}:{record.lineno}"

        # Merge any extra fields (filtering out built-in attributes)
        for key, value in record.__dict__.items():
            if key not in _BUILTIN_KEYS and not key.startswith("_"):
                doc[key] = value

        try:
            return json.dumps(doc, default=str)
        except Exception as exc:  # noqa: BLE001
            return json.dumps(
                {
                    "level": "ERROR",
                    "logger": record.name,
                    "message": f"Failed to serialize log record: {exc}",
                    "original_message": str(record.message),
                }
            )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_configured: bool = False


def configure_logging(
    level: Optional[str] = None,
    structured: Optional[bool] = None,
    stream: Any = None,
) -> None:
    """Configure the root logger.

    Can safely be called multiple times; subsequent calls update the level but
    do not add duplicate handlers.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to ``QAI_LOG_LEVEL`` env var or ``INFO``.
        structured: Emit JSON logs when *True*.
                    Defaults to ``QAI_STRUCTURED_LOGGING`` env var.
        stream: Output stream (default: sys.stdout).
    """
    global _configured

    # Resolve effective settings
    if level is None:
        level = os.environ.get("QAI_LOG_LEVEL", "INFO").upper()
    else:
        level = level.upper()

    if structured is None:
        structured = os.environ.get("QAI_STRUCTURED_LOGGING", "").lower() in (
            "1",
            "true",
            "yes",
        )

    numeric_level = getattr(logging, level, logging.INFO)
    root = logging.getLogger()
    root.setLevel(numeric_level)

    if not _configured:
        # Remove existing stream handlers to avoid duplicates when running
        # under frameworks that add their own handlers (e.g. Azure Functions).
        for h in list(root.handlers):
            if isinstance(h, logging.StreamHandler) and not isinstance(
                h, logging.FileHandler
            ):
                root.removeHandler(h)

        handler = logging.StreamHandler(stream or sys.stdout)
        if structured:
            handler.setFormatter(JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
        handler.setLevel(numeric_level)
        root.addHandler(handler)
        _configured = True
    else:
        # Just update levels on existing handlers
        root.setLevel(numeric_level)
        for h in root.handlers:
            h.setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """Return a logger, ensuring the root logger has at least one handler."""
    if not logging.root.handlers:
        configure_logging()
    return logging.getLogger(name)
