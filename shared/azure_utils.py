"""Helpers for handling Azure OpenAI quota/rate-limit errors.

This module centralizes heuristics used across the codebase to detect
Azure quota/premium allowance errors and format helpful user-facing
messages. We keep heuristics simple and robust (string matching + status
code checks) because SDK exceptions and shapes can vary between environments.

Functions:
  - is_quota_error(exc) -> bool
  - is_transient_rate_error(exc) -> bool
  - format_quota_message(exc, service_name='Azure OpenAI') -> str

This keeps other modules (chat providers, embedding helpers) small and
consistent when turning SDK errors into friendly fallbacks.
"""
from __future__ import annotations

import logging
import re
from typing import Any

LOGGER = logging.getLogger(__name__)

# Heuristic keywords that indicate a billing/quota/premium limit on Azure
_QUOTA_KEYWORDS = re.compile(
    r"\b(quota|quota exceeded|quota_exceeded|exceed|exceeded|premium|allowance|insufficient|billing)\b", re.I)

# Heuristic keywords for transient rate-limit style errors (429 or RateLimit)
_RATE_LIMIT_KEYWORDS = re.compile(
    r"\b(rate\s*limit|rate_limit|too\s*many\s*requests|429|RateLimit)\b", re.I)


def _text_of(exc: Any) -> str:
    """Return a safe textual representation for an exception for analysis."""
    try:
        return str(exc) if exc is not None else ""
    except Exception:
        return ""


def is_quota_error(exc: Any) -> bool:
    """Return True when the exception text or attributes strongly suggest
    this is an Azure quota / premium allowance error.

    We intentionally avoid binding to SDK exception classes, since errors
    can differ by runtime and SDK versions. Simple string checks and status
    code membership checks are robust across environments.
    """
    if exc is None:
        return False
    txt = _text_of(exc)
    # Fast check for explicit keyword patterns
    if _QUOTA_KEYWORDS.search(txt):
        return True
    # Some SDKs expose HTTP status-like attributes
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status in (429, 403):
        # 403 can indicate billing/permission issue in some environments
        return True
    # Check nested attributes often used by OpenAI SDKs
    err = getattr(exc, "error", None)
    if err:
        if _QUOTA_KEYWORDS.search(_text_of(err)):
            return True
        code = getattr(err, "code", None)
        if isinstance(code, (int, str)) and str(code).lower() in ("insufficient_quota", "quota_exceeded"):
            return True
    return False


def is_transient_rate_error(exc: Any) -> bool:
    """Return True for rate-limit like errors where retries may help.

    This uses simple keyword checks and status code heuristics.
    """
    if exc is None:
        return False
    txt = _text_of(exc)
    if _RATE_LIMIT_KEYWORDS.search(txt):
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    return status == 429


def format_quota_message(exc: Any, service_name: str = "Azure OpenAI") -> str:
    """Return a short, helpful, user-facing message describing the issue
    and next steps when we detect a quota/premium limit error.
    """
    details = _text_of(exc)
    # Keep the message concise and actionable
    msg = (
        f"{service_name} quota/premium limit reached. "
        "This resource appears to have exceeded its configured allowance or billing quota. "
        "Check your Azure subscription, billing and resource limits, or switch to a different provider (OpenAI, LMStudio, or the local fallback)."
    )
    if details:
        # Attach a short excerpt of the underlying error to aid debugging
        excerpt = details if len(details) < 400 else details[:400] + "..."
        msg = f"{msg} Error details: {excerpt}"
    LOGGER.warning("Detected quota error: %s", details)
    return msg
