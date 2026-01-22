---
name: qai
description: Operate and troubleshoot the QAI/Aria workspace: run automation scripts, orchestrators, dashboards, provider detection, and status/health checks. Use when asked to manage Aria, quantum, chat, training, or repo automation tasks.
---

# QAI Operations Skill

Use this skill for any work inside the Aria/QAI repo (automation, training, quantum, chat, dashboards).

## Quick facts
- Three isolated Python projects (`quantum-ai/`, `talk-to-ai/`, `AI/microsoft_phi-silica-3.6_v1/`) + `function_app.py` glue; run commands from repo root unless noted.
- Dataset discipline: read-only `datasets/`; writes go under `data_out/`.
- Provider detection (via `shared/chat_providers.py`): LMStudio → Azure OpenAI (needs 4 vars) → OpenAI → LoRA adapter → local echo.

## Common commands
- Repo automation (daemonized): `./scripts/automation/start_repo_automation.sh full|aria|training|status|stop|components <list>`; logs `data_out/repo_automation/automation.log`.
- Status API: `curl http://localhost:7071/api/ai/status | jq` (after `func host start` if using Functions locally).
- Aria web: `cd aria_web && python server.py` (http://localhost:8080; auto-execute UI at /auto-execute.html).
- Chat CLI: `cd talk-to-ai && python src/chat_cli.py --provider local --once "Hello"`.
- Orchestrator dry-runs: `python scripts/training/autotrain.py --dry-run`; `python scripts/evaluation/quantum_autorun.py --dry-run`; `python scripts/evaluation/evaluation_autorun.py --dry-run`.
- Tests/validation: `python scripts/fast_validate.py`; `python scripts/test_runner.py --unit` (respect virtualenvs if configured per project).

## Environment checklist
- Copy/edit `local.settings.json.example` to `local.settings.json` (and `.env` if used).
- Key vars: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`; `OPENAI_API_KEY`; `LMSTUDIO_BASE_URL` (optional); `QAI_ENABLE_LOCAL_TTS=true` for local TTS; `QAI_SQL_URL` or `QAI_DB_CONN`; `QAI_ENABLE_COSMOS=true` if Cosmos needed.
- Azure Functions: ensure Functions Core Tools present; run from repo root.

## Dashboards & UIs
- Automation/training dashboards under `dashboard/` (HTML files) and `scripts/status_dashboard.py --watch`.
- Shared nav/components in `shared/`; automation hub pages in `src/web/dashboard/dashboard/`.

## References
- `.github/copilot-instructions.md` for full architecture/command details.
- `docs/README.md` plus quick refs under `docs/quickref/`.
- Commands cheat sheet: `skills/public/qai/references/commands.md`.
