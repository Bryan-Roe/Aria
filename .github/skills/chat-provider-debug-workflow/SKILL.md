---
name: chat-provider-debug-workflow
description: 'Diagnose chat provider detection, fallback behavior, streaming output, and configuration readiness across LMStudio, Azure OpenAI, OpenAI, LoRA, and local fallback paths. Use when chat falls back unexpectedly, provider selection is wrong, or SSE consumers break.'
argument-hint: 'Describe the provider issue, fallback behavior, environment setup, or streaming symptom.'
---

# Chat Provider Debug Workflow

## What This Skill Produces

Use this skill to trace chat failures from configuration through provider selection to streaming output. The expected result is:
- a clear explanation of why a provider was selected or skipped
- a focused fix in provider selection, initialization, or streaming behavior
- preserved fallback semantics instead of brittle one-provider assumptions
- verification using health checks, chat requests, or targeted tests

## When to Use

Use this skill when you need to:
- diagnose unexpected fallback to local responses
- verify provider detection order and readiness
- fix chat streaming behavior or malformed SSE output
- investigate Azure/OpenAI/LMStudio configuration issues
- debug provider-specific initialization or timeout failures

Common trigger phrases:
- "why did chat fall back to local"
- "the wrong provider is being selected"
- "streaming is broken"
- "provider detection is wrong"
- "Azure OpenAI or OpenAI configuration is not working"
- "LMStudio should be used but is skipped"

## Procedure

1. Reproduce the issue with the smallest path
   - Capture whether the problem appears in the web endpoint, CLI, or a direct provider invocation.
   - Note whether the failure is selection, initialization, streaming, or response quality.

2. Verify provider detection order
   - Check for explicit provider choice first.
   - Then confirm readiness in order: LMStudio, Azure OpenAI, OpenAI, explicit LoRA mode, and local fallback.
   - Do not assume a provider is eligible unless its required configuration is present.

3. Inspect configuration and env-driven readiness
   - Verify the exact environment variables expected by the candidate provider.
   - Keep all keys externalized; debug with configuration visibility, never by hardcoding credentials.

4. Trace the implementation boundary
   - Remember that `shared/chat_providers.py` re-exports the main implementation from `ai-projects/chat-cli/src/chat_providers.py`.
   - Fix the real implementation layer rather than patching the re-export unless the import boundary itself is broken.

5. Preserve the provider contract
   - Ensure providers still support both streaming and non-streaming usage.
   - For streamed responses, keep SSE chunks in the expected event format and end with `[DONE]` when appropriate.

6. Fix with fallback safety in mind
   - Prefer fixes that preserve graceful degradation when remote providers are unavailable.
   - Avoid changes that make the system fail hard when it should fall back safely.

7. Verify from the outside in
   - Use `/api/ai/status` as a readiness check.
   - Re-run the failing chat path and confirm the selected provider matches the intended configuration.
   - Add or adjust targeted tests if the selection or streaming contract changed.

## Quality Checks

Before finishing, confirm that:
- the selected provider and fallback reasoning are explainable
- no credentials were introduced into source files
- both streaming and non-streaming behavior remain intact
- the fix was validated through a real request or focused test
- fallback behavior still works when preferred providers are unavailable
