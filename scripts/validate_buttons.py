import sys
import re
from pathlib import Path

html_file = Path('dashboard/unified.html')
content = html_file.read_text(encoding='utf-8')

print('=== Automated Button Function Validation ===\n')

# Extract all onclick handlers
onclick_pattern = r'onclick=["\']([^"\']+)["\']'
onclick_matches = re.findall(onclick_pattern, content)

print(f' Found {len(onclick_matches)} onclick handlers\n')

# Extract function names from onclick handlers
function_calls = set()
for match in onclick_matches:
    # Extract function name (handle cases like "functionName()", "event.stopPropagation(); functionName()")
    func_names = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', match)
    function_calls.update(func_names)

# Remove common JavaScript methods that aren't custom functions
built_in_methods = {'stopPropagation', 'preventDefault'}
function_calls -= built_in_methods

print(f' Unique functions called: {len(function_calls)}\n')

# Check if each function is defined
missing_functions = []
defined_functions = []

for func_name in sorted(function_calls):
    # Look for function definition patterns
    patterns = [
        rf'function\s+{func_name}\s*\(',
        rf'const\s+{func_name}\s*=',
        rf'let\s+{func_name}\s*=',
        rf'var\s+{func_name}\s*='
    ]
    
    found = False
    for pattern in patterns:
        if re.search(pattern, content):
            found = True
            break
    
    if found:
        defined_functions.append(func_name)
        print(f' {func_name}')
    else:
        missing_functions.append(func_name)
        print(f' {func_name} - NOT DEFINED')

print(f'\n=== Summary ===')
print(f' Defined: {len(defined_functions)}/{len(function_calls)}')
print(f' Missing: {len(missing_functions)}/{len(function_calls)}')

if missing_functions:
    print(f'\n Missing functions that need to be defined:')
    for func in missing_functions:
        print(f'   - {func}')
    sys.exit(1)
else:
    print(f'\n All button functions are properly defined!')
    sys.exit(0)
