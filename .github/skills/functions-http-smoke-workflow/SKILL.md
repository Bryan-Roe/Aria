---
name: functions-http-smoke-workflow
description: 'Add or debug lightweight HTTP smoke checks for Azure Functions endpoints using reusable CI actions and targeted local validation. Use when endpoint availability, status codes, or minimal contract checks need fast verification.'
argument-hint: 'Describe the endpoint, expected status/shape, and whether you need local or CI smoke coverage.'
---

# Functions HTTP Smoke Workflow

## What This Skill Produces

Use this skill to add fast, deterministic endpoint checks. The expected output is:
- a clear endpoint + expected status contract
- minimal local smoke verification steps
- reusable CI smoke action usage
- concise failure diagnostics

## When to Use

Use this skill when you need to:
- verify an endpoint is reachable after changes
- catch route regressions early in CI
- validate simple response health without heavy integration tests
- quickly triage whether a failure is startup, routing, or contract related

Common trigger phrases:
- "smoke this endpoint"
- "check function route health"
- "status endpoint failing"
- "add quick API check in CI"

## Procedure

1. Define the smoke contract
   - endpoint URL/route
   - expected status code
   - optional minimal response key/shape expectation

2. Validate locally first
   - call endpoint directly with curl
   - confirm status and short response excerpt

3. Add reusable workflow enforcement
   - prefer composite action usage over ad-hoc shell duplication
   - keep checks focused and fast

4. Report actionable diagnostics
   - route mismatch vs startup failure vs provider/config failure
   - exact next step command

## Quality Checks

Before finishing, confirm that:
- expected status is explicit
- check is deterministic and low-latency
- CI usage is reusable and documented
- diagnostics remain concise and operator-friendly
