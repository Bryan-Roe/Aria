---
name: functions-sse-contract-workflow
description: 'Add, verify, or debug server-sent event contracts between `function_app.py` endpoints and web consumers. Use when `/api/chat` streaming stalls, `[DONE]` is missing, event JSON is malformed, content types are wrong, or a client assumes plain text instead of SSE.'
argument-hint: 'Describe the streaming endpoint, consuming page or script, and what the stream does wrong.'
---

# Functions SSE Contract Workflow

## What This Skill Produces

Use this skill to keep streaming contracts stable between Functions endpoints and browser clients. The expected result is:
- a clear producer/consumer contract for the stream
- a verified raw event format on the wire
- a minimal fix in either the endpoint or the parser
- regression checks for both stream producer and consumer

## When to Use

Use this skill when you need to:
- debug `/api/chat` streaming behavior
- add or change an SSE-producing endpoint in `function_app.py`
- fix browser/client parsing of `data:` event lines
- investigate why a web page hangs, truncates, or never sees completion
- confirm a frontend is using SSE instead of assuming plain text chunks

Common trigger phrases:
- "streaming is broken"
- "the client never receives [DONE]"
- "SSE payload is malformed"
- "the page assumes plain text but the backend sends SSE"
- "chat-web hangs forever"
- "the stream works in one client but not another"

## Procedure

1. Define the contract first
   - Identify the SSE endpoint, the consuming script/page, and the expected event shape.
   - Confirm whether the client expects `content`, `delta`, or another JSON field.

2. Inspect the raw stream on the wire
   - Verify the endpoint emits `data: {json}` lines.
   - Verify the stream ends with `data: [DONE]`.
   - Confirm event ordering before changing any parser logic.

3. Validate endpoint response behavior
   - Ensure the route advertises the right content type for streaming.
   - Keep streaming logic separate from static page-serving logic.
   - Preserve no-cache or freshness behavior where the web surface depends on it.

4. Validate the client parser
   - Confirm it reads line-oriented `data:` events rather than assuming plain text chunks.
   - Ensure it ignores the `[DONE]` sentinel correctly.
   - Verify JSON decoding and incremental UI updates use the actual event schema.

5. Check health and dependency prerequisites
   - Use `/api/ai/status` to confirm provider readiness before blaming the stream format.
   - If the endpoint depends on TTS or another backend path, isolate those separately.

6. Fix the smallest contract mismatch
   - Change the producer if the wire format is wrong.
   - Change the consumer if the parser assumption is wrong.
   - Avoid changing both sides unless the contract is intentionally evolving.

7. Re-verify at two levels
   - Re-check the raw stream directly.
   - Then re-test the browser or client flow end to end.

## Quality Checks

Before finishing, confirm that:
- the stream emits valid `data:` events and terminates with `[DONE]`
- the client parses SSE rather than raw text chunks
- event JSON fields match what the consumer expects
- static UI routes and streaming routes remain clearly separated
- the original stalled or malformed stream repro is resolved
