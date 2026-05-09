# QAI Integration Service

A unified microservice that integrates and orchestrates all QAI workspace components: Quantum AI, Chat systems, and Training pipelines.

**✨ NEW: Beautiful Web UI included!** See [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) for details.

## 🎯 Purpose

This service provides a single REST API to:
- **Quantum AI**: Train quantum classifiers, manage backends, run autorun jobs
- **Chat**: Interface with multiple providers (local, Azure OpenAI, LoRA), manage conversations
- **Training**: Run LoRA training, orchestrate autotrain jobs, monitor training runs

## 🚀 Quick Start

### Installation

```powershell
cd mount
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuration

Edit `config.yaml` to customize:
- Service settings (host, port, debug mode)
- Paths to other QAI components
- Enable/disable specific integrations
- API settings (CORS, rate limiting)

### Run the Service

```powershell
# Quick start with web UI
.\start.ps1

# Or manual start
python app.py

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Access the Web UI**: Open http://localhost:8000 in your browser

**Access the API docs**: http://localhost:8000/docs

## 📚 API Documentation

Once running, visit:
- **🎨 Web UI**: <http://localhost:8000> (Main interface)
- **Interactive API docs**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/openapi.json>

**Prefer the Web UI?** See the complete [Web UI Guide](WEB_UI_GUIDE.md)

## 🔌 Endpoints

### Root & Health

- `GET /` - Service information
- `GET /health` - Health check
- `GET /status` - Comprehensive system status

### Quantum AI (`/quantum/*`)

- `GET /quantum/status` - Quantum system status
- `GET /quantum/datasets` - List quantum datasets
- `GET /quantum/backends` - List available backends
- `GET /quantum/circuit-info` - Circuit type information
- `POST /quantum/train` - Train quantum classifier
- `POST /quantum/autorun` - Run quantum autorun job

Example:
```bash
curl -X POST http://localhost:8000/quantum/train \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "heart",
    "n_qubits": 4,
    "epochs": 10,
    "backend": "qiskit_aer"
  }'
```

### Chat (`/chat/*`)

- `GET /chat/status` - Chat system status
- `GET /chat/providers` - Available providers and their status
- `GET /chat/detect-provider` - Auto-detect best provider
- `POST /chat/message` - Send message and get response
- `GET /chat/conversations` - List saved conversations
- `GET /chat/conversations/{filename}` - Get specific conversation

Example:
```bash
curl -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "provider": "local"
  }'
```

### Training (`/training/*`)

- `GET /training/status` - Training system status
- `GET /training/datasets` - List available datasets
- `GET /training/lora-adapter` - LoRA adapter info
- `GET /training/runs` - List training runs
- `GET /training/runs/{run_name}` - Get specific run metrics
- `GET /training/autotrain/jobs` - List autotrain jobs
- `POST /training/lora` - Train LoRA adapter
- `POST /training/autotrain` - Run autotrain orchestrator

Example:
```bash
curl -X POST http://localhost:8000/training/lora \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": "../../datasets/chat/dolly",
    "max_train_samples": 64,
    "epochs": 1
  }'
```

## 🏗️ Architecture

```
mount/
├── app.py                      # FastAPI application
├── config.yaml                 # Configuration file
├── quantum_integration.py      # Quantum AI integration
├── chat_integration.py         # Chat integration
├── training_integration.py     # Training integration
└── requirements.txt            # Python dependencies
```

### Integration Modules

Each integration module provides:
- **Status checking**: Current state and availability
- **Operation execution**: Run jobs, train models, send messages
- **Data retrieval**: List datasets, conversations, results
- **Configuration**: Load and validate settings

### Design Patterns

- **Async/await**: Non-blocking operations
- **Background tasks**: Long-running operations (training, etc.)
- **Subprocess execution**: Isolated execution of existing scripts
- **CORS support**: Cross-origin requests for web frontends
- **Pydantic validation**: Type-safe request/response models

## 🔧 Configuration

### Service Settings

```yaml
service:
  name: qai-integration-service
  version: 0.1.0
  host: 0.0.0.0
  port: 8000
  debug: true
```

### Path Configuration

All paths are relative to the workspace root:

```yaml
paths:
  workspace_root: ..
  quantum_ai: ../quantum-ai
  talk_to_ai: ../talk-to-ai
  phi_training: ../AI/microsoft_phi-silica-3.6_v1
  datasets: ../datasets
  data_out: ../data_out
```

### Feature Flags

Enable/disable integrations:

```yaml
quantum:
  enabled: true
chat:
  enabled: true
training:
  enabled: true
```

## 💡 Usage Examples

### Check Overall Status

```powershell
curl http://localhost:8000/status
```

### Train Quantum Classifier

```powershell
$body = @{
    dataset = "heart"
    n_qubits = 4
    epochs = 10
    backend = "qiskit_aer"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/quantum/train -Method Post -Body $body -ContentType "application/json"
```

### Chat with Local Provider

```powershell
$body = @{
    message = "What is quantum computing?"
    provider = "local"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/chat/message -Method Post -Body $body -ContentType "application/json"
```

### Run AutoTrain Job

```powershell
$body = @{
    job_name = "phi36_mixed_chat"
    dry_run = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/training/autotrain -Method Post -Body $body -ContentType "application/json"
```

## 🐛 Debugging

### Enable Debug Logging

Set `debug: true` in `config.yaml` or run with:

```powershell
$env:LOG_LEVEL = "DEBUG"
python app.py
```

### Check Integration Status

Each integration can be checked individually:

```powershell
curl http://localhost:8000/quantum/status
curl http://localhost:8000/chat/status
curl http://localhost:8000/training/status
```

## 🔐 Security Notes

- **Local development**: Default configuration is for local development only
- **Production**: Update CORS origins, enable rate limiting, add authentication
- **Environment variables**: Store API keys in environment, not config files
- **Network exposure**: Bind to `127.0.0.1` instead of `0.0.0.0` for local-only access

## 🚦 Testing

### Manual Testing

Use the interactive Swagger UI at http://localhost:8000/docs

### Automated Testing

```powershell
# Create test script
pytest tests/test_integration_service.py
```

### Health Check

```powershell
# Simple health check
curl http://localhost:8000/health

# Should return: {"status": "healthy", ...}
```

## 📈 Monitoring

### Status Endpoint

The `/status` endpoint provides comprehensive information:

```json
{
  "service": "qai-integration-service",
  "version": "0.1.0",
  "quantum": {
    "enabled": true,
    "backend": "qiskit_aer",
    "azure_connected": false,
    "available_backends": ["qiskit_aer", "lightning.qubit"],
    "recent_results": [...]
  },
  "chat": {
    "enabled": true,
    "default_provider": "local",
    "providers": {...}
  },
  "training": {
    "enabled": true,
    "orchestrators": {...},
    "lora_adapter": {...}
  }
}
```

## 🛠️ Development

### Adding New Endpoints

1. Add method to appropriate integration module
2. Create Pydantic models for request/response
3. Add route to `app.py`
4. Update this README

### Adding New Integration

1. Create new `*_integration.py` module
2. Implement `get_status()` method
3. Add to `config.yaml`
4. Import and initialize in `app.py`
5. Add routes

## 📝 Future Enhancements

- [ ] WebSocket support for streaming responses
- [ ] Authentication and authorization
- [ ] Rate limiting per endpoint
- [ ] Metrics collection (Prometheus)
- [ ] Job queuing system (Celery/Redis)
- [ ] Docker containerization
- [ ] Azure deployment templates
- [ ] Integration tests

## 🤝 Contributing

Follow the QAI workspace patterns:
- YAML-driven configuration
- Async operations where possible
- Comprehensive error handling
- Clear logging
- Type hints and Pydantic models

## 📄 License

Part of the QAI workspace. See root LICENSE file.
