# Git Hooks — Test Automation

This directory contains Git hooks that run automated checks before commits, helping
catch issues early and keep the `main` branch healthy.

## Contents

| File | Platform | Description |
| ----------------- | ------------------------------ | ------------------------------------------- |
| `pre-commit` | Linux / macOS / Git Bash (Win) | Bash hook that runs fast unit tests. |
| `pre-commit.ps1` | Windows (PowerShell) | PowerShell equivalent for native Windows. |

## Installation

Point Git at this directory so it picks up the hooks (run from the repository root):

```bash
git config core.hooksPath .githooks
```

On Linux/macOS, ensure the bash hook is executable:

```bash
chmod +x .githooks/pre-commit
```

> **Note:** `core.hooksPath` is configured per clone. Each contributor must run the
> command above once after cloning. Consider adding it to your project's onboarding
> docs or a `make setup` / bootstrap script.

### Verify the installation

```bash
git config --get core.hooksPath   # should print: .githooks
```

## Available Hooks

### `pre-commit` (Bash)

Runs fast unit tests before a commit is finalized. Intended for Linux, macOS, or
Windows users running Git Bash / WSL.

### `pre-commit.ps1` (PowerShell)

PowerShell port of the bash hook for native Windows environments. It is invoked
automatically when `core.hooksPath` is set, provided PowerShell is available on
the `PATH`.

## What Gets Tested

The pre-commit hook is intentionally fast so it doesn't disrupt your workflow:

- ✅ Unit tests only (target runtime **< 30s**)
- ⏭️ Skips slow / integration tests
- ⏭️ Skips Azure-dependent tests (no cloud credentials required)

For a full test run (CI parity), use:

```bash
python scripts/test_runner.py --all --coverage
```

## Bypassing the Hook (emergency only)

If you absolutely must commit without running the hook (e.g., committing docs while
tests are temporarily broken on `main`), use:

```bash
git commit --no-verify
```

> ⚠�� Use sparingly. Skipping the hook can let regressions into the codebase. Prefer
> fixing the failing test or marking it appropriately.

## Troubleshooting

- **Hook does not run**
  - Confirm `git config --get core.hooksPath` returns `.githooks`.
  - On Linux/macOS, confirm the file is executable (`ls -l .githooks/pre-commit`).
- **`pre-commit.ps1` is blocked by execution policy (Windows)**
  - Run PowerShell as your user and execute:
    ```powershell
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
    ```
- **Tests are too slow**
  - Ensure only unit tests are selected; integration/Azure suites should be excluded.
  - Profile with `pytest --durations=10` to identify slow tests.
- **Need to debug what the hook runs**
  - Inspect [`pre-commit`](./pre-commit) or [`pre-commit.ps1`](./pre-commit.ps1)
    directly — they are plain scripts.

## Contributing

When adding or modifying a hook:

1. Keep the total runtime under **30 seconds** for the common case.
2. Mirror behavior between the Bash and PowerShell versions.
3. Exit with a non-zero status code on failure so Git aborts the commit.
4. Print actionable error messages (what failed, how to reproduce, how to fix).
