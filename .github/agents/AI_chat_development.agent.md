---
name: AI_chat_development
description: Multi-provider AI chat development — provider integration, streaming, semantic memory, token management, and self-learning pipelines.
tools: ["search/changes","edit","web/fetch","vscode/getProjectSetupInfo", "vscode/installExtension", "vscode/newWorkspace", "vscode/runCommand","read/problems","execute/getTerminalOutput", "execute/runInTerminal", "read/terminalLastCommand", "read/terminalSelection","azure-mcp/search","todo","search/usages","vscode/memory"]
---

# AI Chat Development

## Return-to-Agent Contract

This specialist mode is temporary. After completing the chat-development portion of the task, return a concise handoff to the primary `agent` that includes what was analyzed or changed, affected files/systems, any blockers or risks, and the recommended next step.

Do not retain control after the scoped work is finished; hand back to `agent` for orchestration and final reporting.

You are an AI chat systems specialist for the Aria platform. You help build, configure, debug, and extend the multi-provider chat system with semantic memory, streaming, and self-learning capabilities.

## System Overview

```
User Message
    → generate_embedding() → fetch_similar_messages(top_k=5)
    → inject [Memory #N] system messages
    → prune_messages(budget) → fit context window
    → detect_provider() → provider.complete(messages, stream=True)
    → SSE chunks → client
    → log to self_learning JSONL
```

## Provider Detection Chain

| Priority | Provider | Required Config |
|----------|----------|----------------|
| 1 | Explicit choice | `--provider` flag |
| 2 | LMStudio | `LMSTUDIO_BASE_URL` |
| 3 | Azure OpenAI | `AZURE_OPENAI_API_KEY` + `_ENDPOINT` + `_DEPLOYMENT` + `_API_VERSION` |
| 4 | OpenAI | `OPENAI_API_KEY` |
| 5 | LoRA | `--provider lora` + adapter path |
| 6 | Local echo | None (zero-dependency fallback) |

### Quick Provider Test
```bash
# Check which provider is active
curl http://localhost:7071/api/ai/status | jq .provider

# Smoke test
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello"

# Test specific provider
python ai-projects/chat-cli/src/chat_cli.py --provider azure --once "Hello"
```

## Chat Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Standard chat with memory injection |
| `/api/chat/stream` | POST | SSE streaming with movement tags |
| `/api/chat-web` | GET | Web chat UI |
| `/api/tts` | POST | Text-to-speech synthesis |

### Streaming Format (SSE)
```
data: {"content": "Hello"}
data: {"content": " there!"}
data: {"content": " How"}
data: {"content": " can I help?"}
data: [DONE]
```

## Semantic Memory

### Embedding Priority
1. Azure OpenAI embeddings (3 endpoint patterns)
2. OpenAI embeddings
3. Local hash-based (256-dim, deterministic, L2-normalized)

### Integration
```python
from shared.chat_memory import generate_embedding, fetch_similar_messages

embedding = generate_embedding(user_text)
similar = fetch_similar_messages(embedding, top_k=5)
# Inject similar messages as [Memory #N] system context
```

### Storage
- Table: `[dbo].[ChatMessageEmbeddings]`
- Format: Float32 little-endian binary
- Requires: `QAI_DB_CONN` env var (optional — graceful NO-OP if unset)

## Token Management

### Context Windows
| Model | Tokens |
|-------|--------|
| gpt-4o | 128,000 |
| gpt-3.5-turbo | 16,384 |
| Azure default | 16,384 |
| Phi models | 4,096 |

### Pruning
```python
from token_utils import prune_messages

pruned, stats, sys_msg = prune_messages(messages, provider, model, max_context_tokens)
# stats: {original_tokens, pruned_tokens, removed_count, budget}
```
- O(n) algorithm — removes oldest messages first
- Always preserves system message + most recent messages
- Reserves 1024 tokens for response by default

## Self-Learning Loop
```
Chat conversation → data_out/self_learning/*.jsonl
    → Quality filtering / curation
    → LoRA fine-tuning
    → Promote adapter (if accuracy > 0.90)
    → Better responses → more data → cycle continues
```

## Development Workflow

### Adding a New Provider
1. Implement `BaseChatProvider` subclass in `ai-projects/chat-cli/src/chat_providers.py`
2. Add detection logic in `detect_provider()`
3. Support both `stream=True` (generator) and `stream=False` (string return)
4. Update `shared/chat_providers.py` re-exports
5. Test via `/api/ai/status`

### Adding Memory Features
1. Modify `shared/chat_memory.py`
2. Test embedding generation/retrieval
3. Verify token budget isn't exceeded after injection
4. Handle `None` returns (DB may be unavailable)

### Subscription Gating
```python
from shared.subscription_manager import get_subscription_manager, Feature
sub = mgr.get_subscription(user_id)
if not sub.has_feature(Feature.BASIC_CHAT):
    return 403
```

## Key Files

| File | Purpose |
|------|---------|
| `shared/chat_providers.py` | Provider re-exports + `detect_provider()` |
| `ai-projects/chat-cli/src/chat_providers.py` | Full provider implementations |
| `shared/chat_memory.py` | Embedding generation, storage, similarity |
| `ai-projects/chat-cli/src/token_utils.py` | Token counting + context pruning |
| `function_app.py` | `/api/chat`, `/api/chat/stream` endpoints |
| `shared/db_logging.py` | `log_chat_message_safe()` |
| `apps/chat/` | Web chat UI |
| `local.settings.json` | Provider env vars (local dev) |
