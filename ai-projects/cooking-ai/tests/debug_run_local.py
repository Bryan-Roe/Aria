import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from providers.local import LocalProvider

p = LocalProvider()
prompt = """
TASK:RECIPE_SEARCH
Query: vegan pasta
Filters:
Limit: 5
"""
print(p._handle_search(prompt))
