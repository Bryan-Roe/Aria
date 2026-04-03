---
name: chat-provider-implementation-workflow
description: "Implement or refactor chat provider adapters and detection flow while preserving fallback order, streaming contract, and env-var readiness checks. Use when adding a provider, fixing provider selection logic, or debugging provider-specific complete/stream behaviors in chat CLI and shared providers."
argument-hint: "Describe the provider change: new provider integration, detection bug, streaming mismatch, or env readiness issue."
---

# Chat Provider Implementation Workflow

## What This Skill Produces

Use this skill to add/fix providers without breaking fallback behavior. The expected result is:

- correct provider adapter implementation
- preserved detection and fallback semantics
- streaming and non-streaming consistency
- clear readiness diagnostics tied to environment configuration

## When to Use

Use this skill when you need to:

- add a new `BaseChatProvider` implementation
- fix provider detection order or readiness checks
- debug differences between CLI and Functions provider behavior
- repair stream/non-stream output handling per provider
- validate LoRA adapter provider constraints

Common trigger phrases:

- "add a new chat provider"
- "provider fallback is wrong"
- "Azure vars are set but provider not selected"
- "streaming works for one provider only"
- "LoRA provider load fails"
- "provider complete() contract mismatch"

## Procedure

1. Preserve core detection semantics
   - Keep documented detection order and explicit override behavior.
   - Ensure readiness checks use the required env-var set per provider.

2. Implement provider contract faithfully
   - `complete(messages, stream)` behavior must be consistent with shared abstractions.
   - Keep return types/stream chunks aligned with downstream consumers.

3. Validate stream vs non-stream parity
   - Non-stream should produce full coherent response.
   - Stream should produce incremental events compatible with SSE consumers.

4. Keep LoRA constraints explicit
   - Require adapter directory essentials and fail clearly when missing.
   - Avoid silent fallback that masks adapter misconfiguration.

5. Keep CLI and API integration aligned
   - Confirm provider behavior in chat CLI and Functions surfaces matches expectations.
   - Avoid codepath-specific schema drift between interfaces.

6. Add minimal readiness diagnostics
   - Expose actionable reason when provider is skipped.
   - Keep secrets out of logs while preserving debugging utility.

7. Re-verify fallback chain
   - Test explicit provider selection and auto-detection paths.
   - Confirm fallback only occurs for real readiness/runtime failures.

## Quality Checks

Before finishing, confirm that:

- provider adapter follows shared contract for stream/non-stream calls
- detection order and readiness checks are preserved
- fallback behavior is intentional and observable
- LoRA adapter requirements are enforced with clear errors
- CLI/API surfaces consume provider outputs consistently
