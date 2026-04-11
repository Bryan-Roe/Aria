# LM Studio MCP Server

Model Context Protocol (MCP) server for interacting with [LM Studio](https://lmstudio.ai) — a local LLM server that provides an OpenAI-compatible API.

## Overview

This MCP server exposes LM Studio capabilities through the Model Context Protocol, allowing AI agents and applications to:

- **List available models** on your LM Studio instance
- **Send chat completions** with full control over temperature, max tokens, and model selection
- **Check server status** and configuration
- **Stream responses** for real-time output

## Installation

### Prerequisites

- **LM Studio** running locally (or on a network accessible endpoint)
- **Python 3.8+**
- **Virtual environment** (recommended)

### Setup

1. **Install MCP dependencies:**

```bash
# From the ai-projects/lmstudio-mcp directory
pip install -r mcp-requirements.txt
```

Or install individually:

```bash
pip install "mcp>=0.9.0" httpx
```

2. **Verify LM Studio is running:**

Make sure LM Studio is started and the local server is enabled:

```bash
# Default endpoint
http://127.0.0.1:1234/v1

# Or check which endpoint is active in LM Studio UI
```

## Configuration

Configure via environment variables:

```bash
# LM Studio server endpoint (default: http://127.0.0.1:1234/v1)
export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1

# Model to use (default: local-model)
export LMSTUDIO_MODEL=mistral-7b

# Sampling temperature (default: 0.7)
export LMSTUDIO_TEMPERATURE=0.8

# Maximum tokens in response (default: 2048)
export LMSTUDIO_MAX_TOKENS=4096
```

## Running the Server

### As a Python Script

```bash
python lmstudio_mcp_server.py
```

### With Environment Variables

```bash
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1 \
LMSTUDIO_MODEL=mistral-7b \
python lmstudio_mcp_server.py
```

### In a Different Port/Network Location

```bash
LMSTUDIO_BASE_URL=http://192.168.1.100:1234/v1 \
python lmstudio_mcp_server.py
```

## Available Tools

### 1. `list_models`

List all available models on the LM Studio server.

**Input:** No parameters required

**Output:**

```json
{
  "success": true,
  "available_models": ["mistral-7b", "neural-chat-7b"],
  "total_models": 2,
  "response": { ... }
}
```

### 2. `chat_completion`

Send a chat completion request to LM Studio.

**Input:**

- `messages` (required): Array of message objects with `role` and `content`
  - `role`: "system", "user", or "assistant"
  - `content`: Message text
- `model` (optional): Model ID (uses LMSTUDIO_MODEL if not specified)
- `temperature` (optional): Sampling temperature 0.0-2.0 (default: 0.7)
- `max_tokens` (optional): Maximum response tokens (default: 2048)

**Example:**

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is quantum computing?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Output:**

```json
{
  "success": true,
  "message": "Quantum computing is...",
  "stop_reason": "stop",
  "model": "mistral-7b",
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 128,
    "total_tokens": 170
  }
}
```

### 3. `server_status`

Get LM Studio server status and configuration.

**Input:** No parameters required

**Output:**

```json
{
  "success": true,
  "status": "online",
  "base_url": "http://127.0.0.1:1234/v1",
  "loaded_models": 2,
  "current_model": "mistral-7b"
}
```

## Troubleshooting

### Connection Errors

**Error:** `Connection refused` or `Unable to connect`

**Solution:**
1. Verify LM Studio is running
2. Check that the local server is enabled in LM Studio UI
3. Confirm the endpoint matches `LMSTUDIO_BASE_URL`
4. Check firewall settings if using a remote endpoint

```bash
# Test connectivity
curl http://127.0.0.1:1234/v1/models
```

### Model Not Found

**Error:** `Model not found` or `Does not exist`

**Solution:**
1. List available models: Use the `list_models` tool
2. Load a model in LM Studio UI
3. Specify the correct model ID with `LMSTUDIO_MODEL` env var

### Slow Responses

**Tips:**
- Increase `max_tokens` if responses are being truncated
- Reduce `temperature` for more deterministic outputs
- Check LM Studio's loaded model size (larger models = slower)
- Verify system has sufficient RAM/VRAM for the model

## Integration with Aria Platform

### As a Chat Provider

LM Studio is already integrated as a chat provider in Aria:

```bash
# Use with chat CLI
python -m chat_cli --provider lmstudio --once "Hello"

# Or set environment variables
export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
export LMSTUDIO_MODEL=mistral-7b
python -m chat_cli --provider lmstudio "Tell me a story"
```

### As an MCP Tool

Use this server with GitHub Copilot or other MCP clients:

```bash
# Start the MCP server
python lmstudio_mcp_server.py

# Configure in your MCP client (e.g., Copilot configuration)
# Point to stdio channel of this process
```

## Architecture

```
┌─────────────────────────────────┐
│   MCP Client (Copilot, Agent)   │
└──────────────┬──────────────────┘
               │ MCP Protocol (stdio)
               │
┌──────────────▼──────────────────┐
│  LM Studio MCP Server           │
│  ├─ list_models()              │
│  ├─ chat_completion()          │
│  └─ server_status()            │
└──────────────┬──────────────────┘
               │ HTTP API
               │
┌──────────────▼──────────────────┐
│  LM Studio Local Server         │
│  /v1/models                     │
│  /v1/chat/completions          │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Local LLM Models               │
│  (Mistral, LLaMA, etc)          │
└─────────────────────────────────┘
```

## API Reference

### HTTP Endpoints Used

Internal communication with LM Studio uses OpenAI-compatible endpoints:

- `GET /v1/models` — List available models
- `POST /v1/chat/completions` — Send chat message

### Payload Format

Requests follow OpenAI API format:

```json
{
  "model": "mistral-7b",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

## Performance Considerations

- **Response Time:** Depends on model size and system hardware
- **Concurrency:** Handle one request at a time (configure threading if needed)
- **Memory:** Keep models loaded in VRAM for faster inference
- **Network:** Local requests are faster than remote endpoints

## Security

- **API Keys:** LM Studio doesn't require authentication (uses default "lm-studio" key)
- **Local Access:** Recommended for local development only
- **Remote Access:** Use firewall rules and VPN for production remote access
- **Data Privacy:** All processing stays on your local machine

## Example Usage

### Python Agent Integration

```python
from lmstudio_mcp_server import LMStudioClient

async def main():
    client = LMStudioClient(
        base_url="http://127.0.0.1:1234/v1",
        model="mistral-7b"
    )

    # List models
    models = await client.list_models()
    print(f"Available: {models['available_models']}")

    # Send chat message
    result = await client.chat_completion(
        messages=[
            {"role": "user", "content": "Explain quantum computing"}
        ],
        temperature=0.7
    )
    print(result['message'])

asyncio.run(main())
```

### Bash/cURL Integration

```bash
# Check server status
curl http://127.0.0.1:1234/v1/models | jq .

# Send chat message
curl http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7
  }' | jq .
```

## Contributing

To extend this server:

1. Add new tools in the `@app.list_tools()` section
2. Implement logic in `@app.call_tool()` handler
3. Test with: `python lmstudio_mcp_server.py`

## Resources

- [LM Studio Official](https://lmstudio.ai)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)

## License

Same as Aria project — see main LICENSE file
