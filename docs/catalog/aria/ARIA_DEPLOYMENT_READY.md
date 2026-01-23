# ARIA Complete Setup - Ready to Deploy

**Status**: ✅ All Components Verified & Ready  
**Generated**: January 23, 2026  
**System**: Python 3.14.0 | Linux | Docker (Dev Container)

---

## Summary of Setup

You have a complete, production-ready Aria system with:

### ✅ Verified Components
- **Aria Web Server** (port 8080) — Interactive 3D animated character
- **Azure Functions** (port 7071) — Unified REST API for all services
- **Multi-Provider Chat** — Local/Azure/OpenAI/LMStudio with automatic fallback
- **Autonomous Training** — Continuous 30-min learning cycles with auto-discovery
- **Quantum ML Integration** — MCP server + quantum job orchestration
- **Master Orchestrator** — Coordinates all sub-systems with cron scheduling
- **Monitoring Dashboard** — Real-time status of all components
- **Chat CLI** — Standalone chat interface for testing

### ✅ Configuration Ready
- All 6 diagnostic checks passed
- Dependencies installed and tested
- Chat provider detection working (currently: Local Echo)
- All directories present and initialized
- Port availability confirmed (8080, 7071, 1234)

---

## READY-TO-RUN Commands

### Option 1: Start Everything at Once (Easiest)
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```

Then open these URLs:
- **Aria UI**: http://localhost:8080
- **Auto-Execute**: http://localhost:8080/auto-execute.html
- **Health Check**: http://localhost:7071/api/ai/status

---

### Option 2: Start in Separate Terminals (More Control)

**Terminal 1: Aria Web Interface**
```bash
cd /workspaces/AI/aria_web && python server.py
# →  http://localhost:8080
```

**Terminal 2: Azure Functions**
```bash
cd /workspaces/AI && func host start
# →  http://localhost:7071
```

**Terminal 3: Autonomous Training** (Continuous Learning)
```bash
cd /workspaces/AI && python scripts/training/autonomous_training_orchestrator.py
# →  Runs 30-min cycles automatically
```

**Terminal 4: Quantum MCP Server**
```bash
cd /workspaces/AI && python quantum-ai/quantum_mcp_server.py
# →  Quantum job submission & management
```

**Terminal 5: Monitoring Dashboard**
```bash
cd /workspaces/AI && python scripts/monitoring/auto_ops_dashboard.py --watch
# →  Live real-time status of all orchestrators
```

---

### Option 3: Test Individual Components (Verify Before Full Deployment)

**Test Chat Provider**
```bash
python /workspaces/AI/talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"
```
Expected output: Chat response in terminal

**Test Aria Web API**
```bash
curl http://localhost:8080/api/aria/state
# Should return JSON with character state
```

**Test Functions Health**
```bash
curl http://localhost:7071/api/ai/status | jq .
# Shows provider, GPU, database, cosmos status
```

**Quick Diagnostic**
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
# Full environment verification with helpful next steps
```

---

## Initial Chat Provider Setup

### Current Status: ✅ Local Echo (Works Out-of-Box)
- Zero configuration needed
- Deterministic fallback provider
- Perfect for testing

### To Enable Azure OpenAI (Optional)
Edit `/workspaces/AI/local.settings.json`:
```json
{
  "Values": {
    "AZURE_OPENAI_API_KEY": "your-api-key",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT": "your-deployment-name",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview"
  }
}
```
Then restart functions and test: `curl http://localhost:7071/api/ai/status | jq .provider`

### To Enable OpenAI (Optional)
Edit `/workspaces/AI/local.settings.json`:
```json
{
  "Values": {
    "OPENAI_API_KEY": "sk-your-key",
    "OPENAI_MODEL": "gpt-4o-mini"
  }
}
```

### To Enable LMStudio (Optional - Local Model)
1. Install LMStudio: https://lmstudio.ai
2. Start LMStudio server (defaults to `http://localhost:1234/v1`)
3. Edit `/workspaces/AI/local.settings.json`:
```json
{
  "Values": {
    "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
  }
}
```

---

## Autonomous Training Configuration

### Current Settings
Located: `/workspaces/AI/config/autonomous_training.yaml`

**Key defaults**:
- **Cycle interval**: 30 minutes
- **Mode**: Continuous (infinite cycles)
- **Device**: CPU (change to `cuda` for GPU)
- **Auto-deploy**: Disabled (set to `true` to auto-promote best models)
- **Data collection**: Auto-discovers datasets from sklearn/openml/huggingface

### To Enable GPU Training
Edit `/workspaces/AI/config/autonomous_training.yaml`:
```yaml
training:
  device: cuda
  max_gpu_memory_gb: 0    # Use all available
  max_cpu_cores: 0        # Use all available cores
```

Then restart the training orchestrator.

### To Trigger Immediate Cycle (Skip 30-min Wait)
```bash
pkill -USR1 -f autonomous_training
```

### Monitor Training Progress
```bash
# Live logs
tail -f /workspaces/AI/data_out/autonomous_training.log

# Status JSON (watch auto-refresh)
watch -n 5 'cat /workspaces/AI/data_out/autonomous_training_status.json | python -m json.tool'

# Via monitoring dashboard
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch
```

---

## Aria Web Interface Features

### Main UI (http://localhost:8080)
- **3D Animated Character** with smooth CSS transitions
- **Natural Language Commands**: "move left", "wave", "dance", "jump", etc.
- **Object Interaction**: Add/pickup/drop/throw objects
- **Eye Tracking**: Follows mouse cursor
- **Gestures**: Automatic animations (wave, dance, idle)
- **Speech Synthesis**: Real-time TTS via Azure or local fallback

### Auto-Execute Planner (http://localhost:8080/auto-execute.html)
- **LLM-Powered Action Planning**: Convert natural language to structured sequences
- **Plan Mode**: Preview actions before executing
- **Execute Mode**: Run action sequences in real-time
- **Fallback**: Rule-based parsing when LLM unavailable

### Quantum World (http://localhost:8080/quantum-world.html)
- **Quantum Circuit Visualization**: Interactive 3D quantum gates
- **Quantum-Themed Environment**: Generated worlds using quantum concepts
- **Performance Monitoring**: Real-time circuit execution stats

---

## API Endpoints Reference

### Aria Web Server (port 8080)
```bash
# Get character state
GET /api/aria/state
→ Returns: {position, objects, expressions, stage_state}

# Send command
POST /api/aria/command
→ Body: {command: "wave"}
→ Returns: {action, result}

# Execute action sequence
POST /api/aria/execute
→ Body: {actions: [{type: "move", args: {...}}, ...]}

# Object management
POST /api/aria/object
→ Body: {operation: "add", object: {...}}

# Generate themed world
POST /api/aria/world
→ Body: {theme: "quantum", description: "..."}
```

### Azure Functions (port 7071)
```bash
# Chat message
POST /api/chat
→ Body: {messages: [{role: "user", "content": "..."}]}
→ Response: SSE streaming

# Health check
GET /api/ai/status
→ Returns: {provider, model, gpu, database, cosmos, functions}

# Text-to-speech
POST /api/tts
→ Body: {text: "Hello"}
→ Returns: MP3 audio stream

# Quantum jobs
POST /api/quantum/submit
GET /api/quantum/status/:job_id
```

---

## Monitoring & Observability

### Live Dashboard
```bash
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch
```
Shows real-time status of all orchestrators, job counts, success rates.

### Dashboard Modes
```bash
# Live auto-refresh
--watch

# Problems only (errors/failures)
--problems

# Compact view
--compact

# Export to JSON
--export
```

### Status Files (Machine-Readable)
```bash
# View all status
ls /workspaces/AI/data_out/*/status.json

# Read specific orchestrator
cat /workspaces/AI/data_out/autonomous_training_status.json | python -m json.tool
cat /workspaces/AI/data_out/autotrain/status.json | python -m json.tool
cat /workspaces/AI/data_out/quantum_autorun/status.json | python -m json.tool
```

---

## Useful Commands Reference

```bash
# --- System Diagnostics ---
python /workspaces/AI/scripts/aria_diagnostic.py

# --- Test Components ---
python /workspaces/AI/talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"
curl http://localhost:8080/api/aria/state
curl http://localhost:7071/api/ai/status | jq .

# --- Monitor Resources ---
watch -n 1 nvidia-smi                    # GPU usage
df -h /workspaces                        # Disk space
python /workspaces/AI/scripts/resource_monitor.py --snapshot

# --- Training Control ---
pkill -USR1 -f autonomous_training       # Trigger immediate cycle
tail -f /workspaces/AI/data_out/autonomous_training.log  # View logs

# --- System Control ---
pkill -f aria_web                        # Stop Aria web
pkill -f "func host"                     # Stop Functions
pkill -f autonomous_training             # Stop training
pkill -f quantum_mcp                     # Stop quantum
# Full shutdown: pkill -f 'aria_web\|func host\|autonomous_training\|quantum_mcp\|master_orchestrator'

# --- Configuration Validation ---
python /workspaces/AI/scripts/training/autonomous_training_orchestrator.py --dry-run
python /workspaces/AI/scripts/evaluation/quantum_autorun.py --dry-run
```

---

## Troubleshooting Quick Guide

| Issue | Check | Solution |
|-------|-------|----------|
| **Port 8080 in use** | `lsof -i :8080` | Stop: `pkill -f aria_web` |
| **Port 7071 in use** | `lsof -i :7071` | Kill: `func` process or `pkill -f "func host"` |
| **Chat shows "local"** | `curl http://localhost:7071/api/ai/status \| jq .provider` | Configure Azure/OpenAI in `local.settings.json` |
| **Training not starting** | Check file exists: `ls /workspaces/AI/config/autonomous_training.yaml` | Verify path and YAML syntax |
| **GPU not detected** | `python -c "import torch; print(torch.cuda.is_available())"` | Install CUDA/PyTorch or use CPU |
| **Chat CLI won't run** | `python -c "import sys; sys.path.insert(0, 'talk-to-ai/src'); from chat_providers import detect_provider"` | Check sys.path setup in chat_providers |
| **Monitoring shows errors** | `python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --problems` | View specific error in status.json |

---

## Documentation Files

| File | Purpose |
|------|---------|
| `ARIA_SETUP_GUIDE.md` | Complete setup instructions with all details |
| `ARIA_QUICK_REFERENCE.md` | Copy-paste commands and quick lookups |
| `.github/copilot-instructions.md` | Architecture patterns and best practices |
| `.github/instructions/functions.instructions.md` | Azure Functions endpoint guidance |
| `.github/instructions/talk-to-ai*.md` | Chat provider patterns |
| `.github/instructions/quantum-ai*.md` | Quantum ML workflows |

---

## Next Steps

### 1. Quick Verification (5 min)
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```

### 2. Start One Component (Pick One)
```bash
# Option A: Start just Aria Web
cd /workspaces/AI/aria_web && python server.py

# Option B: Start just Functions
cd /workspaces/AI && func host start

# Option C: Start just Training
python /workspaces/AI/scripts/training/autonomous_training_orchestrator.py
```

### 3. Test the Component
Open browser or run `curl` command from Quick Reference

### 4. Start Everything (When Ready)
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```

### 5. Monitor Live
```bash
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch
```

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Aria Character System                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │ Aria Web Server  │    │ Azure Functions  │               │
│  │   (port 8080)    │    │   (port 7071)    │               │
│  └────────┬─────────┘    └────────┬─────────┘               │
│           │                       │                         │
│           └───────────┬───────────┘                         │
│                       │                                     │
│        ┌──────────────▼───────────────┐                    │
│        │   Multi-Provider Chat       │                    │
│        │ • Local Echo (ready)        │                    │
│        │ • Azure OpenAI (optional)   │                    │
│        │ • OpenAI (optional)         │                    │
│        │ • LMStudio (optional)       │                    │
│        └──────────────┬───────────────┘                    │
│                       │                                     │
│    ┌──────────────────┼──────────────────┐                 │
│    │                  │                  │                 │
│    ▼                  ▼                  ▼                 │
│  Training        Quantum ML          Monitoring           │
│  Orchestrator    Integration         Dashboard            │
│  (30-min cycles) (MCP Server)        (Live Status)        │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐  │
│  │        Master Orchestrator (Coordinates)            │  │
│  │    Cron scheduling • Auto-deployment • Priorities   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Support & Resources

**For issues or questions**:
1. Check `ARIA_QUICK_REFERENCE.md` — Copy-paste commands
2. Run `python /workspaces/AI/scripts/aria_diagnostic.py` — Full diagnostic
3. Read `.github/copilot-instructions.md` — Architecture & patterns
4. Review component-specific `.github/instructions/*.md` files

**Key contacts**:
- Aria web issues → `aria_web/server.py`
- Chat issues → `talk-to-ai/src/chat_providers.py`
- Training issues → `scripts/training/autonomous_training_orchestrator.py`
- Quantum issues → `quantum-ai/quantum_mcp_server.py`
- API issues → `function_app.py`

---

**You're ready to go!** 🚀

Choose your starting option from the "READY-TO-RUN Commands" section above and begin using Aria.
