# QAI – Copilot Instructions

Essential knowledge for AI agents working in this hybrid quantum-AI/ML workspace. Focus: immediate productivity, safe execution, and cost awareness.

## 🚀 Getting Started (New Contributors)

### First-Time Setup (5 minutes)

```powershell
# 1. Clone and navigate to workspace
cd c:\Users\Bryan\OneDrive\AI

# 2. Verify Python 3.9+ installed
python --version

# 3. Run health check
python .\scripts\system_health_check.py

# 4. Test basic functionality (no API keys needed)
python .\talk-to-ai\src\chat_cli.py --provider local --once "Hello"

# 5. Run fast unit tests to verify setup
python .\scripts\test_runner.py --unit
```

### Your First Training Run (2 minutes)

```powershell
# Quick LoRA training with TinyLlama (CPU-friendly, ~15 seconds)
python .\scripts\automated_training_pipeline.py --models tinyllama --quick

# Results will be in: data_out/lora_training/tinyllama_ultra_<timestamp>/
```

### Essential Files to Read First

1. **This file** (`.github/copilot-instructions.md`) - Architecture & conventions
2. **Root README.md** - Project overviews & quick starts
3. **AUTOMATION_QUICKREF.md** - One-command training pipelines
4. **scripts/README.md** - All available automation tools

### Common First Tasks

- **Add a dataset**: Place `train.json` + `test.json` in `datasets/chat/<name>/`
- **Run existing job**: `python .\scripts\autotrain.py --job phi35_mixed_chat`
- **Check system status**: `GET http://localhost:7071/api/ai/status` (after `func host start`)
- **Debug a test**: Open Test Explorer (🧪), right-click test → "Debug Test"

## Architecture Overview

**Three Independent Projects** (isolated venvs):
- `quantum-ai/` – Hybrid quantum-classical ML (PennyLane + Azure Quantum) with interactive web dashboard + MCP Server (8 quantum tools for AI agents)
- `talk-to-ai/` – Multi-provider chat CLI (Azure OpenAI, OpenAI, LoRA, Local fallback)
- `AI/microsoft_phi-silica-3.6_v1/` – Phi-3.5 LoRA fine-tuning workspace (shared by all orchestrators)

**Integration Layer**: Root `function_app.py` (Azure Functions) dynamically imports from all three via `sys.path` injection:
- `/api/chat` - Multi-provider chat with memory/embeddings (streaming support)
- `/api/chat-web` - Web UI serving (HTML/JS frontend)
- `/api/tts` - Azure Speech + local fallback (pyttsx3/gTTS)
- `/api/quantum/*` - Quantum job submission/monitoring
- `/api/ai/status` - Unified health endpoint (providers, SQL, Cosmos, Quantum, AutoTrain status)
- `/api/vision/inference` - Image analysis (anime avatar generation)

**Shared Infrastructure** (`shared/`):
- **Provider abstraction**: `chat_providers.py` - `BaseChatProvider.complete()` interface with auto-detection (Azure OpenAI → OpenAI → LoRA → Local)
- **Persistence**: `sql_engine.py` (unified multi-DB engine: Azure SQL/PostgreSQL/MySQL/SQLite), `cosmos_client.py` (feature-flagged), `db_logging.py` (safe wrappers)
- **Memory**: `chat_memory.py` - Embeddings + similarity search for chat context
- **Observability**: `telemetry.py` - Application Insights integration (non-fatal init)

## Orchestrator-Driven Workflow

**Critical Pattern**: All training/quantum jobs are YAML-driven orchestrators in `scripts/`:
- `autotrain.py` → `autotrain.yaml` (LoRA fine-tuning jobs)
- `quantum_autorun.py` → `quantum_autorun.yaml` (quantum ML training)
- `evaluation_autorun.py` → `evaluation_autorun.yaml` (model evaluation)

**Advanced Automation** (multi-model orchestration):
- `automated_training_pipeline.py`: Single entry point for data gen + training + eval + ranking
- `parallel_train.py`: Concurrent multi-model training with shared evaluation
- `train_and_promote.py`: Full pipeline (train → evaluate → auto-deploy best model)

**Execution Protocol**:
1. **Always dry-run first**: `python .\scripts\autotrain.py --dry-run` (validates paths, config, dataset metadata without GPU/QPU execution)
2. **Consume status.json**: Read `data_out/<orchestrator>/status.json` for job states (never parse stdout/stderr for state)
3. **Respect data immutability**: Read-only from `datasets/`, write-only to `data_out/` (orchestrators run from repo root)
4. **Config precedence**: YAML base config < CLI flags < per-job YAML overrides < environment variables
5. **Status aggregation**: Use `master_orchestrator.py --status` for unified view across all orchestrators

**Example Status JSON**:
```json
{
  "jobs": [{"name": "phi35_mixed_chat", "status": "validated", "dataset_samples": 1000}],
  "errors": [],
  "timestamp": "2025-11-24T10:30:00Z"
}
```

**Ranking Metrics** (parallel_train.py, automated_training_pipeline.py):
- `perplexity_improvement`: Relative reduction (higher is better, default)
- `post_perplexity`: Final perplexity (lower is better, stored as negative for sorting)
- `diversity_avg` / `distinct_diversity`: Average of Distinct-1 & Distinct-2 (higher is better)
- `combined_improvement`: 70% perplexity + 30% diversity (balanced quality + variety)

## Provider Auto-Detection

**Detection Order** (see `shared/chat_providers.py:detect_provider()`):
1. **Azure OpenAI**: Requires ALL 4 env vars (`AZURE_OPENAI_API_KEY`, `ENDPOINT`, `DEPLOYMENT`, `API_VERSION`)
2. **OpenAI**: Requires `OPENAI_API_KEY`
3. **LoRA**: Auto-detect if `adapter_model.safetensors` exists in adapter dir
4. **Local Echo**: Zero-dependency fallback (no API calls)

**Health Check**: `GET /api/ai/status` shows `active_provider`, missing env vars, LoRA readiness (`adapter_config.json` + `adapter_model.safetensors`), and SQL/Cosmos/Telemetry status.

**Adding Providers**: Subclass `BaseChatProvider.complete(messages, stream)`, add detection logic to `detect_provider()`, test with `chat_cli.py --provider <name>`.

## MCP Server Integration (Quantum Tools for AI Agents)

**Location**: `quantum-ai/quantum_mcp_server.py` (8 quantum computing tools via Model Context Protocol)

### Available Tools

#### Circuit Creation & Simulation
- `create_quantum_circuit` - Build circuits (bell, ghz, entanglement, random, custom gate sequences)
- `simulate_quantum_circuit` - Local Qiskit Aer simulation (up to 100k shots, ~10 qubits practical limit)
- `get_quantum_circuit_properties` - Analyze circuit depth, gate counts, qubit connectivity

#### Azure Quantum Integration
- `connect_azure_quantum` - Authenticate to workspace (requires `az login` + valid `quantum_config.yaml`)
- `list_quantum_backends` - Enumerate available hardware/simulators with cost info
- `submit_quantum_job` - Execute on real quantum computers (IonQ, Quantinuum, Rigetti)
- `estimate_quantum_cost` - Calculate costs before running (gate-shot pricing)

#### Machine Learning
- `train_quantum_classifier` - Train hybrid quantum-classical models on iris/wine/breast_cancer/synthetic datasets

### VS Code Integration

**Method 1: MCP Settings** (if VS Code supports `.vscode/mcp.json`):
```json
{
  "mcpServers": {
    "quantum-ai": {
      "type": "stdio",
      "command": "python",
      "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"],
      "env": {}
    }
  }
}
```

**Method 2: Direct Invocation**:
```powershell
# Start MCP server in stdio mode
python .\quantum-ai\quantum_mcp_server.py

# Example client interaction (see example_mcp_client.py)
import json
request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "create_quantum_circuit", "arguments": {"circuit_type": "bell", "n_qubits": 2}}}
```

### Tool Usage Examples

**Example 1: Create and simulate Bell state**
```python
# Tool: create_quantum_circuit
{"circuit_type": "bell", "n_qubits": 2}
# Returns: Circuit definition with entangled |00⟩ + |11⟩ state

# Tool: simulate_quantum_circuit
{"circuit_qasm": "<from_previous>", "shots": 1000, "backend": "qiskit_aer"}
# Returns: {"00": 503, "11": 497}  # ~50/50 distribution
```

**Example 2: Cost estimation for real hardware**
```python
# Tool: estimate_quantum_cost
{"circuit_qasm": "<circuit>", "backend": "ionq.qpu", "shots": 500}
# Returns: {"estimated_cost_usd": 0.045, "gate_count": 3, "warning": "Real hardware execution"}
```

**Example 3: Train quantum ML model**
```python
# Tool: train_quantum_classifier
{"dataset": "iris", "n_qubits": 4, "n_layers": 2, "epochs": 10}
# Returns: {"final_accuracy": 0.94, "training_time_s": 45.2, "model_path": "..."}
```

### CircuitCache (Performance Optimization)

- **LRU Eviction**: Max 100 circuits cached (oldest evicted first)
- **TTL**: Cached results expire after 3600 seconds (1 hour)
- **Cache Key**: SHA256 hash of (circuit_qasm, shots, backend)
- **Bypass**: Set `use_cache=false` in tool arguments to force fresh execution

### Safety Limits

- **Max Qubits**: 10 (local simulator), 20 (Azure with approval)
- **Max Shots**: 1000 (default), 100000 (with `high_shots=true`)
- **Timeout**: 60 seconds per tool call
- **Cost Gate**: Azure jobs require explicit `confirm_cost=true` parameter

## Quantum Computing Boundaries

**Two Modes**:
- **Training**: `quantum-ai/train_custom_dataset.py` (long-running, local simulator, epochs/batching)
- **MCP Server**: `quantum-ai/quantum_mcp_server.py` (8 tools, ≤10 qubits, ≤1k shots, 60s timeout, CircuitCache with LRU+TTL)
- **Web Dashboard**: `quantum-ai/start_dashboard.sh` (interactive training UI at http://localhost:5000, real-time charts, session management)

**Cost Gates**:
- Local simulators (qiskit_aer, pennylane default.qubit): FREE
- Azure simulators (ionq.simulator): FREE
- **Paid QPU** (ionq.qpu, quantinuum.*): ~$0.00003-$0.00015 per gate-shot
  - Safety: YAML jobs require `azure_confirm_cost: true`
  - Always test Bell state on simulator first: `quantum_autorun.py --job azure_ionq_simulator --dry-run`

**Auth**: `az login` + valid `quantum-ai/config/quantum_config.yaml` (subscription_id, resource_group, workspace).

**Hardware Validation**: See `quantum-ai/HARDWARE_TEST_RESULTS.md` for multi-backend testing (Rigetti ✅ validated for production, Quantinuum ⚠️ has known bugs).

## Testing Strategy

**Fast Unit Tests** (40 tests, ~0.5s):
```powershell
pytest tests/ -m "not slow and not azure"
# Or via orchestrator (recommended): python .\scripts\test_runner.py --unit
```

**Integration Tests** (30 tests, external services):
```powershell
pytest tests/ -m "integration"  # 29/30 passing (requires external services)
```

**VS Code Test Explorer**: Native UI integration (🧪 sidebar) with breakpoint debugging. See `VSCODE_TESTING_QUICKREF.md` for keyboard shortcuts.
- `Ctrl+; Ctrl+A` - Run all tests
- `Ctrl+; Ctrl+F` - Run failed tests only
- Right-click test → "Debug Test" for breakpoint debugging

**Test Profiles** (configured in `.vscode/settings.json`):
- Unit Tests (Fast) - Quick feedback loop
- Integration Tests - External service validation
- All Fast Tests - Everything except slow/Azure (83 tests, ~10s)
- All with Coverage - Full suite + HTML report

**CI Pipeline**: `python .\scripts\ci_orchestrator.py --ci-pipeline` (5/10 critical steps passing: orchestrator validation + unit tests + artifact prep).

**Test Discovery**: `pytest.ini` configures `testpaths`, markers (`azure`, `slow`, `integration`, `unit`), and exclusions. Tests auto-discover from `tests/`, `quantum-ai/tests/`, `cooking-ai/tests/`.

## Dataset & Training Conventions

**Dataset Structure** (immutable):
- Location: `datasets/<category>/<name>/train.json` + `test.json`
- Categories: `chat/`, `quantum/`, `vision/`, `massive_quantum/`
- Format (chat): `[{"messages": [{"role": "user|assistant", "content": "..."}]}]`
- Index: `datasets/dataset_index.json` tracks all available datasets

**Dataset Validation**:
```powershell
python .\scripts\validate_datasets.py --category chat  # Validate chat datasets
python .\scripts\validate_datasets.py --category all   # Validate everything
```

**GPU Training**: `train_lora.py --device auto` (auto-detects cuda/directml/mps). Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"`. Install GPU build first: `pip install torch --index-url https://download.pytorch.org/whl/cu121`.

**Quick Smoke Test**:
```powershell
python .\AI\microsoft_phi-silica-3.6_v1\scripts\train_lora.py --dataset datasets/chat/mixed_chat --max-train-samples 64 --epochs 1
```

**LoRA Readiness Check**: Adapter ready when both exist:
- `data_out/lora_training/<job_name>/lora_adapter/adapter_config.json`
- `data_out/lora_training/<job_name>/lora_adapter/adapter_model.safetensors`

**Model Selection** (defined in `autotrain.yaml`):
- Phi-3.5: `microsoft/Phi-3.5-mini-instruct` (most efficient, 3.8B params)
- Qwen2.5: `Qwen/Qwen2.5-3B-Instruct` (excellent performance, no gating)
- TinyLlama: `TinyLlama/TinyLlama-1.1B-Chat-v1.0` (ultrafast CPU iteration, ~10-15s per run)

## Common Workflows

### Workflow 1: Full Training Pipeline (Data → Training → Evaluation → Deployment)

```powershell
# Step 1: Validate dataset exists
python .\scripts\validate_datasets.py --category chat

# Step 2: Dry-run to check config
python .\scripts\autotrain.py --dry-run

# Step 3: Train with auto-promote (deploys best model)
python .\scripts\train_and_promote.py --quick --auto-promote
# Output: deployed_models/<model_id>_<timestamp>/
# Status: deployed_models/LATEST.txt points to newest

# Step 4: Verify deployment
python .\talk-to-ai\src\chat_cli.py --provider lora --model deployed_models/$(cat deployed_models/LATEST.txt)
```

### Workflow 2: Multi-Model Comparison

```powershell
# Train Phi-3.5 and Qwen2.5 in parallel
python .\scripts\parallel_train.py --models phi,qwen --quick --ranking-metric combined_improvement

# Results ranked by 70% perplexity + 30% diversity
# View rankings: cat data_out/parallel_training/status.json | jq '.job_ranking'

# Deploy winner automatically
python .\scripts\model_deployer.py --deploy best --strategy canary
```

### Workflow 3: Hyperparameter Tuning

```powershell
# Grid search across learning rates and batch sizes
python .\scripts\training_scheduler.py --grid-search \
    --learning-rates 1e-5 2e-5 5e-5 \
    --batch-sizes 4 8 16 \
    --epochs-list 2 3

# Review results
python .\scripts\training_analytics.py --compare phi qwen tinyllama
```

### Workflow 4: Quantum ML Training

```powershell
# Step 1: Test on local simulator (FREE)
python .\scripts\quantum_autorun.py --job local_simulator --dry-run
python .\scripts\quantum_autorun.py --job local_simulator

# Step 2: Validate on Azure simulator (FREE)
python .\scripts\quantum_autorun.py --job azure_ionq_simulator

# Step 3: Run on real hardware (PAID - requires azure_confirm_cost: true)
# Edit quantum_autorun.yaml, add: azure_confirm_cost: true
python .\scripts\quantum_autorun.py --job azure_ionq_qpu

# Monitor results: data_out/quantum_autorun/<job>/results.json
```

### Workflow 5: Continuous Integration

```powershell
# Full CI pipeline (5/10 steps passing)
python .\scripts\ci_orchestrator.py --ci-pipeline

# Review results
cat data_out/ci_orchestrator/ci_results.json | jq '.steps[] | select(.status != "passed")'

# Fix failing steps and re-run
python .\scripts\ci_orchestrator.py --validate-all
```

### Workflow 6: Adding a New Dataset

```powershell
# Step 1: Create dataset directory
mkdir datasets/chat/my_dataset

# Step 2: Add train.json and test.json (see existing datasets for format)
# Format: [{"messages": [{"role": "user|assistant", "content": "..."}]}]

# Step 3: Update dataset index
python .\scripts\validate_datasets.py --category chat --update-index

# Step 4: Add job to autotrain.yaml
# - name: my_custom_job
#   dataset: datasets/chat/my_dataset
#   ...

# Step 5: Dry-run to validate
python .\scripts\autotrain.py --job my_custom_job --dry-run

# Step 6: Execute training
python .\scripts\autotrain.py --job my_custom_job
```

### Workflow 7: Web Dashboard (Quantum Training)

```bash
# Start interactive dashboard
cd quantum-ai
./start_dashboard.sh

# Open browser: http://localhost:5000
# 1. Select dataset (iris/wine/breast_cancer)
# 2. Configure: qubits (2-10), layers (1-5), learning rate
# 3. Click "Start Training"
# 4. Watch real-time loss/accuracy charts
# 5. Download trained model or view session history
```

## Database & Observability (Optional)

**SQL Logging** (unified engine supports Azure SQL, PostgreSQL, MySQL, SQLite):

**Setup**:
```powershell
# Azure SQL (recommended for production)
$env:QAI_DB_CONN = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=qai;Uid=myuser;Pwd=mypass;Encrypt=yes;TrustServerCertificate=no;"

# PostgreSQL
$env:QAI_DB_CONN = "postgresql://user:pass@localhost:5432/qai"

# SQLite (local dev - no setup needed)
$env:QAI_DB_CONN = "sqlite:///c:/Users/Bryan/OneDrive/AI/data_out/qai.db"

# Run migrations
python .\scripts\sql_migrate.py
```

**Tables Created**:
- `ChatConversations` - Message history with embeddings
- `QuantumTrainingRuns` - Quantum job metadata and results
- `LoRATrainingRuns` - Fine-tuning metrics and hyperparameters
- `EmbeddingCache` - Vector similarity cache

**Connection Pooling**:
- Pool size: 5-20 connections (auto-scales)
- Saturation threshold: 80% (triggers warning in `/api/ai/status`)
- Idle timeout: 300 seconds
- Monitor: `python .\scripts\sql_health_monitor.py`

**Graceful Degradation**: All `log_*_safe()` functions no-op if DB unavailable (chat endpoints remain functional)

**Health Check**: `GET /api/ai/status` → `sql.pool.saturation_alert` (≥80% = warning)

**Cosmos DB Persistence** (feature-flagged):

**Setup**:
```powershell
# Required environment variables
$env:QAI_ENABLE_COSMOS = "true"
$env:COSMOS_ENDPOINT = "https://myaccount.documents.azure.com:443/"
$env:COSMOS_KEY = "<your-primary-key>"
$env:COSMOS_DATABASE = "qai"
$env:COSMOS_CONTAINER = "chat_sessions"

# Persistence strategy
$env:QAI_COSMOS_PERSIST_STRATEGY = "messages"  # or "sessions"
```

**Strategies**:
- `messages`: Store each message individually (better for large conversations, supports TTL)
- `sessions`: Store entire conversation as one document (better for retrieval, simpler queries)

**Container Requirements**:
- Partition key: `/session_id` (recommended) or `/user_id`
- Indexing policy: Include `/timestamp` and `/role` for efficient queries
- TTL: Enable with default `-1` (inherit from documents)

**Cost Optimization**:
- Use autoscale RU/s (min 1000, max 4000 for development)
- Set TTL on messages: 30 days for ephemeral, unlimited for important
- Query pattern: Point reads (1 RU) > queries (3-5 RU) > cross-partition (10+ RU)

**Graceful Degradation**: Cosmos failures logged to Application Insights but don't block `/api/chat` endpoint

**Telemetry Integration**: All Cosmos operations tracked in Application Insights with `cosmos_persisted=true/false` span attributes

**Telemetry** (Application Insights):
- Enable: `APPLICATIONINSIGHTS_CONNECTION_STRING` env var
- Spans: `/api/chat` annotated with provider, model, duration_ms, memory_injected, cosmos_persisted
- See `TELEMETRY_COSMOS_ENABLEMENT.md` for setup

## Key Commands Reference

```powershell
# Orchestrator dry-runs (validation only)
python .\scripts\autotrain.py --dry-run
python .\scripts\quantum_autorun.py --dry-run
python .\scripts\evaluation_autorun.py --dry-run

# Run specific job
python .\scripts\autotrain.py --job phi35_mixed_chat

# Advanced automation (NEW)
python .\scripts\automated_training_pipeline.py --quick  # Multi-model training + eval
python .\scripts\parallel_train.py --models phi,qwen --quick  # Parallel execution
python .\scripts\train_and_promote.py --quick --auto-promote  # Train + deploy best

# Azure Functions local dev
func host start  # Serves /api/chat, /api/ai/status, /api/quantum/*, /api/chat-web

# Chat CLI (multi-provider)
python .\talk-to-ai\src\chat_cli.py --provider azure --once "Test"
python .\talk-to-ai\src\chat_cli.py --provider lora --model data_out/lora_training/lora_adapter

# MCP Server (quantum tools for AI agents)
python .\quantum-ai\quantum_mcp_server.py

# Quantum Web Dashboard
cd quantum-ai; ./start_dashboard.sh  # Opens http://localhost:5000

# Testing
pytest tests/ -m "not slow and not azure"  # Fast unit tests
python .\scripts\test_runner.py --all --coverage  # Full suite + HTML report
python .\scripts\ci_orchestrator.py --ci-pipeline  # Full CI validation

# Dataset validation
python .\scripts\validate_datasets.py --category chat

# Status checks
python .\scripts\master_orchestrator.py --status  # All orchestrators
curl http://localhost:7071/api/ai/status | jq  # Runtime health

# VS Code Tasks (Ctrl+Shift+P → "Run Task")
# Available: AutoTrain (dry-run/all), LoRA quick, Quantum AutoRun, CI Pipeline,
# Master Orchestrator, Train & Promote, Resource Monitor, Batch Evaluator, Tests
```

## Troubleshooting Guide

### Provider Detection Issues

**Problem**: Chat endpoint returns "Local Echo" instead of Azure/OpenAI

**Solution**:
```powershell
# Check which env vars are missing
curl http://localhost:7071/api/ai/status | jq '.env'

# Azure OpenAI requires ALL 4:
$env:AZURE_OPENAI_API_KEY = "your-key"
$env:AZURE_OPENAI_ENDPOINT = "https://your-resource.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-08-01-preview"

# Restart Functions host
func host start
```

### LoRA Model Won't Load

**Problem**: `FileNotFoundError: adapter_model.safetensors not found`

**Diagnosis**:
```powershell
# Check adapter directory exists
ls data_out/lora_training/<job_name>/lora_adapter/

# Must contain BOTH files:
# - adapter_config.json
# - adapter_model.safetensors
```

**Solutions**:
1. **Training didn't complete**: Check `data_out/autotrain/<job>/last_run.json` for errors
2. **Wrong path**: Use absolute path or ensure working directory is repo root
3. **Base model mismatch**: Verify `adapter_config.json` → `base_model_name_or_path` matches your local model

### CUDA Not Available

**Problem**: `torch.cuda.is_available()` returns `False`

**Solutions**:
```powershell
# 1. Check GPU is visible
nvidia-smi

# 2. Reinstall PyTorch with CUDA support
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Verify installation
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"}')"
```

### Test Discovery Failures

**Problem**: VS Code Test Explorer shows "No tests found"

**Solutions**:
1. **Check pytest.ini exists in repo root**:
   ```powershell
   cat pytest.ini
   ```

2. **Verify Python interpreter**: Select correct venv in VS Code (Ctrl+Shift+P → "Python: Select Interpreter")

3. **Clear test cache**:
   ```powershell
   Remove-Item -Recurse -Force .pytest_cache, __pycache__
   ```

4. **Reload window**: Ctrl+Shift+P → "Developer: Reload Window"

### Quantum Job Stuck "Running"

**Problem**: Azure Quantum job status never updates

**Diagnosis**:
```powershell
# Check job status directly
az quantum job show -g <resource-group> -w <workspace> -j <job-id> --query "status"
```

**Common Causes**:
- **Backend offline**: Check `az quantum workspace show` for provider status
- **Queue backlog**: IonQ/Quantinuum may have 30min+ wait times
- **Job failed silently**: Check Azure portal → Quantum workspace → Jobs for error details

**Workaround**: Use simulator first to validate circuit:
```powershell
python .\scripts\quantum_autorun.py --job azure_ionq_simulator
```

### SQL Connection Pool Saturation

**Problem**: `/api/ai/status` shows `saturation_alert: true`

**Immediate Fix**:
```powershell
# Increase pool size (temporary)
$env:QAI_SQL_POOL_SIZE = "20"  # Default: 10

# Restart app
func host start
```

**Long-term Solutions**:
1. **Add connection timeout**: Set `pool_timeout=30` in connection string
2. **Reduce query frequency**: Cache frequent lookups (embeddings, user profiles)
3. **Scale database tier**: Upgrade Azure SQL to higher DTU/vCore

### Streaming Chat Returns Gibberish

**Problem**: Chat response contains `data: [DONE]` or JSON fragments

**Cause**: Client not handling Server-Sent Events (SSE) correctly

**Solution** (JavaScript example):
```javascript
const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({messages, stream: true}),
    headers: {'Content-Type': 'application/json'}
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const {done, value} = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n').filter(line => line.startsWith('data: '));
    
    for (const line of lines) {
        if (line === 'data: [DONE]') continue;
        const data = JSON.parse(line.slice(6));
        console.log(data.content);  // Actual message content
    }
}
```

### Dataset Validation Fails

**Problem**: `validate_datasets.py` reports "Invalid format"

**Check Format**:
```powershell
# Valid chat dataset structure
cat datasets/chat/example/train.json | jq '.[0]'
# Output should be:
# {
#   "messages": [
#     {"role": "user", "content": "Hello"},
#     {"role": "assistant", "content": "Hi there!"}
#   ]
# }
```

**Common Issues**:
- Missing `messages` key (should not be `conversations` or `data`)
- Wrong role names (`human/ai` should be `user/assistant`)
- Empty content fields
- Invalid JSON (trailing commas, unquoted keys)

**Auto-fix script**:
```powershell
python .\scripts\env_autofix.py --fix-datasets --category chat
```

## Common Pitfalls

1. **Azure OpenAI not detected**: Missing any of 4 required env vars (check `/api/ai/status` → `env.azure_openai`)
2. **LoRA fails to load**: Missing `adapter_model.safetensors` or base model mismatch in `adapter_config.json`
3. **Quantum job cost surprises**: Forgot `azure_confirm_cost: true` in YAML (safety gate prevents execution)
4. **Status JSON outdated**: Each orchestrator writes independent status files; use master_orchestrator for unified view
5. **Dataset not found**: Orchestrators run from repo root; relative paths in YAML assume `datasets/` prefix
6. **Parallel training conflicts**: `parallel_train.py` uses ThreadPoolExecutor; avoid running concurrent instances manually
7. **VS Code tasks not found**: Ensure `.vscode/tasks.json` exists; tasks auto-register from workspace config
8. **Import errors in function_app.py**: Check `sys.path` injections point to correct venv for each sub-project
9. **Test discovery failures**: `pytest.ini` must be in repo root; virtual envs excluded via `norecursedirs`
10. **Streaming chat broken**: Verify `openai>=1.37.0` installed; streaming requires async iteration support

## Safety & Secrets

- **No secrets in git**: Use `local.settings.json` (dev) or Azure App Settings (prod)
- **Dry-run everything first**: Prevents costly GPU/QPU runs with bad configs
- **Initial QPU shots ≤100**: Incremental cost validation before scaling
- **SQL connection pooling**: Monitor saturation alerts in `/api/ai/status` (threshold: 80% of max connections)

## References

- **AUTOTRAIN_README.md**: LoRA training orchestration details
- **QUANTUM_AUTORUN_README.md**: Quantum job configuration & Azure submission
- **TELEMETRY_COSMOS_ENABLEMENT.md**: Observability stack setup
- **VSCODE_TESTING_QUICKREF.md**: Test Explorer keyboard shortcuts
- **ADVANCED_AUTOMATION.md**: Multi-level orchestration architecture
- **AUTOMATION_QUICKREF.md**: One-command training pipelines
- **scripts/README.md**: Comprehensive script documentation
- **Root README.md**: Project overviews, quick starts, deployment guides
- **quantum-ai/WEB_DASHBOARD_README.md**: Interactive training UI guide
- **quantum-ai/HARDWARE_TEST_RESULTS.md**: Multi-backend validation results
- **quantum-ai/MCP_SERVER_README.md**: Quantum tools for AI agents

## Workspace Structure Quick Reference

```
AI/                                  # Root workspace
├── .github/
│   └── copilot-instructions.md     # This file (AI agent guidance)
├── shared/                          # Cross-project shared modules
│   ├── chat_providers.py            # Multi-provider abstraction (Azure/OpenAI/LoRA/Local)
│   ├── sql_engine.py                # Unified DB engine (Azure SQL/PostgreSQL/MySQL/SQLite)
│   ├── cosmos_client.py             # Feature-flagged Cosmos persistence
│   ├── chat_memory.py               # Embeddings + similarity search
│   ├── telemetry.py                 # Application Insights integration
│   └── db_logging.py                # Safe database logging wrappers
├── scripts/                         # Automation & orchestration
│   ├── autotrain.py                 # LoRA training orchestrator
│   ├── quantum_autorun.py           # Quantum ML job runner
│   ├── evaluation_autorun.py        # Model evaluation pipeline
│   ├── parallel_train.py            # Concurrent multi-model training
│   ├── automated_training_pipeline.py  # Single-entry multi-model automation
│   ├── train_and_promote.py         # Full train→eval→deploy pipeline
│   ├── test_runner.py               # Centralized test orchestrator
│   ├── ci_orchestrator.py           # CI/CD pipeline coordinator
│   ├── master_orchestrator.py       # High-level workflow coordinator
│   └── README.md                    # Comprehensive script documentation
├── datasets/                        # Immutable training data
│   ├── chat/                        # Chat conversation datasets
│   ├── quantum/                     # Quantum ML datasets
│   ├── vision/                      # Image/vision datasets
│   ├── massive_quantum/             # Large-scale quantum datasets
│   └── dataset_index.json           # Dataset catalog
├── data_out/                        # All training outputs (write-only)
│   ├── lora_training/               # LoRA adapter outputs
│   ├── autotrain/                   # AutoTrain job logs/status
│   ├── quantum_autorun/             # Quantum training results
│   ├── evaluation_autorun/          # Evaluation metrics
│   └── parallel_training/           # Parallel job aggregated results
├── deployed_models/                 # Production-ready model snapshots
│   └── LATEST.txt                   # Symlink to most recent deployment
├── quantum-ai/                      # Quantum ML project (isolated venv)
│   ├── src/                         # Quantum ML source code
│   ├── quantum_mcp_server.py        # MCP server (8 quantum tools)
│   ├── start_dashboard.sh           # Web dashboard launcher
│   ├── config/quantum_config.yaml   # Quantum workspace configuration
│   └── tests/                       # Quantum-specific tests
├── talk-to-ai/                      # Chat CLI project (isolated venv)
│   └── src/
│       ├── chat_cli.py              # Multi-provider chat interface
│       └── token_utils.py           # Token management
├── AI/microsoft_phi-silica-3.6_v1/  # LoRA fine-tuning workspace
│   ├── scripts/train_lora.py        # HuggingFace LoRA trainer
│   └── lora/lora.yaml               # LoRA configuration
├── function_app.py                  # Azure Functions entry point
├── autotrain.yaml                   # AutoTrain job definitions
├── quantum_autorun.yaml             # Quantum job configurations
├── evaluation_autorun.yaml          # Evaluation job specs
├── pytest.ini                       # Test configuration
├── .vscode/
│   ├── tasks.json                   # 30+ predefined VS Code tasks
│   └── settings.json                # Test profiles & editor config
└── tests/                           # Root test suite (68+ tests)
    ├── test_autotrain_unit.py       # AutoTrain unit tests
    ├── test_quantum_integration.py   # Quantum integration tests
    └── test_chat_providers.py       # Provider detection tests
```

**Key Principles**:
- **Immutable datasets**: Never modify files in `datasets/` - always write to `data_out/`
- **Isolated venvs**: Each sub-project (quantum-ai, talk-to-ai, AI/*) has its own venv
- **Shared infrastructure**: Common code in `shared/` used by all projects via `sys.path` injection
- **YAML-driven**: All training/quantum jobs defined declaratively in YAML files
- **Status files**: Machine-readable JSON status in `data_out/<orchestrator>/status.json`

Last updated: 2025-11-27
