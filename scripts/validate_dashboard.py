import re
from pathlib import Path

# Pre-compile regex patterns for performance
_RE_CONSOLE_LOG = re.compile(r'console\.log\([^)]+\)')
_RE_GET_BY_ID = re.compile(r"getElementById\(['\"]([^'\"]+)['\"]\)")
_RE_QUERY_SELECTOR = re.compile(r"querySelector\(['\"]([^'\"]+)['\"]\)")
_RE_ELEMENT_IDS = re.compile(r'id=["\']([^"\']+)["\']')
_RE_ASYNC_FUNCTION = re.compile(r'async\s+function')
_RE_AWAIT = re.compile(r'\bawait\s+')
_RE_EVENT_LISTENER = re.compile(r'addEventListener\s*\(')
_RE_FETCH_CALLS = re.compile(r"fetch\(['\"]([^'\"]+)['\"]\)")
_RE_LOCALSTORAGE = re.compile(r"localStorage\.(getItem|setItem|removeItem)\(['\"]([^'\"]+)['\"]\)")
_RE_ONCLICK = re.compile(r'onclick=["\']([^"\']+)["\']')

html_file = Path('dashboard/unified.html')
content = html_file.read_text(encoding='utf-8')

print('=== Extended Dashboard Validation ===\n')

issues_found = []

# 1. Check for console.log statements (potential debugging artifacts)
console_logs = _RE_CONSOLE_LOG.findall(content)
if console_logs:
    print(f'  Found {len(console_logs)} console.log statements (consider removing for production)')
else:
    print(' No console.log statements')

# 2. Check for undefined variable references in common patterns
print('\n Checking variable references...')
potential_issues = {
    'getElementById': _RE_GET_BY_ID.findall(content),
    'querySelector': _RE_QUERY_SELECTOR.findall(content),
}

element_ids = _RE_ELEMENT_IDS.findall(content)
print(f' Found {len(element_ids)} element IDs defined')

missing_ids = []
for method, ids in potential_issues.items():
    for id_ref in ids:
        if '#' not in id_ref and '.' not in id_ref and '[' not in id_ref:  # Simple ID check
            if id_ref not in element_ids:
                missing_ids.append((method, id_ref))

if missing_ids:
    print(f'\n  Potential missing element IDs:')
    for method, id_ref in missing_ids:
        print(f'   - {method}("{id_ref}")')
else:
    print(' All element ID references appear valid')

# 3. Check for async/await patterns
async_functions = len(_RE_ASYNC_FUNCTION.findall(content))
await_calls = len(_RE_AWAIT.findall(content))
print(f'\n Async functions: {async_functions}, await calls: {await_calls}')

# 4. Check for event listeners
event_listeners = len(_RE_EVENT_LISTENER.findall(content))
print(f' Event listeners: {event_listeners}')

# 5. Check for fetch calls (API endpoints)
fetch_calls = _RE_FETCH_CALLS.findall(content)
print(f'\n API endpoints used: {len(set(fetch_calls))}')
for endpoint in sorted(set(fetch_calls)):
    print(f'   - {endpoint}')

# 6. Check for localStorage usage
localstorage_keys = _RE_LOCALSTORAGE.findall(content)
if localstorage_keys:
    print(f'\n LocalStorage keys: {len(set([k[1] for k in localstorage_keys]))}')
    for method, key in sorted(set(localstorage_keys)):
        print(f'   - {key} ({method})')

# 7. Check for potential syntax errors in inline onclick handlers
print('\n Checking inline onclick syntax...')
onclick_handlers = _RE_ONCLICK.findall(content)
syntax_ok = True
for i, handler in enumerate(onclick_handlers, 1):
    # Check for balanced parentheses
    if handler.count('(') != handler.count(')'):
        print(f' Unbalanced parentheses in onclick #{i}: {handler[:50]}...')
        syntax_ok = False
        issues_found.append(f'onclick_{i}')

if syntax_ok:
    print(' All onclick handlers have valid syntax')

# 8. Check for Chart.js dependency
if 'Chart.js' in content or 'chartjs' in content.lower():
    print('\n Chart.js dependency detected')
    if 'cdn.jsdelivr.net/npm/chart.js' in content:
        print(' Chart.js loaded from CDN')

# Summary
print(f'\n{"="*50}')
if not issues_found:
    print(' Dashboard validation complete - No critical issues found!')
    print('\n Dashboard is ready for use at http://localhost:8000/unified.html')
else:
    print(f'  Found {len(issues_found)} potential issues')
    for issue in issues_found:
        print(f'   - {issue}')
