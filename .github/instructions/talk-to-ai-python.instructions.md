---
name: "Chat-CLI-Python"
description: "Python-specific guidance for talk-to-ai/"
applyTo: "talk-to-ai/src/**/*.py"
---
# Chat CLI – Python files

- Provider detection order (see `shared/chat_providers.py:detect_provider()`): Azure OpenAI → OpenAI → LoRA → Local.
  - Azure requires ALL: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
- Implement providers by subclassing `BaseChatProvider` and implementing `complete(messages, stream)`.
- Streaming support: emit SSE lines (`data: {json}`) and `[DONE]` sentinel; clients must parse SSE correctly.
- CLI usage examples:
  - Local: `python .\\talk-to-ai\\src\\chat_cli.py --provider local --once "Hello"`
  - OpenAI: set `$env:OPENAI_API_KEY`; then `--provider openai`
  - Azure: set the 4 env vars; then `--provider azure`
  - LoRA: `python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model <adapter_dir>`
- LoRA adapter directory must contain BOTH `adapter_config.json` and `adapter_model.safetensors`.
- Conversations persisted in JSONL; interactive commands: `/new`, `/save`, `/exit`.
- Functions endpoints for web integration: `/api/chat`, `/api/chat-web`; check `/api/ai/status` for provider readiness.
- Secrets and local dev: prefer `local.settings.json` or env vars; Azurite storage files exist at repo root for offline testing.
- Tests: `python .\\scripts\\test_runner.py --unit` for quick validation.
