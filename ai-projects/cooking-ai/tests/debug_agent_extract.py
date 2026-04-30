import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from agents.recipe_agent import RecipeAgent
from providers.local import LocalProvider

a = RecipeAgent(LocalProvider())
print(a.extract_ingredients("2 cups flour, 1 tsp salt\n3 eggs"))
