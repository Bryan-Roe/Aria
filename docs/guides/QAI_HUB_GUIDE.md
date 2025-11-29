# QAI Hub - Command Center Guide

## 🌌 Overview

The **QAI Hub** (http://localhost:8000/) is the central command center that unifies all three QAI projects into a single, cohesive interface. It provides quick access to training dashboards, quantum ML pipelines, chat interfaces, and monitoring tools.

---

## 🚀 Quick Start

### 1. Start the Dashboard Server

```powershell
# From repo root
python .\dashboard\serve.py

# Or use the pre-configured task
# Press Ctrl+Shift+P → "Tasks: Run Task" → "func: host start"
```

Server will start at **http://localhost:8000/**

The root page (/) automatically redirects to **/hub.html** - your command center.

### 2. Navigate the Hub

The hub is organized into:
- **Header**: System status badges (Dashboard, Training Pipeline, API, Quantum MCP)
- **Stats Bar**: Real-time counts (Jobs, Datasets, Models, GPU Usage)
- **Quick Actions**: 6 one-click shortcuts
- **System Cards**: 8 detailed system interfaces

---

## 📊 System Cards

### 1. 🎯 Training Dashboard (`/unified.html`)

**Primary interface for LoRA fine-tuning**

Features:
- 20+ training parameters (6 basic + 9 advanced + 4 evaluation)
- Real-time GPU monitoring
- 4 preset configurations (Quick/Standard/Full/Production)
- Config save/load (JSON export/import)
- Live job tracking with auto-refresh
- Comprehensive validation (5 checks)

**Usage**:
1. Click "Training Dashboard" card
2. Navigate to "Train" tab
3. Fill in job name, select model/dataset
4. Adjust epochs, samples, learning rate
5. (Optional) Expand Advanced Options for fine-grained control
6. Click "Start Training"
7. Monitor progress in "All Jobs" tab

**Presets**:
- **Quick Test**: 1 epoch, 100 samples (~2 min) - Fast validation
- **Standard**: 3 epochs, 1k samples (~10 min) - Good baseline
- **Full**: 5 epochs, all samples (~60 min) - Production quality
- **Production**: 10 epochs, all samples (~4 hours) - Maximum quality

---

### 2. ⚛️ Quantum ML Pipeline

**Hybrid quantum-classical machine learning**

Features:
- Quantum circuit training (PennyLane)
- Azure Quantum integration (ionq.simulator, ionq.qpu)
- 8 MCP server tools (circuit execution, job submission, result retrieval)
- Local & cloud simulators
- Cost estimation before QPU execution

**Usage**:
```powershell
# Dry-run validation
python .\scripts\quantum_autorun.py --dry-run

# Run specific job
python .\scripts\quantum_autorun.py --job local_pennylane

# Azure Quantum submission (requires az login)
python .\scripts\quantum_autorun.py --job azure_ionq_simulator
```

**MCP Server** (for AI agents):
```powershell
python .\quantum-ai\quantum_mcp_server.py
```

**Cost Gates**:
- Local simulators: FREE
- Azure simulators: FREE
- QPU execution: ~$0.00003-$0.00015 per gate-shot
  - Requires `azure_confirm_cost: true` in YAML

---

### 3. 💬 Multi-Provider Chat

**Unified chat CLI with 4 provider backends**

Features:
- Azure OpenAI (primary)
- OpenAI (fallback)
- LoRA adapter (custom models)
- Local echo (zero-dependency)
- Automatic provider detection
- Streaming responses
- Memory persistence (SQL/Cosmos)

**Usage**:
```powershell
# Auto-detect provider
python .\talk-to-ai\src\chat_cli.py

# Specific provider
python .\talk-to-ai\src\chat_cli.py --provider azure
python .\talk-to-ai\src\chat_cli.py --provider lora --model data_out\lora_training\lora_adapter

# One-shot mode
python .\talk-to-ai\src\chat_cli.py --provider azure --once "What is quantum computing?"
```

**Health Check**:
```powershell
# Check active provider and env vars
curl http://localhost:7071/api/ai/status | ConvertFrom-Json
```

---

### 4. 📊 Evaluation Suite

**Automated model assessment**

Features:
- Perplexity calculation (pre/post training)
- Loss comparison
- Batch evaluation across multiple models
- Model ranking
- Export reports (Markdown/JSON)

**Usage**:
```powershell
# Dry-run validation
python .\scripts\evaluation_autorun.py --dry-run

# Run all evaluations
python .\scripts\evaluation_autorun.py

# Specific evaluation
python .\scripts\evaluation_autorun.py --job perplexity_check
```

**Batch Evaluation**:
```powershell
# Scan for models and evaluate all
python .\scripts\batch_evaluator.py --scan-models --evaluate-all

# Generate comparison report
python .\scripts\results_exporter.py --all --format markdown
```

---

### 5. 🗃️ Dataset Manager

**Browse, validate, and manage datasets**

Features:
- Auto-discovery (datasets/chat/*)
- Sample counting (train/test splits)
- Format validation (JSON schema)
- Dataset generation tools
- Direct access from hub

**Usage via Dashboard**:
1. Open hub → Quick Actions → "View Datasets"
2. Or Training Dashboard → "Datasets" tab
3. See all datasets with sample counts

**API Access**:
```powershell
# List all datasets
curl http://localhost:8000/api/datasets | ConvertFrom-Json

# Response format:
# {
#   "datasets": [
#     {
#       "name": "chat_logs",
#       "path": "datasets\\chat\\chat_logs",
#       "train_samples": 1000,
#       "test_samples": 200
#     }
#   ]
# }
```

**Generate Synthetic Data**:
```powershell
# Create 2000 samples
python .\scripts\auto_data_train.py --samples 2000 --output-dir datasets/chat/synthetic_2k
```

---

### 6. 🔌 API Gateway

**Azure Functions unified API**

Endpoints:
- `/api/chat` - Multi-provider chat completion
- `/api/quantum/*` - Quantum circuit execution
- `/api/ai/status` - Health check (provider, env vars, SQL, Cosmos, telemetry)

**Integration**:
- Dynamic imports from all 3 projects (quantum-ai, talk-to-ai, lora training)
- SQL persistence (unified engine: Azure SQL, PostgreSQL, MySQL, SQLite)
- Cosmos DB persistence (optional, feature-flagged)
- Application Insights telemetry (optional)

**Usage**:
```powershell
# Start local dev server
func host start

# Test health endpoint
curl http://localhost:7071/api/ai/status

# Chat endpoint
curl http://localhost:7071/api/chat `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"messages":[{"role":"user","content":"Hello"}]}'
```

---

### 7. 📈 Resource Monitor

**Real-time system monitoring**

Features:
- GPU utilization & VRAM
- CPU & RAM usage
- Process tracking (PID, memory, CPU%)
- Historical graphs
- Alert system (thresholds)

**Usage**:
```powershell
# Snapshot (current state)
python .\scripts\resource_monitor.py --snapshot

# Stream mode (60 seconds)
python .\scripts\resource_monitor.py --stream --duration 60
```

**API Access**:
```powershell
# GPU info
curl http://localhost:8000/api/gpu | ConvertFrom-Json

# System resources
curl http://localhost:8000/api/system | ConvertFrom-Json

# Active processes
curl http://localhost:8000/api/processes | ConvertFrom-Json
```

---

### 8. 🔄 CI/CD Pipeline

**Automated testing & validation**

Features:
- 40 unit tests (~0.5s total)
- 30 integration tests (external services)
- Orchestrator validation (YAML configs)
- Artifact packaging
- Deployment automation

**Usage**:
```powershell
# Run fast unit tests
pytest tests/ -m "not slow and not azure"

# Or via test runner
python .\scripts\test_runner.py --unit

# Full CI pipeline
python .\scripts\ci_orchestrator.py --ci-pipeline

# Master orchestrator (all systems)
python .\scripts\master_orchestrator.py --status
```

**VS Code Integration**:
- Native Test Explorer (🧪 sidebar)
- Breakpoint debugging
- Per-test run/debug buttons
- See `VSCODE_TESTING_QUICKREF.md`

---

## ⚡ Quick Actions

The hub provides 6 one-click shortcuts:

1. **🚀 Start Training** → `/unified.html#train`
2. **📊 View Datasets** → `/unified.html#datasets`
3. **🤖 Browse Models** → `/unified.html#models`
4. **📈 Monitor GPU** → `/unified.html#monitor`
5. **⚛️ Quantum Jobs** → Toast with CLI command
6. **💬 Chat Interface** → Toast with CLI command

**Toast Messages**:
- Quick actions that require CLI show instructional toasts
- Example: "To use chat: python talk-to-ai/src/chat_cli.py --provider azure"

---

## 📡 API Endpoints

### Training Status
```http
GET /status
```
Returns training job status (no cache headers).

### Datasets
```http
GET /api/datasets
```
Returns all datasets with sample counts.

### Models
```http
GET /api/models
```
Returns trained models in `data_out/lora_training/marathon/`.

### Configs
```http
GET /api/configs
```
Returns available YAML configs with job counts and estimates.

### GPU Monitoring
```http
GET /api/gpu
GET /api/gpu-processes
GET /api/system
```
Returns GPU utilization, VRAM, active processes.

### Health Check
```http
GET /api/health
```
Returns comprehensive system health (datasets, output dir, GPU, venvs).

### Quick Stats
```http
GET /api/stats
```
Returns summary: jobs, datasets, models, GPU usage, active processes.

### Active Processes
```http
GET /api/processes
```
Returns Python processes running training/quantum/chat/serve.

### Start Training
```http
POST /api/start-training
Content-Type: application/json

{
  "name": "my_job",
  "model": "phi35",
  "dataset": "chat_logs",
  "epochs": 3,
  "max_samples": 1000,
  "learning_rate": "2e-4"
}
```

---

## 🎨 UI Features

### Dark Theme
- Gradient background (dark blue tones)
- Glass-morphism cards (backdrop blur)
- Smooth animations (hover effects, transitions)
- Color-coded status badges

### Responsive Design
- Grid layout (auto-fit, min 350px cards)
- Flexbox for stats and actions
- Mobile-friendly (wraps on small screens)

### Real-Time Updates
- Stats refresh every 30 seconds
- Status badges update on load
- GPU usage live polling
- Toast notifications for actions

### Accessibility
- Tooltips on all system cards
- Clear action labels
- Keyboard navigation support
- ARIA-compliant badges

---

## 🔧 Configuration

### Server Settings

**Port**: 8000 (default)
**Root Redirect**: `/` → `/hub.html`

To change:
```python
# dashboard/serve.py
PORT = 8080  # Change here
```

### Rate Limiting

**Default**: 60 requests per minute per IP

To adjust:
```python
# dashboard/serve.py
MAX_REQUESTS_PER_MINUTE = 120  # Increase limit
```

### System Status Badges

Update status in hub.html:
```javascript
// Green = online
<div class="status-badge online">
  <div class="status-dot"></div>
  <span>System Name</span>
</div>

// Yellow = warning
<div class="status-badge">
  <div class="status-dot" style="background: #ffc107;"></div>
  <span>System Name</span>
</div>

// Red = offline
<div class="status-badge">
  <div class="status-dot" style="background: #dc3545;"></div>
  <span>System Name</span>
</div>
```

---

## 📚 Documentation Files

- **QAI_HUB_GUIDE.md** (this file) - Hub overview
- **TRAINING_TAB_ENHANCEMENTS.md** - Training dashboard features
- **TRAINING_TAB_QUICKREF.md** - Quick reference for training
- **DASHBOARD_DEMO.md** - Live demo script
- **AUTOTRAIN_README.md** - LoRA training orchestration
- **QUANTUM_AUTORUN_README.md** - Quantum job configuration
- **TELEMETRY_COSMOS_ENABLEMENT.md** - Observability setup
- **VSCODE_TESTING_QUICKREF.md** - Test Explorer shortcuts

---

## 🐛 Troubleshooting

### Hub Not Loading

**Symptom**: 404 or blank page at http://localhost:8000/

**Fix**:
```powershell
# Check server is running
Get-Process python | Where-Object {$_.CommandLine -like "*serve.py*"}

# Restart server
Stop-Process -Name python -Force
python .\dashboard\serve.py
```

### Stats Showing "--"

**Symptom**: Stats bar shows dashes instead of numbers

**Fix**:
```powershell
# Ensure status.json exists
Test-Path .\data_out\autotrain\status.json

# Run a training job to generate status
python .\scripts\autotrain.py --dry-run
```

### System Cards Not Clickable

**Symptom**: Clicking cards doesn't navigate

**Fix**:
- Check browser console for JavaScript errors
- Hard refresh: Ctrl+Shift+R
- Clear browser cache

### API Endpoints 404

**Symptom**: /api/* returns 404

**Fix**:
```powershell
# Check serve.py is running (not Azure Functions)
# Dashboard server: http://localhost:8000
# Azure Functions: http://localhost:7071

# Restart dashboard server
python .\dashboard\serve.py
```

---

## 🚀 Advanced Usage

### Custom System Cards

Add new systems to hub.html:

```html
<div class="system-card" onclick="openSystem('newsystem.html')">
  <div class="system-icon">🆕</div>
  <h2 class="system-title">New System</h2>
  <p class="system-description">Description here...</p>
  <ul class="system-features">
    <li>Feature 1</li>
    <li>Feature 2</li>
  </ul>
  <div class="system-actions">
    <button class="btn btn-primary">Primary Action</button>
    <button class="btn btn-secondary">Secondary</button>
  </div>
</div>
```

### Custom Quick Actions

Add to actions-grid:

```html
<div class="action-btn" onclick="quickAction('myaction')">
  <div class="action-icon">🔥</div>
  <div class="action-label">My Action</div>
</div>
```

Update JavaScript:

```javascript
function quickAction(action) {
  const actions = {
    // ... existing actions ...
    myaction: () => showToast('Custom action triggered!')
  };
  // ... rest of function
}
```

### Custom API Endpoints

Add to serve.py:

```python
# In MyHTTPRequestHandler.do_GET()
elif self.path == '/api/custom':
    self.send_json_response(self.get_custom_data())
    return

# Add handler method
def get_custom_data(self):
    return {
        'message': 'Custom API response',
        'data': [1, 2, 3]
    }
```

---

## 🎯 Best Practices

### 1. Use Hub as Single Entry Point
- Bookmark http://localhost:8000/ (not unified.html)
- All navigation starts from hub
- Consistent UX across systems

### 2. Monitor Stats Bar
- Quick health check at a glance
- GPU usage = training activity indicator
- Dataset count = new data available

### 3. Leverage Quick Actions
- Faster than navigating through cards
- Direct deep links to tabs
- Toast messages for CLI commands

### 4. Check System Status Badges
- Green = fully operational
- Yellow = degraded/optional
- Red = offline/unavailable

### 5. Use API Endpoints for Automation
- `/api/stats` for dashboard widgets
- `/api/health` for monitoring scripts
- `/api/processes` for job tracking

---

## 📈 Metrics & Monitoring

### Training Jobs
- Total count (all time)
- Active running jobs
- Completed/failed status
- Average duration

### Datasets
- Count in `datasets/chat/`
- Train/test sample counts
- Format validation status

### Models
- Trained adapters in `data_out/lora_training/marathon/`
- Base model references
- LoRA rank configurations

### GPU Usage
- Utilization percentage (0-100%)
- VRAM allocated vs total
- Active processes on GPU
- Temperature (if available)

---

## 🔐 Security Notes

### Local Development Only
- Hub is designed for localhost:8000
- **NOT production-ready** as-is
- No authentication/authorization

### For Production Deployment
1. Add authentication (OAuth, JWT)
2. Enable HTTPS
3. Implement proper CORS
4. Rate limiting per user (not IP)
5. Input sanitization
6. API key management
7. Secure environment variables

### Sensitive Data
- SQL connection strings in `.env` or `local.settings.json`
- Azure Quantum credentials via `az login`
- OpenAI/Azure OpenAI keys in environment
- Never commit secrets to git

---

## 🌟 Future Enhancements

### Planned Features
- [ ] WebSocket support (real-time updates)
- [ ] User authentication
- [ ] Job queue management (pause/resume/cancel)
- [ ] Historical charts (training metrics over time)
- [ ] Model comparison dashboard
- [ ] Dataset visualization (sample previews)
- [ ] Notification system (email/SMS on completion)
- [ ] Remote training submission (from mobile)

### Suggestions Welcome
Submit ideas via GitHub Issues or contribute PRs!

---

## 📞 Support

### Documentation
- Main README.md (repo root)
- Individual project READMEs (quantum-ai, talk-to-ai, AI/microsoft_phi-silica-3.6_v1)
- Markdown guides in repo root (20+ files)

### Testing
- Unit tests: `pytest tests/ -m "not slow and not azure"`
- Integration tests: `pytest tests/ -m integration`
- VS Code Test Explorer: 🧪 sidebar

### Debugging
- Server logs: Check terminal running serve.py
- Browser console: F12 → Console tab
- API responses: Use curl or Postman
- Process inspection: Task Manager or `Get-Process python`

---

## 📄 License

Same as main QAI repository (see root LICENSE file).

---

**Last Updated**: 2025-11-25  
**Version**: 2.0  
**Author**: QAI Development Team
