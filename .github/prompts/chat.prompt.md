---
description: "Multi-provider chat with memory injection and streaming"
name: "Chat"
argument-hint: "Message + optional provider and memory context (example: provider + message or question)"
agent: chat-provider
---
# Chat

Start a chat conversation using the Aria platform's multi-provider system with semantic memory.

## Pipeline

1. **Provider auto-detection**: Azure OpenAI → OpenAI → LMStudio → LoRA → Local
2. **Memory injection**: Embed user message → fetch similar past messages → inject as context
3. **Token pruning**: Fit conversation within context window budget
4. **Streaming**: SSE-based response delivery with movement tag extraction
5. **Self-learning**: Log conversation to JSONL for future training

## Provider Configuration

| Provider | Required Env Vars |
| ---------- | ------------------ |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION` |
| OpenAI | `OPENAI_API_KEY` |
| LMStudio | `LMSTUDIO_BASE_URL` |
| LoRA | `--provider lora` + adapter path |
| Local | None (zero-dependency fallback) |

## Memory Modes

- **Semantic memory**: Cosine similarity search on embeddings
- **Session memory**: Scoped to current session_id
- **No memory**: Stateless single-turn

## Usage

```
Chat with: {{input}}

Using provider: [auto-detect | azure | openai | lmstudio | lora | local]
Memory: [enabled | disabled]
Streaming: [yes | no]
```

## Endpoints

- `POST /api/chat` — Standard chat with memory injection
- `POST /api/chat/stream` — SSE streaming with movement commands
- `GET /api/ai/status` — Check active provider and system health
