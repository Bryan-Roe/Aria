---
name: "Tests"
description: "Guidance for test files and testing infrastructure"
applyTo: "tests/**"
---
# Tests — Implementation Guidance

## Test Infrastructure
- Runner: `python scripts/test_runner.py --unit` (fast) or `--all` (comprehensive)
- Framework: pytest with markers `@pytest.mark.slow`, `@pytest.mark.azure`, `@pytest.mark.integration`
- Fast local: `pytest tests/ -m "not slow and not azure"`
- VS Code: Use Test Explorer (🧪 icon)

## Test Organization

| Test File | Tests | Requires |
|-----------|-------|----------|
| `test_aria_server.py` | Aria server API endpoints | — |
| `test_object_api_integration.py` | Object CRUD operations | — |
| `test_ui_playwright.py` | Browser E2E (Playwright) | Aria server running |
| `test_ui_pyppeteer.py` | Browser E2E (Pyppeteer) | Aria server + Chromium |
| `test_auto_execute.py` | Action sequence execution | — |

## Patterns
- Server tests mock the HTTP handler; E2E tests start real server.
- E2E tests connect to `http://localhost:8080` (Aria) or `http://localhost:7071` (Functions).
- Use `ARIA_SERVER_URL` and `PYTHONPATH` env vars for CI.
- Validate datasets: `python scripts/validate_datasets.py --category chat`
- Quick cross-component validation: `python scripts/fast_validate.py`

## CI Workflows
- `aria-tests.yml` — Multi-version, multi-browser (path-filtered to `aria_web/`)
- `e2e-tests.yml` — Quick regression (runs on all pushes to main)
- `ci-pipeline.yml` — Full CI with unit + integration tests
