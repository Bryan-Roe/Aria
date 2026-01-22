# QAI Command Cheat Sheet

Run from repo root unless specified.

## Automation
- Full automation (daemon): `./scripts/automation/start_repo_automation.sh full`
- Aria only: `./scripts/automation/start_repo_automation.sh aria`
- Training only: `./scripts/automation/start_repo_automation.sh training`
- Custom components: `./scripts/automation/start_repo_automation.sh components aria,training,quantum`
- Status: `./scripts/automation/start_repo_automation.sh status`
- Stop: `./scripts/automation/start_repo_automation.sh stop`
- Logs: `tail -f data_out/repo_automation/automation.log`

## Functions & APIs
- Start Functions host: `func host start`
- Health check: `curl http://localhost:7071/api/ai/status | jq`
- Quantum endpoints proxied via Function App `/api/quantum/*`

## Aria Web / Chat
- Aria web server: `cd aria_web && python server.py` (http://localhost:8080; /auto-execute.html for planner)
- Chat web UI: `cd chat-web && python -m http.server 8001` (or serve via preferred static server)
- Chat CLI: `cd talk-to-ai && python src/chat_cli.py --provider local --once "Hello"`

## Orchestrators (dry-runs first)
- LoRA training: `python scripts/training/autotrain.py --dry-run`
- Quantum eval: `python scripts/evaluation/quantum_autorun.py --dry-run`
- Evaluation: `python scripts/evaluation/evaluation_autorun.py --dry-run`
- Autonomous training cycles: `python scripts/training/autonomous_training_orchestrator.py --cycles 1 --dry-run`

## Monitoring
- Status dashboard: `python scripts/status_dashboard.py --watch`
- Resource snapshot: `python scripts/resource_monitor.py --snapshot`
- Training analytics: `python scripts/training_analytics.py`

## Data & DB
- SQL env vars: `QAI_SQL_URL` (preferred) or `QAI_DB_CONN`; optional `QAI_SQL_SLOW_MS`, `QAI_ENABLE_QUERY_TRACKING=true`
- Migrations: `python database/migrate.py`
- Query metrics table migration: `python database/migrate.py --ensure-query-metrics`

## Testing & Validation
- Fast validation: `python scripts/fast_validate.py`
- Unit tests: `python scripts/test_runner.py --unit`
- Full tests: `python scripts/test_runner.py --all` (heavier)
