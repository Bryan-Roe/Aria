from __future__ import annotations

"""High-level Cooking AI agent.

Provides methods:
  - search_recipes(query: str, filters: list[str], limit: int)
  - extract_ingredients(text: str)

Abstracts provider differences. Providers must implement:
  complete(messages: list[dict[str,str]], json_mode: bool=False) -> str
"""

from typing import Any, Protocol

try:
    # When running tests that inject src/ into sys.path
    from utils.json_utils import INGREDIENT_EXTRACTION_SCHEMA, RECIPE_SEARCH_SCHEMA, parse_and_validate
except ImportError:  # pragma: no cover
    # Fallback for package-style execution (not typical here but defensive)
    from ..utils.json_utils import INGREDIENT_EXTRACTION_SCHEMA, RECIPE_SEARCH_SCHEMA, parse_and_validate


class ProviderProtocol(Protocol):  # Structural typing for providers
    def complete(self, messages: list[dict[str, str]], json_mode: bool = False) -> str:  # pragma: no cover
        ...


SYSTEM_PROMPT = "You are a helpful cooking assistant. Always output STRICT JSON with no commentary."

SEARCH_PROMPT_TEMPLATE = """
TASK:RECIPE_SEARCH
Return a JSON object: {{"recipes": [ {{"title":..., "ingredients": [...], "instructions": "...", "tags": [...], "est_time_minutes": <number|null>}} ]}}
Rules:
- Provide diverse, concise recipes.
- Include estimated time if obvious else null.
- Use simple ingredient forms.
Query: {query}
Filters: {filters}
Limit: {limit}

Examples (follow structure exactly):
Input:
    Query: vegan pasta
    Filters: vegan
    Limit: 2
Output:
    {{"recipes": [
        {{"title": "Vegan Tomato Pasta", "ingredients": ["spaghetti", "olive oil", "garlic", "tomatoes", "basil"], "instructions": "Boil pasta; sauté garlic; add tomatoes; toss with pasta and basil.", "tags": ["vegan"], "est_time_minutes": 20}},
        {{"title": "Mushroom Bolognese", "ingredients": ["mushrooms", "onion", "garlic", "tomato paste", "pasta"], "instructions": "Cook mushrooms; add aromatics and paste; simmer; serve with pasta.", "tags": ["vegan"], "est_time_minutes": 30}}
    ]}}

Output must be valid JSON ONLY with no extra text.
""".strip()

EXTRACT_PROMPT_TEMPLATE = """
TASK:INGREDIENT_EXTRACTION
Given raw recipe text lines, extract structured ingredients.
Return JSON: {{"ingredients": [{{"raw":..., "name":..., "quantity":..., "unit":..., "notes":...}}]}}
Text: {text}

Example:
Input Text:
    2 cups flour\n1 tsp salt\n3 eggs
Output JSON:
    {{"ingredients": [
        {{"raw": "2 cups flour", "name": "flour", "quantity": "2", "unit": "cups", "notes": null}},
        {{"raw": "1 tsp salt", "name": "salt", "quantity": "1", "unit": "tsp", "notes": null}},
        {{"raw": "3 eggs", "name": "eggs", "quantity": "3", "unit": null, "notes": null}}
    ]}}

Output must be valid JSON ONLY with no extra text.
""".strip()


class RecipeAgent:
    def __init__(self, provider: ProviderProtocol) -> None:
        self.provider = provider

    def _invoke(self, user_content: str, json_schema: dict[str, Any]) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        # Stricter JSON mode with up to 2 retries
        for _attempt in range(2):
            raw = self.provider.complete(messages, json_mode=True)
            data, err = parse_and_validate(raw, json_schema)
            if data is not None:
                return data
            # reinforce instruction for retry
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": user_content
                    + "\nReturn ONLY a valid minified JSON object matching the schema. No comments.",
                },
            ]

        # Try without JSON mode (prompt-only enforcement)
        raw2 = self.provider.complete(messages, json_mode=False)
        data2, err2 = parse_and_validate(raw2, json_schema)
        if data2 is not None:
            return data2
        # Last resort: empty structure
        if json_schema is RECIPE_SEARCH_SCHEMA:
            return {"recipes": []}
        if json_schema is INGREDIENT_EXTRACTION_SCHEMA:
            return {"ingredients": []}
        return {"recipes": []}

    def search_recipes(self, query: str, filters: list[str] | None = None, limit: int = 5) -> dict[str, Any]:
        filters = filters or []
        prompt = SEARCH_PROMPT_TEMPLATE.format(query=query, filters=", ".join(filters), limit=limit)
        return self._invoke(prompt, RECIPE_SEARCH_SCHEMA)

    def extract_ingredients(self, text: str) -> dict[str, Any]:
        prompt = EXTRACT_PROMPT_TEMPLATE.format(text=text)
        return self._invoke(prompt, INGREDIENT_EXTRACTION_SCHEMA)


__all__ = ["RecipeAgent"]
