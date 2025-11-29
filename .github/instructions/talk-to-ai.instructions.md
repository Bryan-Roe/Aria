---
name: "Chat-CLI-workspace"
description: "Slim instructions for talk-to-ai/"
applyTo: "talk-to-ai/**"
---
# Chat CLI – workspace-specific guidance

- Provider detection order (see `shared/chat_providers.py:detect_provider()`): Azure OpenAI → OpenAI → LoRA → Local.
  - Azure requires ALL: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
- CLI usage examples:
  - Local (no keys): `python .\\talk-to-ai\\src\\chat_cli.py --provider local --once "Hello"`
  - OpenAI: set `$env:OPENAI_API_KEY`; then `--provider openai`
  - Azure: set the 4 env vars; then `--provider azure`
  - LoRA: `python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model <adapter_dir>`
- Streaming responses supported; interactive commands: `/new`, `/save`, `/exit`. Conversations persisted as JSONL.
- Abstraction pattern: implement `BaseChatProvider.complete(messages, stream)`; wire detection in `shared/chat_providers.py`.
- LoRA provider requirements: adapter directory must contain `adapter_config.json` and `adapter_model.safetensors`.
- Web integration: Azure Functions serves `/api/chat` and `/api/chat-web`; check `/api/ai/status` for provider readiness (env vars, LoRA, SQL/Cosmos status).
- Secrets & local dev: never hardcode secrets; use `local.settings.json` (dev) or environment variables; Azurite storage files are present at repo root for offline testing.
- Tests: quick validation via `python .\\scripts\\test_runner.py --unit` or `pytest -m "not slow and not azure"`.
