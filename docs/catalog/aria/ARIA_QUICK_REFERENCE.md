# Aria Quick Reference Cards

**Generated: January 23, 2026** | Status: ✅ All Systems Ready

---

## Card 1: Quick Start (Copy-Paste)

### Start Everything (One Script)
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```

### Start Individual Components

**Terminal 1: Aria Web Interface**
```bash
cd /workspaces/AI/aria_web && python server.py
# Opens http://localhost:8080
```

**Terminal 2: Azure Functions**
```bash
cd /workspaces/AI && func host start
# API on http://localhost:7071
```

**Terminal 3: Autonomous Training**
```bash
cd /workspaces/AI && python scripts/training/autonomous_training_orchestrator.py
```

**Terminal 4: Quantum MCP Server**
```bash
cd /workspaces/AI && python quantum-ai/quantum_mcp_server.py
```

**Terminal 5: Monitoring Dashboard**
```bash
cd /workspaces/AI && python scripts/monitoring/auto_ops_dashboard.py --watch
```

---

## Card 2: Test Commands

### Test Chat Provider
```bash
python /workspaces/AI/talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"
```

### Test Aria Web API
```bash
# Get character state
curl http://localhost:8080/api/aria/state

# Send command
curl -X POST http://localhost:8080/api/aria/command \
  -H "Content-Type: application/json" \
  -d '{"command": "wave"}'
```

### Test Functions Health
```bash
curl http://localhost:7071/api/ai/status | jq .
```

### Test Chat via Functions
```bash
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

---

## Card 3: Web Interfaces

| URL | Purpose | Notes |
|-----|---------|-------|
| http://localhost:8080 | Main Aria Character | 3D animated avatar, natural language commands |
| http://localhost:8080/auto-execute.html | Auto-Execute Planner | LLM-powered action sequences |
| http://localhost:8080/quantum-world.html | Quantum 3D World | Quantum circuit visualization |

### Example Commands in Aria
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

---

## Card 4: Configuration

### Local Settings (Chat Providers)
File: `/workspaces/AI/local.settings.json`

**Current Status**: Local Echo (works out-of-box)

**To enable Azure OpenAI**:
```json
{
  "Values": {
    "AZURE_OPENAI_API_KEY": "your-key",
    "AZURE_OPENAI_ENDPOINT": "https://your-resource.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT": "deployment-name",
    "AZURE_OPENAI_API_VERSION": "2024-08-01-preview"
  }
}
```

**To enable OpenAI**:
```json
{
  "Values": {
    "OPENAI_API_KEY": "sk-...",
    "OPENAI_MODEL": "gpt-4o-mini"
  }
}
```

**To enable LMStudio**:
```json
{
  "Values": {
    "LMSTUDIO_BASE_URL": "http://localhost:1234/v1"
  }
}
```

### Autonomous Training Config
File: `/workspaces/AI/config/autonomous_training.yaml`

**Key settings**:
```yaml
autonomous_mode:
  enabled: true
  continuous: true           # infinite cycles
  cycle_interval_minutes: 30

training:
  device: cpu                # change to 'cuda' for GPU
  epochs_progression: [25, 50, 100, 200]
```

---

## Card 5: Monitoring & Logs

### Live Monitoring
```bash
# Watch all orchestrators
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch

# Show problems only
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --problems

# Compact view
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --compact
```

### View Logs
```bash
# Autonomous training
tail -f /workspaces/AI/data_out/autonomous_training.log

# Training status (JSON)
watch -n 5 'cat /workspaces/AI/data_out/autonomous_training_status.json | python -m json.tool'

# Functions (if running)
# Check function_app console output

# Aria web server (if running in foreground)
# Check server console
```

### Check Status Files
```bash
# All orchestrator status
ls -lh /workspaces/AI/data_out/*/status.json

# View specific status
cat /workspaces/AI/data_out/autonomous_training_status.json | python -m json.tool
cat /workspaces/AI/data_out/autotrain/status.json | python -m json.tool
```

---

## Card 6: Useful Commands

### Trigger Immediate Training Cycle
```bash
# Skip 30-min wait, run now
pkill -USR1 -f autonomous_training
```

### Check GPU Status
```bash
# Is CUDA available?
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# GPU usage (if training)
watch -n 1 nvidia-smi
```

### Validate Orchestrator Config (Dry-Run)
```bash
# Validate autonomous training (no execution)
python /workspaces/AI/scripts/training/autonomous_training_orchestrator.py --dry-run

# Validate quantum jobs (no execution)
python /workspaces/AI/scripts/evaluation/quantum_autorun.py --dry-run
```

### List Deployed Models
```bash
ls -lh /workspaces/AI/deployed_models/
```

### Export Monitoring Data
```bash
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --export > /tmp/aria_status.json
```

---

## Card 7: Troubleshooting

| Problem | Check | Fix |
|---------|-------|-----|
| Port 8080 in use | `lsof -i :8080` | Kill: `pkill -f aria_web` |
| Port 7071 in use | `lsof -i :7071` | Kill: `func` process |
| Provider: local only | `curl http://localhost:7071/api/ai/status \| jq .provider` | Add env vars to local.settings.json |
| Training not starting | Check log: `tail -f /workspaces/AI/data_out/autonomous_training.log` | Verify `config/autonomous_training.yaml` |
| GPU not detected | `python -c "import torch; print(torch.cuda.is_available())"` | Install CUDA/PyTorch, or use CPU |
| Chat not responding | `python talk-to-ai/src/chat_cli.py --provider local --once test` | Check chat_providers.py import |

---

## Card 8: Restart/Reset

### Graceful Shutdown (All Components)
```bash
pkill -f 'aria_web\|func host\|autonomous_training\|quantum_mcp\|master_orchestrator\|auto_ops'
```

### Full Reset
```bash
# Clear all training/output data
rm -rf /workspaces/AI/data_out/*

# Clear deployed models
rm -rf /workspaces/AI/deployed_models/*

# Restart everything
bash /workspaces/AI/scripts/start_aria_full.sh
```

### Restart Single Component
```bash
# Find process
ps aux | grep aria_web

# Kill by PID
kill -9 <PID>

# Restart
cd /workspaces/AI/aria_web && python server.py
```

---

## Card 9: Performance Tuning

### Enable GPU Training
1. Edit `/workspaces/AI/config/autonomous_training.yaml`:
```yaml
training:
  device: cuda
  max_gpu_memory_gb: 0  # Use all available
```

2. Restart training

### Increase Training Speed
```yaml
data_collection:
  parallel_downloads: 20  # Increase from 15

training:
  workers: 32             # Increase from 20
  gradient_accumulation_steps: 4
```

### Reduce Training Cost
```yaml
data_collection:
  min_datasets: 100       # Reduce from 500
  
training:
  epochs_progression: [25, 50]  # Reduce epochs
```

---

## Card 10: System Status Overview

### Current System State
```
✅ Python 3.14.0
✅ All projects present
✅ Dependencies installed
✅ Chat provider working (local echo)
✅ All ports available
✅ Data directories ready
```

### To Get Full Diagnostic
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```

---

## Card 11: File Locations Reference

| Component | Main File | Config | Logs |
|-----------|-----------|--------|------|
| Aria Web | `/workspaces/AI/aria_web/server.py` | N/A | Console |
| Azure Functions | `/workspaces/AI/function_app.py` | `local.settings.json` | Console |
| Chat | `/workspaces/AI/talk-to-ai/src/chat_cli.py` | `local.settings.json` | Console |
| Training | `/workspaces/AI/scripts/training/autonomous_training_orchestrator.py` | `config/autonomous_training.yaml` | `data_out/autonomous_training.log` |
| Quantum | `/workspaces/AI/quantum-ai/quantum_mcp_server.py` | `quantum_autorun.yaml` | Console |
| Orchestrator | `/workspaces/AI/scripts/automation/master_orchestrator.py` | `config/master_orchestrator.yaml` | Console |
| Dashboard | `/workspaces/AI/scripts/monitoring/auto_ops_dashboard.py` | N/A | Console |

---

## Card 12: API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/aria/state` | GET | Current character state |
| `/api/aria/command` | POST | Process natural language command |
| `/api/aria/execute` | POST | Execute action sequence |
| `/api/aria/object` | POST | Add/update/remove objects |
| `/api/aria/world` | POST | Generate themed world |
| `/api/chat` | POST | Send chat message (SSE streaming) |
| `/api/ai/status` | GET | Health check + provider info |
| `/api/tts` | POST | Text-to-speech |
| `/api/quantum/*` | POST/GET | Quantum job submission/status |

---

## Quick Diagnostic

Run this to verify everything:
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```

For complete setup guide, see: `/workspaces/AI/ARIA_SETUP_GUIDE.md`
