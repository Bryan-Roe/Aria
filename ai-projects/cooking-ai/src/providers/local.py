from __future__ import annotations

import re
import json
from typing import List, Dict

# Pre-compile regex pattern for performance
_RE_QUANTITY = re.compile(r"^(?P<qty>(\d+\/\d+|\d+(\.\d+)?))\s*(?P<unit>[a-zA-Z]+)?\s*(?P<name>.*)")

SAMPLE_RECIPES = [
    {
        "title": "Simple Tomato Pasta",
        "ingredients": [
            "200g spaghetti",
            "2 tbsp olive oil",
            "3 cloves garlic",
            "400g canned tomatoes",
            "salt",
            "pepper",
            "fresh basil",
        ],
        "instructions": "Cook pasta; sauté garlic; add tomatoes; simmer; toss with pasta and basil.",
        "tags": ["vegetarian", "weeknight"],
        "est_time_minutes": 25,
    },
    {
        "title": "Vegan Chickpea Curry",
        "ingredients": [
            "1 tbsp coconut oil",
            "1 onion",
            "2 cloves garlic",
            "1 tbsp curry powder",
            "400g chickpeas",
            "400ml coconut milk",
            "spinach handful",
            "salt",
        ],
        "instructions": "Sauté aromatics; add spices; add chickpeas & coconut milk; simmer; fold in spinach.",
        "tags": ["vegan", "gluten-free"],
        "est_time_minutes": 30,
    },
    {
        "title": "Garlic Butter Salmon",
        "ingredients": [
            "2 salmon fillets",
            "2 tbsp butter",
            "2 cloves garlic",
            "lemon juice",
            "parsley",
            "salt",
            "pepper",
        ],
        "instructions": "Pan sear salmon; melt butter with garlic; finish with lemon and parsley.",
        "tags": ["high-protein"],
        "est_time_minutes": 18,
    },
]


class LocalProvider:
    """Offline deterministic provider.

    Interprets task markers in the last user message:
      - TASK:RECIPE_SEARCH
      - TASK:INGREDIENT_EXTRACTION
    Returns JSON strings for predictable testing.
    """

    def complete(self, messages: List[Dict[str, str]], json_mode: bool = False) -> str:  # noqa: D401
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        if "TASK:RECIPE_SEARCH" in last_user:
            return self._handle_search(last_user)
        if "TASK:INGREDIENT_EXTRACTION" in last_user:
            return self._handle_extract(last_user)
        return json.dumps({"recipes": []})

    def _handle_search(self, prompt: str) -> str:
        # Dynamic scoring based on query tokens and optional tag filters.
        # Prompt format lines: Query: <text>, Filters: comma,separated, Limit: N
        q_match = re.search(r"Query:\s*(.*)", prompt)
        query = (q_match.group(1).strip() if q_match else "").lower()
        f_match = re.search(r"Filters:\s*(.*)", prompt)
        filters_raw = (f_match.group(1).strip() if f_match else "")
        filters = [f.strip().lower() for f in filters_raw.split(',') if f.strip()]
        l_match = re.search(r"Limit:\s*(\d+)", prompt)
        limit = int(l_match.group(1)) if l_match else 5

        tokens = [t for t in re.split(r"[^a-zA-Z]+", query) if t]
        scored = []
        for r in SAMPLE_RECIPES:
            # Filter by tags (optimized: pre-compute tag set for O(1) membership check)
            if filters:
                recipe_tags = {tag.lower() for tag in r["tags"]}
                if not all(any(f in tag for tag in recipe_tags) for f in filters):
                    continue
            title = r["title"].lower()
            ingredients_blob = " ".join(r["ingredients"]).lower()
            score = 0
            if tokens:
                for tok in tokens:
                    if tok in title:
                        score += 3  # title match weight
                    if tok in ingredients_blob:
                        score += 1  # ingredient mention weight
            else:
                # If no tokens provided, give small baseline score
                score = 1
            scored.append((score, r))

        # Sort by score desc then by title for stability
        scored.sort(key=lambda x: (-x[0], x[1]["title"]))
        # If no results after filtering, fall back to unfiltered list with baseline scoring
        if not scored:
            fallback = []
            for r in SAMPLE_RECIPES:
                title = r["title"].lower()
                ingredients_blob = " ".join(r["ingredients"]).lower()
                score = 0
                for tok in tokens:
                    if tok in title:
                        score += 3
                    if tok in ingredients_blob:
                        score += 1
                fallback.append((score, r))
            fallback.sort(key=lambda x: (-x[0], x[1]["title"]))
            scored = fallback or [(1, r) for r in SAMPLE_RECIPES]

        results = [r for _, r in scored[:limit]]
        return json.dumps({"recipes": results})

    def _handle_extract(self, prompt: str) -> str:
        # Pull raw text after marker (fallback to whole prompt if not found)
        text_match = re.search(r"Text:\s*(.*)", prompt, re.DOTALL)
        text = text_match.group(1).strip() if text_match else prompt
        lines = [l.strip() for l in re.split(r"[\n,;]", text) if l.strip()]
        items = []
        for raw in lines:
            m = _RE_QUANTITY.match(raw)
            if m:
                items.append(
                    {
                        "raw": raw,
                        "name": m.group("name").strip(),
                        "quantity": m.group("qty"),
                        "unit": m.group("unit"),
                        "notes": None,
                    }
                )
            else:
                items.append(
                    {
                        "raw": raw,
                        "name": re.sub(r"\d+", "", raw).strip(),
                        "quantity": None,
                        "unit": None,
                        "notes": None,
                    }
                )
        return json.dumps({"ingredients": items})
