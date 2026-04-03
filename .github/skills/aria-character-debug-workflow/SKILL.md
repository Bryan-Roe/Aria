---
name: aria-character-debug-workflow
description: 'Debug Aria character commands, action parsing, auto-execute flows, object interactions, world generation, and UI/server state sync. Use when Aria does the wrong action, gestures fail, pickup or throw breaks, state looks wrong, or the web UI and server disagree.'
argument-hint: 'Describe the Aria command, endpoint, state mismatch, or failing action sequence.'
---

# Aria Character Debug Workflow

## What This Skill Produces

Use this skill to investigate and fix Aria character issues end to end. The expected result is:
- a reproducible failing command, action, or state transition
- a focused diagnosis across `apps/aria/server.py`, client behavior, and API responses
- a minimal fix that preserves stage-state rules and tag formats
- targeted verification through endpoint checks and Aria-specific tests

## When to Use

Use this skill when you need to:
- debug natural language commands that Aria interprets incorrectly
- fix auto-execute action sequences
- repair object interactions like pickup, drop, or throw
- investigate world generation or expression/gesture issues
- diagnose UI and server state mismatches

Common trigger phrases:
- "Aria is not following commands"
- "the character does the wrong action"
- "auto execute is broken"
- "pickup or throw is failing"
- "the Aria UI and server state do not match"
- "world generation or gestures are broken"

## Procedure

1. Reproduce the issue
   - Capture the exact natural-language command, structured action payload, or UI interaction.
   - Compare the observed result with the expected movement, gesture, object interaction, or state change.

2. Check the API surface first
   - Use `GET /api/aria/state` to inspect current stage state.
   - Use `POST /api/aria/command` to inspect parsing output and tags.
   - Use `POST /api/aria/execute` for structured sequences.
   - Use `POST /api/aria/object` or `POST /api/aria/world` when the issue involves objects or themed environments.

3. Inspect server rules before changing code
   - Confirm that `stage_state['aria']`, `stage_state['objects']`, and `stage_state['environment']` are updated consistently.
   - Validate movement bounds stay within 0-100 percent for x and y.
   - Check pickup distance logic and held-object preconditions before changing behavior.
   - Preserve gesture allowlists and text length safeguards.

4. Verify parser behavior
   - Prefer the LLM-backed parser path when available, but preserve the rule-based fallback.
   - Inspect generated tags and action parameters before assuming the executor is wrong.
   - Keep tag formats stable: `[aria:action:param]`.

5. Inspect client-side state only after confirming the server contract
   - Compare API responses with `apps/aria/aria_controller.js` state updates and animation triggers.
   - Look for mismatches in position, held object, mood, or gesture rendering rather than changing both sides at once.

6. Fix incrementally
   - Make the smallest change that restores the broken command or state transition.
   - Avoid changing unrelated gestures, object rules, or animation behavior in the same patch.

7. Verify with focused checks
   - Run targeted tests such as `tests/test_aria_server.py`, `tests/test_object_api_integration.py`, or relevant auto-execute tests.
   - Re-run the exact failing command through the API after the change.
   - Confirm the final state matches the expected action and tags.

## Quality Checks

Before finishing, confirm that:
- the failing command or action sequence is reproducible and then fixed
- stage-state mutations remain valid and bounded
- tags and API responses stay backward compatible
- UI behavior matches the corrected server state
- tests or smoke checks cover the changed path
