---
name: function-binding-debug-workflow
description: 'Debug Azure Functions folder wiring, function.json bindings, HTTP routes, and trigger contract mismatches. Use when a function route 404s, a binding is malformed, startup skips a function, or local Functions indexing behaves unexpectedly.'
argument-hint: 'Describe the function folder, failing route/trigger, and observed host or startup error.'
---

# Function Binding Debug Workflow

## What This Skill Produces

Use this skill to diagnose Azure Functions folder-level contract issues. The expected output is:
- a precise binding or route mismatch diagnosis
- minimal fixes to `function.json` or paired module files
- reusable validation steps for local and CI checks

## When to Use

Use this skill when you need to:
- debug `function.json` parse or indexing issues
- fix missing or broken HTTP routes
- confirm trigger method/auth/route wiring
- ensure Functions folders are CI-validated consistently

Common trigger phrases:
- "function route 404"
- "function.json broken"
- "Azure Functions indexing failed"
- "binding mismatch"
- "local host skips my function"

## Procedure

1. Inspect the function folder pair
   - confirm `function.json` exists
   - confirm Python entry module exists (`__init__.py` or expected module file)

2. Validate binding structure
   - JSON parseability
   - required `bindings` array
   - expected HTTP trigger properties (`direction`, `methods`, `route`, `authLevel`)

3. Reproduce with smallest route check
   - call the function route directly or inspect the host indexing output

4. Apply minimal repair
   - patch route/method/direction mismatches only
   - avoid unrelated logic edits if host contract is the real problem

5. Add reusable enforcement
   - prefer CI validation through a composite action instead of ad-hoc shell snippets

## Quality Checks

Before finishing, confirm that:
- the function folder contract is complete and parseable
- route/trigger expectations are explicit
- local or CI validation steps are documented
- the fix targets binding wiring, not unrelated runtime behavior
