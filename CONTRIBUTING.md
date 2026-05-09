# Contributing to Aria

Thank you for your interest in contributing to **Aria** — an interactive AI character platform with autonomous learning, quantum ML integration, and multi-provider chat backends. This guide describes how to set up your environment, run tests, and submit high-quality contributions.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Development Environment](#development-environment)
  - [Local Setup](#local-setup)
  - [Codespaces / Devcontainer](#codespaces--devcontainer)
  - [Project-Specific Virtualenvs](#project-specific-virtualenvs)
- [Running Tests](#running-tests)
  - [Full Suite](#full-suite)
  - [Targeted Runs](#targeted-runs)
  - [Test Watcher](#test-watcher)
- [Code Style & Quality](#code-style--quality)
- [Commit & Branch Conventions](#commit--branch-conventions)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [Security](#security)
- [License](#license)

---

## Code of Conduct

Participation in this project is governed by our community standards. Be respectful, constructive, and inclusive. Please report unacceptable behavior to the maintainers via a private channel (see [Security](#security)).

## Ways to Contribute

- 🐛 **Bug reports** — open an issue with reproduction steps, expected vs. actual behavior, and environment details.
- ✨ **Feature requests** — describe the use case and proposed API/UX before opening a PR for large changes.
- 📖 **Documentation** — improvements to READMEs, inline docstrings, and examples are always welcome.
- 🧪 **Tests** — adding coverage for existing untested paths is a great first contribution.
- 🔧 **Code** — bug fixes, refactors, performance improvements, and new features.

> **Tip:** For non-trivial changes, open a discussion or issue first to align on design.

---

## Development Environment

### Local Setup

Requirements:

- Python **3.10+** (3.11 recommended)
- `git`
- (Optional) [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) for running `function_app.py`

Create an isolated virtualenv and install development dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Codespaces / Devcontainer

This repo includes a [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json) that provisions a Python dev container and installs `requirements-dev.txt` on first start. Open in GitHub Codespaces or VS Code Dev Containers for a zero-config setup.

### Project-Specific Virtualenvs

Aria is composed of three isolated sub-projects, each with its own virtualenv and dependencies:

| Project | Path | Purpose |
| --- | --- | --- |
| Quantum ML | `ai-projects/quantum-ml/` | MCP server, dashboard, quantum ML pipelines |
| Chat CLI | `ai-projects/chat-cli/` | Multi-provider chat CLI |
| Phi-Silica fine-tuning | `AI/microsoft_phi-silica-3.6_v1/` | Phi-3.5 LoRA fine-tuning |

When working in any of these, create a separate virtualenv inside that directory and install its `requirements.txt`. See each project's README for details.

---

## Running Tests

### Full Suite

Run the complete test suite (fail-fast):

```bash
python3 -m pytest tests -q --maxfail=1
```

For full output with coverage (if `pytest-cov` is installed):

```bash
python3 -m pytest tests --cov=. --cov-report=term-missing
```

### Targeted Runs

Run a single file or test:

```bash
python3 -m pytest tests/test_function_app.py -q
python3 -m pytest tests/test_function_app.py::test_status_endpoint -q
```

Filter by keyword:

```bash
python3 -m pytest -k "chat and not slow" -q
```

### Test Watcher

A lightweight file watcher at [`scripts/test_watcher.py`](scripts/test_watcher.py) re-runs the suite on file changes:

```bash
python3 scripts/test_watcher.py
```

See [`NEXT_STEPS.md`](docs/NEXT_STEPS.md) for troubleshooting notes, or check the [open issues](https://github.com/Bryan-Roe/Aria/issues).

---

## Code Style & Quality

- **Formatting:** [`black`](https://black.readthedocs.io/) (line length 100) and [`isort`](https://pycqa.github.io/isort/) for imports.
- **Linting:** [`ruff`](https://docs.astral.sh/ruff/) for fast static analysis.
- **Typing:** Add type hints to all new public functions; `mypy` is run in CI where configured.
- **Docstrings:** Use Google-style docstrings for modules, classes, and public functions.

Run all checks locally before pushing:

```bash
ruff check .
black --check .
isort --check-only .
```

Auto-fix formatting:

```bash
ruff check --fix .
black .
isort .
```

---

## Commit & Branch Conventions

- **Branch names:** `feature/<short-description>`, `fix/<short-description>`, `docs/<short-description>`.
- **Commits:** Follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add auto-execute action parser`
  - `fix(chat): handle SSE disconnect gracefully`
  - `docs: clarify devcontainer setup`
  - `test: cover quantum job submission errors`
  - `refactor:`, `perf:`, `chore:`, `ci:` as appropriate.
- Keep commits focused; avoid mixing unrelated changes.

---

## Pull Request Process

1. **Fork** the repo and create a topic branch from `main`.
2. **Make your changes** with tests and documentation updates.
3. **Run the full test suite and linters locally** — they must pass.
4. **Update the changelog / docs** if your change is user-visible.
5. **Open a Pull Request** against `main`:
   - Fill out the PR template completely.
   - Link related issues (`Fixes #123`).
   - Provide context: what, why, and how to test.
   - Include screenshots/recordings for UI changes (e.g., `apps/aria/`).
6. **CI must pass.** The [`.github/workflows/pr-tests.yml`](.github/workflows/pr-tests.yml) workflow runs `pytest` on every PR targeting `main`.
7. **Address review feedback** by pushing follow-up commits (avoid force-pushing during review unless asked).
8. A maintainer will merge once approved.

> **Note:** Large or breaking changes should be discussed in an issue or draft PR first.

---

## Reporting Issues

When opening an issue, please include:

- A clear, descriptive title.
- Steps to reproduce (minimal example preferred).
- Expected vs. actual behavior.
- Environment: OS, Python version, relevant package versions, provider (Azure OpenAI / OpenAI / LMStudio / local).
- Logs or stack traces (redact secrets).

## Security

**Do not open public issues for security vulnerabilities.** Instead, follow the process described in [`SECURITY.md`](SECURITY.md) (or contact the maintainers privately). We aim to acknowledge reports within a few business days.

## License

By contributing, you agree that your contributions will be licensed under the same license as this project. See [`LICENSE`](LICENSE) for details.

---

Thanks again for helping make Aria better! 💙
