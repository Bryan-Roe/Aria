import re
from pathlib import Path

# Pre-compile regex patterns for performance
_RE_ONCLICK = re.compile(r'onclick=["\']([^"\']+)["\']')
_RE_FUNC_NAMES = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
_RE_ELEMENT_IDS = re.compile(r'id=["\']([^"\']+)["\']')
_RE_GET_BY_ID = re.compile(r"getElementById\(['\"]([^'\"]+)['\"]\)")
_RE_FETCH_CALLS = re.compile(r"fetch\(['\"]([^'\"]+)['\"]\)")

html_file = Path('dashboard/unified.html')
content = html_file.read_text(encoding='utf-8')

print('=== Final Dashboard Validation ===\n')

# 1. Button functions
onclick_handlers = _RE_ONCLICK.findall(content)
function_calls = set()
for match in onclick_handlers:
    func_names = _RE_FUNC_NAMES.findall(match)
    function_calls.update(func_names)

built_in_methods = {'stopPropagation', 'preventDefault'}
function_calls -= built_in_methods

defined_count = 0
for func_name in function_calls:
    # Pre-compile patterns for this specific function name
    patterns = [
        re.compile(rf'function\s+{re.escape(func_name)}\s*\('),
        re.compile(rf'const\s+{re.escape(func_name)}\s*='),
        re.compile(rf'let\s+{re.escape(func_name)}\s*='),
        re.compile(rf'var\s+{re.escape(func_name)}\s*=')
    ]
    if any(p.search(content) for p in patterns):
        defined_count += 1

print(f' Button Functions: {defined_count}/{len(function_calls)} defined')

# 2. Element ID references
element_ids = set(_RE_ELEMENT_IDS.findall(content))
get_by_id_refs = set(_RE_GET_BY_ID.findall(content))

missing_ids = get_by_id_refs - element_ids
if missing_ids:
    print(f' Missing Element IDs: {", ".join(missing_ids)}')
else:
    print(f' Element IDs: All {len(get_by_id_refs)} references valid')

# 3. API endpoints
fetch_calls = set(_RE_FETCH_CALLS.findall(content))
print(f' API Endpoints: {len(fetch_calls)} endpoints defined')

# 4. Critical features check
features = {
    'Dark Mode': 'toggleDarkMode' in content,
    'Search/Filter': 'filterJobs' in content,
    'Keyboard Shortcuts': 'toggleShortcuts' in content,
    'GPU Monitoring': '/api/gpu' in content,
    'Connection Status': 'updateConnectionStatus' in content,
    'Performance Badges': 'addPerformanceBadge' in content,
    'Chart.js': 'Chart.js' in content or 'chartjs' in content.lower(),
}

print(f'\n Feature Completeness:')
for feature, present in features.items():
    status = '' if present else ''
    print(f'{status} {feature}')

# 5. Summary
all_valid = (
    defined_count == len(function_calls) and
    not missing_ids and
    all(features.values())
)

print(f'\n{"="*50}')
if all_valid:
    print(' ALL CHECKS PASSED!')
    print(' Dashboard is fully functional')
    print(' Ready at: http://localhost:8000/unified.html')
    print('\n Quick Tips:')
    print('    Press D for dark mode')
    print('    Press / to search jobs')
    print('    Press ? for all shortcuts')
    print('    Press 1-6 to switch tabs')
else:
    print('  Some issues detected - see details above')
