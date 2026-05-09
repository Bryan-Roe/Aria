---
name: release-readiness-workflow
description: 'Run a pre-release readiness pass for Aria changes using health checks, targeted tests, orchestrator safeguards, and deployment-risk review. Use when preparing PRs, merges, or deployments and you need a clear go/no-go decision.'
argument-hint: 'Describe the change scope, impacted components, and target release path (local, staging, or production-like).'
---

# Release Readiness Workflow

## What This Skill Produces

Use this skill to produce an evidence-based release decision. The expected output is:
- a scoped list of affected components and risks
- verification results for APIs, providers, orchestrators, and tests
- explicit go/no-go recommendation with blockers and mitigations
- a concise release summary that can be pasted into PR or deployment notes

## When to Use

Use this skill when you need to:
- prepare a PR for merge with confidence checks
- run a pre-deployment readiness gate
- validate cross-component changes touching APIs + training + chat
- confirm no regressions in safety-critical or cost-gated paths

Common trigger phrases:
- "is this release-ready"
- "run release checks"
- "pre-merge readiness"
- "go/no-go for deployment"
- "final validation before merge"

## Procedure

1. Scope the release surface
   - Identify changed files, affected subsystems, and user-facing behaviors.
   - Separate high-risk paths (provider selection, orchestration, static routing, cost-gated quantum) from low-risk edits.

2. Run health and dependency checks first
   - Check `/api/ai/status` for provider readiness, environment signals, SQL/Cosmos health, and runtime diagnostics.
   - Confirm optional dependencies degrade gracefully instead of hard-failing.

3. Validate core contracts
   - API contracts: ensure endpoints return expected status/payload shapes.
   - Streaming contracts: ensure SSE behavior remains parseable and includes completion sentinel when applicable.
   - Static routes: ensure route-to-file mapping and MIME/cache behavior are correct.

4. Validate automation and safety controls
   - Confirm orchestrator/status-file conventions are preserved under `data_out/<orchestrator>/status.json`.
   - Confirm dataset immutability (`datasets/` stays read-only).
   - For quantum paths, keep simulator-first progression and cost-gate requirements intact.

5. Run targeted tests, then broader checks
   - Start with focused tests for changed behavior.
   - Expand to unit or integration suites as needed for confidence.
   - Prefer failing-fast checks before long-running suites.

6. Review security and configuration hygiene
   - Confirm no secrets were introduced in source files.
   - Confirm environment-variable expectations are documented and unchanged or intentionally updated.
   - Confirm no accidental weakening of guardrails (timeouts, retries, thresholds).

7. Decide go/no-go with evidence
   - GO if critical checks pass and residual risk is acceptable.
   - NO-GO if contract breaks, safety gates regress, or unresolved blockers remain.
   - Provide exact blocker list and next remediation steps.

## Quality Checks

Before finishing, confirm that:
- readiness includes both runtime health and test evidence
- high-risk subsystems were explicitly checked
- safety/cost gates were not bypassed
- results are summarized as clear go/no-go with rationale
- blockers include actionable next steps
