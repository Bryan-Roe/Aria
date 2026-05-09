import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from providers.local import LocalProvider

p = LocalProvider()
prompt = """
TASK:INGREDIENT_EXTRACTION
Text: 2 cups flour, 1 tsp salt\n3 eggs
"""
print(p._handle_extract(prompt))
