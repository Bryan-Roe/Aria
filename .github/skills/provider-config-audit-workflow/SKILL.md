---
name: provider-config-audit-workflow
description: 'Audit chat/model provider configuration, readiness, and fallback behavior across LMStudio, Azure OpenAI, OpenAI, LoRA, and local fallback. Use when provider selection is unexpected, env setup is unclear, or streaming behavior differs by backend.'
argument-hint: 'Describe the expected provider, current behavior, environment context, and whether streaming or non-streaming is affected.'
---

# Provider Config Audit Workflow

## What This Skill Produces

Use this skill to produce a clear provider-readiness and fallback diagnosis. The expected output is:
- a provider eligibility matrix based on current configuration
- explanation of why the selected provider won the detection chain
- identified misconfigurations (missing vars, invalid adapter path, endpoint mismatch)
- remediation steps and verification checks for stable provider behavior

## When to Use

Use this skill when you need to:
- debug why the app chose the wrong provider
- verify environment setup for Azure/OpenAI/LMStudio/LoRA
- diagnose fallback-to-local behavior
- confirm streaming compatibility across providers
- audit provider-related changes before release

Common trigger phrases:
- "why is provider selection wrong"
- "audit provider config"
- "it keeps falling back to local"
- "Azure/OpenAI setup is not taking effect"
- "verify fallback chain"

## Procedure

1. Capture expected vs actual provider behavior
   - Record which provider should have been selected and which provider was actually used.
   - Include whether the issue is selection, initialization, rate-limit fallback, or streaming behavior.

2. Build an eligibility matrix from configuration
   - Evaluate explicit provider override first.
   - Evaluate detection prerequisites for LMStudio, Azure OpenAI, OpenAI, explicit LoRA mode, then local fallback.
   - Mark each provider as eligible, ineligible, or partially configured.

3. Verify runtime signals
   - Check `/api/ai/status` for active provider and readiness clues.
   - Cross-check the implementation boundary (`shared/chat_providers.py` re-export vs source provider module).

4. Validate contract and behavior
   - Ensure both `stream=True` and `stream=False` paths remain supported.
   - Confirm streaming output remains contract-compatible for consumers.
   - Confirm fallback behavior is graceful and deterministic under dependency failure.

5. Identify root cause category
   - Missing/incorrect environment variables
   - Wrong explicit provider override
   - Broken adapter/model path for LoRA
   - Endpoint/auth mismatch for remote providers
   - Runtime exceptions causing fallback cascade

6. Apply least-invasive fixes
   - Update configuration first when possible.
   - Change provider selection logic only when behavior genuinely conflicts with intended precedence.
   - Do not hardcode secrets while debugging.

7. Re-verify end to end
   - Re-test selection with same input path.
   - Verify provider name and response behavior (including streaming, if applicable).
   - Document final expected configuration and fallback behavior.

## Quality Checks

Before finishing, confirm that:
- provider order and eligibility are explicitly explained
- no credentials are added to source control
- fallback behavior remains intentional and resilient
- both streaming and non-streaming behavior are verified when relevant
- remediation steps are concrete and reproducible
