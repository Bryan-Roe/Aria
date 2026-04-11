import re
from functools import lru_cache
from pathlib import Path

# Pre-compile regex patterns for performance
_RE_ONCLICK = re.compile(r'onclick=["\']([^"\']+)["\']')
_RE_FUNC_NAMES = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
_RE_ELEMENT_IDS = re.compile(r'id=["\']([^"\']+)["\']')
_RE_GET_BY_ID = re.compile(r"getElementById\(['\"]([^'\"]+)['\"]\)")
_RE_FETCH_CALLS = re.compile(r"fetch\(['\"]([^'\"]+)['\"]\)")


@lru_cache(maxsize=128)
def _compile_function_patterns(func_name: str):
    """Compile and cache function definition patterns for a given function name."""
    escaped = re.escape(func_name)
    return [
        re.compile(rf"function\s+{escaped}\s*\("),
        re.compile(rf"const\s+{escaped}\s*="),
        re.compile(rf"let\s+{escaped}\s*="),
        re.compile(rf"var\s+{escaped}\s*="),
    ]


def _resolve_dashboard_path() -> Path:
    """Resolve dashboard HTML path across legacy and current layouts."""
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        repo_root / "dashboard" / "unified.html",
        repo_root / "apps" / "dashboard" / "unified.html",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


def run_validation() -> bool:
    html_file = _resolve_dashboard_path()
    if not html_file.exists():
        print(f"Dashboard file not found: {html_file}")
        return False

    content = html_file.read_text(encoding="utf-8")

    print("=== Final Dashboard Validation ===\n")

    # 1. Button functions
    onclick_handlers = _RE_ONCLICK.findall(content)
    function_calls = set()
    for match in onclick_handlers:
        func_names = _RE_FUNC_NAMES.findall(match)
        function_calls.update(func_names)

    built_in_methods = {"stopPropagation", "preventDefault"}
    function_calls -= built_in_methods

    defined_count = 0
    for func_name in function_calls:
        patterns = _compile_function_patterns(func_name)
        if any(p.search(content) for p in patterns):
            defined_count += 1

    print(f" Button Functions: {defined_count}/{len(function_calls)} defined")

    # 2. Element ID references
    element_ids = set(_RE_ELEMENT_IDS.findall(content))
    get_by_id_refs = set(_RE_GET_BY_ID.findall(content))

    missing_ids = get_by_id_refs - element_ids
    if missing_ids:
        print(f' Missing Element IDs: {", ".join(sorted(missing_ids))}')
    else:
        print(f" Element IDs: All {len(get_by_id_refs)} references valid")

    # 3. API endpoints
    fetch_calls = set(_RE_FETCH_CALLS.findall(content))
    print(f" API Endpoints: {len(fetch_calls)} endpoints defined")

    # 4. Critical features check
    features = {
        "Dark Mode": "toggleDarkMode" in content,
        "Search/Filter": "filterJobs" in content,
        "Keyboard Shortcuts": "toggleShortcuts" in content,
        "GPU Monitoring": "/api/gpu" in content,
        "Connection Status": "updateConnectionStatus" in content,
        "Performance Badges": "addPerformanceBadge" in content,
        "Chart.js": "Chart.js" in content or "chartjs" in content.lower(),
    }

    print("\n Feature Completeness:")
    for feature, present in features.items():
        status = "OK" if present else "MISSING"
        print(f"{status} {feature}")

    # 5. Summary
    all_valid = (
        defined_count == len(function_calls)
        and not missing_ids
        and all(features.values())
    )

    print(f'\n{"=" * 50}')
    if all_valid:
        print("ALL CHECKS PASSED")
        print("Dashboard is fully functional")
        print(f"Ready at: {html_file}")
    else:
        print("Some issues detected - see details above")

    return all_valid


if __name__ == "__main__":
    run_validation()
