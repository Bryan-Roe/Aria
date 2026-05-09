# LM Studio MCP Agent Integration Guide

## Overview

This guide shows how to use LM Studio with Aria's AI agent system. The LM Studio MCP server can be integrated with:

- **Aria's AGI provider** — Multi-agent routing and reasoning
- **Chat CLI** — Direct agent usage
- **Custom agents** — Build your own agent workflows
- **Function App** — API endpoint for agents

## Quick Start

### 1. Start LM Studio & MCP Server

```bash
# Terminal 1: Start LM Studio (https://lmstudio.ai)
# - Open LM Studio app
# - Load a model (e.g., Mistral 7B)
# - Enable "Local Server"

# Terminal 2: Start MCP server
cd ai-projects/lmstudio-mcp
python lmstudio_mcp_server.py
```

### 2. Use with Chat CLI

```bash
# List available models
python -m chat_cli --provider lmstudio --list-models

# Chat with LM Studio
python -m chat_cli --provider lmstudio "What is quantum computing?"

# With specific model
export LMSTUDIO_MODEL=mistral-7b
python -m chat_cli --provider lmstudio "Explain AI training"

# Streaming mode
python -m chat_cli --provider lmstudio --stream "Tell me a story"
```

### 3. Use with AGI Provider

The AGI provider can automatically route complex queries to LM Studio when appropriate:

```python
from agi_provider import detect_provider

# Detect will include LM Studio in provider options
provider, choice = detect_provider(provider_choice="lmstudio")

# Use with simple message
response = provider.complete([
    {"role": "user", "content": "Explain neural networks"}
])
```

## Agent Integration

### Register LM Studio Agent

Add LM Studio to the agent registry:

```python
# In your main script or agi_provider initialization
from lmstudio_agent_integration import register_lmstudio_agent
from agi_provider import _AGENT_REGISTRY

# Register the agent
register_lmstudio_agent(_AGENT_REGISTRY)

# Now agents will automatically consider LM Studio
```

### Agent Capabilities

The LM Studio agent is registered with:

- **Domains**: technical, coding, ai, general
- **Intents**: explanation, coding, question, creation
- **Features**: streaming, temperature control, token budgeting, model switching
- **Profile**: "Local LM Studio instance — fast, private, no cloud dependencies"

### When LM Studio Agent is Selected

LM Studio agent is automatically selected when:

1. User explicitly asks for "local model" or "offline"
2. Query mentions privacy, self-hosted, or no cloud
3. No other provider is explicitly specified and LM Studio is available

### Custom Agent Logic

Route to LM Studio with custom logic:

```python
from lmstudio_agent_integration import should_use_lmstudio

def select_provider(query: str):
    if should_use_lmstudio(query):
        return "lmstudio"
    # ... other logic
```

## Usage Examples

### Example 1: Direct Agent Client

```python
import asyncio
from lmstudio_agent_integration import get_lmstudio_agent_client

async def main():
    client = get_lmstudio_agent_client()

    # Check health
    healthy = await client.check_health()
    print(f"Server healthy: {healthy}")

    # List models
    models = await client.list_models()
    print(f"Models: {models}")

    # Send message
    response = await client.complete(
        messages=[
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello!"}
        ],
        temperature=0.7
    )
    print(f"Response: {response}")

asyncio.run(main())
```

### Example 2: Integration with AGI Provider

```python
from agi_provider import AGIProvider, detect_provider
from lmstudio_agent_integration import register_lmstudio_agent, _AGENT_REGISTRY

# Register LM Studio agent
register_lmstudio_agent(_AGENT_REGISTRY)

# Create AGI provider
base_provider, _ = detect_provider("lmstudio")
agi = AGIProvider(base_provider=base_provider)

# Use multi-agent reasoning
response = agi.reason(
    "Explain quantum entanglement in simple terms",
    trace=True,  # Show reasoning
    decompose=True  # Break into subtasks
)
print(response)
```

### Example 3: Custom Multi-Agent Workflow

```python
from lmstudio_agent_integration import get_lmstudio_agent_client
import asyncio

async def multi_agent_workflow():
    client = get_lmstudio_agent_client()

    # Agent 1: Technical Explanation
    tech_response = await client.complete(
        messages=[
            {"role": "system", "content": "You are a technical expert."},
            {"role": "user", "content": "What is machine learning?"}
        ],
        temperature=0.3  # Deterministic
    )

    # Agent 2: Simplification
    simple_response = await client.complete(
        messages=[
            {"role": "system", "content": "Simplify complex technical content."},
            {"role": "user", "content": f"Simplify: {tech_response}"}
        ],
        temperature=0.5
    )

    print("Technical:", tech_response)
    print("Simplified:", simple_response)

asyncio.run(multi_agent_workflow())
```

### Example 4: Model Selection

```python
from lmstudio_agent_integration import get_lmstudio_agent_client
import asyncio

async def compare_models():
    client = get_lmstudio_agent_client()

    # Get available models
    models = await client.list_models()

    # Compare responses from different models
    for model in models:
        response = await client.complete(
            messages=[{"role": "user", "content": "What is AI?"}],
            model=model,
            max_tokens=256
        )
        print(f"\n{model}:\n{response}")

asyncio.run(compare_models())
```

## Configuration

### Environment Variables

```bash
# Server endpoint
export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1

# Default model
export LMSTUDIO_MODEL=mistral-7b

# Sampling temperature (0.0-2.0)
export LMSTUDIO_TEMPERATURE=0.7

# Max response tokens
export LMSTUDIO_MAX_TOKENS=2048
```

### Dynamic Configuration

```python
from lmstudio_agent_integration import LMStudioAgentClient

# Custom configuration
client = LMStudioAgentClient(
    base_url="http://192.168.1.100:1234/v1",
    model="mistral-7b",
    temperature=0.5,
    max_tokens=4096
)

# Use with custom settings
response = await client.complete(
    messages=[...],
    temperature=0.3,  # Override default
    max_tokens=512    # Override default
)
```

## Integration with Function App

### Chat Endpoint with LM Studio

```python
# In function_app.py
from lmstudio_agent_integration import get_lmstudio_agent_client
import asyncio

@app.route(route="api/chat", methods=["POST"])
async def chat(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()
    provider = body.get("provider", "auto")

    if provider == "lmstudio":
        client = get_lmstudio_agent_client()

        messages = body.get("messages", [])
        response = await client.complete(messages)

        return func.HttpResponse(
            json.dumps({"response": response}),
            status_code=200
        )
```

## Troubleshooting

### Error: "Cannot connect to LM Studio"

```bash
# Check LM Studio is running
curl http://127.0.0.1:1234/v1/models

# Check environment variables
echo $LMSTUDIO_BASE_URL
echo $LMSTUDIO_MODEL

# Verify server is enabled in LM Studio UI
```

### Error: "Model not found"

```bash
# List available models
python -m lmstudio_mcp_server list-models

# Or check via API
curl http://127.0.0.1:1234/v1/models | jq .data[].id

# Update LMSTUDIO_MODEL
export LMSTUDIO_MODEL=<actual-model-name>
```

### Slow Responses

```bash
# Reduce max tokens
export LMSTUDIO_MAX_TOKENS=256

# Reduce temperature for faster inference
export LMSTUDIO_TEMPERATURE=0.3

# Check available system RAM/VRAM
```

## Performance Tips

1. **Keep models loaded** — Load model in LM Studio once, reuse
2. **Tune temperature** — Lower = faster & more deterministic
3. **Batch requests** — Send multiple completions async
4. **Monitor tokens** — Reduce max_tokens if not needed
5. **Use local endpoint** — Network latency matters

## Security Notes

- LM Studio uses default "lm-studio" API key (no real auth)
- Recommended for localhost or private networks only
- For remote access, use SSH tunneling or firewall rules
- No data persistence by default — responses not logged

## Architecture

```
┌─────────────────────┐
│   Your Agent        │
│   (multi-agent)     │
└──────────┬──────────┘
           │
┌──────────▼──────────────────────┐
│ lmstudio_agent_integration       │
│ - LMStudioAgentClient            │
│ - Agent registration             │
│ - Routing logic                  │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ lmstudio_mcp_server (MCP)        │
│ - list_models                    │
│ - chat_completion                │
│ - server_status                  │
└──────────┬──────────────────────┘
           │ HTTP/REST
┌──────────▼──────────────────────┐
│ LM Studio Local Server            │
│ /v1/models                       │
│ /v1/chat/completions             │
└──────────┬──────────────────────┘
           │
┌──────────▼──────────────────────┐
│ Local LLM Models                 │
│ (Mistral, LLaMA, etc)            │
└──────────────────────────────────┘
```

## Next Steps

1. ✅ Start LM Studio app
2. ✅ Load a model
3. ✅ Start MCP server: `python lmstudio_mcp_server.py`
4. ✅ Test with CLI: `python -m chat_cli --provider lmstudio "test"`
5. ✅ Integrate with agents (see examples above)
6. ✅ Build custom workflows

## Resources

- **LMStudio Docs**: https://lmstudio.ai
- **MCP Protocol**: https://modelcontextprotocol.io
- **Aria AGI Provider**: See `ai-projects/chat-cli/src/agi_provider.py`
- **Examples**: Run `python lmstudio_agent_integration.py`

---

**Happy local agent development!** 🚀
