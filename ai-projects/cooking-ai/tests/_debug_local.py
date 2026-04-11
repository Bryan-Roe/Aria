from providers.local import LocalProvider

p = LocalProvider()
prompt = """
TASK:RECIPE_SEARCH
Query: vegan pasta
Filters:
Limit: 5
"""
print(p._handle_search(prompt))
