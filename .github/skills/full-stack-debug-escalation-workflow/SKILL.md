---
name: full-stack-debug-escalation-workflow
description: 'Escalate debugging across browser UI, JavaScript clients, Azure Functions routes, shared Python infrastructure, and orchestrator status artifacts. Use when a bug crosses layers, the visible symptom is far from the root cause, or you need a disciplined path from frontend repro to backend fix.'
argument-hint: 'Describe the symptom, affected surface, and the first failing request, page, or workflow you can reproduce.'
---

# Full-Stack Debug Escalation Workflow

## What This Skill Produces

Use this skill to trace failures across Aria’s browser, API, shared-infra, and orchestration boundaries. The expected result is:
- a reproducible symptom at the outermost layer
- a ranked set of likely failure domains
- a narrowed root cause at one layer boundary
- a minimal repair plus focused regression checks

## When to Use

Use this skill when you need to:
- debug a frontend issue that may actually be backend or config related
- trace API errors through Functions routes into provider or DB code
- investigate Aria, chat, dashboard, training, or quantum issues spanning multiple systems
- reconcile browser-visible behavior with health endpoints and status files
- diagnose regressions where several subsystems appear broken at once

Common trigger phrases:
- "this issue spans the whole stack"
- "the UI is broken but I think the backend is the real problem"
- "why does the page fail even though the API looks up"
- "chat returns 500 and the browser hangs"
- "the tests pass but the app still breaks in the browser"
- "trace this from frontend to backend"

## Procedure

1. Characterize the symptom at the outermost layer
   - Start with the user-visible failure: page behavior, API response, stalled workflow, or incorrect rendered state.
   - Capture the exact failing path before opening code.

2. Reproduce with the smallest external check
   - For browser surfaces, identify the exact page, route, or action.
   - For APIs, replay the request directly and record the status code, payload, and timing.
   - For orchestrators, identify the failing job or stale status artifact.

3. Snapshot top-level health signals
   - Check `/api/ai/status` for provider readiness, SQL pool, Cosmos, and dependency health.
   - Inspect relevant `data_out/<orchestrator>/status.json` files before assuming a live-process issue.
   - Use resource snapshots when the symptom could be saturation-related.

4. Isolate the boundary that breaks
   - Browser/UI layer: rendering logic, event wiring, state synchronization, static asset loading.
   - API layer: route contract, SSE/static serving, request validation, response format.
   - Shared infra layer: provider selection, SQL/Cosmos/telemetry, embedding or logging helpers.
   - Orchestration layer: YAML config, status-file generation, lifecycle transitions, batch jobs.

5. Escalate inward one layer at a time
   - Do not patch multiple layers at once.
   - Confirm the frontend contract before changing backend shape.
   - Confirm the backend route before changing shared utilities.
   - Confirm shared utilities before blaming orchestration or environment state.

6. Fix minimally at the real layer
   - Change only the boundary that actually failed.
   - Preserve public contracts, route names, status schemas, and dataset immutability unless the task explicitly changes them.

7. Verify from the inside out and then outside in
   - Re-run the lowest-level focused check first.
   - Re-test the affected route or workflow.
   - Finish by re-running the original browser- or user-level repro.

## Quality Checks

Before finishing, confirm that:
- the original symptom is reproducible before the fix and gone after it
- the failing layer boundary is identified explicitly
- `/api/ai/status` and relevant `status.json` artifacts agree with the diagnosis
- unrelated layers were not changed speculatively
- focused tests or smoke checks cover the repaired path
