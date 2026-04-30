from __future__ import annotations

import argparse
import os
from typing import List

from agents.recipe_agent import RecipeAgent
from providers.local import LocalProvider

try:  # Optional import for GitHub Models
    from providers.github_models import GitHubModelsProvider  # type: ignore
except Exception:  # pragma: no cover
    GitHubModelsProvider = None  # type: ignore


def detect_provider(name: str):
    name = name.lower()
    if name == "github" and GitHubModelsProvider is not None:
        api_key = os.getenv("GITHUB_MODELS_API_KEY") or os.getenv("GITHUB_TOKEN")
        if api_key:
            try:
                return GitHubModelsProvider(api_key=api_key)
            except Exception as e:  # pragma: no cover
                print(
                    f"[warn] Failed to init GitHubModelsProvider: {e}. Falling back to local."
                )
    return LocalProvider()


def interactive_loop(agent: RecipeAgent, provider_name: str):
    print(
        f"Cooking AI - provider: {provider_name}\nCommands: /search <query>; /extract <text>; /exit"
    )
    while True:
        try:
            line = input("cooking> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line == "/exit":
            break
        if line.startswith("/search"):
            query = line[len("/search") :].strip() or "pasta"
            data = agent.search_recipes(query=query, filters=[], limit=5)
            print(data)
            continue
        if line.startswith("/extract"):
            text = line[len("/extract") :].strip() or "2 eggs, 1 cup milk"
            data = agent.extract_ingredients(text)
            print(data)
            continue
        print("Unknown command. Use /search or /extract or /exit.")


def run_once(agent: RecipeAgent, args):
    if args.recipe_search:
        data = agent.search_recipes(
            query=args.recipe_search, filters=args.filter or [], limit=args.limit
        )
        print(data)
    elif args.extract:
        data = agent.extract_ingredients(args.extract)
        print(data)
    else:
        print(
            "No action specified. Use --recipe-search or --extract, or run without --once for interactive mode."
        )


def build_parser():
    p = argparse.ArgumentParser(
        description="Cooking AI - recipe search and ingredient extraction"
    )
    p.add_argument("--provider", default="local", help="Provider: github or local")
    p.add_argument("--model", help="Model override (GitHub Models only)")
    p.add_argument("--recipe-search", dest="recipe_search", help="Recipe search query")
    p.add_argument("--filter", action="append", help="Add filter tag (repeatable)")
    p.add_argument("--limit", type=int, default=5, help="Max recipes to return")
    p.add_argument("--extract", help="Raw recipe text for ingredient extraction")
    p.add_argument("--once", action="store_true", help="Run a single action and exit")
    return p


def main(argv: List[str] | None = None):
    parser = build_parser()
    args = parser.parse_args(argv)
    provider = detect_provider(args.provider)
    agent = RecipeAgent(provider)
    provider_name = provider.__class__.__name__

    if args.once:
        run_once(agent, args)
        return 0

    interactive_loop(agent, provider_name)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
