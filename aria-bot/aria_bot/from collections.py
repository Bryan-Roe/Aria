from collections.abc import Sequence
from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _extract_assistant_text(payload: Any) -> str:
    root = _as_dict(payload)

    choices_raw = root.get("choices")
    choices = _as_list(choices_raw)
    first = _as_dict(choices[0]) if choices else {}

    message = _as_dict(first.get("message"))
    content_raw = message.get("content")

    if isinstance(content_raw, str):
        return content_raw

    if isinstance(content_raw, Sequence) and not isinstance(content_raw, (str, bytes)):
        parts: list[str] = []
        for item in content_raw:
            item_dict = _as_dict(item)
            text_piece = item_dict.get("text")
            if isinstance(text_piece, str):
                parts.append(text_piece)
        if parts:
            return "".join(parts)

    first.get("text")
