# =============================================================================
# Aria Platform — Makefile
# =============================================================================
# Common targets for local development, testing, linting, and building.
#
# Prerequisites: python 3.11+, pip, docker, docker-compose
#
# Quick start:
#   make install      # install all dependencies
#   make dev          # start all services locally (Aria + Functions)
#   make test         # run unit tests
#   make lint         # run ruff + black --check
#   make format       # auto-format code
# =============================================================================

VENV_PYTHON  := $(wildcard .venv/bin/python)
PYTHON       ?= $(if $(VENV_PYTHON),$(VENV_PYTHON),python3)
PIP          ?= $(PYTHON) -m pip
PYTEST       ?= $(PYTHON) -m pytest
RUFF         ?= $(PYTHON) -m ruff
BLACK        ?= $(PYTHON) -m black
MYPY         ?= $(PYTHON) -m mypy
COMPOSE      ?= docker compose
TEST_PATH    ?= tests
ARIA_PORT    ?= 8080
FUNC_PORT    ?= 7071
GRADIO_PORT  ?= 7860
GRADIO_SHARE ?= false

.PHONY: all install install-qai dev start stop build test test-unit test-integration \
	lint format type-check clean docker-build docker-dev start-gradio \
	start-local-status start-qai validate-mcp validate-mcp-json help

# Default target
all: lint test

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

## Install all project dependencies (runtime + dev)
install:
	$(PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	@if [ -f requirements-dev.txt ]; then $(PIP) install -r requirements-dev.txt; fi
	@echo "✅ Dependencies installed."

## Install only runtime dependencies
install-prod:
	$(PIP) install --upgrade pip
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi

# ---------------------------------------------------------------------------
# Development servers
# ---------------------------------------------------------------------------

## Start all services via Docker Compose (Aria web UI + Azure Functions)
dev:
	$(COMPOSE) -f docker-compose.dev.yml up --build

## Start Aria web server locally (without Docker)
start:
	@echo "🚀 Starting Aria web server on port $(ARIA_PORT)..."
	$(PYTHON) apps/aria/server.py --port $(ARIA_PORT)

## Start Azure Functions host locally (requires func CLI)
start-functions:
	@command -v func >/dev/null 2>&1 || { echo "❌ func CLI not found. Install: npm i -g azure-functions-core-tools@4"; exit 1; }
	func host start --port $(FUNC_PORT)

## Start the lightweight local /api/ai/status adapter on FUNC_PORT
start-local-status:
	$(PYTHON) local_dev_adapter.py --port $(FUNC_PORT)

## Install QAI integration service dependencies
install-qai:
	$(PIP) install -r mount/requirements.txt

## Start the QAI integration service on port 8000
start-qai: install-qai
	@echo "🚀 Starting QAI integration service on http://localhost:8000..."
	$(PYTHON) mount/app.py

## Start local Gradio demo UI
start-gradio:
	@echo "🚀 Starting local Gradio demo on port $(GRADIO_PORT)..."
	GRADIO_PORT=$(GRADIO_PORT) GRADIO_SHARE=$(GRADIO_SHARE) $(PYTHON) scripts/gradio_demo.py

## Start autonomous training orchestrator (dry-run by default)
start-orchestrator:
	$(PYTHON) scripts/autonomous_training_orchestrator.py --max-cycles 1 --dry-run

## Stop all Docker Compose services
stop:
	$(COMPOSE) -f docker-compose.dev.yml down

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

## Run all tests
test:
	$(PYTEST) $(TEST_PATH) -q --tb=short

## Run only unit tests (fast, no cloud)
test-unit:
	$(PYTEST) $(TEST_PATH) -q --tb=short -m "not slow and not azure and not integration"

## Run integration tests
test-integration:
	$(PYTEST) $(TEST_PATH) -q --tb=short -m integration

## Run tests with coverage report
test-coverage:
	$(PYTEST) $(TEST_PATH) -q --tb=short --cov=shared --cov=scripts \
		--cov-report=term-missing --cov-report=html:data_out/coverage_html

## Run a quick smoke test (import check)
smoke:
	$(PYTHON) -c "from shared.config import get_settings; s = get_settings(); print('Active provider:', s.active_provider())"
	$(PYTHON) -c "from shared.logging import configure_logging, get_logger; configure_logging(); get_logger('smoke').info('OK')"
	@echo "✅ Smoke test passed."

## Validate configured VS Code MCP stdio servers
validate-mcp:
	@$(PYTHON) scripts/validate_mcp_setup.py

## Validate configured VS Code MCP stdio servers with JSON output
validate-mcp-json:
	@$(PYTHON) scripts/validate_mcp_setup.py --json

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

## Run ruff linter and black formatter check
lint:
	$(RUFF) check $(TEST_PATH) shared/ scripts/ apps/aria/server.py
	$(BLACK) --check --quiet shared/ scripts/ apps/aria/server.py $(TEST_PATH)
	@echo "✅ Lint passed."

## Auto-format code with black and isort via ruff
format:
	$(RUFF) check --fix shared/ scripts/ apps/ $(TEST_PATH) || true
	$(BLACK) shared/ scripts/ apps/aria/server.py $(TEST_PATH)
	@echo "✅ Formatting complete."

## Run mypy type checks
type-check:
	$(MYPY) shared/ --ignore-missing-imports --no-error-summary || true
	@echo "✅ Type check done (warnings above are non-fatal)."

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

## Build Docker images
docker-build:
	docker build -f apps/aria/Dockerfile -t aria-server:local .
	docker build -f Dockerfile -t aria-functions:local .
	@echo "✅ Docker images built."

## Start services with docker-compose (same as dev)
docker-dev: dev

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

## Remove temporary build artifacts
clean:
	find . -type d -name __pycache__ -not -path './.git/*' | xargs rm -rf
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .ruff_cache .pytest_cache data_out/coverage_html
	@echo "✅ Cleaned up."

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

## Show this help message
help:
	@echo ""
	@echo "Aria Platform — available make targets:"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## /  /'
	@echo ""
