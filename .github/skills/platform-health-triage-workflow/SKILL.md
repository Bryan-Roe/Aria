---
name: platform-health-triage-workflow
description: 'Triage platform health across API readiness, orchestrator status files, resource usage, and provider/DB dependencies. Use when services feel degraded, dashboards disagree, or you need a fast root-cause path for system incidents.'
argument-hint: 'Describe the outage or degradation signal (endpoint, script, dashboard metric, or failing workflow).'
---

# Platform Health Triage Workflow

## What This Skill Produces

Use this skill to diagnose system health issues quickly and consistently. The expected output is:
- a prioritized incident picture (what is broken vs what is healthy)
- a layer-by-layer root-cause hypothesis with evidence
- immediate mitigation options and focused follow-up checks
- a concise summary of status, impact, and next actions

## When to Use

Use this skill when you need to:
- investigate "system seems down/slow" reports
- debug provider-readiness or dependency health issues
- reconcile conflicting dashboard vs runtime status
- diagnose orchestrator failures from status artifacts
- identify resource saturation (CPU/memory/disk/GPU) impacts

Common trigger phrases:
- "check platform health"
- "why is the system unstable"
- "dashboard status is wrong"
- "API is up but workflows fail"
- "orchestrator jobs are stuck"
- "triage this production-like incident"

## Procedure

1. Start at the health contract
   - Check `/api/ai/status` as the top-level runtime health signal.
   - Capture provider, environment-readiness, SQL pool, Cosmos, and related diagnostics.

2. Correlate with orchestrator artifacts
   - Inspect `data_out/<orchestrator>/status.json` files for job-level state.
   - For autonomous training, inspect `data_out/autonomous_training_status.json` and its trend context.
   - Prefer status files over ad hoc process introspection when they disagree.

3. Check resource pressure
   - Use resource snapshots to detect CPU, memory, disk, or GPU saturation.
   - Validate whether high resource load aligns with incident timing.

4. Isolate the failure domain
   - API layer: endpoint or contract issue.
   - Dependency layer: provider credentials, DB connectivity, Cosmos readiness.
   - Orchestration layer: scheduler/job failures, stuck states, partial outputs.
   - Capacity layer: resource starvation causing cascading errors.

5. Propose least-risk mitigation first
   - Prefer reversible mitigations (restart one component, reduce load, isolate failing workflow).
   - Avoid broad multi-component restarts unless evidence points to systemic corruption.

6. Verify recovery signals
   - Re-check `/api/ai/status` and the impacted status files.
   - Confirm key workflows resume and metrics stabilize.

7. Close with an incident summary
   - State root cause confidence level, mitigation applied, residual risk, and follow-up tasks.

## Quality Checks

Before finishing, confirm that:
- health conclusions are grounded in endpoint + status-file evidence
- impacted components are clearly scoped
- mitigation steps are low-risk and testable
- recovery is validated, not assumed
- follow-up actions are explicit for unresolved risk
