# Local LLM Setup Guide - Complete

This guide walks through setting up **4 local LLM options** for running Aria without cloud APIs.

---

## Option 1: LMStudio (Fastest Local-Only)

**Why:** Simplest setup, OpenAI API-compatible, runs locally without dependencies.

### 1.1 Installation

1. **Download LMStudio**
   - Windows: https://lmstudio.ai/ (installer)
   - macOS: Homebrew or direct download
   - Linux: Direct download

2. **Launch LMStudio**
   - Open the application
   - Go to **Chat** tab (left sidebar)
   - Look for **"Local Server"** section at top-right

### 1.2 Download a Model

In LMStudio, click the **search icon** (magnifying glass) to browse models:

**Recommended for Aria (smallest to largest):**
- `Phi-3-mini-4k-instruct` (3.8GB) — Fastest, minimal setup
- `Qwen2.5-7B-Instruct` (4.7GB) — Balanced speed/quality  
- `Llama-2-7B-Chat` (3.5GB) — Good all-rounder
- `Mistral-7B-Instruct` (4.1GB) — Fast reasoning

**Download steps:**
1. Search for model name (e.g., "Phi-3-mini")
2. Click the ⬇️ **Download** button
3. Wait for download to complete (shows in **My Models**)

### 1.3 Start Local Server

1. Click **Local Server** tab in LMStudio
2. Select your model from dropdown (e.g., "Phi-3-mini")
3. Click **"Start Server"** button
4. Wait for status to show: `Server is running on http://127.0.0.1:1234`

**Verify it's running:**
```bash
curl http://127.0.0.1:1234/v1/models
```
Should return a JSON list of available models.

### 1.4 Configure Aria to Use LMStudio

Edit your `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "LMSTUDIO_BASE_URL": "http://127.0.0.1:1234/v1",
    "LMSTUDIO_MODEL": "phi-3-mini-instruct",
    "QAI_ENABLE_LOCAL_TTS": "true"
  }
}
```

### 1.5 Test LMStudio Provider

```bash
# Quick test
python src/chat/chat_cli.py --provider lmstudio --once "Hello, what can you do?"

# Or use function app
curl http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "provider": "lmstudio"}'
```

### 1.6 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Ensure LMStudio server is running (`Local Server` tab active) |
| "Model not found" | Verify model is downloaded in `My Models` and selected in dropdown |
| Slow responses | Use smaller model (Phi-3-mini) or reduce `max_output_tokens` |
| Port 1234 already in use | Change port: LMStudio Settings → Server Port (then update `LMSTUDIO_BASE_URL`) |

---

## Option 2: LoRA Adapter (Fine-Tuned Local Models)

**Why:** Deploy your own fine-tuned Phi-3.5/Qwen without cloud training.

### 2.1 Quick Start (Use Existing Adapter)

If you have a pre-trained LoRA adapter:

```bash
# Directory structure must have both:
# my_adapter/
#   ├── adapter_config.json
#   └── adapter_model.safetensors

python src/chat/chat_cli.py --provider lora --model ./path/to/adapter "Your prompt here"
```

### 2.2 Train Your Own LoRA Adapter

**Prerequisites:**
```bash
cd AI/microsoft_phi-silica-3.6_v1
pip install -r requirements.txt
```

**Quick Training (5-10 min):**
```bash
python scripts/training/lora_quick_train.py \
  --base-model microsoft/phi-3.5-mini-instruct \
  --adapter-output ./my_adapter \
  --epochs 1 \
  --batch-size 2 \
  --device cuda
```

**Dry-run first (validates config):**
```bash
python scripts/training/lora_quick_train.py \
  --base-model microsoft/phi-3.5-mini-instruct \
  --dry-run
```

### 2.3 What Gets Created

After training, you'll have:

```
my_adapter/
├── adapter_config.json       # LoRA config (must exist)
├── adapter_model.safetensors # Model weights (must exist)
├── training_args.json        # Training parameters
└── README.md                 # Summary
```

### 2.4 Deploy Adapter

Edit `local.settings.json` to use your adapter:

```json
{
  "Values": {
    "QAI_DEFAULT_PROVIDER": "lora",
    "QAI_LORA_ADAPTER": "./my_adapter"
  }
}
```

**Or use it directly:**
```bash
python src/chat/chat_cli.py --provider lora --model ./my_adapter "Your prompt"
```

### 2.5 Advanced: Grid Search Training

Run multiple adapter configurations automatically:

```bash
python scripts/training/grid_search_lora.py \
  --config config/training/grid_search.yaml \
  --output-dir ./adapters_grid
```

This trains 5-10 adapters with different learning rates/batch sizes, saves all to `adapters_grid/`, and ranks by perplexity.

### 2.6 Troubleshooting

| Issue | Solution |
|-------|----------|
| "adapter_config.json not found" | Ensure **both** `adapter_config.json` AND `adapter_model.safetensors` exist |
| CUDA out of memory | Reduce `--batch-size` to 1 or use `--device cpu` (slower) |
| "torch not found" | Run `pip install -r requirements.txt` in `AI/microsoft_phi-silica-3.6_v1/` |
| Model download stuck | Models auto-download from Hugging Face on first run; check network |

---

## Option 3: Local Inference (Standalone)

**Why:** Run inference without cloud APIs, no streaming needed.

### 3.1 Quick Inference Script

Create `scripts/local_inference.py`:

```python
#!/usr/bin/env python3
"""Standalone local inference without cloud APIs."""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chat.chat_providers import detect_provider

def main():
    print("=== Local LLM Inference ===")
    print("Attempting to detect provider...")
    
    try:
        provider, choice = detect_provider()
        print(f"Provider: {choice.name}")
        print(f"Model: {choice.model}")
        
        # Simple non-streaming inference
        messages = [
            {"role": "user", "content": "Explain quantum computing in one sentence."}
        ]
        
        print("\nInference output:")
        response = provider.complete(messages, stream=False)
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nSet env vars:")
        print("  LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1")
        print("  OR")
        print("  AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 3.2 Run It

```bash
python scripts/local_inference.py
```

### 3.3 Batch Inference

Process multiple prompts:

```bash
python -c "
import sys
sys.path.insert(0, '.')
from src.chat.chat_providers import detect_provider

provider, choice = detect_provider()

prompts = [
    'What is AI?',
    'Summarize quantum computing.',
    'Explain LoRA fine-tuning.',
]

for prompt in prompts:
    messages = [{'role': 'user', 'content': prompt}]
    response = provider.complete(messages, stream=False)
    print(f'Q: {prompt}')
    print(f'A: {response}\n')
"
```

### 3.4 Performance Tuning

Modify inference parameters in `src/chat/chat_providers.py`:

```python
provider = LoraLocalProvider(
    adapter_dir="./my_adapter",
    device="cuda",              # or "cpu"
    temperature=0.7,            # 0=deterministic, 1=random
    max_new_tokens=512,         # increase for longer outputs
    top_p=0.9,                  # nucleus sampling
    top_k=50,                   # top-k sampling
    repetition_penalty=1.1      # avoid repetition
)
```

---

## Option 4: Chat CLI with Local Provider (Smoke Test)

**Why:** Verify local LLM integration end-to-end.

### 4.1 Test with LMStudio

Ensure LMStudio server is running, then:

```bash
# Single message
python src/chat/chat_cli.py --provider lmstudio --once "Hello, how are you?"

# Interactive mode
python src/chat/chat_cli.py --provider lmstudio

# With streaming
python src/chat/chat_cli.py --provider lmstudio --stream
```

### 4.2 Test with LoRA Adapter

```bash
# Single message
python src/chat/chat_cli.py --provider lora --model ./my_adapter --once "Explain recursion."

# Interactive
python src/chat/chat_cli.py --provider lora --model ./my_adapter
```

### 4.3 Test Auto-Detection

Remove explicit provider (will auto-detect):

```bash
# Will use LMStudio if LMSTUDIO_BASE_URL is set
python src/chat/chat_cli.py --once "What is Python?"
```

**Detection priority:**
1. `--provider lmstudio` flag
2. `LMSTUDIO_BASE_URL` environment variable
3. Azure OpenAI (if env vars set)
4. OpenAI (if OPENAI_API_KEY set)
5. Local LoRA adapter
6. Fallback echo (deterministic, no LLM)

### 4.4 Full Integration Test

```bash
#!/bin/bash
# Test all local options

echo "=== Testing LMStudio ==="
python src/chat/chat_cli.py --provider lmstudio --once "Hello" || echo "LMStudio failed"

echo ""
echo "=== Testing LoRA ==="
python src/chat/chat_cli.py --provider lora --model ./my_adapter --once "Hello" || echo "LoRA failed"

echo ""
echo "=== Testing Auto-Detection ==="
python src/chat/chat_cli.py --once "Hello" || echo "Auto-detect failed"

echo ""
echo "All tests completed!"
```

---

## Side-by-Side Comparison

| Feature | LMStudio | LoRA | Local Echo | Cloud (Azure/OpenAI) |
|---------|----------|------|-----------|----------------------|
| Setup Time | 5 min | 10 min (quick) / 1 hr (train) | Instant | 30 min |
| Cost | Free | Free | Free | $ per API call |
| Quality | Excellent (7B+) | Custom-tuned | Deterministic | Best |
| Speed | Fast (GPU: 20 tok/s) | Fast (GPU) or Slow (CPU) | Instant | Network latency |
| Dependencies | None (standalone) | torch, transformers, peft | None | openai SDK |
| Customization | Download different models | Fine-tune on your data | Not customizable | API settings only |
| **Best For** | General chat, low latency | Domain-specific tasks | Testing, CI/CD | Production SaaS |

---

## Common Workflows

### 📝 Workflow 1: LMStudio + Chat CLI

Perfect for local development without cloud APIs.

```bash
# 1. Start LMStudio (do this once, keep running)
# (Open LMStudio app → Local Server tab → Start Server)

# 2. In VS Code terminal, run chat
python src/chat/chat_cli.py --provider lmstudio

# 3. Start typing prompts
```

### 🎯 Workflow 2: Train LoRA → Deploy

For domain-specific models.

```bash
# 1. Prepare training data
# (see AI/microsoft_phi-silica-3.6_v1/data/)

# 2. Train adapter (5-10 min)
cd AI/microsoft_phi-silica-3.6_v1
python scripts/training/lora_quick_train.py --output-dir ../../my_adapter

# 3. Use in chat
cd ../..
python src/chat/chat_cli.py --provider lora --model ./my_adapter
```

### 🚀 Workflow 3: Aria Web + LMStudio

Run Aria character with local LLM.

```bash
# 1. Start LMStudio server (keep running)

# 2. Edit local.settings.json
# Set: LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1

# 3. Start Azure Functions
func host start

# 4. In another terminal, start Aria web server
cd src/web/aria/aria_web
python server.py

# 5. Open http://localhost:8080
# Aria will use LMStudio for conversations
```

### 🧪 Workflow 4: CI/CD (No Cloud APIs)

```bash
# Run tests without AZURE_OPENAI_API_KEY or OPENAI_API_KEY
python scripts/test_runner.py --unit

# All tests fall back to LocalEchoProvider
# (deterministic, always passes)
```

---

## Performance Tips

### LMStudio
- **Bigger model = better quality but slower** (test locally first)
- Phi-3-mini = 5-10 tokens/sec (CPU), 50+ tokens/sec (GPU)
- Keep server running in background; it persists across chats

### LoRA
- Train on GPU for speed (100x faster than CPU)
- Smaller adapters (< 100MB) load instantly
- Can quantize to GGUF for mobile deployment

### Local Inference
- Set `max_new_tokens=256` for fast responses
- Use `temperature=0` for deterministic output (debugging)
- Batch prompts to amortize model loading cost

### Aria Web
- LMStudio will feel like cloud API but runs locally
- Disable auto-execute planner if generating too many tokens
- Use smaller model (Phi-3) for responsive UI

---

## Debugging

### Check Provider Detection

```bash
python -c "
from src.chat.chat_providers import detect_provider
provider, choice = detect_provider()
print(f'Provider: {choice.name}')
print(f'Model: {choice.model}')
"
```

### Check Environment

```bash
python -c "import os; print('LMSTUDIO_BASE_URL:', os.getenv('LMSTUDIO_BASE_URL')); print('LMSTUDIO_MODEL:', os.getenv('LMSTUDIO_MODEL'))"
```

### Check LMStudio Server

```bash
# Verify it's listening
curl http://127.0.0.1:1234/v1/models -s | python -m json.tool

# Should return:
# {
#   "object": "list",
#   "data": [
#     {"id": "phi-3-mini-instruct", ...}
#   ]
# }
```

### Logs

```bash
# Watch chat logs
tail -f data_out/chat.log

# Watch Aria server logs  
tail -f logs/aria_server.log
```

---

## Next Steps

- ✅ **Immediate**: Start LMStudio, test with chat CLI
- 📅 **This week**: Fine-tune LoRA adapter on custom data
- 🚀 **Later**: Deploy LoRA to production, monitor inference costs

Questions? Check `/api/ai/status` endpoint for provider health:

```bash
curl http://localhost:7071/api/ai/status | python -m json.tool
```
