---
name: ai-safety-guardrails-workflow
description: "Design and enforce practical safety guardrails for AI features, including prompt controls, output filtering, abuse handling, and operational fail-safes."
argument-hint: "Describe the AI flow, risk concerns (prompt injection, unsafe output, data leakage), and enforcement points."
---

# AI Safety Guardrails Workflow

## What This Skill Produces

Use this skill to establish safety controls around AI behavior. The expected output is:

- threat/risk map for the AI interaction path
- prioritized guardrails at input, runtime, and output stages
- explicit policy decisions and fail-closed/soft-fail behavior
- monitoring hooks for policy violations and drift
- verification plan for safety controls

## When to Use

Use this skill when you need to:

- harden an AI endpoint before release
- reduce prompt-injection and data-leak risks
- add moderation or policy enforcement checks
- define safe fallback behavior under uncertainty
- audit an existing AI workflow for safety gaps

Common trigger phrases:

- "add guardrails"
- "harden this AI endpoint"
- "prevent prompt injection"
- "avoid unsafe responses"
- "audit model safety"

## Procedure

1. Model risks and abuse cases
   - Enumerate misuse paths (injection, exfiltration, harmful output, overreach).
   - Rank by likelihood and impact.

2. Add input controls
   - Validate/normalize inputs and enforce scope constraints.
   - Strip or quarantine unsupported instruction patterns when possible.

3. Add runtime controls
   - Constrain tool access and side-effect permissions.
   - Set timeout/token/attempt budgets to avoid runaway behavior.

4. Add output controls
   - Enforce schema, redact sensitive patterns, and moderate unsafe content.
   - Apply fail-safe response when policy confidence is low.

5. Add observability
   - Log violation types and control decisions without leaking secrets.
   - Track trend metrics to detect safety drift.

6. Verify with adversarial tests
   - Run targeted adversarial prompts and boundary cases.
   - Confirm controls trigger correctly and degrade gracefully.

## Quality Checks

Before finishing, confirm that:

- highest-risk abuse cases have concrete mitigations
- tool/permission boundaries are explicit
- moderation and redaction behavior is deterministic
- safety logs are actionable and privacy-aware
- adversarial validation was executed
