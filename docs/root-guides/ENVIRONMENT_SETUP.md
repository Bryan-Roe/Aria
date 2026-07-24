# Aria Environment Setup — Configuration Guide

**Status:** Python 3.14 venv configured for main workspace + isolated sub-projects
**Date:** May 16, 2026
**Setup Completion:** ✅ Ready for dependency installation & validation

---

## 📋 Setup Overview

Your Aria workspace is configured with:

| Component         | Status        | Python | Venv Path                         |
| ----------------- | ------------- | ------ | --------------------------------- |
| **Main Aria**     | ✅ Configured | 3.14   | `/workspaces/Aria/.venv`          |
| **Quantum ML**    | ✅ Configured | 3.14   | `/workspaces/Aria/.venv` (shared) |
| **Chat CLI**      | ✅ Configured | 3.14   | `/workspaces/Aria/.venv` (shared) |
| **LoRA Training** | ✅ Configured | 3.14   | `/workspaces/Aria/.venv` (shared) |

---

## 🚀 Quick Start Commands

### Step 1: Install Main Dependencies

```bash
cd /workspaces/Aria
/workspaces/Aria/.venv/bin/python -m pip install --upgrade pip setuptools wheel
/workspaces/Aria/.venv/bin/pip install -r requirements.txt
/workspaces/Aria/.venv/bin/pip install -r requirements-dev.txt  # For development
```

### Step 2: Install Sub-Project Dependencies

```bash
# Quantum ML
/workspaces/Aria/.venv/bin/pip install -r ai-projects/quantum-ml/requirements.txt

# Chat CLI
/workspaces/Aria/.venv/bin/pip install -r ai-projects/chat-cli/requirements.txt

# LLM Maker
/workspaces/Aria/.venv/bin/pip install -r ai-projects/llm-maker/requirements.txt

# Cooking AI
/workspaces/Aria/.venv/bin/pip install -r ai-projects/cooking-ai/requirements.txt

# Writer-Reviewer Workflow
/workspaces/Aria/.venv/bin/pip install -r ai-projects/writer-reviewer-workflow/requirements.txt
```

### Step 3: Validate Installation

```bash
# Fast validation (instant)
/workspaces/Aria/.venv/bin/python scripts/fast_validate.py

# Detailed provider validation
curl http://localhost:7071/api/ai/status | python3 -m json.tool
```

### Step 4: Test Azure Functions

```bash
# Start Functions runtime (requires func CLI)
func host start

# In another terminal, smoke test:
curl http://localhost:7071/api/ai/routes | python3 -m json.tool
```

---

## 📦 Dependency Overview

### Main Aria (`requirements.txt`)

**Core AI/ML Stack:**

- `openai>=1.58.0` — OpenAI provider
- `azure-functions` — Azure Functions integration
- `azure-cosmos>=4.7.0` — Cosmos DB client
- `pyyaml>=6.0.1` — Config management
- `tiktoken>=0.8.0` — Token counting

**ML Libraries:**

- `torch>=2.8.0` — PyTorch (deep learning)
- `numpy>=1.26.4` — Numerical computing
- `scikit-learn>=1.6.0` — ML utilities
- `Pillow>=11.1.0` — Image processing

**Optional TTS & Speech:**

- `pyttsx3>=2.90` — Local TTS fallback
- `gTTS>=2.3.0` — Google TTS

**Dashboard & Visualization:**

- `Flask>=3.1.3` — Web framework
- `flask-socketio>=5.4.0` — WebSocket support
- `gradio>=5.24.0` — Model UI
- `matplotlib>=3.9.0`, `seaborn>=0.13.0` — Plotting

**Database & Logging:**

- `pyodbc>=5.0.1` — SQL Server/Azure SQL
- `sqlalchemy>=2.0.36` — ORM
- `azure-monitor-opentelemetry>=1.0.0` — Application Insights

---

### Quantum ML (`ai-projects/quantum-ml/requirements.txt`)

**Core Quantum:**

- `qiskit==1.3.0` — Quantum circuits
- `qiskit-aer==0.16.4` — Aer simulator
- `qiskit-machine-learning==0.8.2` — Quantum ML algorithms
- `azure-quantum[qiskit]>=1.0.0` — Azure Quantum service

**Classical ML:**

- `pennylane>=0.39.0` — Hybrid quantum-classical
- `torch>=2.8.0` — PyTorch
- `scipy>=1.14.0` — Scientific computing
- `pandas>=2.2.0` — Data handling

**Azure Integration:**

- `azure-identity>=1.15.0` — Auth
- `azure-core>=1.29.0` — Core SDK

---

### Chat CLI (`ai-projects/chat-cli/requirements.txt`)

**Minimal provider support:**

- `openai>=1.58.0` — OpenAI API

_Note: All other providers (Azure OpenAI, LMStudio, etc.) come from main `requirements.txt`_

---

### LLM Maker (`ai-projects/llm-maker/requirements.txt`)

**Code Safety & Analysis:**

- `ast-grep-py>=0.39.0` — AST-based code search
- `astroid>=3.0.0` — Python AST analysis
- `RestrictedPython>=6.0` — Sandboxed code execution

**MCP Protocol:**

- `mcp>=1.0.0` — Model Context Protocol

---

## 🔌 Provider Detection & Configuration

### Provider Detection Chain

The system checks providers in this order:

1. **Explicit choice** — `--provider` flag
2. **LMStudio** — `LMSTUDIO_BASE_URL` env var
3. **Azure OpenAI** — All 4 vars set:
    - `AZURE_OPENAI_API_KEY`
    - `AZURE_OPENAI_ENDPOINT`
    - `AZURE_OPENAI_DEPLOYMENT`
    - `AZURE_OPENAI_API_VERSION`
4. **OpenAI** — `OPENAI_API_KEY` set
5. **LoRA Adapter** — Explicit `--provider lora` + adapter path
6. **Local Fallback** — No config (zero dependencies)

### Configuration File: `local.settings.json`

```json
{
    "IsEncrypted": false,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",

        "AZURE_SPEECH_KEY": "<your-speech-key>",
        "AZURE_SPEECH_REGION": "<your-region>",

        "AZURE_OPENAI_API_KEY": "<key>",
        "AZURE_OPENAI_ENDPOINT": "<endpoint>",
        "AZURE_OPENAI_DEPLOYMENT": "<deployment>",

        "OPENAI_API_KEY": "<key>",

        "LMSTUDIO_BASE_URL": "http://localhost:1234/v1",
        "LMSTUDIO_MODEL": "local-model",

        "QAI_ENABLE_LOCAL_TTS": "true"
    }
}
```

---

## ✅ Critical Dependencies Check

Run this to verify key packages are installed:

```python
python3 << "EOF"
import sys

critical = {
    "torch": "2.8+",
    "transformers": "latest",
    "qiskit": "1.3+",
    "peft": "latest",
    "azure-openai": "latest",
    "azure-quantum": "1.0+",
    "mcp": "1.0+",
}

missing = []
for pkg, version in critical.items():
    try:
        __import__(pkg.replace("-", "_"))
        print(f"✓ {pkg:<20} installed")
    except ImportError:
        print(f"✗ {pkg:<20} MISSING")
        missing.append(pkg)

if missing:
    print(f"\nMissing: {', '.join(missing)}")
    sys.exit(1)
else:
    print("\n✓ All critical packages available")
EOF
```

---

## 🧪 Validation & Testing

### 1. Fast Validation (Instant)

```bash
python scripts/fast_validate.py
```

Checks:

- ✓ Dataset directories exist
- ✓ Critical scripts present
- ✓ Output directories writable
- ✓ Config files valid

### 2. Provider Readiness

```bash
# Start Functions
func host start

# In another terminal:
curl http://localhost:7071/api/ai/status | python3 -m json.tool
```

Expected output includes:

```json
{
  "active_provider": "azure|openai|local|lora",
  "azure_openai_ready": true/false,
  "openai_ready": true/false,
  "lmstudio_ready": true/false,
  "ml_libraries": {
    "torch": true,
    "transformers": true,
    "qiskit": true,
    "peft": true
  },
  "database": {
    "sql_pool_status": "healthy|warning|unavailable",
    "saturation_pct": 45
  }
}
```

### 3. Provider Probe

```bash
curl -X POST http://localhost:7071/api/ai/provider-probe \
  -H 'Content-Type: application/json' \
  -d '{"provider":"auto"}' | python3 -m json.tool
```

### 4. Unit Tests

```bash
# All unit tests
pytest tests/ -m "not slow and not azure" -v

# Using test runner
python scripts/test_runner.py --unit

# With coverage
python scripts/test_runner.py --unit --coverage
```

### 5. Chat Provider Tests

```bash
# Test local provider (no setup needed)
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello"

# Test OpenAI (requires OPENAI_API_KEY)
python ai-projects/chat-cli/src/chat_cli.py --provider openai --once "What is 2+2?"

# Test Azure OpenAI (requires all 4 Azure vars)
python ai-projects/chat-cli/src/chat_cli.py --provider azure-openai --once "Hello"
```

---

## 🔗 API Endpoints (Once Functions Start)

### Health & Status

- `GET /api/ai/routes` — Available routes
- `GET /api/ai/status` — Comprehensive health check
- `POST /api/ai/provider-probe` — Provider detection

### Chat

- `GET /api/chat-web` — Web UI HTML
- `POST /api/chat/stream` — SSE streaming chat
- `POST /api/chat` — Non-streaming chat

### Quantum

- `GET /api/quantum-llm/status` — Quantum backend info
- `POST /api/quantum-llm/stream` — SSE quantum chat
- `POST /api/quantum/submit` — Submit quantum job

### Aria Character

- `GET /api/aria/state` — Character state
- `POST /api/aria/command` — Execute command
- `POST /api/aria/object` — Manage objects

### TTS

- `POST /api/tts` — Speech synthesis (Azure or fallback)

---

## 📊 Isolated Venv Strategy

All sub-projects currently share the main `.venv`. If you need **isolated venvs** (e.g., for conflicting deps), use:

```bash
# Quantum ML isolated venv
cd ai-projects/quantum-ml
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Chat CLI isolated venv
cd ai-projects/chat-cli
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# LoRA Training isolated venv
cd AI/microsoft_phi-silica-3.6_v1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # if exists, or install manually
```

Then update VS Code Python interpreter settings:

- `.vscode/settings.json` → `"python.defaultInterpreterPath": "/path/to/venv/bin/python"`

---

## 🛠️ Advanced Configuration

### Optional: SQL Persistence

Enable SQL backend for session/logging data:

```json
{
    "Values": {
        "QAI_DB_CONN": "sqlite:////workspaces/Aria/data_out/qai.db",
        "QAI_SQL_POOL_SIZE": "10"
    }
}
```

Supported backends:

- `sqlite:///path/to/db.db` — SQLite (easiest, no server needed)
- `postgresql://user:pass@host/db` — PostgreSQL
- `mssql+pyodbc://user:pass@host/db` — Azure SQL / SQL Server

### Optional: Cosmos DB

Feature-flagged support (performance trade-off vs SQL):

```json
{
    "Values": {
        "QAI_ENABLE_COSMOS": "true",
        "COSMOS_ENDPOINT": "<endpoint>",
        "COSMOS_KEY": "<key>",
        "COSMOS_DATABASE": "qai",
        "COSMOS_CONTAINER": "conversations"
    }
}
```

### Optional: Azure Speech TTS

```json
{
    "Values": {
        "AZURE_SPEECH_KEY": "<your-key>",
        "AZURE_SPEECH_REGION": "eastus"
    }
}
```

Without it, system falls back to local TTS (`pyttsx3` or `gTTS`).

### Optional: Telemetry

```json
{
    "Values": {
        "APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=...;"
    }
}
```

---

## 🚨 Common Issues & Fixes

### Issue: `ModuleNotFoundError: No module named 'torch'`

**Fix:** Install PyTorch

```bash
pip install torch>=2.8.0
```

### Issue: `ModuleNotFoundError: No module named 'azure.quantum'`

**Fix:** Install Quantum SDK

```bash
pip install azure-quantum[qiskit]>=1.0.0 qiskit==1.3.0
```

### Issue: `ModuleNotFoundError: No module named 'openai'`

**Fix:** Install OpenAI

```bash
pip install openai>=1.58.0
```

### Issue: `Functions failed to import module` (func host start fails)

**Fix:** Verify `host.json` and `functions.json` paths, reinstall Functions tools:

```bash
pip install azure-functions
# or
npm install -g azure-functions-core-tools@4
```

### Issue: Provider detection returns "local" (zero-config fallback)

**Fix:** Verify env vars in `local.settings.json`:

```bash
curl http://localhost:7071/api/ai/status | python3 -m json.tool
# Check azure_openai_ready, openai_ready, lmstudio_ready fields
```

### Issue: `/api/chat/stream` returns 500

**Fix:** Check logs and run provider probe:

```bash
curl -X POST http://localhost:7071/api/ai/provider-probe \
  -H 'Content-Type: application/json' \
  -d '{"provider":"auto"}' | python3 -m json.tool
```

---

## 📝 Next Steps

1. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    pip install -r ai-projects/quantum-ml/requirements.txt
    pip install -r ai-projects/chat-cli/requirements.txt
    ```

2. **Configure secrets** (optional):
    - Edit `local.settings.json` with your API keys
    - Or set env vars directly

3. **Run validation:**

    ```bash
    python scripts/fast_validate.py
    ```

4. **Start Functions:**

    ```bash
    func host start
    ```

5. **Test endpoints:**

    ```bash
    curl http://localhost:7071/api/ai/status | python3 -m json.tool
    ```

---

## 📚 Related Documentation

- `.github/copilot-instructions.md` — Quick commands & patterns
- `AUTONOMOUS_AGENT_GUIDE.md` — Autonomous learning setup
- `README.md` — Project overview
- `.github/instructions/` — Component-specific patterns

---

**Generated:** May 16, 2026
**Python Version:** 3.14
**Status:** ✅ Ready for dependency installation
