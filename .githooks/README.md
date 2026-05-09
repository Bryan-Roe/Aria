# Test Automation Setup

This directory contains pre-commit hooks for automated testing.

## Installation

Enable these hooks with:

```powershell
git config core.hooksPath .githooks
```

## Available Hooks

### pre-commit (bash)
Runs fast unit tests before allowing commits. Use on Linux/Mac or Windows with Git Bash.

### pre-commit.ps1 (PowerShell)
PowerShell version for Windows users. Configure with:

```powershell
# Add to .git/config or run:
git config core.hooksPath .githooks
```

## Bypass (emergency only)

```bash
git commit --no-verify
```

## What Gets Tested

Pre-commit runs:
- Unit tests only (fast, < 30s)
- Excludes slow/integration tests
- Excludes Azure-dependent tests

For full testing:
```bash
python scripts/test_runner.py --all --coverage
```
