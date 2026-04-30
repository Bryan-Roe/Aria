"""JSON parsing, validation, and light repair utilities for Cooking AI."""

from __future__ import annotations

import json
import re
from typing import Optional, Tuple

from jsonschema import ValidationError, validate

# Basic schemas
RECIPE_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "recipes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "ingredients": {"type": "array", "items": {"type": "string"}},
                    "instructions": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "est_time_minutes": {"type": ["number", "null"]},
                },
                "required": ["title", "ingredients"],
            },
        }
    },
    "required": ["recipes"],
}

INGREDIENT_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "ingredients": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "raw": {"type": "string"},
                    "name": {"type": "string"},
                    "quantity": {"type": ["string", "number", "null"]},
                    "unit": {"type": ["string", "null"]},
                    "notes": {"type": ["string", "null"]},
                },
                "required": ["raw", "name"],
            },
        }
    },
    "required": ["ingredients"],
}

# Simple JSON repair heuristics: extract first JSON object or array block
JSON_BLOCK_RE = re.compile(r"({[\s\S]*}|\[[\s\S]*])")


def _coerce_json(text: str) -> str:
    # Trim leading non-json characters
    text = text.strip()
    # If already valid, return
    if text.startswith("{") or text.startswith("["):
        return text
    m = JSON_BLOCK_RE.search(text)
    if m:
        return m.group(0)
    return text


def parse_and_validate(raw: str, schema: dict) -> Tuple[Optional[dict], Optional[str]]:
    candidate = _coerce_json(raw)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"
    try:
        validate(data, schema)
    except ValidationError as ve:
        return None, f"Schema validation error: {ve.message}"
    return data, None


__all__ = [
    "RECIPE_SEARCH_SCHEMA",
    "INGREDIENT_EXTRACTION_SCHEMA",
    "parse_and_validate",
]
