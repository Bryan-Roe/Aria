# Using Ollama for Local LLM

Ollama is now fully integrated and running on **port 11434**. This guide shows you how to use it across the Aria platform.

## Quick Start

**Use Ollama explicitly (recommended):**
```bash
cd /workspaces/Aria/ai-projects/chat-cli
python3 src/chat_cli.py --provider ollama --model tinyllama --once "Hello!"
```

**Or via environment variable:**
```bash
export OLLAMA_BASE_URL="http://127.0.0.1:11434/v1"
export OLLAMA_MODEL="mistral"
python3 src/chat_cli.py --once "Your question"
```

## Available Models

Current models in Ollama:
- **tinyllama:latest** (1B) - Fast, good for quick responses
- **mistral:latest** (7B) - Balanced quality & speed

Add more models:
```bash
ollama pull llama2          # Meta's Llama 2 (7B)
ollama pull neural-chat     # Intel's optimized (7B)
ollama pull orca-mini       # Microsoft's Orca (3B, very fast)
ollama pull phi             # Microsoft's Phi (2.7B)
```

## Integration Points

### 1. Chat CLI
**Direct usage:**
```bash
cd /workspaces/Aria/ai-projects/chat-cli
python3 src/chat_cli.py --provider ollama --model mistral --once "What is quantum computing?"
```

**Interactive mode:**
```bash
python3 src/chat_cli.py --provider ollama --interactive
# Type messages and press Enter to chat
# Type 'quit' or 'exit' to quit
```

### 2. Aria Web Interface
Ollama is auto-detected and used automatically:
```bash
cd /workspaces/Aria/apps/aria
python3 server.py
# Visit http://localhost:8080
# Chat uses Ollama by default
```

### 3. Azure Functions
```bash
cd /workspaces/Aria
func host start
# POST to http://localhost:7071/api/chat with {"message": "your question"}
# Automatically detects Ollama
```

### 4. Direct HTTP
```bash
curl -s http://localhost:11434/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "tinyllama",
    "messages": [{"role": "user", "content": "What is AI?"}],
    "max_tokens": 150
  }' | python3 -m json.tool
```

## Provider Detection Order

When `--provider` is **not** specified, the system auto-detects in this order:

1. **LM Studio** (if `LMSTUDIO_BASE_URL` env var set or port 1234 listening)
2. **Ollama** (if `OLLAMA_BASE_URL` env var set or port 11434 listening)
3. **Azure OpenAI** (if `AZURE_OPENAI_API_KEY` + other vars set)
4. **OpenAI** (if `OPENAI_API_KEY` set)
5. **Local fallback** (canned responses)

**To prefer Ollama over LM Studio, use explicit `--provider ollama`**

## Configuration

### Environment Variables
```bash
# Custom Ollama endpoint
export OLLAMA_BASE_URL="http://192.168.1.100:11434/v1"

# Default model to use
export OLLAMA_MODEL="mistral"

# Chat temperature (creativity 0.0-1.0)
export CHAT_TEMPERATURE="0.7"
```

### Local Settings (local.settings.json)
Add to `local.settings.json` for Azure Functions:
```json
{
  "Values": {
    "OLLAMA_BASE_URL": "http://127.0.0.1:11434/v1",
    "OLLAMA_MODEL": "tinyllama"
  }
}
```

## Troubleshooting

### Ollama not responding
```bash
# Check if Ollama is running
ps aux | grep ollama

# Restart Ollama
pkill ollama
ollama serve &

# Test connection
curl http://localhost:11434/api/tags | python3 -m json.tool
```

### Model not found
```bash
# List available models
curl http://localhost:11434/api/tags | python3 -m json.tool

# Pull missing model
ollama pull tinyllama
```

### Slow inference
- Use smaller models: `tinyllama`, `orca-mini`, `phi`
- Reduce `max_tokens` in queries
- Check system resources: `top`, `nvidia-smi` (if GPU available)

## Making Ollama Persistent

### Option A: systemd Service
```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Option B: Dev Container Startup
Edit `.devcontainer/devcontainer.json`:
```json
{
  "postStartCommand": "nohup ollama serve > /tmp/ollama.log 2>&1 &"
}
```

### Option C: Background Process with nohup
```bash
nohup ollama serve > /tmp/ollama.log 2>&1 &
```

### Option D: tmux Session
```bash
tmux new-session -d -s ollama 'ollama serve'
# Restore later: tmux attach -t ollama
```

## Performance Tips

1. **Use tinyllama for quick testing** - 1B model responses in < 5 seconds
2. **Pin model in environment** - `OLLAMA_MODEL=tinyllama` avoids fallback
3. **Increase timeout for mistral** - 7B model can take 10-30 seconds
4. **Use GPU if available** - Ollama auto-detects NVIDIA/AMD GPUs
5. **Monitor resources** - Keep an eye on RAM/CPU during inference

## API Compatibility

Ollama provides **OpenAI-compatible API**, so any OpenAI client works:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:11434/v1",
    api_key="ollama"  # Dummy key, not validated
)

response = client.chat.completions.create(
    model="tinyllama",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100
)

print(response.choices[0].message.content)
```

## When to Use Ollama

✅ **Good for:**
- Local development (no API keys needed)
- Privacy-sensitive work (no cloud calls)
- Testing chat integrations
- Iterating on prompts
- Running offline

❌ **Limitations:**
- Slower than commercial APIs (2-20x depending on model)
- Results quality lower than GPT-4/Claude
- Limited context window (typically 2K-4K tokens)
- Requires local resources

## Status Check

```bash
# List all models with sizes
ollama list

# Check Ollama endpoint
curl http://localhost:11434

# Monitor Ollama logs
tail -f /tmp/ollama.log
```

---

**Ollama is currently running and ready to use.** Start with `--provider ollama --model tinyllama` for fastest results or `--model mistral` for better quality with longer latency.
