---
name: function-app-endpoint-workflow
description: 'Add, modify, or debug `function_app.py` routes, API contracts, static page serving, and SSE responses. Use when changing chat, TTS, AI status, quantum endpoints, or other Function App routes and you need to preserve existing patterns and verify behavior safely.'
argument-hint: 'Describe the route, endpoint behavior, static file, or streaming response you need to change.'
---

# Function App Endpoint Workflow

## What This Skill Produces

Use this skill to make safe changes to `function_app.py` endpoints and helpers. The expected output is:
- a clear contract for the endpoint being changed
- a minimal route or helper update aligned with existing patterns
- preserved streaming, health, and secret-handling behavior
- targeted verification through local requests or focused tests

## When to Use

Use this skill when you need to:
- add a new API route in `function_app.py`
- debug an existing route returning the wrong payload or status
- change static page or asset serving behavior
- update SSE streaming behavior for chat-style responses
- verify provider readiness or health reporting through `/api/ai/status`

Common trigger phrases:
- "add an endpoint"
- "fix this Function App route"
- "update `function_app.py`"
- "static page serving is broken"
- "the SSE response is malformed"
- "the AI status endpoint is wrong"

## Procedure

1. Define the contract before editing
   - Identify the route path, allowed methods, expected request shape, response format, and failure modes.
   - Check nearby endpoints in `function_app.py` for the established routing and helper patterns.

2. Inspect dependencies and side effects
   - Determine whether the route touches chat providers, telemetry, Cosmos, SQL, TTS, or static files.
   - Preserve existing secret handling and configuration flow; never hardcode keys or connection strings.

3. Keep streaming behavior stable when applicable
   - For SSE endpoints, preserve the `data: {json}` event format and the terminating `data: [DONE]` message.
   - Avoid changing the wire contract unless the task explicitly requires coordinated client updates.

4. Reuse helper patterns for static and shared behavior
   - Prefer the existing static-serving and response helper patterns instead of adding one-off route logic.
   - Keep error handling and headers consistent with neighboring endpoints.

5. Validate readiness and provider assumptions
   - If the endpoint depends on model or service configuration, use `/api/ai/status` as a health reference.
   - Confirm any provider-dependent logic still behaves sensibly when optional services are unavailable.

6. Implement the smallest route change
   - Change only the specific endpoint or helper required.
   - Avoid refactoring unrelated routes in the same patch unless the bug is clearly shared.

7. Verify locally and with tests
   - Use focused requests against the changed route.
   - Run targeted tests or the repository test runner when the change affects shared behavior.
   - Re-test adjacent routes if they share helpers or static-serving utilities.

## Quality Checks

Before finishing, confirm that:
- request and response contracts are explicit and preserved
- secrets remain externalized to configuration
- SSE output stays valid for streaming consumers
- health and fallback behavior remain sensible when dependencies are missing
- the changed route is covered by smoke checks or focused tests
