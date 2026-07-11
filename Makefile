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
LINT_PATHS   ?= $(TEST_PATH) shared/ scripts/ apps/aria/server.py
PYTEST_COMMON_ARGS ?= -q --tb=short
PYTEST_UNIT_MARKERS ?= not slow and not azure and not integration
PYTEST_XDIST_WORKERS ?= auto
PYTEST_FALLBACK_MIN_FILES_PER_WORKER ?= 2
PYTEST_CHANGED_FALLBACK_MIN_FILES_PER_WORKER ?= 1
CHANGED_QUALITY_PY_FILES ?=
CHANGED_TEST_PY_FILES ?=
CHANGED_SHARED_PY_FILES ?=
ARIA_PORT    ?= 8080
FUNC_PORT    ?= 7071
GRADIO_PORT  ?= 7860
GRADIO_SHARE ?= false
BASELINE_RESULT ?= /home/vscode/.aitk/evals/foundry/eval_f5ba66e749794172942de2d1001dd594/evalrun_d0a3c099c518434892c2e968dca64311/result.json
CANDIDATE_RESULT ?= /home/vscode/.aitk/evals/foundry/eval_f5ba66e749794172942de2d1001dd594/evalrun_d0a3c099c518434892c2e968dca64311/result.json
REPORT_OUTPUT ?= data_out/pr_review_eval_comparison_report.md
REPORT_OUTPUT_LATEST ?= data_out/pr_review_eval_comparison_report_latest.md

.PHONY: all install install-qai dev dev-local start stop build test test-fast test-fast-changed test-unit test-unit-changed test-integration verify-fast verify-changed verify-changed-full \
	lint lint-fast lint-changed format format-changed type-check type-check-changed clean docker-build docker-dev start-gradio \
	start-local-status start-functions-clean restart-functions-clean start-qai \
	validate-mcp validate-mcp-json validate-mcp-config \
	validate-mcp-config-json validate-mcp-config-strict \
	validate-mcp-config-strict-json validate-mcp-suite \
	validate-mcp-suite-server validate-mcp-suite-strict \
	validate-mcp-suite-server-strict validate-mcp-suite-drift \
	validate-mcp-suite-drift-json \
	agents agents-dry ai-automation aria-bot \
	aria-bot-apply test-aria-bot sql-setup-local sql-status sql-status-json \
	sql-doctor sql-doctor-json sql-reset-local sql-verify dab-verify \
	ignore-verify setup-verify help pr-eval-report pr-eval-report-latest \
	pr-eval-gate pr-eval-gate-latest pr-eval-mock pr-eval-all \
	pr-eval-all-strict pr-eval-list pr-eval-status pr-eval-triage-latest \
	validate-eval-workflow-setup validate-eval-workflow-setup-json \
	validate-eval-artifacts validate-eval-artifacts-json

# Default target
all: lint test

define run_pytest_with_optional_xdist
	@XDIST_FLAGS=""; \
	if $(PYTHON) -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('xdist') else 1)" >/dev/null 2>&1; then \
		XDIST_FLAGS="-n $(PYTEST_XDIST_WORKERS)"; \
		echo "🧪 pytest-xdist enabled ($$XDIST_FLAGS)"; \
		$(PYTEST) $(1) $(PYTEST_COMMON_ARGS) $$XDIST_FLAGS $(2); \
	else \
		echo "🧪 pytest-xdist not installed; using builtin parallel fallback (install with .venv/bin/python -m pip install -r requirements-dev.txt or make install to use xdist instead)"; \
		$(PYTHON) scripts/run_pytest_parallel.py --workers "$(PYTEST_XDIST_WORKERS)" --min-files-per-worker "$(PYTEST_FALLBACK_MIN_FILES_PER_WORKER)" $(1) $(PYTEST_COMMON_ARGS) $(2); \
	fi; \

endef

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

## Start all services locally without Docker (Aria on :8080 + local status on :7071)
## Both processes run in the foreground; Ctrl-C stops both.
dev-local:
	@echo "🚀 Starting Aria (port $(ARIA_PORT)) and local status adapter (port $(FUNC_PORT)) without Docker..."
	@trap 'kill 0' INT TERM; \
	$(PYTHON) apps/aria/server.py --port $(ARIA_PORT) & \
	$(PYTHON) local_dev_adapter.py --port $(FUNC_PORT) & \
	wait

## Start Aria web server locally (without Docker)
start:
	@echo "🚀 Starting Aria web server on port $(ARIA_PORT)..."
	$(PYTHON) apps/aria/server.py --port $(ARIA_PORT)

## Start Azure Functions host locally (requires func CLI)
start-functions:
	@command -v func >/dev/null 2>&1 || { echo "❌ func CLI not found. Install: npm i -g azure-functions-core-tools@4"; exit 1; }
	func host start --port $(FUNC_PORT)

## Stop any listener on FUNC_PORT (deterministic, port-based)
start-functions-clean:
	@pids=$$(lsof -t -i:$(FUNC_PORT) -sTCP:LISTEN 2>/dev/null || true); \
	if [ -n "$$pids" ]; then \
		echo "🛑 Stopping process(es) on :$(FUNC_PORT): $$pids"; \
		kill -9 $$pids; \
	else \
		echo "ℹ️ No listener on :$(FUNC_PORT)"; \
	fi

## Restart Azure Functions host using a clean, port-based stop/start flow
restart-functions-clean: start-functions-clean
	@echo "🚀 Restarting Functions host on :$(FUNC_PORT)..."
	@command -v func >/dev/null 2>&1 || { echo "❌ func CLI not found. Install: npm i -g azure-functions-core-tools@4"; exit 1; }
	func host start --port $(FUNC_PORT)

## Start the lightweight local /api/ai/status adapter on FUNC_PORT
start-local-status:
	@if $(PYTHON) -c "import socket,sys; s=socket.socket(); rc=s.connect_ex(('127.0.0.1', $(FUNC_PORT))); s.close(); sys.exit(0 if rc==0 else 1)" >/dev/null 2>&1; then echo "ℹ️ Port $(FUNC_PORT) already in use; checking existing /api/ai/status..."; if $(PYTHON) -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$(FUNC_PORT)/api/ai/status', timeout=3).read(1)" >/dev/null 2>&1; then echo "✅ Local status adapter already running on :$(FUNC_PORT)."; exit 0; else echo "❌ Port $(FUNC_PORT) is occupied by a different service. Stop it or choose another port."; exit 1; fi; else $(PYTHON) local_dev_adapter.py --port $(FUNC_PORT); fi

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

## Bootstrap local SQL (SQLite) and verify connectivity
sql-setup-local:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py setup

## Read-only SQL status check (health + validation row count)
sql-status:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py status

## Read-only SQL status check in JSON format
sql-status-json:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py status --json

## SQL health gate for local/CI usage (non-zero when unhealthy)
sql-doctor:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py doctor

## SQL health gate in JSON format (non-zero when unhealthy)
sql-doctor-json:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py doctor --json

## Reset local SQLite DB file and re-bootstrap sql_setup_check
sql-reset-local:
	@QAI_SQL_URL=$${QAI_SQL_URL:-sqlite:///data_out/qai_local.db} $(PYTHON) scripts/sql_local_tools.py reset

## End-to-end SQL verification (bootstrap + status + focused tests)
sql-verify:
	@$(MAKE) sql-setup-local
	@$(MAKE) sql-status
	@QAI_SQL_URL=sqlite:///:memory: $(PYTEST) -q tests/test_sql_integration.py tests/test_sql_engine_extended.py

## Verify DAB config wiring and local env placeholders (fails on drift)
dab-verify:
	@$(PYTHON) scripts/dab_verify.py

## Verify .gitignore recursively ignores venv/.venv folders
ignore-verify:
	@$(PYTHON) scripts/ignore_verify.py

## Run all local setup guardrails in one command
setup-verify:
	@$(MAKE) ignore-verify
	@$(MAKE) dab-verify

## Start autonomous training orchestrator (dry-run by default)
start-orchestrator:
	$(PYTHON) scripts/autonomous_training_orchestrator.py --max-cycles 1 --dry-run

## Run aria-bot against the repo in dry-run mode
aria-bot:
	@echo "🤖 Running aria-bot in dry-run mode..."
	$(PYTHON) -m aria_bot --repo-root .

## Run aria-bot against the repo and apply safe changes
aria-bot-apply:
	@echo "🤖 Running aria-bot with --apply..."
	$(PYTHON) -m aria_bot --repo-root . --apply

## Stop all Docker Compose services
stop:
	$(COMPOSE) -f docker-compose.dev.yml down

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

## Run all tests
test:
	$(call run_pytest_with_optional_xdist,$(TEST_PATH),)

## Run the fastest local test loop (smoke + unit markers)
test-fast:
	@set -e; \
	$(MAKE) smoke & \
	smoke_pid=$$!; \
	$(MAKE) test-unit & \
	test_pid=$$!; \
	wait $$smoke_pid; \
	wait $$test_pid

## Run the fastest non-mutating local verification loop (fast lint + fast tests)
verify-fast:
	@set -e; \
	$(MAKE) lint-fast & \
	lint_pid=$$!; \
	$(MAKE) test-fast & \
	test_pid=$$!; \
	wait $$lint_pid; \
	wait $$test_pid

## Run the fastest changed-scope local test loop (smoke + changed unit tests)
test-fast-changed:
	@set -e; \
	files="$(CHANGED_TEST_PY_FILES)"; \
	$(MAKE) smoke & \
	smoke_pid=$$!; \
	$(MAKE) test-unit-changed CHANGED_TEST_PY_FILES="$$files" & \
	test_pid=$$!; \
	wait $$smoke_pid; \
	wait $$test_pid

## Run the fastest changed-scope verification loop (lint + smoke + changed unit tests)
verify-changed:
	@set -e; \
	quality_files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py' 'scripts/**/*.py' 'scripts/*.py' 'apps/**/*.py' 'apps/*.py' 'tests/**/*.py' 'tests/*.py' | tr '\n' ' ')"; \
	test_files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'tests/**/*.py' 'tests/*.py' | tr '\n' ' ')"; \
	$(MAKE) lint-changed CHANGED_QUALITY_PY_FILES="$$quality_files" & \
	lint_pid=$$!; \
	$(MAKE) test-fast-changed CHANGED_TEST_PY_FILES="$$test_files" & \
	test_pid=$$!; \
	wait $$lint_pid; \
	wait $$test_pid

## Run the fullest changed-scope verification loop (lint + type-check + smoke + changed unit tests)
verify-changed-full:
	@set -e; \
	quality_files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py' 'scripts/**/*.py' 'scripts/*.py' 'apps/**/*.py' 'apps/*.py' 'tests/**/*.py' 'tests/*.py' | tr '\n' ' ')"; \
	test_files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'tests/**/*.py' 'tests/*.py' | tr '\n' ' ')"; \
	shared_files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py' | tr '\n' ' ')"; \
	$(MAKE) lint-changed CHANGED_QUALITY_PY_FILES="$$quality_files" & \
	lint_pid=$$!; \
	$(MAKE) type-check-changed CHANGED_SHARED_PY_FILES="$$shared_files" & \
	typecheck_pid=$$!; \
	$(MAKE) test-fast-changed CHANGED_TEST_PY_FILES="$$test_files" & \
	test_pid=$$!; \
	wait $$lint_pid; \
	wait $$typecheck_pid; \
	wait $$test_pid

## Run only unit tests (fast, no cloud)
test-unit:
	$(call run_pytest_with_optional_xdist,$(TEST_PATH),-m "$(PYTEST_UNIT_MARKERS)")

## Run only changed test files through the fast unit-test path
test-unit-changed:
	@files="$(CHANGED_TEST_PY_FILES)"; \
	if [ -z "$$files" ]; then \
		files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'tests/**/*.py' 'tests/*.py')"; \
	fi; \
	if [ -z "$$files" ]; then \
		echo "ℹ️ No changed test files to run."; \
		exit 0; \
	fi; \
	echo "🧪 Running changed test files:"; \
	printf '  %s\n' $$files; \
	XDIST_FLAGS=""; \
	if $(PYTHON) -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('xdist') else 1)" >/dev/null 2>&1; then \
		XDIST_FLAGS="-n $(PYTEST_XDIST_WORKERS)"; \
		echo "🧪 pytest-xdist enabled ($$XDIST_FLAGS)"; \
		$(PYTEST) $$files $(PYTEST_COMMON_ARGS) $$XDIST_FLAGS -m "$(PYTEST_UNIT_MARKERS)"; \
	else \
		echo "🧪 pytest-xdist not installed; using builtin parallel fallback (install with .venv/bin/python -m pip install -r requirements-dev.txt or make install to use xdist instead)"; \
		$(PYTHON) scripts/run_pytest_parallel.py --workers "$(PYTEST_XDIST_WORKERS)" --min-files-per-worker "$(PYTEST_CHANGED_FALLBACK_MIN_FILES_PER_WORKER)" $$files $(PYTEST_COMMON_ARGS) -m "$(PYTEST_UNIT_MARKERS)"; \
	fi

## Run integration tests
test-integration:
	$(PYTEST) $(TEST_PATH) $(PYTEST_COMMON_ARGS) -m integration

## Run the focused aria-bot startup and entrypoint regression suite
test-aria-bot:
	$(call run_pytest_with_optional_xdist,tests/test_aria_bot.py tests/test_aria_bot_root_shim.py tests/test_aria_bot_dev_entrypoints.py,)

## Run tests with coverage report
test-coverage:
	$(PYTEST) $(TEST_PATH) $(PYTEST_COMMON_ARGS) --cov=shared --cov=scripts \
		--cov-report=term-missing --cov-report=html:data_out/coverage_html

## Run a quick smoke test (import check)
smoke:
	@set -e; \
	$(PYTHON) -c "from shared.config import get_settings; s = get_settings(); print('Active provider:', s.active_provider())" & \
	provider_pid=$$!; \
	$(PYTHON) -c "from shared.logging import configure_logging, get_logger; configure_logging(); get_logger('smoke').info('OK')" & \
	logging_pid=$$!; \
	wait $$provider_pid; \
	wait $$logging_pid
	@echo "✅ Smoke test passed."

## Validate configured VS Code MCP stdio servers
validate-mcp:
	@$(PYTHON) scripts/validate_mcp_setup.py

## Validate configured VS Code MCP stdio servers with JSON output
validate-mcp-json:
	@$(PYTHON) scripts/validate_mcp_setup.py --json

## Validate MCP config statically (no server launch)
validate-mcp-config:
	@$(PYTHON) scripts/validate_mcp_setup.py --config-only

## Validate MCP config statically with JSON output
validate-mcp-config-json:
	@$(PYTHON) scripts/validate_mcp_setup.py --config-only --json

## Validate MCP config statically with strict env-reference checks
validate-mcp-config-strict:
	@$(PYTHON) scripts/validate_mcp_setup.py --config-only --env-strict

## Validate MCP config statically with strict env-reference checks in JSON output
validate-mcp-config-strict-json:
	@$(PYTHON) scripts/validate_mcp_setup.py --config-only --env-strict --json

## Run full MCP validation suite (config-only + runtime probe) and write JSON artifact
validate-mcp-suite:
	@$(PYTHON) scripts/validate_mcp_suite.py

## Run MCP validation suite for a single server (usage: make validate-mcp-suite-server SERVER=llm-maker)
validate-mcp-suite-server:
	@test -n "$(SERVER)" || (echo "SERVER is required, e.g. make $@ SERVER=llm-maker" && exit 2)
	@$(PYTHON) scripts/validate_mcp_suite.py --server "$(SERVER)" --output "data_out/mcp_validation_suite_$(SERVER).json"

## Run full MCP validation suite with strict env-reference checks
validate-mcp-suite-strict:
	@$(PYTHON) scripts/validate_mcp_suite.py --env-strict --output data_out/mcp_validation_suite_strict.json

## Run strict MCP validation suite for a single server
validate-mcp-suite-server-strict:
	@test -n "$(SERVER)" || (echo "SERVER is required, e.g. make $@ SERVER=llm-maker" && exit 2)
	@$(PYTHON) scripts/validate_mcp_suite.py --env-strict --server "$(SERVER)" --output "data_out/mcp_validation_suite_$(SERVER)_strict.json"

## Validate drift between non-strict and strict MCP suite artifacts
validate-mcp-suite-drift:
	@$(PYTHON) scripts/validate_mcp_suite_drift.py

## Validate MCP suite drift in JSON mode
validate-mcp-suite-drift-json:
	@$(PYTHON) scripts/validate_mcp_suite_drift.py --json

# ---------------------------------------------------------------------------
# Repository inspection agents
# ---------------------------------------------------------------------------

## Run all repository inspection agents
agents:
	$(PYTHON) scripts/run_repo_agents.py

## Preview agent results without writing data_out/agents/*
agents-dry:
	$(PYTHON) scripts/run_repo_agents.py --dry-run

## Alias for agents
ai-automation: agents

## Generate PR review eval comparison markdown report
## Override paths as needed:
## make pr-eval-report BASELINE_RESULT=/path/base.json CANDIDATE_RESULT=/path/new.json REPORT_OUTPUT=data_out/report.md
pr-eval-report:
	@$(PYTHON) data_out/run_pr_review_eval_report.py \
		$(BASELINE_RESULT) \
		$(CANDIDATE_RESULT) \
		$(REPORT_OUTPUT)
	@echo "✅ Wrote report to $(REPORT_OUTPUT)"

## Generate eval report using auto-discovered latest Foundry eval runs
## Optionally override output path:
## make pr-eval-report-latest REPORT_OUTPUT_LATEST=data_out/latest.md
pr-eval-report-latest:
	@$(PYTHON) data_out/run_pr_review_eval_report_latest.py $(REPORT_OUTPUT_LATEST)
	@echo "✅ Wrote latest-run report to $(REPORT_OUTPUT_LATEST)"

## Generate report and fail (non-zero) when gate decision is BLOCK
pr-eval-gate:
	@$(PYTHON) data_out/run_pr_review_eval_report.py \
		$(BASELINE_RESULT) \
		$(CANDIDATE_RESULT) \
		$(REPORT_OUTPUT) \
		--fail-on-block

## Auto-discover latest eval runs and fail when gate is BLOCK
pr-eval-gate-latest:
	@$(PYTHON) data_out/run_pr_review_eval_report_latest.py \
		$(REPORT_OUTPUT_LATEST) --fail-on-block

## Generate mock non-empty eval result from seed dataset and compare vs baseline
## Useful when Foundry result files are empty but pipeline validation is needed.
pr-eval-mock:
	@$(PYTHON) data_out/generate_mock_pr_review_eval_result.py
	@$(PYTHON) data_out/run_pr_review_eval_report.py \
		$(BASELINE_RESULT) \
		data_out/mock_eval_result.json \
		data_out/pr_review_eval_comparison_report_mock.md
	@echo "✅ Wrote mock comparison report to data_out/pr_review_eval_comparison_report_mock.md"

## Run a full non-blocking evaluation pass: mock validation + latest report
pr-eval-all:
	@$(MAKE) pr-eval-mock
	@$(MAKE) pr-eval-report-latest
	@echo "✅ Completed full non-blocking evaluation pass."

## Run full evaluation pass and fail if latest gate is BLOCK
pr-eval-all-strict:
	@$(MAKE) pr-eval-mock
	@$(MAKE) pr-eval-gate-latest

## List discovered eval runs with sample counts and auto-selected baseline/candidate
pr-eval-list:
	@$(PYTHON) data_out/list_pr_review_eval_runs.py

## Print concise status from latest eval comparison JSON
## Exits with code 2 when gate=BLOCK (useful for lightweight checks)
pr-eval-status:
	@$(PYTHON) data_out/print_pr_eval_status.py

## One-command triage: list runs, generate latest report, print status
pr-eval-triage-latest:
	@$(MAKE) pr-eval-list
	@$(MAKE) pr-eval-report-latest
	@$(MAKE) pr-eval-status

## Validate wiring for PR eval workflow (scripts, Make targets, VS Code tasks)
validate-eval-workflow-setup:
	@$(PYTHON) scripts/validate_eval_workflow_setup.py

## Validate PR eval workflow wiring in JSON mode (automation-friendly)
validate-eval-workflow-setup-json:
	@$(PYTHON) scripts/validate_eval_workflow_setup.py --json

## Validate generated PR eval report artifacts (.md/.json pairs)
validate-eval-artifacts:
	@$(PYTHON) scripts/validate_eval_artifacts.py

## Validate generated PR eval artifacts in JSON mode
validate-eval-artifacts-json:
	@$(PYTHON) scripts/validate_eval_artifacts.py --json

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

## Run ruff linter and black formatter check
lint:
	@set -e; \
	$(RUFF) check $(LINT_PATHS) & \
	ruff_pid=$$!; \
	$(BLACK) --check --quiet $(LINT_PATHS) & \
	black_pid=$$!; \
	wait $$ruff_pid; \
	wait $$black_pid
	@echo "✅ Lint passed."

## Run the quickest useful lint loop (Ruff only)
lint-fast:
	$(RUFF) check $(LINT_PATHS)
	@echo "✅ Fast lint passed."

## Run lint checks only for changed Python files
lint-changed:
	@files="$(CHANGED_QUALITY_PY_FILES)"; \
	if [ -z "$$files" ]; then \
		files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py' 'scripts/**/*.py' 'scripts/*.py' 'apps/**/*.py' 'apps/*.py' 'tests/**/*.py' 'tests/*.py')"; \
	fi; \
	if [ -z "$$files" ]; then \
		echo "ℹ️ No changed Python files to lint within the standard repo quality paths."; \
		exit 0; \
	fi; \
	echo "🧪 Linting changed Python files:"; \
	printf '  %s\n' $$files; \
	$(RUFF) check $$files & \
	ruff_pid=$$!; \
	$(BLACK) --check --quiet $$files & \
	black_pid=$$!; \
	wait $$ruff_pid; \
	wait $$black_pid
	@echo "✅ Changed-file lint passed."

## Auto-format code with black and isort via ruff
format:
	$(RUFF) check --fix shared/ scripts/ apps/ $(TEST_PATH) || true
	$(BLACK) shared/ scripts/ apps/aria/server.py $(TEST_PATH)
	@echo "✅ Formatting complete."

## Auto-format only changed Python files
format-changed:
	@files="$(CHANGED_QUALITY_PY_FILES)"; \
	if [ -z "$$files" ]; then \
		files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py' 'scripts/**/*.py' 'scripts/*.py' 'apps/**/*.py' 'apps/*.py' 'tests/**/*.py' 'tests/*.py')"; \
	fi; \
	if [ -z "$$files" ]; then \
		echo "ℹ️ No changed Python files to format within the standard repo quality paths."; \
		exit 0; \
	fi; \
	echo "🧪 Formatting changed Python files:"; \
	printf '  %s\n' $$files; \
	$(RUFF) check --fix $$files || true; \
	$(BLACK) $$files
	@echo "✅ Changed-file formatting complete."

## Run mypy type checks
type-check:
	$(MYPY) shared/ --ignore-missing-imports --no-error-summary || true
	@echo "✅ Type check done (warnings above are non-fatal)."

## Run mypy only for changed shared Python files
type-check-changed:
	@files="$(CHANGED_SHARED_PY_FILES)"; \
	if [ -z "$$files" ]; then \
		files="$$(git diff --name-only --diff-filter=ACMRTUXB HEAD -- 'shared/**/*.py' 'shared/*.py')"; \
	fi; \
	if [ -z "$$files" ]; then \
		echo "ℹ️ No changed shared Python files to type-check."; \
		exit 0; \
	fi; \
	echo "🧪 Type-checking changed shared Python files:"; \
	printf '  %s\n' $$files; \
	$(MYPY) $$files --ignore-missing-imports --no-error-summary || true
	@echo "✅ Changed-file type check done (warnings above are non-fatal)."

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
