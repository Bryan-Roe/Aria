# Changelog

All notable changes to **Aria** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
uses [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

### Added
- `LICENSE` file (MIT) added to repo root.
- `CHANGELOG.md` (this file) added to track changes going forward.
- `[tool.black]`, `[tool.isort]`, `[tool.pytest.ini_options]` sections in `pyproject.toml`.
- `ruff` blocking check added to the `code-quality` CI workflow.
- `pytest-cov`, `black`, `isort`, `pre-commit` added to `requirements-dev.txt`.
- `.gitattributes` to enforce LF line endings across the repository.

### Changed
- `pyproject.toml` dev dependency `pytest>=7.0,<8.0` updated to `pytest>=8.0.0` to match
  `requirements.txt` and avoid resolution conflicts.
- `requirements-dev.txt` updated to include `pytest-cov`, `black`, `isort`, `pre-commit`.
- `SECURITY.md` replaced with a complete security policy (SLA table fixed, boilerplate removed).
- `README.md` trailing stray code block (pseudocode plan) removed.
- `CONTRIBUTING.md` broken `NEXT_STEPS.md` link updated to point to `docs/NEXT_STEPS.md`.
- `pytest.ini` extended with `filterwarnings` to suppress noisy deprecation warnings.

### Fixed
- `pr-tests.yml` watcher job `if:` condition used `${...}` instead of `${{...}}` — corrected
  to valid GitHub Actions expression syntax.

---

## [0.1.0] — Initial public release

### Added
- Animated 3D Aria character stage (`apps/aria/`).
- Multi-provider chat CLI supporting LM Studio, Ollama, Azure OpenAI, OpenAI, and local echo.
- Azure Functions API layer (`function_app.py`) with `/api/chat`, `/api/tts`, `/api/ai/status`
  and quantum endpoints.
- LoRA fine-tuning workspace (`AI/`) for Phi / TinyLlama adapters.
- Hybrid quantum-classical ML platform (`ai-projects/quantum-ml/`).
- Autonomous training orchestrator (`scripts/autonomous_training_orchestrator.py`).
- Gradio Hugging Face Space entry point (`app.py`).
- Comprehensive CI/CD workflow suite (`.github/workflows/`).
- Shared infrastructure modules (`shared/`) for providers, DB, telemetry, and Cosmos.

[Unreleased]: https://github.com/Bryan-Roe/Aria/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Bryan-Roe/Aria/releases/tag/v0.1.0
