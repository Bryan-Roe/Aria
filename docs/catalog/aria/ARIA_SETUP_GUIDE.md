# Aria Complete Setup Guide
**Generated: January 23, 2026**

This guide walks you through setting up all Aria components: web interface, multi-provider chat, autonomous training, and quantum ML integration.

---

## 1. Environment Verification ✓

**Status**: Python 3.14.0 detected
```bash
Python: /usr/local/bin/python
Projects verified:
  ✓ aria_web/ (web server)
  ✓ talk-to-ai/src/ (chat CLI & providers)
  ✓ quantum-ai/src/ (quantum ML)
```

---

## 2. Multi-Provider Chat Configuration

### Current Status
- **Detected Provider**: Local Echo (fallback)
- **Provider Chain**: 
  1. LMStudio (if `LMSTUDIO_BASE_URL` set)
  2. Azure OpenAI (if all 4 vars set)
  3. OpenAI (if `OPENAI_API_KEY` set)
  4. LoRA adapter (explicit `--provider lora`)
  5. Local Echo (zero dependencies, always available)

### Setup Steps

#### Option A: Use Local Echo (No Configuration Needed)
Already working! Test with:
```bash
python talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"
```

#### Option B: Configure Azure OpenAI
Edit `local.settings.json`:
```json
{
  "Values": {
    "AZURE_OPENAI_API_KEY": "your-key-here",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT": "your-deployment-name",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview"
  }
}
```

Then test:
```bash
python talk-to-ai/src/chat_cli.py --provider azure --once "Hello"
```

#### Option C: Configure OpenAI
Edit `local.settings.json`:
```json
{
  "Values": {
    "OPENAI_API_KEY": "sk-...",
    "OPENAI_MODEL": "gpt-4o-mini"
  }
}
```

Then test:
```bash
python talk-to-ai/src/chat_cli.py --provider openai --once "Hello"
```

#### Option D: Configure LMStudio (Local Model)
1. Install LMStudio from https://lmstudio.ai
2. Start LMStudio server (listens on `http://localhost:1234/v1`)
3. Edit `local.settings.json`:
```json
{
  "Values": {
    "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
  }
}
```

Then test:
```bash
python talk-to-ai/src/chat_cli.py --provider lmstudio --once "Hello"
```

### Verify Provider Detection
```bash
curl http://localhost:7071/api/ai/status | jq '.provider'
```

---

## 3. Aria Web Interface Setup

### Quick Start
```bash
cd aria_web && python server.py
# Server starts on http://localhost:8080
```

### Web Interfaces Available
- **Main UI**: http://localhost:8080
  - 3D animated character
  - Natural language commands: "move left", "wave", "dance", "jump"
  - Object interaction and gestures

- **Auto-Execute Planner**: http://localhost:8080/auto-execute.html
  - LLM-powered action sequence planning
  - Plan mode (preview) and execute mode (run)
  - Works with any provider

- **Quantum 3D World**: http://localhost:8080/quantum-world.html
  - Quantum circuit visualization
  - Interactive quantum gates

### Example Commands
```
move left
move right
wave
dance
jump
pickup ball
throw
say hello
look around
```

### Server Endpoints
- `GET /api/aria/state` — Current character position & objects
- `POST /api/aria/command` — Process natural language
- `POST /api/aria/execute` — Run action sequences
- `POST /api/aria/object` — Add/remove/update objects
- `POST /api/aria/world` — Generate themed worlds

---

## 4. Autonomous Training Setup

### Current Configuration
File: `config/autonomous_training.yaml`

**Key Settings**:
- **Cycle Interval**: 30 minutes
- **Mode**: Continuous (infinite cycles)
- **Device**: CPU (set to `cuda` for GPU)
- **Epochs**: Progressive [25, 50, 100, 200]
- **Auto-deploy**: Disabled (set `true` to auto-deploy best models)

### Start Autonomous Training

#### Quick Start (Background Process)
```bash
nohup python scripts/training/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &
```

#### With Monitoring
```bash
# Terminal 1: Start training
python scripts/training/autonomous_training_orchestrator.py

# Terminal 2: Monitor status (watch auto-refresh)
python scripts/monitoring/auto_ops_dashboard.py --watch
```

#### Manual Cycle Trigger
Force immediate training cycle (skip 30-min wait):
```bash
pkill -USR1 -f autonomous_training
```

### Monitor Progress
```bash
# View live logs
tail -f data_out/autonomous_training.log

# View status JSON
watch -n 5 'cat data_out/autonomous_training_status.json | python -m json.tool'

# Check dashboard
python scripts/monitoring/auto_ops_dashboard.py --watch
```

### Status File
Location: `data_out/autonomous_training_status.json`

Tracks:
- Total datasets discovered
- Training epochs & accuracy
- Auto-deployment status
- Error count & recovery

---

## 5. Azure Functions & APIs

### Start Function App
```bash
func host start
# Listens on http://localhost:7071
```

### Available Endpoints

#### Chat
```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello Aria"}]}'
```

#### Health Check (Comprehensive)
```bash
curl http://localhost:7071/api/ai/status | jq .
```

Returns:
- Active provider (LMStudio/Azure/OpenAI/Local)
- Environment variables status
- GPU/CPU info
- Database pool saturation
- Quantum integration status
- Cosmos DB status (if enabled)

#### TTS (Text-to-Speech)
```bash
curl -X POST http://localhost:7071/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Aria"}' \
  --output audio.mp3
```

#### Quantum Jobs
```bash
# Submit job
curl -X POST http://localhost:7071/api/quantum/submit \
  -H "Content-Type: application/json" \
  -d '{...job_config...}'

# Monitor job
curl http://localhost:7071/api/quantum/status/<job_id>
```

---

## 6. Quantum ML Integration

### Start Quantum MCP Server
```bash
python quantum-ai/quantum_mcp_server.py
# Server provides quantum tools for Model Context Protocol
```

### Quantum Workflows

#### Validate Configuration (Dry-Run)
```bash
python scripts/evaluation/quantum_autorun.py --dry-run
# Shows all configured quantum jobs without execution
```

#### Run All Quantum Jobs
```bash
python scripts/evaluation/quantum_autorun.py
```

#### Monitor Quantum Status
```bash
curl http://localhost:7071/api/quantum/status | jq .
```

### Configuration File
Location: `quantum_autorun.yaml`

Contains:
- Quantum circuit definitions
- Job parameters (shots, backend)
- Cost estimation
- Auto-deployment rules

---

## 7. Complete Integration: Master Orchestrator

Coordinates all sub-systems with cron scheduling:

### Start Master Orchestrator
```bash
python scripts/automation/master_orchestrator.py
```

### Configuration
File: `config/master_orchestrator.yaml`

Orchestrates:
1. Training (autotrain.py)
2. Quantum evaluation (quantum_autorun.py)
3. Model evaluation (evaluation_autorun.py)
4. Aria automation (aria_automation.py)

### Monitor All Systems
```bash
# Live dashboard with all orchestrators
python scripts/monitoring/auto_ops_dashboard.py --watch

# Compact view
python scripts/monitoring/auto_ops_dashboard.py --compact

# Problems only
python scripts/monitoring/auto_ops_dashboard.py --problems

# Export JSON
python scripts/monitoring/auto_ops_dashboard.py --export > orchestrator_status.json
```

---

## 8. Full Integration: Run Everything

### One-Line Complete Setup (Recommended)
```bash
./scripts/start_repo_automation.sh full
```

Or manually:

```bash
# Terminal 1: Aria Web Server
cd aria_web && python server.py

# Terminal 2: Azure Functions
func host start

# Terminal 3: Autonomous Training
python scripts/training/autonomous_training_orchestrator.py

# Terminal 4: Quantum MCP Server
python quantum-ai/quantum_mcp_server.py

# Terminal 5: Master Orchestrator
python scripts/automation/master_orchestrator.py

# Terminal 6: Monitoring Dashboard
python scripts/monitoring/auto_ops_dashboard.py --watch
```

### Quick Status Check
```bash
curl http://localhost:7071/api/ai/status | jq '{provider, gpu, database, cosmos}'
```

---

## 9. Debugging & Troubleshooting

### Test Each Component

#### Chat Provider
```bash
python talk-to-ai/src/chat_cli.py --provider local --once "test"
python talk-to-ai/src/chat_cli.py --provider azure --once "test"  # if configured
```

#### Aria Web
```bash
# Check server is running
curl http://localhost:8080 | head -20

# Test API endpoint
curl http://localhost:8080/api/aria/state
```

#### Functions
```bash
curl http://localhost:7071/api/ai/status | jq .
```

#### Autonomous Training
```bash
# Check logs
tail -f data_out/autonomous_training.log

# Check status
cat data_out/autonomous_training_status.json | python -m json.tool
```

#### Quantum
```bash
# Validate config
python scripts/evaluation/quantum_autorun.py --dry-run

# Check status
curl http://localhost:7071/api/quantum/status
```

### Common Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 8080 in use | Aria server still running | `pkill -f aria_web` or `lsof -ti:8080 \| xargs kill` |
| Provider: local | No env vars set | Configure Azure/OpenAI in local.settings.json |
| GPU not detected | CUDA not available | Check `python -c "import torch; print(torch.cuda.is_available())"` |
| Training not starting | Wrong config path | Verify `config/autonomous_training.yaml` exists |
| Functions 404 | Wrong port/path | Verify `func host start` on port 7071 |
| Quantum submission fails | Azure credentials missing | Set `AZURE_QUANTUM_SUBSCRIPTION_ID` env var |

---

## 10. Next Steps

### After Setup
1. **Test chat**: `python talk-to-ai/src/chat_cli.py --once "Hello Aria"`
2. **Open Aria UI**: http://localhost:8080
3. **Try auto-execute**: http://localhost:8080/auto-execute.html
4. **Monitor systems**: `python scripts/monitoring/auto_ops_dashboard.py --watch`
5. **Check health**: `curl http://localhost:7071/api/ai/status | jq .`

### Configuration Tuning
- **GPU training**: Set `device: cuda` in `config/autonomous_training.yaml`
- **Auto-deploy**: Set `auto_deploy_best: true` to auto-promote best models
- **Quantum cost**: Review `/api/quantum/status` before running real QPU jobs
- **Cycle speed**: Change `cycle_interval_minutes` in autonomous_training.yaml

### Integration Points
- Aria web UI ↔ Chat providers (multi-provider chat)
- Training orchestrator ↔ Auto-execute planner (LLM-powered actions)
- Quantum ML ↔ Aria world generator (quantum-themed environments)
- Master orchestrator ↔ Monitoring dashboard (real-time status)

---

## 11. Summary

You now have a complete Aria setup with:

✅ **Aria Web Interface** (port 8080)
✅ **Multi-Provider Chat** (Local/Azure/OpenAI/LMStudio)
✅ **Azure Functions** (port 7071)
✅ **Autonomous Training** (continuous 30-min cycles)
✅ **Quantum ML Integration** (MCP server + quantum jobs)
✅ **Master Orchestrator** (coordinates everything)
✅ **Live Monitoring Dashboard** (watch all systems)

---

**For detailed guidance, see**:
- `.github/copilot-instructions.md` — Architecture & patterns
- `.github/instructions/` — Component-specific rules
- `README.md` — Quick reference

