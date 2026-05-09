---
name: cooking-ai-recipe-agent-workflow
description: 'Develop, debug, and harden Cooking AI recipe-agent flows with schema-safe JSON output, provider fallback handling, and robust ingredient extraction. Use when recipe responses are malformed, JSON mode fails, fallback parsing breaks, or provider errors should degrade gracefully.'
argument-hint: 'Describe the recipe/ingredient workflow issue: malformed JSON, fallback parse failure, provider behavior, or schema mismatch.'
---

# Cooking AI Recipe Agent Workflow

## What This Skill Produces

Use this skill to keep Cooking AI outputs structured and resilient. The expected result is:
- schema-valid recipe and ingredient outputs
- reliable JSON-mode invocation with fallback parsing
- graceful handling of provider failures
- idempotent agent behavior for repeated prompts

## When to Use

Use this skill when you need to:
- debug `ai-projects/cooking-ai/src/agents/recipe_agent.py`
- fix malformed recipe/ingredient JSON outputs
- tune provider JSON-mode/fallback behavior
- improve resilience when providers fail or return free text
- validate output schema contracts in downstream consumers

Common trigger phrases:
- "recipe agent returned invalid JSON"
- "ingredient extraction output is malformed"
- "json_mode failed"
- "fallback parsing didn’t recover"
- "provider crashed and agent broke"
- "recipe output schema mismatch"

## Procedure

1. Confirm protocol compatibility first
   - Ensure provider satisfies structural protocol (`complete(messages, json_mode=...)`).
   - Avoid inheritance-only assumptions; structural typing is accepted.

2. Validate schema targets explicitly
   - Recipe search output:
     - `recipes[].title`, `ingredients[]`, `instructions[]`, `tags[]`, `est_time_minutes`
   - Ingredient extraction output:
     - `ingredients[].raw`, `name`, `quantity`, `unit`, `notes`

3. Verify 2-stage invoke behavior
   - Stage 1: request JSON mode from provider.
   - Stage 2: on failure, request free text and parse embedded JSON.
   - If both fail, return empty structures that still match schema.

4. Keep failure behavior non-fatal
   - Provider failures should not crash endpoint/agent flow.
   - Return safe empty schema payloads rather than raising raw provider exceptions.

5. Preserve idempotent shape
   - For same input, preserve output shape and keys consistently.
   - Avoid dynamic key drift across retries.

6. Fix minimally in the failing stage
   - If JSON mode is weak: tighten prompt/schema instruction.
   - If fallback parse is weak: improve extraction robustness without changing schema.
   - If provider contract is wrong: patch adapter layer, not recipe schema.

7. Re-validate with representative prompts
   - Test both successful JSON mode and forced-fallback scenarios.
   - Confirm outputs parse cleanly and downstream code receives expected keys.

## Quality Checks

Before finishing, confirm that:
- provider protocol usage is valid and stable
- recipe and ingredient schemas are always satisfied
- fallback behavior handles malformed provider responses gracefully
- failures degrade to empty-but-valid structures (not crashes)
- output keys remain stable across retries and providers
