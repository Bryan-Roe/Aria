# Aria E2E Testing Guide

This document describes the comprehensive testing strategy for the Aria 3D character web interface, focusing on UI-to-server synchronization testing.

## Overview

The Aria project includes multiple layers of testing to ensure the frontend (JavaScript) properly syncs object state with the backend (Python server):

1. **Unit Tests** - Test individual server functions (tag generation, helper functions)
2. **Integration Tests** - Test HTTP API endpoints directly (object add/update/remove)
3. **E2E Browser Tests** - Test the complete flow in a real browser (UI → JavaScript → Server)

## Test Files

### Unit Tests
- **`tests/test_aria_server.py`** - Server-side unit tests
  - Tests tag generation (`[aria:say]`, `[aria:position]`, etc.)
  - Fast, no external dependencies
  - Run with: `pytest tests/test_aria_server.py`

### Integration Tests
- **`tests/test_object_api_integration.py`** - HTTP API integration tests
  - Tests REST endpoints (`/api/aria/object`, `/api/aria/state`)
  - Requires server running on port 8000
  - Simulates client requests without browser
  - Run with: `pytest tests/test_object_api_integration.py`

### E2E Browser Tests

#### Pyppeteer (Chromium via CDP)
- **`tests/test_ui_pyppeteer.py`** - Browser automation using pyppeteer
  - Uses Chrome DevTools Protocol
  - Lightweight, Python-native
  - Supports custom Chrome path via `CHROME_PATH` env var
  - Run with: `pytest tests/test_ui_pyppeteer.py`

#### Playwright (Modern browser automation)
- **`tests/test_ui_playwright.py`** - Browser automation using Playwright
  - Modern, cross-browser (Chrome/Firefox/Safari)
  - Better debugging and error messages
  - Recommended for local development
  - Run with: `pytest tests/test_ui_playwright.py -m playwright`

#### Selenium (Containerized Chrome)
- **`tests/test_ui_selenium.py`** - Browser automation using Selenium Grid
  - Uses remote Chrome in Docker container
  - Best for CI/CD and isolated testing
  - Supports VNC for watching tests run
  - Run with: `pytest tests/test_ui_selenium.py -m selenium`

## Running Tests Locally

### Prerequisites

```bash
# Install base dependencies
pip install pytest requests

# For Pyppeteer tests
pip install pyppeteer
# Download Chromium (one-time)
python -c "import asyncio; from pyppeteer import chromium_downloader; asyncio.get_event_loop().run_until_complete(chromium_downloader.download_chromium())"

# For Playwright tests
pip install playwright
playwright install chromium

# For Selenium tests
pip install selenium
# Start Selenium Chrome container
docker run -d -p 4444:4444 -p 5900:5900 --shm-size=2g selenium/standalone-chrome:latest
```

### Quick Test Commands

```bash
# Run all fast tests (unit + integration)
pytest tests/test_aria_server.py tests/test_object_api_integration.py -v

# Run Pyppeteer E2E tests
pytest tests/test_ui_pyppeteer.py -v

# Run Playwright E2E tests
pytest tests/test_ui_playwright.py -m playwright -v

# Run Selenium E2E tests (requires Docker container)
pytest tests/test_ui_selenium.py -m selenium -v

# Run ALL tests (excluding browser tests)
pytest tests/test_*aria*.py tests/test_object_api*.py -v

# Run ALL E2E tests (will skip if browsers not available)
pytest tests/test_ui_*.py -v
```

### Using pytest markers

```bash
# Run only E2E tests
pytest -m e2e -v

# Run unit tests only
pytest -m unit -v

# Run integration tests only
pytest -m integration -v

# Run everything except slow tests
pytest -m "not slow" -v

# Run everything except E2E tests
pytest -m "not e2e" -v
```

## CI/CD Integration

The project includes a comprehensive GitHub Actions workflow (`.github/workflows/aria-tests.yml`) that runs all test types in parallel:

### Workflow Jobs

1. **unit-integration-tests** (Python 3.10, 3.11, 3.12)
   - Runs unit and integration tests
   - Fast feedback (< 1 minute)
   - No browser dependencies

2. **playwright-e2e**
   - Installs Playwright and Chromium
   - Starts Aria server
   - Runs full E2E tests
   - Duration: ~2-3 minutes

3. **pyppeteer-e2e**
   - Installs system dependencies for Chromium
   - Downloads Pyppeteer Chromium
   - Runs E2E tests
   - Duration: ~2-3 minutes

4. **containerized-chrome-e2e**
   - Uses Selenium standalone Chrome service
   - Isolated browser environment
   - Best for consistency across environments
   - Duration: ~2-3 minutes

5. **test-summary**
   - Aggregates results from all jobs
   - Provides unified test report

### Triggering the Workflow

The workflow runs automatically on:
- Push to `main` or `develop` branches
- Pull requests targeting `main` or `develop`
- Changes to `aria_web/` directory or test files

Manual trigger:
```bash
# Go to GitHub Actions tab → Select "Aria E2E Tests" → Click "Run workflow"
```

## Environment Variables

### Server Configuration
- `ARIA_SERVER_URL` - Base URL for Aria server (default: `http://localhost:8000`)

### Pyppeteer Configuration
- `CHROME_PATH` - Custom Chrome/Chromium binary path
- `PUPPETEER_EXECUTABLE_PATH` - Alternative to CHROME_PATH
- `PYPPETEER_DEBUG` - Enable debug output (set to `true`)

### Selenium Configuration
- `SELENIUM_REMOTE_URL` - Selenium Grid hub URL (default: `http://localhost:4444/wd/hub`)

## Test Architecture

### What Each Test Type Validates

#### Unit Tests
- `[aria:say]` tag generation for speech commands
- `[aria:position]` tag generation for movement
- Object detection in command strings
- Helper function correctness

#### Integration Tests
- POST `/api/aria/object` with action `add` creates object
- POST `/api/aria/object` with action `update` modifies object position
- POST `/api/aria/object` with action `remove` deletes object
- GET `/api/aria/state` returns current state
- GET `/api/aria/objects` lists all objects

#### E2E Tests (All Variants)
1. **Add Object**: Click "Add Object" → Verify object appears in server state
2. **Pick Up Object**: Click object → Call `pickUpObject()` → Verify `state: 'held'` on server
3. **Drop Object**: Call `dropObject()` → Verify object state changes to `on_stage` or `on_table`
4. **Remove Object**: Send remove command → Verify object deleted from server

### Test Flow Diagram

```
┌─────────────────────┐
│   Browser UI        │
│  (aria_web/index.html)│
└──────────┬──────────┘
           │ User clicks/drags
           ▼
┌─────────────────────┐
│  aria_controller.js │
│  - addObject()      │
│  - pickUpObject()   │
│  - dropObject()     │
│  - sendObjectUpdate()│
└──────────┬──────────┘
           │ POST /api/aria/object
           ▼
┌─────────────────────┐
│   aria server.py    │
│  - stage_state{}    │
│  - handle_object()  │
└──────────┬──────────┘
           │ Updates state
           ▼
┌─────────────────────┐
│  E2E Test Validates │
│  - GET /api/aria/state│
│  - Asserts object   │
│    position/state   │
└─────────────────────┘
```

## Troubleshooting

### Pyppeteer: "Browser launch failed"

**Cause**: Missing system dependencies for Chromium

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# Or use custom Chrome
export CHROME_PATH=/usr/bin/google-chrome
pytest tests/test_ui_pyppeteer.py -v
```

### Playwright: "Executable doesn't exist"

**Cause**: Browsers not installed

**Solution**:
```bash
playwright install chromium
# Or install all browsers
playwright install
```

### Selenium: "Connection refused to localhost:4444"

**Cause**: Selenium Chrome container not running

**Solution**:
```bash
# Start container
docker run -d -p 4444:4444 -p 5900:5900 --shm-size=2g selenium/standalone-chrome:latest

# Verify container is running
docker ps | grep selenium

# Check Selenium hub status
curl http://localhost:4444/wd/hub/status
```

### Server: "Connection refused on port 8000"

**Cause**: Aria server not running

**Solution**:
```bash
# Start server manually
cd aria_web
python server.py

# Or let test start it (tests auto-start if not running)
```

### Test skipped: "Chromium not available"

**Cause**: Browser automation library can't launch browser

**Solution**:
- Check if you're in a headless environment (CI, container)
- Ensure system dependencies are installed
- Verify browser installation
- Set custom Chrome path if needed

## Best Practices

1. **Start with integration tests** - Fastest feedback loop, no browser overhead
2. **Use Playwright for local development** - Best error messages and debugging
3. **Use Selenium in CI/CD** - Most consistent across environments
4. **Mark tests appropriately** - Use pytest markers for selective execution
5. **Keep E2E tests focused** - Test critical user flows, not every button click
6. **Mock external services in unit tests** - Don't hit real APIs
7. **Clean up test data** - Always remove test objects after tests

## Future Improvements

- [ ] Add visual regression testing (screenshot comparison)
- [ ] Add performance testing (measure API response times)
- [ ] Add load testing (concurrent users)
- [ ] Add accessibility testing (ARIA labels, keyboard navigation)
- [ ] Add cross-browser testing (Firefox, Safari via Playwright)
- [ ] Add mobile browser testing (Chrome Mobile, Safari iOS)
- [ ] Add test coverage reporting
- [ ] Add mutation testing

## Contributing

When adding new features to the Aria interface:

1. Write unit tests first (TDD approach)
2. Add integration tests for new API endpoints
3. Add E2E tests for critical user flows
4. Update this documentation
5. Ensure all tests pass before submitting PR

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python Documentation](https://playwright.dev/python/)
- [Pyppeteer Documentation](https://pyppeteer.github.io/pyppeteer/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
