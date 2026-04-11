#!/usr/bin/env python3
"""Hook: detect and warn upon scope-drift signals in user prompts.

Conversation-derived policy this enforces:
- Tasks in this repo frequently expand beyond their stated objective
  ("while we're at it…", "also fix…", "and then…") causing unplanned
  refactors, adjacent cleanups, and unrelated improvements.
- This hook injects a concise scope reminder when expansion signals are
  detected, so the agent pauses and explicitly acknowledges whether the
  new work is in-scope.

Behavior by event:
  UserPromptSubmit → if drift signals detected, inject a context reminder
                     as a systemMessage (non-blocking, exit 0).

The reminder quotes the five scope rules from copilot-instructions.md:
  1. Filter the plan — every todo must directly support the active objective
  2. Reject drift  — avoid unrelated refactors, redesigns, cleanup sweeps
  3. Defer discoveries — mention worthwhile but out-of-scope items as follow-ups
  4. Re-check after delegation — verify recommendations still match the original request
  5. Finish the requested loop first — complete the ask before polishing adjacent systems

Override: ARIA_ALLOW_SCOPE_DRIFT=1 silences the reminder for the session.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Phrases that signal the user is bolting on additional work mid-prompt.
_EXPANSION_PHRASES: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\balso\s+(?:fix|improve|update|refactor|add|change|check|clean|remove|make)\b",
        r"\bwhile\s+(?:you(?:'re)?|we(?:'re)?)\s+(?:at it|in there|here)\b",
        r"\band\s+also\b",
        r"\bone\s+more\s+thing\b",
        r"\boh[,]?\s+and\b",
        r"\bcan\s+you\s+also\b",
        r"\bwhile\s+(?:at it|doing this|we're at it)\b",
        r"\blet['']?s\s+also\b",
        r"\band\s+(?:then\s+)?(?:also\s+)?(?:fix|improve|update|refactor|add|change)\b",
        r"\btoo\s*[,.]?\s*(while|since|since we['']re)\b",
        r"\bthrow in\b",
        r"\bquick(?:ly)?\s+also\b",
    ]
]

# Words that indicate large-scope changes that weren't in the original request.
_HIGH_IMPACT_DRIFT_WORDS = re.compile(
    r"\b(?:refactor|redesign|rewrite|overhaul|restructure|rearchitect|"
    r"cleanup|clean[\s-]up|polish|nice[\s-]to[\s-]have|follow[\s-]up|"
    r"explore|investigate|research|opportunistic)\b",
    re.IGNORECASE,
)

# Thresholds
_MIN_PROMPT_WORDS = 6   # ignore very short prompts (< 6 words)
_MAX_INJECTION_LENGTH = 50  # chars — only inject if base message is short enough to scan

_COMMAND_KEYS = {
    "command",
    "cmd",
    "query",
    "prompt",
    "input",
    "description",
    "usermessage",
    "message",
    "text",
    "goal",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walk(obj: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k, v
            yield from _walk(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _event_name() -> str:
    return os.environ.get("COPILOT_HOOK_EVENT", "UserPromptSubmit")


def _extract_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    for key, val in _walk(payload):
        if isinstance(val, str) and key.lower() in _COMMAND_KEYS:
            chunks.append(val)
    return "\n".join(chunks)


def _has_expansion_phrase(text: str) -> bool:
    return any(p.search(text) for p in _EXPANSION_PHRASES)


def _has_high_impact_drift(text: str) -> bool:
    return bool(_HIGH_IMPACT_DRIFT_WORDS.search(text))


def _word_count(text: str) -> int:
    return len(text.split())


def _is_drift(text: str) -> bool:
    if _word_count(text) < _MIN_PROMPT_WORDS:
        return False
    return _has_expansion_phrase(text) or _has_high_impact_drift(text)


def _allowed_by_env() -> bool:
    return os.environ.get("ARIA_ALLOW_SCOPE_DRIFT", "").strip() == "1"


def _reminder_message() -> str:
    return (
        "⚠️  Scope reminder: this prompt appears to add work beyond the current objective.\n\n"
        "Before expanding scope, check the five rules (copilot-instructions.md):\n"
        "  1. Filter the plan — every todo item must directly support the active objective.\n"
        "  2. Reject drift   — avoid unrelated refactors, redesigns, or cleanup sweeps.\n"
        "  3. Defer discoveries — note worthwhile out-of-scope items as follow-ups instead.\n"
        "  4. Re-check after delegation — verify specialist output still matches the original request.\n"
        "  5. Finish first   — complete the requested outcome before polishing adjacent systems.\n\n"
        "If the new work is genuinely in scope, proceed. "
        "If not, finish the current task first, then start a new session for the follow-up.\n"
        "Silence with: ARIA_ALLOW_SCOPE_DRIFT=1"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    if _allowed_by_env():
        sys.exit(0)

    event = _event_name()
    if event != "UserPromptSubmit":
        sys.exit(0)

    text = _extract_text(payload)
    if _is_drift(text):
        print(_reminder_message())

    sys.exit(0)


if __name__ == "__main__":
    main()
