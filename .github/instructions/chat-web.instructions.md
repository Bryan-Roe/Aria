---
name: "Chat-Web"
description: "Guidance for chat-web frontend and SSE integration"
applyTo: "chat-web/**"
---
# Chat Web – frontend & SSE

- Endpoints used: `/api/chat` (SSE streaming), `/api/chat-web` (web UI), `/api/tts` (audio synthesis).
- SSE parsing on the client: read streamed `data: {json}` lines and handle final `data: [DONE]`.
  - Each `data:` line contains JSON with `content` or delta; skip `[DONE]` sentinel.
- TTS usage: backend tries Azure Speech first, then pyttsx3, then gTTS; `/api/tts` returns `audio_base64` and `format` (mp3 or wav).
- Provider readiness: use `/api/ai/status` to check active provider, required env vars, LoRA readiness, SQL/Cosmos status.
- Avoid hardcoding secrets; use environment variables or `local.settings.json` (Functions host).
- Development tips:
  - Ensure the Functions host is running (VS Code task `func: host start`).
  - Azurite storage emulator files at repo root support offline development; backend endpoints work without Azure.
- Recommended SDK versions: `openai>=1.37.0` for streaming compatibility on clients.
