---
applyTo: "**/chat_memory.py"
---

# Chat Memory — Instruction Guide

## Embedding Generation

Priority chain (first available wins):
1. **Azure OpenAI** — checks 3 endpoint patterns for embedding API
2. **OpenAI** — standard embedding API
3. **Local hash** — deterministic, fixed 256-dim, L2-normalized (offline fallback)

```python
embedding = generate_embedding(text)  # → List[float] (256+ dimensions)
```

## Storage

- Table: `[dbo].[ChatMessageEmbeddings]`
- Format: Float32 little-endian binary blobs
- Fault-tolerant: returns `None` if DB unavailable

```python
store_embedding(message_id, embedding, model="text-embedding-ada-002")
```

## Similarity Search

```python
similar = fetch_similar_messages(query_embedding, top_k=5, session_id=None)
# Returns: List[Dict] with message content, ordered by cosine similarity
# Algorithm: O(n log k) via heapq (min-heap of top-k results)
```

## Connection Pooling

- Thread-per-connection cache (thread-local storage)
- Shared pool: `MAX_POOL_SIZE = 5`
- Pre-compiled regex patterns for performance
- Graceful degradation if `QAI_DB_CONN` is unset

## Integration Pattern

```python
from shared.chat_memory import generate_embedding, fetch_similar_messages

# 1. Embed user message
embedding = generate_embedding(user_text)

# 2. Find similar past messages
similar = fetch_similar_messages(embedding, top_k=5)

# 3. Inject as system context
for i, msg in enumerate(similar):
    messages.insert(1, {"role": "system", "content": f"[Memory #{i+1}] {msg['content']}"})

# 4. Prune to fit context window
messages, stats, sys_msg = prune_messages(messages, provider, model, max_tokens)
```

## Coding Conventions

- Embedding dimension must be consistent within a deployment (mixing dimensions breaks similarity)
- Always handle `None` returns from `generate_embedding()` — DB may be unavailable
- Session-scoped queries use `session_id` parameter for isolation
- Never block on embedding storage — it's fire-and-forget with fault tolerance
