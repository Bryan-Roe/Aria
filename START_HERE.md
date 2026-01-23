# 🎨 ARIA - START HERE

**Quick Start Card** | January 23, 2026 | Status: ✅ Ready

---

## 🟢 START EVERYTHING (1 Command)

```bash
bash /workspaces/AI/scripts/start_aria_full.sh
```

Then open: **http://localhost:8080**

---

## 🟡 START INDIVIDUALLY (Pick Your Approach)

### Start Aria Web Interface
```bash
cd /workspaces/AI/aria_web && python server.py
# → http://localhost:8080
```

### Start Azure Functions
```bash
cd /workspaces/AI && func host start
# → http://localhost:7071/api/ai/status
```

### Start Training (Continuous 30-min cycles)
```bash
cd /workspaces/AI && python scripts/training/autonomous_training_orchestrator.py
# → Monitors: tail -f data_out/autonomous_training.log
```

### Start Quantum ML Server
```bash
cd /workspaces/AI && python quantum-ai/quantum_mcp_server.py
# → Quantum job management
```

### Start Monitoring Dashboard
```bash
cd /workspaces/AI && python scripts/monitoring/auto_ops_dashboard.py --watch
# → Live real-time status
```

---

## 🔵 TEST FIRST (Verify Everything Works)

```bash
# Test 1: Chat
python /workspaces/AI/talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"

# Test 2: Web API
curl http://localhost:8080/api/aria/state

# Test 3: Functions Health
curl http://localhost:7071/api/ai/status | jq .

# Test 4: Full Diagnostic
python /workspaces/AI/scripts/aria_diagnostic.py
```

---

## 📚 WEB INTERFACES

| URL | Purpose |
|-----|---------|
| http://localhost:8080 | **Aria Character UI** — 3D avatar, commands, objects |
| http://localhost:8080/auto-execute.html | **Auto-Execute Planner** — LLM action sequences |
| http://localhost:8080/quantum-world.html | **Quantum World** — Quantum visualization |

---

## 💬 EXAMPLE ARIA COMMANDS

```
move left
move right
wave
dance
jump
say hello
pickup ball
throw
look around
```

---

## 📊 MONITORING

```bash
# Live dashboard (auto-refresh every 10s)
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --watch

# Show problems only
python /workspaces/AI/scripts/monitoring/auto_ops_dashboard.py --problems

# View training logs
tail -f /workspaces/AI/data_out/autonomous_training.log

# Trigger immediate training cycle
pkill -USR1 -f autonomous_training
```

---

## ⚙️ CONFIGURATION (Optional)

### Enable Azure OpenAI
Edit `/workspaces/AI/local.settings.json`:
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

### Enable GPU Training
Edit `/workspaces/AI/config/autonomous_training.yaml`:
```yaml
training:
  device: cuda
  max_gpu_memory_gb: 0  # Use all available
```

---

## 🐛 QUICK TROUBLESHOOTING

| Issue | Fix |
|-------|-----|
| Port 8080 in use | `pkill -f aria_web` |
| Port 7071 in use | `pkill -f "func host"` |
| Chat shows "local" | Add env vars to `local.settings.json` |
| Training won't start | Check `config/autonomous_training.yaml` exists |
| GPU not found | `python -c "import torch; print(torch.cuda.is_available())"` |

---

## 📖 DOCUMENTATION

- **Full Setup**: `/workspaces/AI/ARIA_SETUP_GUIDE.md`
- **Quick Ref**: `/workspaces/AI/ARIA_QUICK_REFERENCE.md`
- **Deploy Ready**: `/workspaces/AI/ARIA_DEPLOYMENT_READY.md`
- **Summary**: `/workspaces/AI/ARIA_COMPLETE_SETUP_SUMMARY.md`

---

## 🎯 WHAT YOU NOW HAVE

✅ Aria Web Interface (3D interactive character)  
✅ Multi-Provider Chat (Local/Azure/OpenAI/LMStudio)  
✅ Azure Functions API  
✅ Autonomous Training (30-min cycles)  
✅ Quantum ML Integration  
✅ Master Orchestrator + Monitoring  
✅ Full Documentation  

---

## 🚀 NEXT ACTION

Choose one:

**A) Just want to see it?**
```bash
bash /workspaces/AI/scripts/start_aria_full.sh
# Then open http://localhost:8080
```

**B) Want to test first?**
```bash
python /workspaces/AI/scripts/aria_diagnostic.py
```

**C) Want to customize?**
```bash
# See ARIA_SETUP_GUIDE.md for detailed configuration
```

---

**You're ready! Pick option A, B, or C above and start using Aria.** 🎉

