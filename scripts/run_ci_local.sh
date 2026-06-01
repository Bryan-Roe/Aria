#!/usr/bin/env bash
# =============================================================================
# run_ci_local.sh — Run GitHub Actions CI steps locally (no Docker required)
# =============================================================================
# Mirrors the jobs from .github/workflows/ci.yml:
#   1. Lint (ruff + black)
#   2. Type check (mypy) — advisory
#   3. Unit tests (pytest)
#
# Usage:
#   bash scripts/run_ci_local.sh          # Run all jobs
#   bash scripts/run_ci_local.sh lint     # Lint only
#   bash scripts/run_ci_local.sh typecheck # Type check only
#   bash scripts/run_ci_local.sh test     # Unit tests only
#   bash scripts/run_ci_local.sh install  # Install deps only
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LINT_PATHS=("shared" "scripts" "tests" "apps/aria/server.py")

collect_python_paths() {
    mapfile -t LINT_FILES < <(find shared scripts tests -name '*.py' -print | sort)
    LINT_FILES+=("apps/aria/server.py")
}
PASS=0
FAIL=0
ADVISORY_FAIL=0

banner() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

pass() {
    echo -e "  ${GREEN}✓ $1${NC}"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "  ${RED}✗ $1${NC}"
    FAIL=$((FAIL + 1))
}

advisory_fail() {
    echo -e "  ${YELLOW}⚠ $1 (advisory — not blocking)${NC}"
    ADVISORY_FAIL=$((ADVISORY_FAIL + 1))
}

# Use repo venv if available, otherwise system python
if [[ -f "$REPO_ROOT/.venv/bin/python" ]]; then
    PYTHON="$REPO_ROOT/.venv/bin/python"
    PIP="$PYTHON -m pip"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
    PIP="python3 -m pip"
else
    echo -e "${RED}No Python found. Install Python 3.11+ first.${NC}"
    exit 1
fi

echo -e "${BLUE}Using Python: $($PYTHON --version) at $PYTHON${NC}"

# ─────────────────────────────────────────────────────────────────────────────
# Job: Install dependencies
# ─────────────────────────────────────────────────────────────────────────────
do_install() {
    banner "Checking CI tool dependencies"

    # Check which CI tools are missing and install only those
    MISSING=()
    $PYTHON -c "import ruff" 2>/dev/null   || MISSING+=("ruff>=0.5,<1.0")
    $PYTHON -c "import black" 2>/dev/null  || MISSING+=("black>=24.0,<26.0")
    $PYTHON -c "import mypy" 2>/dev/null   || MISSING+=("mypy>=1.10,<2.0")
    $PYTHON -c "import pytest" 2>/dev/null || MISSING+=("pytest")
    $PYTHON -c "import pytest_cov" 2>/dev/null || MISSING+=("pytest-cov")

    if [[ ${#MISSING[@]} -gt 0 ]]; then
        echo "  Installing missing CI tools: ${MISSING[*]}"
        $PIP install --quiet "${MISSING[@]}" 2>&1 | tail -5
    fi

    pass "CI tools ready"
}

# ─────────────────────────────────────────────────────────────────────────────
# Job 1: Lint (ruff + black)
# ─────────────────────────────────────────────────────────────────────────────
do_lint() {
    banner "Job 1/3: Lint (ruff + black)"

    collect_python_paths

    echo "  Running ruff check..."
    if $PYTHON -m ruff check "${LINT_FILES[@]}" 2>&1; then
        pass "ruff check passed"
    else
        fail "ruff check failed"
    fi

    echo "  Running black --check..."
    if $PYTHON -m black --check --quiet "${LINT_FILES[@]}" 2>&1; then
        pass "black format check passed"
    else
        fail "black format check failed (run: black ${LINT_FILES[*]})"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Job 2: Type check (mypy) — advisory
# ─────────────────────────────────────────────────────────────────────────────
do_typecheck() {
    banner "Job 2/3: Type check (mypy) — advisory"

    echo "  Running mypy on shared/..."
    if $PYTHON -m mypy shared/ --ignore-missing-imports --show-error-codes 2>&1; then
        pass "mypy passed"
    else
        advisory_fail "mypy has type errors (advisory, not blocking)"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Job 3: Unit tests (pytest)
# ─────────────────────────────────────────────────────────────────────────────
do_test() {
    banner "Job 3/3: Unit tests (pytest)"

    mkdir -p data_out

    echo "  Running pytest..."
    if $PYTHON -m pytest tests/ \
        -q --tb=short \
        -m "not slow and not azure and not integration" \
        --ignore=tests/test_ui_playwright.py \
        --ignore=tests/test_ui_pyppeteer.py \
        --ignore=tests/test_ui_selenium.py \
        --maxfail=5 \
        --durations=10 \
        --junitxml=data_out/junit-local.xml \
        --cov=shared --cov=scripts \
        --cov-report=term-missing \
        --cov-report=xml:data_out/coverage-local.xml 2>&1; then
        pass "Unit tests passed"
    else
        fail "Unit tests failed"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
summary() {
    banner "CI Summary"
    echo -e "  ${GREEN}Passed: $PASS${NC}"
    if [[ $ADVISORY_FAIL -gt 0 ]]; then
        echo -e "  ${YELLOW}Advisory failures: $ADVISORY_FAIL${NC}"
    fi
    if [[ $FAIL -gt 0 ]]; then
        echo -e "  ${RED}Failed: $FAIL${NC}"
        echo ""
        echo -e "${RED}CI would FAIL${NC}"
        exit 1
    else
        echo ""
        echo -e "${GREEN}CI would PASS${NC}"
    fi
}

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
JOB="${1:-all}"

case "$JOB" in
    install)
        do_install
        ;;
    lint)
        do_install
        do_lint
        summary
        ;;
    typecheck|type-check|mypy)
        do_install
        do_typecheck
        summary
        ;;
    test|tests|pytest)
        do_install
        do_test
        summary
        ;;
    all)
        do_install
        do_lint
        do_typecheck
        do_test
        summary
        ;;
    *)
        echo "Usage: $0 {all|lint|typecheck|test|install}"
        exit 1
        ;;
esac
