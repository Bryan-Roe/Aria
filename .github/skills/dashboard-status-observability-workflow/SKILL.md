---
name: dashboard-status-observability-workflow
description: "Build and debug dashboard views that consume status artifacts and health endpoints consistently across orchestrators. Use when dashboard metrics disagree with runtime, status schemas drift, polling logic is unstable, or system-health panes misreport provider/resource state."
argument-hint: "Describe which dashboard view is wrong, which status file/endpoint it reads, and the observed mismatch."
---

# Dashboard Status Observability Workflow

## What This Skill Produces

Use this skill to keep dashboard observability trustworthy. The expected result is:

- dashboard metrics that map cleanly to status-file and health-endpoint sources
- stable polling and refresh behavior
- clear handling of missing/stale/partial status data
- consistent cross-surface system health reporting

## When to Use

Use this skill when you need to:

- debug `apps/dashboard` metrics or panels
- reconcile dashboard values with `data_out/<orchestrator>/status.json`
- fix stale refresh/polling behavior
- align system health cards with `/api/ai/status`
- handle autonomous training special status schema correctly

Common trigger phrases:

- "dashboard numbers are wrong"
- "status file says X but dashboard shows Y"
- "health panel misreports provider status"
- "polling stops or flickers"
- "autonomous metrics not rendering"
- "resource usage panel is stale"

## Procedure

1. Identify source-of-truth mapping
   - For each panel, list exact source (status file vs health endpoint).
   - Avoid implicit mixing of data from unmatched timestamps.

2. Validate schema assumptions
   - Standard orchestrator schema: `{total_jobs,succeeded,failed,running,last_updated,avg_duration}`.
   - Autonomous schema: `{cycles_completed,best_accuracy,performance_history,dataset_inventory}`.

3. Check polling behavior
   - Ensure interval cadence is stable and not duplicated by multiple timers.
   - Handle request failures with retries/backoff and visible stale-data indicators.

4. Align health endpoint display
   - `/api/ai/status` fields should map directly to UI labels.
   - Distinguish unavailable vs disabled vs unhealthy states clearly.

5. Handle missing/stale data explicitly
   - Don’t crash on absent files/keys.
   - Show “no data yet” vs “error loading” distinctly.

6. Fix minimal layer
   - Source mapping bug -> selector/adapter fix.
   - Schema drift bug -> parser normalization.
   - Polling bug -> timer/state lifecycle fix.

7. Re-verify panel-by-panel
   - Compare each rendered metric against raw source values.

## Quality Checks

Before finishing, confirm that:

- every dashboard metric maps to a clear source of truth
- schema parsing handles both standard and autonomous status shapes
- polling is single-instance, stable, and failure-tolerant
- `/api/ai/status` mapping is accurate and unambiguous
- stale/missing data states are user-visible and non-misleading
