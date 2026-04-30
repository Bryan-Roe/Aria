# Running Ollama with Multi-Agent Mode

Since the dev container has networking isolation, follow these steps:

## Option 1: Run Ollama on Host Machine (Recommended)

### macOS (Intel/Apple Silicon):
```bash
# Download installer
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Pull a code model
ollama pull mistral  # or: neural-chat, codellama, dolphin-mixtral
```

### Linux (Ubuntu/Debian):
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start as systemd service
sudo systemctl start ollama

# Pull a model
ollama pull mistral
```

### Windows:
1. Download: https://ollama.ai/download
2. Run installer
3. Ollama will auto-start on http://localhost:11434

## Option 2: After Ollama is Running on Host

From inside the dev container, run multi-agent with real LLM:

```bash
# From /workspaces/Aria
export OLLAMA_BASE_URL="http://host.docker.internal:11434"
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --task "Add comprehensive docstrings to shared/chat_memory.py" \
  --task "Modernize error handling in shared/chat_providers.py" \
  --llm-type ollama \
  --model mistral \
  --workers 2 \
  --verbose
```

## Available Models (sorted by speed):

**Fast (good for code tasks):**
- `mistral` - 7B, excellent code understanding
- `neural-chat` - 7B, optimized for chat
- `dolphin-mixtral` - High quality reasoning

**Balanced:**
- `llama2` - 7B, general purpose
- `codellama` - 7B, specialized for code

**Detailed (slower):**
- `llama2:13b` - 13B parameters
- `mixtral` - 8x7B, very capable

## From Container Terminal:

Once Ollama is running on host:

```bash
# Test connection to host Ollama
curl http://host.docker.internal:11434/api/tags

# Run multi-agent with real LLM
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --tasks-file data_out/multi_agent_run_tasks.json \
  --llm-type ollama \
  --model mistral \
  --workers 3 \
  --verbose
```

## Current Status

Multi-agent mode is ready for real LLM - just need Ollama running on host!
