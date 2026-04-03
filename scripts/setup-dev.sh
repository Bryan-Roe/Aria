#!/usr/bin/env bash
set -euo pipefail

echo "[setup-dev] Starting developer environment setup..."

# Install Python dev requirements if present
if [ -f requirements-dev.txt ]; then
  echo "[setup-dev] Installing Python dev requirements from requirements-dev.txt..."
  pip install --upgrade pip
  pip install -r requirements-dev.txt
else
  echo "[setup-dev] requirements-dev.txt not found — ensuring pre-commit is available..."
  pip install --upgrade pip
  pip install pre-commit
fi

# Install pre-commit hooks
if command -v pre-commit >/dev/null 2>&1; then
  echo "[setup-dev] Installing pre-commit hooks..."
  pre-commit install || true
  echo "[setup-dev] Running pre-commit on all files (may show warnings)..."
  pre-commit run --all-files || true
else
  echo "[setup-dev] pre-commit not found after install — please install it manually: pip install pre-commit"
fi

echo "[setup-dev] Developer environment setup complete."
echo "To activate a virtualenv, create one with: python3 -m venv .venv && source .venv/bin/activate"

exit 0
