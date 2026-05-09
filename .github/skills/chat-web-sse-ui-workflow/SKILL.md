---
name: chat-web-sse-ui-workflow
description: "Debug and evolve chat web frontend SSE behavior, incremental rendering, and `/api/chat` contract handling for browser clients. Use when streaming stalls, `[DONE]` isn’t handled, tokens render incorrectly, TTS playback desyncs, or chat-web UI and backend SSE schema drift apart."
argument-hint: "Describe the chat-web symptom: stalled stream, parse error, partial rendering, TTS mismatch, or endpoint/schema mismatch."
---

# Chat Web SSE UI Workflow

## What This Skill Produces

Use this skill to keep chat web UX consistent with backend streaming contracts. The expected result is:

- correct SSE parsing and stream completion handling
- stable incremental token rendering
- resilient UI behavior on malformed/partial events
- backend/frontend schema alignment for stream payloads

## When to Use

Use this skill when you need to:

- debug chat-web incremental streaming behavior
- fix frontend parsing of `data:` lines and `[DONE]` sentinel
- align client event fields with backend JSON payloads
- troubleshoot TTS playback sequencing with streamed text
- diagnose browser-side hangs while backend is still healthy

Common trigger phrases:

- "chat stream hangs in browser"
- "[DONE] never processed"
- "client expects plain text not SSE"
- "delta/content field mismatch"
- "tokens render out of order"
- "TTS playback doesn’t match stream"

## Procedure

1. Verify producer/consumer contract
   - Confirm exact event JSON fields emitted by `/api/chat`.
   - Confirm client parser consumes those fields and skips `[DONE]` appropriately.

2. Reproduce with raw event visibility
   - Inspect line-by-line stream events before touching render logic.
   - Separate transport failures from rendering bugs.

3. Validate frontend parser robustness
   - Handle keepalive/blank lines safely.
   - Ignore malformed lines without breaking full stream session.
   - Preserve partial content accumulation correctly.

4. Keep completion semantics explicit
   - `[DONE]` must terminate stream state cleanly.
   - UI should finalize message state exactly once.

5. Check TTS integration boundary
   - Ensure streamed text aggregation matches what is sent to `/api/tts`.
   - Avoid race conditions between final message state and audio playback triggers.

6. Apply smallest-side fix
   - Fix backend only if wire format is wrong.
   - Fix frontend only if parser/render assumptions are wrong.
   - Avoid changing both unless contract evolution is intentional.

7. Re-test end to end
   - raw stream check -> frontend rendering check -> optional TTS path check.

## Quality Checks

Before finishing, confirm that:

- SSE parser handles `data:` lines and `[DONE]` correctly
- frontend field extraction matches backend payload schema
- stream completion state is deterministic and non-duplicated
- malformed events degrade gracefully without UI lockups
- TTS sequencing uses finalized content consistently
