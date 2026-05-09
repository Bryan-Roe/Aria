from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.json_utils import (INGREDIENT_EXTRACTION_SCHEMA,
                              RECIPE_SEARCH_SCHEMA, parse_and_validate)


@pytest.mark.unit
def test_parse_and_validate_search_with_extra_text():
    """Test JSON extraction from text with surrounding prose."""
    # Extra prose around JSON; ensure repair extracts first JSON block
    raw = """
    Here are some ideas:
    {"recipes": [{"title": "A", "ingredients": ["x"], "instructions": "...", "tags": ["t"], "est_time_minutes": null}]}
    Thanks!
    """.strip()
    data, err = parse_and_validate(raw, RECIPE_SEARCH_SCHEMA)
    assert err is None, f"Validation error: {err}"
    assert isinstance(data, dict), "Parsed data should be a dict"
    assert "recipes" in data, "Should contain 'recipes' key"


@pytest.mark.unit
def test_parse_and_validate_extract_schema():
    """Test ingredient extraction JSON schema validation."""
    raw = json.dumps(
        {
            "ingredients": [
                {
                    "raw": "2 cups flour",
                    "name": "flour",
                    "quantity": "2",
                    "unit": "cups",
                    "notes": None,
                }
            ]
        }
    )
    data, err = parse_and_validate(raw, INGREDIENT_EXTRACTION_SCHEMA)
    assert err is None, f"Validation error: {err}"
    assert isinstance(data, dict), "Parsed data should be a dict"
    assert "ingredients" in data, "Should contain 'ingredients' key"


@pytest.mark.unit
def test_parse_and_validate_invalid_json():
    """Test that invalid JSON is gracefully handled."""
    raw = '{"recipes": [invalid json}'
    data, err = parse_and_validate(raw, RECIPE_SEARCH_SCHEMA)
    assert err is not None, "Should return an error for invalid JSON"
    assert data is None, "Data should be None on error"


@pytest.mark.unit
def test_parse_and_validate_schema_mismatch():
    """Test that schema mismatches are detected."""
    # Missing required 'recipes' key
    raw = json.dumps({"wrong_key": []})
    data, err = parse_and_validate(raw, RECIPE_SEARCH_SCHEMA)
    assert err is not None, "Should return an error for schema mismatch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
