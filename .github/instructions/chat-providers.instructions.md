---
applyTo: "**/chat_providers.py"
---

# Chat Providers — Instruction Guide

## Provider Detection Chain

Order matters — first match wins:

1. **Explicit choice** — `--provider` flag or API parameter
2. **LMStudio** — if `LMSTUDIO_BASE_URL` is set
3. **Ollama** — if `OLLAMA_BASE_URL` is set (or auto-detected at `http://127.0.0.1:11434/v1`)
4. **Azure OpenAI** — needs ALL 4: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`
5. **OpenAI** — needs `OPENAI_API_KEY`
6. **Groq** — needs `GROQ_API_KEY`; auto-detected by probing `https://api.groq.com/openai/v1/models`
7. **LoRA** — explicit `--provider lora` with adapter path
8. **Local echo** — zero-dependency fallback with context-aware intent recognition

## Provider Contract (BaseChatProvider)

```python
class BaseChatProvider:
    def __init__(self, model=None, temperature=0.7, max_output_tokens=2048): ...
    def complete(self, messages: List[Dict], stream: bool = True) -> Union[str, Generator]:
        # If stream=True: yield string chunks
        # If stream=False: return complete string
```

## Key Implementations

### GroqProvider

- OpenAI-compatible provider for Groq cloud inference
- Requires `GROQ_API_KEY` (get one at https://console.groq.com/keys)
- Default model: `llama-3.1-8b-instant`; override with `GROQ_MODEL` or `--model`
- Default endpoint: `https://api.groq.com/openai/v1`; override with `GROQ_BASE_URL`
- Thread-safe availability cache (`_groq_availability_cache`, 30 s TTL)
- Friendly error messages for auth failures, connection errors, and model-not-found

### LoraLocalProvider

- Bridges torch + subprocess for local LoRA inference
- Requires `adapter_config.json` + `adapter_model.safetensors`
- Thread-safe response caching

### LocalEchoProvider

- Zero external dependencies
- Context-aware intent recognition (greetings, questions, coding)
- Deterministic responses for testing

### Streaming Pattern

```python
for chunk in provider.complete(messages, stream=True):
    yield f"data: {json.dumps({'content': chunk})}\n\n"
yield "data: [DONE]\n\n"
```

## Rate Limit Handling

- Providers implement exponential backoff on rate limits
- Automatic fallback to next provider in chain on persistent failures

## Coding Conventions

- Never hardcode API keys — always use env vars
- Always support both `stream=True` and `stream=False`
- The `shared/chat_providers.py` re-exports from `ai-projects/chat-cli/src/chat_providers.py`
- Test with `/api/ai/status` endpoint to verify provider detection
- `detect_provider()` returns tuple: `(provider_instance, provider_name)`
