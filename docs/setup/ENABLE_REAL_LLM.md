# Enabling Real LLM for Multi-Agent Mode

Choose one of these three options:

## Option 1: Ollama (Local, Recommended for Development)

### Quick Start (Host Machine)

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama serve &
sleep 2
ollama pull mistral  # or: neural-chat, codellama

# Windows: Download from https://ollama.ai/download
```

### From Dev Container

```bash
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --task "Add docstrings to shared/chat_memory.py" \
  --task "Improve error handling in shared/chat_providers.py" \
  --llm-type ollama \
  --model mistral \
  --workers 2 \
  --verbose
```

---

## Option 2: Azure OpenAI (Enterprise)

### Azure Setup

1. Edit `local.settings.json`:

```json
{
  "Values": {
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "your-api-key",
    "AZURE_OPENAI_DEPLOYMENT": "deployment-name",
    "AZURE_OPENAI_API_VERSION": "2024-02-15-preview"
  }
}
```

1. Run multi-agent with Azure:

```bash
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --task "Your task here" \
  --llm-type azure \
  --workers 2 \
  --verbose
```

---

## Option 3: OpenAI API

### OpenAI Setup

1. Edit `local.settings.json`:

```json
{
  "Values": {
    "OPENAI_API_KEY": "sk-..."
  }
}
```

1. Run multi-agent with OpenAI:

```bash
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --task "Your task here" \
  --llm-type openai \
  --model gpt-4 \
  --workers 2 \
  --verbose
```

---

## Model Recommendations by Speed/Cost

**Fastest (Local):**

- Mistral 7B (excellent code understanding)
- Neural-Chat 7B (optimized for conversation)

**Balanced:**

- GPT-4 Turbo (powerful, uses Token)
- GPT-3.5 Turbo (fast, cheaper)

**Most Detailed:**

- GPT-4 (highest quality)
- Codellama 13B (code specialist)
