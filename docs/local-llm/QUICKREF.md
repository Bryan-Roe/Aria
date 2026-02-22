# Local LLM Quick Reference

## TL;DR - Get Started in 5 Minutes

### Option 1: LMStudio (Recommended for Quickstart)
```bash
# 1. Download & install LMStudio from https://lmstudio.ai
# 2. Open app → Local Server tab → Download "Phi-3-mini" → Start Server
# 3. In VS Code terminal:
python src/chat/chat_cli.py --provider lmstudio --once "Hello"
```

### Option 2: Use LoRA Adapter (If Available)
```bash
python src/chat/chat_cli.py --provider lora --model ./my_adapter --once "Hello"
```

### Option 3: Quick Test (No Setup)
```bash
# Uses LocalEchoProvider (deterministic, no LLM)
python src/chat/chat_cli.py --provider local --once "Hello"
```

---

## Installation Scripts

### Interactive Setup Wizard
```bash
python scripts/setup_local_llm.py
```
Walks through: LMStudio config, LoRA adapter setup, environment variables.

### Test Local Inference
```bash
python scripts/local_inference.py
```
Runs 4 test prompts on detected local provider.

### Validate Setup
```bash
python scripts/test_local_llm.py
```
Smoke tests for all providers: imports, detection, chain priority.

---

## Environment Variables

Set in `local.settings.json`:

```json
{
  "Values": {
    "LMSTUDIO_BASE_URL": "http://127.0.0.1:1234/v1",
    "LMSTUDIO_MODEL": "phi-3-mini-instruct",
    "QAI_LORA_ADAPTER": "./my_adapter",
    "QAI_ENABLE_LOCAL_TTS": "true"
  }
}
```

---

## Common Commands

| Task | Command |
|------|---------|
| Interactive chat with LMStudio | `python src/chat/chat_cli.py --provider lmstudio` |
| Single message | `python src/chat/chat_cli.py --provider lmstudio --once "Your question"` |
| Use LoRA adapter | `python src/chat/chat_cli.py --provider lora --model ./my_adapter` |
| Auto-detect provider | `python src/chat/chat_cli.py --once "Hello"` |
| Test inference | `python scripts/local_inference.py` |
| Validate setup | `python scripts/test_local_llm.py` |
| Run Aria web UI | `cd src/web/aria/aria_web && python server.py` |
| Run Azure Functions | `func host start` |

---

## Provider Detection Priority

Auto-detection tries providers in this order (first match wins):

1. **Explicit `--provider` flag** → Use specified provider
2. **`LMSTUDIO_BASE_URL` env var** → LMStudio (offline, no API key needed)
3. **`AZURE_OPENAI_*` env vars** → Azure OpenAI
4. **`OPENAI_API_KEY`** → OpenAI API
5. **`QAI_LORA_ADAPTER`** → Local LoRA adapter
6. **Fallback** → LocalEchoProvider (deterministic, no LLM)

Example:
```bash
# Explicitly use LMStudio (even if OpenAI key is set)
OPENAI_API_KEY=sk-test python src/chat/chat_cli.py --provider lmstudio

# Auto-detect (uses LMStudio if available, then Azure, then OpenAI, etc.)
python src/chat/chat_cli.py
```

---

## LMStudio Models (Recommended)

Download in LMStudio app (search for these):

| Model | Size | Speed | Quality | Recommended For |
|-------|------|-------|---------|-----------------|
| `Phi-3-mini-instruct` | 3.8GB | ⚡ Very Fast | Good | Quick testing, resource-constrained |
| `Qwen2.5-7B-Instruct` | 4.7GB | ⚡ Fast | Excellent | Production, balanced speed/quality |
| `Llama-2-7B-Chat` | 3.5GB | ⚡ Fast | Good | General purpose |
| `Mistral-7B-Instruct` | 4.1GB | ⚡ Fast | Very Good | Reasoning tasks |

---

## Troubleshooting

### "Connection refused" / "Cannot connect"
```bash
# Check if LMStudio is running
curl http://127.0.0.1:1234/v1/models

# If it fails:
# 1. Open LMStudio app
# 2. Go to "Local Server" tab
# 3. Click "Start Server"
# 4. Select a model in dropdown
```

### "No module named 'torch'" (LoRA only)
```bash
cd AI/microsoft_phi-silica-3.6_v1
pip install -r requirements.txt
```

### Slow inference
```bash
# Use smaller model in LMStudio
# Or set max_tokens lower
python src/chat/chat_cli.py --provider lmstudio \
  --max-tokens 128 --once "Quick answer?"
```

### Check environment setup
```bash
python -c "
import os
import json
with open('local.settings.json') as f:
    cfg = json.load(f)
for key, value in cfg['Values'].items():
    if 'URL' in key or 'KEY' in key or 'LORA' in key:
        print(f'{key}={value}')
"
```

---

## Workflow Examples

### 📝 Local Development (No Cloud)
```bash
# 1. Start LMStudio server (keep running)
# (Open app → Local Server tab → Start Server)

# 2. Chat in terminal
python src/chat/chat_cli.py --provider lmstudio

# 3. Or use in Aria web
cd src/web/aria/aria_web && python server.py
# Visit http://localhost:8080
```

### 🎯 Fine-Tuning & Deployment
```bash
# 1. Train LoRA adapter
cd AI/microsoft_phi-silica-3.6_v1
python scripts/training/lora_quick_train.py --output-dir ../../my_adapter

# 2. Use the adapter
cd ../..
python src/chat/chat_cli.py --provider lora --model ./my_adapter

# 3. Deploy to functions
func host start
# API available at http://localhost:7071/api/chat
```

### 🧪 CI/CD (Automated Testing)
```bash
# Run tests without any API keys
# (uses LocalEchoProvider fallback)
python scripts/test_runner.py --unit
python scripts/test_local_llm.py
```

### 🚀 Full Stack (Web + Functions + Local LLM)
```bash
# Terminal 1: Start Azure Functions
func host start

# Terminal 2: Start Aria web UI  
cd src/web/aria/aria_web && python server.py

# Terminal 3: Monitor (optional)
python scripts/monitoring/auto_ops_dashboard.py --watch

# Then visit http://localhost:8080
```

---

## Performance Tips

| Setting | Value | Effect |
|---------|-------|--------|
| `max_new_tokens` | 128-256 | Faster, shorter responses |
| `temperature` | 0.0-0.3 | More deterministic (better for testing) |
| `temperature` | 0.7-0.9 | More creative |
| `top_p` | 0.9 | Balanced sampling |
| `device` (LoRA) | `cuda` | 10-50x faster (requires GPU) |
| `device` (LoRA) | `cpu` | Slower but works everywhere |

---

## File Structure

```
AI/
├── local.settings.json        # Your env vars (⚠ don't commit)
├── LOCAL_LLM_SETUP.md        # Full guide (this file's companion)
├── src/
│   ├── chat/
│   │   └── chat_providers.py # Provider implementations
│   └── web/aria/aria_web/
│       └── server.py          # Aria character UI
├── scripts/
│   ├── setup_local_llm.py    # Interactive setup
│   ├── local_inference.py    # Standalone inference test
│   └── test_local_llm.py     # Provider smoke tests
└── AI/microsoft_phi-silica-3.6_v1/
    └── scripts/
        └── training/          # LoRA training scripts
```

---

## API Usage (Azure Functions)

Once `func host start` is running:

### Chat with Auto-Detected Provider
```bash
curl http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "stream": false}'
```

### Specify LMStudio Provider
```bash
curl http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "lmstudio"}'
```

### Streaming Response
```bash
curl http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain neural networks", "stream": true}'
```

---

## Advanced: LoRA Adapter Training

Quick train (5-10 min):
```bash
cd AI/microsoft_phi-silica-3.6_v1
python scripts/training/lora_quick_train.py \
  --base-model microsoft/phi-3.5-mini-instruct \
  --adapter-output ../../my_adapter \
  --epochs 1 --batch-size 2
```

Dry-run (validates config, no GPU):
```bash
python scripts/training/lora_quick_train.py --dry-run
```

Grid search (multiple configs):
```bash
python scripts/training/grid_search_lora.py \
  --config config/training/grid_search.yaml
```

---

## Links

- 📖 [Full Setup Guide](./LOCAL_LLM_SETUP.md)
- 🔧 [Chat Providers Docs](./src/chat/chat_providers.py)
- 🧠 [LoRA Training Guide](./AI/microsoft_phi-silica-3.6_v1/README.md)
- 🌐 [LMStudio Official](https://lmstudio.ai)
- 📚 [Hugging Face Models](https://huggingface.co/models)

---

## Support

**Test everything works:**
```bash
python scripts/test_local_llm.py
```

**Check provider health:**
```bash
curl http://localhost:7071/api/ai/status | python -m json.tool
```

**View logs:**
```bash
tail -f data_out/chat.log
tail -f data_out/aria_server.log
```
