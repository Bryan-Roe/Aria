# Cooking AI (Console App)

Interactive console app that uses an AI language model to:
- Search for recipes by dish, ingredients, or dietary needs
- Extract structured ingredients from free‑form recipe text

It prefers GitHub Models when available and falls back to a local offline provider for zero‑setup testing.

## Features
- Providers: GitHub Models (OpenAI-compatible) and Local fallback
- Two actions: Recipe Search, Ingredient Extraction
- JSON-only responses with schema validation and repair
- Interactive menu and one-shot CLI flags for automation

## Quick start (no keys required)

```powershell
# From repo root
pip install -r .\cooking-ai\requirements.txt
python .\cooking-ai\src\main.py --provider local --recipe-search "chicken, broccoli, weeknight"
python .\cooking-ai\src\main.py --provider local --extract "2 cups flour, 1 tsp salt"

# Interactive menu
python .\cooking-ai\src\main.py --provider local
```

## Use with GitHub Models

Set your API key and choose a model (defaults included):

```powershell
$env:GITHUB_MODELS_API_KEY = "<your-token>"  # or GITHUB_TOKEN
$env:GITHUB_MODELS_MODEL = "gpt-4o-mini"
python .\cooking-ai\src\main.py --provider github
```

Notes:
- Endpoint: https://models.inference.ai.azure.com (OpenAI compatible)
- The app uses the OpenAI Python SDK with a custom base_url.
- If the provider or key is missing, the app falls back to local mode.

## CLI usage

```powershell
python .\cooking-ai\src\main.py [--provider github|local] [--model <name>] [--once]
                                 [--recipe-search "query"] [--extract "text"]
```

Examples:

```powershell
# Search recipes with GitHub Models (requires token)
$env:GITHUB_MODELS_API_KEY = "..."
python .\cooking-ai\src\main.py --provider github --recipe-search "vegan pasta with mushrooms"

# Extract ingredients locally (offline)
python .\cooking-ai\src\main.py --provider local --extract "3 eggs, 1/2 cup milk, pinch of salt"
```

## Environment variables
- GITHUB_MODELS_API_KEY or GITHUB_TOKEN – API key for GitHub Models
- GITHUB_MODELS_MODEL – model name (default: gpt-4o-mini)
- COOKING_TEMPERATURE – sampling temperature (default: 0.4)

## Project layout
- `src/main.py` – CLI entry point and interactive loop
- `src/agents/recipe_agent.py` – high-level agent for search/extract
- `src/providers/github_models.py` – OpenAI-compatible provider
- `src/providers/local.py` – offline deterministic provider
- `src/utils/json_utils.py` – JSON repair and schema validation
- `tests/test_agent.py` – minimal smoke tests

## License
MIT
