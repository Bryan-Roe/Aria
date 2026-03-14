---
applyTo: "ai-projects/cooking-ai/**"
---

# Cooking AI — Instruction Guide

## Project Structure

```
ai-projects/cooking-ai/
    src/
        agents/
            recipe_agent.py    # RecipeAgent — structured recipe search & ingredient extraction
        utils/
            json_utils.py      # JSON schemas for recipe/ingredient output
```

## RecipeAgent Pattern

### Structural Typing
```python
class ProviderProtocol:
    def complete(self, messages: List[Dict], json_mode: bool = False) -> str: ...
```
The agent accepts any provider matching this protocol — no inheritance required.

### JSON Mode with Fallback
```python
# _invoke() implements 2-retry:
try:
    response = provider.complete(messages, json_mode=True)   # Attempt structured output
    return json.loads(response)
except:
    response = provider.complete(messages, json_mode=False)  # Fallback: free text
    return extract_json(response)  # Parse JSON from freeform response
# If both fail → return empty structure matching schema
```

### Output Schemas

**Recipe Search:**
```json
{
    "recipes": [{
        "title": "string",
        "ingredients": ["string"],
        "instructions": ["string"],
        "tags": ["string"],
        "est_time_minutes": 30
    }]
}
```

**Ingredient Extraction:**
```json
{
    "ingredients": [{
        "raw": "string",
        "name": "string",
        "quantity": "string",
        "unit": "string",
        "notes": "string"
    }]
}
```

## Coding Conventions

- Always return structured JSON matching the defined schemas
- Handle provider failures gracefully — return empty structures, never crash
- Use the 2-retry pattern: JSON mode first, then fallback parsing
- Providers: GitHub Models + Local (configurable)
- Keep agent methods idempotent — same input produces same structure
