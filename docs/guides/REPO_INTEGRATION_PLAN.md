# Aria Repository Integration Plan

Last updated: 2026-03-13
Status: Draft for execution

## Purpose

This document defines an extensive, execution-ready integration roadmap for the Aria monorepo. It aligns runtime behavior, orchestration, documentation, and operations across the following major areas:

- Azure Functions API layer (`function_app.py`)
- Aria character web runtime (`aria_web/`, `apps/aria/`)
- Chat provider stack (`ai-projects/chat-cli/`, `shared/chat_providers.py` wrappers)
- Quantum pipeline (`ai-projects/quantum-ml/`, `scripts/quantum_autorun.py`)
- LoRA training and promotion (`ai-projects/lora-training/`, `scripts/train_and_promote.py`)
- Repository automation (`scripts/repo_automation.py`, `scripts/master_orchestrator.py`)

## Goals

1. Establish one canonical integration contract for paths, configs, and provider behavior.
2. Preserve backward compatibility for legacy paths while transitioning to canonical locations.
3. Ensure end-to-end workflows are testable with local-first dry-run and health checks.
4. Reduce operational drift between docs and actual runtime logic.
5. Provide a phased rollout with clear validation gates and rollback points.

## Non-Goals

1. Replacing all legacy wrappers immediately.
2. Redesigning model architectures or changing provider internals unrelated to integration.
3. Running paid quantum hardware jobs as part of baseline integration validation.

## Current-State Findings

1. Config location drift exists between scripts and actual config files.
2. Documentation still references mixed legacy and canonical path conventions.
3. Orchestration and monitoring are useful but split across multiple tools without a single control-plane contract.
4. Provider auto-selection behavior in code is broader than several docs currently describe.

## Canonical Integration Contract

### Path Canon

Automation configs:

- `config/master_orchestrator.yaml`
- `config/quantum/quantum_autorun.yaml`
- `config/evaluation/evaluation_autorun.yaml`

Automation status artifacts:

- `data_out/repo_automation/status.json`
- `data_out/repo_automation/processes.json`
- `data_out/master_orchestrator/status.json`

Generated outputs:

- All generated artifacts go under `data_out/**`.
- `datasets/**` remains read-only.

### Backward Compatibility

1. Read legacy root-level config/status files when canonical files are absent.
2. Continue writing compatibility status/PID files during migration where needed.
3. Keep import-path wrappers until tests and external scripts are fully migrated.

### Provider Resolution Contract

Default auto mode should reflect actual code behavior and docs:

1. LM Studio (if reachable)
2. Ollama (if reachable)
3. Azure OpenAI (if env complete)
4. OpenAI (if key present)
5. Local fallback

Explicit provider overrides still take precedence (`agi`, `quantum`, `lora`, `azure`, `openai`, `lmstudio`, `ollama`, `local`).

## Phased Execution Plan

## Phase 0: Contract Freeze (Week 1)

Deliverables:

1. Finalize this integration contract.
2. Publish path and provider contract in top-level docs.
3. Add a migration note for legacy compatibility behavior.

Validation:

1. `python scripts/repo_automation.py --status`
2. `python scripts/master_orchestrator.py --status`
3. `curl http://localhost:7071/api/ai/status`

Exit Criteria:

1. No ambiguous path guidance in core docs.

## Phase 1: Path and Config Normalization (Week 1-2)

Deliverables:

1. Normalize default config lookup to canonical `config/**` paths.
2. Keep fallback resolution for legacy root files.
3. Normalize status artifacts to canonical `data_out/**` locations.
4. Keep compatibility reads/writes for legacy status files during transition.

Validation:

1. `python scripts/quantum_autorun.py --dry-run`
2. `python scripts/repo_automation.py --status`
3. `python scripts/master_orchestrator.py --status`

Exit Criteria:

1. Canonical paths work out-of-the-box.
2. Existing workflows depending on legacy files still function.

## Phase 2: Provider and API Integration Alignment (Week 2-3)

Deliverables:

1. Reconcile docs with actual provider auto-detection behavior.
2. Add provider-resolution smoke tests for explicit and auto modes.
3. Ensure `/api/ai/status` exposes enough readiness diagnostics for troubleshooting.

Validation:

1. CLI smoke checks per provider mode.
2. Functions endpoint check for `/api/chat` and `/api/ai/status`.

Exit Criteria:

1. Provider docs and runtime behavior are consistent.

## Phase 3: Orchestration Convergence (Week 3-4)

Deliverables:

1. Clarify responsibilities:

- `repo_automation.py`: process lifecycle and health loops
- `master_orchestrator.py`: workflow dependencies and schedules

1. Implement robust schedule matching for scheduled workflows.
1. Standardize workflow result metadata and logging layout.

Validation:

1. Manual workflow trigger verification.
2. Scheduled trigger verification in daemon mode.

Exit Criteria:

1. Scheduled workflows execute reliably with traceable logs.

## Phase 4: Integration Test Gates (Week 4-5)

Deliverables:

1. Add end-to-end smoke matrix:

- Aria server state endpoint
- Functions status endpoint
- Chat request/response
- Training dry-run
- Quantum dry-run

1. Wire matrix into CI required checks.

Validation:

1. `python scripts/test_runner.py --unit`
2. `pytest -m "not slow and not azure" tests/`
3. CI green for integration matrix.

Exit Criteria:

1. Merge gates catch integration drift before release.

## Phase 5: Observability and Ops Hardening (Week 5-7)

Deliverables:

1. Unified health severity model across dashboard and checks.
2. Single runbook for startup, recovery, and rollback.
3. Systemd and cron profiles validated for Linux deployment.

Validation:

1. `python scripts/system_health_check.py`
2. `python scripts/status_dashboard.py --watch`

Exit Criteria:

1. Fresh environment reaches healthy status via documented runbook.

## Workstreams

### Workstream A: Config and Path Governance

1. Build a shared config-path resolver utility.
2. Adopt it across orchestrators and CI scripts.
3. Add tests for fallback precedence.

### Workstream B: Runtime Integration

1. Normalize API endpoint assumptions and response contracts.
2. Keep chat/tts/status endpoint behavior stable.
3. Verify LoRA adapter readiness checks remain intact.

### Workstream C: Data and Artifact Lineage

1. Standardize `status.json` schema fields.
2. Attach run IDs and source config references.
3. Ensure outputs are traceable from training to deployment.

### Workstream D: Documentation and Enablement

1. Update root README and component READMEs to canonical paths.
2. Keep a migration section with legacy compatibility notes.
3. Provide one quick-start path for local-first integration validation.

## Risk Register

1. Risk: Legacy scripts fail after path normalization.
Mitigation: Keep fallback lookup and compatibility file writes.

2. Risk: Docs and runtime diverge again over time.
Mitigation: CI check for key path strings and provider-order assertions.

3. Risk: Scheduler changes cause unintentional workflow execution.
Mitigation: Add dry-run schedule simulation before enabling live schedules.

4. Risk: Optional dependencies fail in clean environments.
Mitigation: Keep dependency checks explicit and fail with actionable errors.

## Rollout and Rollback

Rollout:

1. Merge Phase 1 with compatibility mode enabled.
2. Observe 1-2 release cycles.
3. Promote canonical paths in docs and scripts by default.

Rollback:

1. Revert path resolver changes.
2. Continue using legacy root-level configs/status files.
3. Keep compatibility wrappers unchanged.

## Definition of Done

1. Canonical config and status paths are used by default.
2. Legacy compatibility remains functional during migration.
3. Provider behavior is documented exactly as implemented.
4. Integration smoke tests run in CI and locally.
5. Runbook enables reproducible startup and diagnosis.

## Immediate Next Actions

1. Keep `scripts/config_paths.py` as the single resolver and require `tests/test_config_paths.py` to pass in path-related changes.
2. Standardize `status.json` schema across `repo_automation`, `master_orchestrator`, and `ci_orchestrator` (include `run_id`, `config_path`, and normalized timestamps).
3. Add schedule simulation tests for cron expressions in `master_orchestrator.py` to guard against accidental trigger regressions.
4. Publish a short runbook section that links integration smoke, CI smoke, and health dashboard commands as one operational flow.
