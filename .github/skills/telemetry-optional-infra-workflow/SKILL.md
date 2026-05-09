---
name: telemetry-optional-infra-workflow
description: 'Implement and debug optional telemetry initialization and tracing behavior so application features never depend on telemetry availability. Use when `APPLICATIONINSIGHTS_CONNECTION_STRING` handling is unclear, telemetry appears uninitialized, or startup/request paths accidentally treat telemetry as required.'
argument-hint: 'Describe the telemetry symptom: init not running, traces missing, env var confusion, or feature behavior changing when telemetry is off.'
---

# Telemetry Optional Infra Workflow

## What This Skill Produces

Use this skill to keep observability robust and optional. The expected result is:
- idempotent one-time telemetry initialization
- graceful no-op behavior when telemetry deps/env are absent
- no feature regressions when telemetry is disabled
- clear verification of enabled/disabled states

## When to Use

Use this skill when you need to:
- debug `shared/telemetry.py` initialization behavior
- ensure telemetry is initialized once at startup (not per request)
- fix logic that blocks app behavior when telemetry is unavailable
- validate environment/config handling for App Insights connection strings

Common trigger phrases:
- "telemetry didn’t initialize"
- "app breaks without telemetry"
- "Application Insights key set but no traces"
- "init_telemetry called too often"
- "is_enabled returns unexpected value"
- "telemetry should be optional"

## Procedure

1. Verify optionality as invariant
   - Telemetry must never be a hard runtime dependency.
   - All feature paths should behave identically when telemetry is disabled.

2. Confirm one-time initialization
   - Call `init_telemetry()` once during startup (e.g., in `function_app.py` bootstrap).
   - Avoid per-request initialization patterns.

3. Validate enablement conditions
   - `APPLICATIONINSIGHTS_CONNECTION_STRING` present and valid.
   - Azure Monitor/OpenTelemetry dependency available.
   - If either is missing, `init_telemetry()` should return false and app continues.

4. Guard custom tracing calls
   - Check `is_enabled()` before optional custom spans/log enrichment.
   - Do not assume telemetry clients are always present.

5. Preserve non-blocking behavior
   - Telemetry failures should not block request handling.
   - Handle SDK import/init errors with graceful degradation.

6. Test both modes explicitly
   - Mode A: telemetry enabled with env var + deps.
   - Mode B: telemetry disabled (missing env/deps) and app still fully functional.

7. Keep diagnostics clear
   - Log concise telemetry enabled/disabled state at startup.
   - Avoid noisy per-request telemetry initialization logs.

## Quality Checks

Before finishing, confirm that:
- telemetry initialization is idempotent and startup-scoped
- features continue working when telemetry is disabled
- `is_enabled()` correctly reflects runtime state
- missing env/deps cause graceful disable, not failures
- no request path treats telemetry as mandatory
