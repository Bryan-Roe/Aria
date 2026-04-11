from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Ensure src is importable when running from repo root
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agents.recipe_agent import RecipeAgent  # type: ignore
from providers.local import LocalProvider  # type: ignore
from utils.json_utils import INGREDIENT_EXTRACTION_SCHEMA  # type: ignore
from utils.json_utils import RECIPE_SEARCH_SCHEMA, parse_and_validate


@pytest.mark.unit
def test_search_recipes_returns_valid_structure():
    """Test that search_recipes returns a valid recipes list."""
    agent = RecipeAgent(LocalProvider())
    data = agent.search_recipes("pasta", limit=2)

    assert "recipes" in data, "Response should contain 'recipes' key"
    assert isinstance(data["recipes"], list), "Recipes should be a list"


@pytest.mark.unit
def test_search_recipes_schema_validation():
    """Test that search results conform to the expected JSON schema."""
    agent = RecipeAgent(LocalProvider())
    data = agent.search_recipes("pasta", limit=2)

    parsed, err = parse_and_validate(json.dumps(data), RECIPE_SEARCH_SCHEMA)
    assert err is None, f"Schema validation failed: {err}"
    assert parsed is not None


@pytest.mark.unit
def test_extract_ingredients_returns_valid_structure():
    """Test that extract_ingredients returns a valid ingredients list."""
    agent = RecipeAgent(LocalProvider())
    text = "2 cups flour, 1 tsp salt\n3 eggs"
    data = agent.extract_ingredients(text)

    assert "ingredients" in data, "Response should contain 'ingredients' key"
    assert isinstance(data["ingredients"], list), "Ingredients should be a list"


@pytest.mark.unit
def test_extract_ingredients_schema_validation():
    """Test that extracted ingredients conform to the expected JSON schema."""
    agent = RecipeAgent(LocalProvider())
    text = "2 cups flour, 1 tsp salt\n3 eggs"
    data = agent.extract_ingredients(text)

    parsed, err = parse_and_validate(json.dumps(data), INGREDIENT_EXTRACTION_SCHEMA)
    assert err is None, f"Schema validation failed: {err}"
    assert parsed is not None


@pytest.mark.unit
def test_local_provider_offline_capability():
    """Test that LocalProvider works without external dependencies."""
    # This test ensures offline functionality
    agent = RecipeAgent(LocalProvider())

    # Should not raise any import or connection errors
    data = agent.search_recipes("test query", limit=1)
    assert data is not None


if __name__ == "__main__":
    # Allow manual execution for backward compatibility
    pytest.main([__file__, "-v"])
