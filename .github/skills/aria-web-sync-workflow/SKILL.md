---
name: aria-web-sync-workflow
description: 'Maintain behavioral parity between `aria_web` and `apps/aria/server.py`, including API contracts, static file serving, and CORS behavior. Use when Aria web entry points diverge, routes behave differently, or wrappers/re-exports drift from canonical server logic.'
argument-hint: 'Describe the Aria endpoint or UI behavior mismatch and which entry point fails (`aria_web` vs `apps/aria/server.py`).'
---

# Aria Web Sync Workflow

## What This Skill Produces

Use this skill to prevent drift between Aria web entry points. The expected result is:
- a clear canonical-vs-wrapper ownership model
- matched API route behavior across both entry points
- consistent static asset and CORS behavior
- focused tests proving contract parity

## When to Use

Use this skill when you need to:
- debug differences between `aria_web` and `apps/aria/server.py`
- add or change Aria routes without breaking wrapper compatibility
- fix static asset path inconsistencies for Aria pages/scripts
- ensure CORS and response contracts stay aligned across entry points

Common trigger phrases:
- "aria_web behaves differently than apps/aria/server.py"
- "same endpoint returns different responses"
- "wrapper entry point drift"
- "Aria state/command endpoint mismatch"
- "static Aria page works in one entry but not the other"
- "keep aria_web in sync"

## Procedure

1. Treat canonical ownership as explicit
   - Canonical route logic belongs in `apps/aria/server.py`.
   - `aria_web` should re-export/wrap canonical behavior, not fork it.

2. Compare contracts before editing
   - Verify method, path, request shape, and response shape for shared endpoints.
   - Confirm parity for:
     - `GET /api/aria/state`
     - `POST /api/aria/command`
     - `POST /api/aria/execute`
     - object/world APIs where applicable.

3. Validate static-serving alignment
   - Confirm static files are served from `apps/aria/` consistently.
   - Ensure `index.html`, `aria_controller.js`, and related assets resolve in both entry paths.

4. Check CORS and headers
   - Keep CORS behavior equivalent across entry points.
   - Avoid one entry point adding/omitting headers the other relies on.

5. Fix in canonical-first order
   - First update canonical server logic if behavior change is intended.
   - Then adjust `aria_web` wrapper/re-export to match canonical behavior.

6. Verify parity with focused tests
   - Run Aria API tests (`tests/test_aria_server.py`) and any related integration tests.
   - Re-run the same request path against both entry points when practical.

7. Prevent future drift
   - Keep wrapper logic minimal and documented.
   - Avoid duplicating route/business logic in `aria_web`.

## Quality Checks

Before finishing, confirm that:
- canonical logic remains in `apps/aria/server.py`
- `aria_web` does not introduce divergent route behavior
- static asset paths resolve consistently
- CORS/headers are aligned between entry points
- tests cover the parity-sensitive endpoints
