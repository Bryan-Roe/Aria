---
name: chat-cli-debug-workflow
description: "Debug chat CLI provider selection, streaming output, JSONL conversation persistence, LoRA adapter loading, and Azure Functions web integration for the ai-projects/chat-cli module. Use when the CLI picks the wrong provider, streaming output breaks, /new or /save commands fail, LoRA adapter won't load, or /api/chat returns unexpected errors."
argument-hint: "Describe the symptom: wrong provider auto-selected, streaming broken, conversation not saved, LoRA adapter missing files, /api/chat endpoint error, or interactive command not working."
---

# Chat CLI Debug Workflow

## What This Skill Produces
- Root cause for provider detection or fallback failures in `ai-projects/chat-cli/`
- Diagnosis of SSE streaming format errors (missing `[DONE]` sentinel, bad JSON lines)
- Verification of LoRA adapter file requirements
- Targeted fix for JSONL conversation persistence and interactive command handling

## When to Use

Trigger phrases:
- "chat CLI picked the wrong provider"
- "CLI fell back to local when it shouldn't"
- "streaming output broken from chat CLI"
- "LoRA adapter won't load in CLI"
- "conversation not saved after /save"
- "/new command doesn't reset context"
- "SSE events malformed"
- "[DONE] sentinel missing"
- "/api/chat returns 500"
- "chat CLI smoke test failing"
- "Azure env vars set but still using OpenAI"
- "JSONL conversation file corrupt"

## Procedure

### Step 1 — Run the smoke test first
```bash
# Quickest sanity check — local provider, no API keys needed:
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello"

# Expected output: echoed response from local fallback provider
# If this fails: Python environment or import path is broken
```

### Step 2 — Verify provider detection order
The detection chain in `shared/chat_providers.py:detect_provider()` runs in order:
1. **Azure OpenAI** — requires ALL 4 env vars:
   ```
   AZURE_OPENAI_API_KEY
   AZURE_OPENAI_ENDPOINT
   AZURE_OPENAI_DEPLOYMENT
   AZURE_OPENAI_API_VERSION
   ```
2. **OpenAI** — requires `OPENAI_API_KEY`
3. **LoRA** — explicit `--provider lora --model <adapter_dir>`
4. **Local** — always available, zero-dependency fallback

```bash
# Check which env vars are present:
echo "Azure key: ${AZURE_OPENAI_API_KEY:+set}"
echo "Azure endpoint: ${AZURE_OPENAI_ENDPOINT:+set}"
echo "Azure deployment: ${AZURE_OPENAI_DEPLOYMENT:+set}"
echo "Azure version: ${AZURE_OPENAI_API_VERSION:+set}"
echo "OpenAI key: ${OPENAI_API_KEY:+set}"

# OR: check /api/ai/status for authoritative provider readiness:
curl http://localhost:7071/api/ai/status | python -m json.tool
```

### Step 3 — Check LoRA adapter directory contents
```bash
# LoRA adapter MUST contain BOTH files — missing either = load failure:
ls -la <adapter_dir>/
# Required:
#   adapter_config.json        ← architecture config
#   adapter_model.safetensors  ← fine-tuned weights

# Run with LoRA:
python ai-projects/chat-cli/src/chat_cli.py --provider lora --model <adapter_dir>
```

### Step 4 — Debug SSE streaming format
```python
# Streaming providers must emit:
# One SSE line per token chunk:
data: {"delta": "Hello", "done": False}

# Followed by done sentinel:
data: [DONE]

# Clients that expect plain text chunks (not SSE) will break.
# Check web/chat-web/chat.js consumer — it must parse SSE correctly.
# Verify backend: /api/chat emits SSE, /api/chat-web serves the HTML shell.
```

### Step 5 — Inspect JSONL persistence
```python
# Conversations are saved to JSONL on /save:
# Format: one JSON object per line, each with {"role": "...", "content": "..."}

# If file is corrupt or missing:
# 1. Check write permissions on the output directory
# 2. Ensure /save was called before /exit
# 3. Interactive commands: /new (reset), /save (persist), /exit (quit)
```

### Step 6 — Verify web integration endpoints
```bash
# The CLI providers are also exposed via Azure Functions:
# /api/chat        → streaming chat SSE
# /api/chat-web    → HTML chat UI shell
# /api/ai/status   → provider readiness diagnostics

# If /api/chat returns 500:
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' -v

# Compare against direct CLI smoke test to isolate Functions vs provider issue
```

### Step 7 — Check local.settings.json vs real env vars
```json
// local.settings.json (dev only — never commit real keys):
{
  "IsEncrypted": false,
  "Values": {
    "AZURE_OPENAI_API_KEY": "...",
    "AZURE_OPENAI_ENDPOINT": "https://...",
    "AZURE_OPENAI_DEPLOYMENT": "gpt-4o",
    "AZURE_OPENAI_API_VERSION": "2024-02-01"
  }
}
// Azure Functions host reads this file automatically in local dev
// CLI reads from OS env vars directly — local.settings.json has no effect on CLI
```

## Quality Checks
- [ ] Smoke test passes: `--provider local --once "Hello"` produces output
- [ ] All 4 Azure env vars present if Azure provider expected
- [ ] LoRA adapter dir contains BOTH `adapter_config.json` + `adapter_model.safetensors`
- [ ] SSE streaming emits `data: {...}` lines then `data: [DONE]` sentinel
- [ ] `/api/ai/status` confirms correct active provider
- [ ] `local.settings.json` not used as source for CLI env vars
- [ ] Tests run: `python scripts/test_runner.py --unit`
