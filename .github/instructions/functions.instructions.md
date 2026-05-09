---
name: "Azure-Functions-App"
description: "Guidance for function_app.py and API endpoints"
applyTo: "**/function_app.py"
---
# Azure Functions – function_app.py

- Endpoints: `/api/chat`, `/api/chat-web`, `/api/tts`, `/api/quantum/*`, `/api/ai/status`.
  - Verify runtime health at `/api/ai/status` (active provider, env vars, SQL pool, Cosmos status).
- Local dev:
  - Use the VS Code task: `func: host start` (depends on `pip install (functions)`).
  - Azurite storage emulator databases are present at repo root; Functions work offline.
- TTS configuration:
  - Azure Speech: set `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` (in env or `local.settings.json`).
  - Local fallback: set `QAI_ENABLE_LOCAL_TTS=true`; server will try Azure → pyttsx3 → gTTS.
- Chat provider detection (see `shared/chat_providers.py`): Azure OpenAI → OpenAI → LoRA → Local.
  - Azure requires: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
- Streaming responses (SSE): emit `data: {json}` lines and a final `data: [DONE]`; clients must parse SSE.
- Secrets: do not hardcode; prefer `local.settings.json` for dev or Azure App Settings in prod.
- Observability: Application Insights via `shared/telemetry.py`; failures are non-blocking.
- Optional Cosmos persistence: feature-flagged in `shared/cosmos_client.py`.
  - Recommended keys: `QAI_ENABLE_COSMOS`, `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER`.
  - Partition key: `/session_id`; enable TTL for ephemeral messages.
- Testing: prefer `python .\\scripts\\test_runner.py --all`; markers `not slow and not azure` for local.
