# Autonomous Dev Bot (Aria Extension)

This module implements an autonomous repository upgrade system designed to continuously improve code quality, maintainability, security, and performance through iterative analysis and safe automated changes.

## Architecture Overview

The system is composed of modular components:

- **Orchestrator**: Controls the upgrade loop and coordinates all modules
- **Analyzer**: Scans repository structure, dependencies, and code quality
- **Planner**: Converts findings into safe upgrade plans
- **Executor**: Applies code changes as minimal diffs
- **Validator**: Runs lint, build, and test checks
- **Risk Manager**: Evaluates safety and prevents destructive changes
- **Commit System**: Handles versioned, atomic commits

## Execution Flow

1. Analyze repository state
2. Generate improvement plan
3. Execute safe changes
4. Validate results
5. Commit changes
6. Repeat cycle

## Design Principles

- Incremental improvements over large rewrites
- Backward compatibility preserved
- Safety-first automation
- Transparent change tracking
- Continuous improvement loop

## Usage

The deterministic loop lives in the `aria_bot` Python package and exposes a
single-cycle CLI:

```bash
# Dry-run (default): analyze + plan, but never touch disk.
python -m aria_bot

# Apply safe fixes to disk (no git commit).
python -m aria_bot --apply

# Apply and create a local git commit (never pushes).
python -m aria_bot --apply --commit
```

Each cycle writes a machine-readable summary to
`data_out/aria_bot/status.json` per the repo's status-file convention.

## Safety Guarantees

These properties are enforced by `aria_bot/risk_manager.py` and cannot be
disabled from configuration:

- **Dry-run by default.** `--apply` is required to write any file.
- **Never pushes.** `commit_system.py` only stages and commits locally.
- **Protected paths** (`datasets/`, `.git/`, `.github/agents/`,
  `local.settings.json`, `data_out/`, `secrets/`, `AI/`) are never modified.
- **Whitelisted transforms only.** v1 supports trailing-whitespace cleanup
  and missing-final-newline fixes — both pure-text and idempotent.
- **No deletions, no renames, no symlink follows.**
- **Per-cycle caps** on plans, file size, and per-plan delta bytes.

Configuration lives in `config/aria_bot.yaml`. Narrowing the operating
envelope (e.g., adding more protected prefixes) is honored; attempts to
widen it past the hard-coded defaults are ignored.

## Adding a New Transform

1. Add a `Finding` kind in `aria_bot/analyzer.py` (with a detector).
2. Add the matching transform function in `aria_bot/executor.py` and
   register it in `_TRANSFORMS`.
3. Add tests under `tests/test_aria_bot.py` covering both detection and
   the idempotency of the transform.

## Future Extensions

- Multi-repo orchestration
- Automated test generation
- Performance benchmarking history
- AI-driven architecture refactoring (would live alongside, not inside,
  this deterministic loop — see `scripts/autonomous_code_agent.py`)
