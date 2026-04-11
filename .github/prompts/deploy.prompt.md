---
description: "Deploy and promote AI models and services"
name: "Deploy"
argument-hint: "Target + model or service details (example: adapter path + deployment target + version tag)"
agent: platform-ops
---
# Deploy

Deploy, promote, or publish AI models and services on the Aria platform.

## Model Deployment

### LoRA Adapter Promotion
```bash
# Train + auto-promote if accuracy > threshold
python scripts/train_and_promote.py --quick --auto-promote

# Manual promotion
cp data_out/lora_training/best_model/adapter_*.* AI/microsoft_phi-silica-3.6_v1/adapters/
```

**Required files for valid LoRA adapter:**
- `adapter_config.json`
- `adapter_model.safetensors`

### Promotion Criteria
- Accuracy > 0.90 (configurable in `config/autonomous_training.yaml`)
- Performance regression detection: alert on > 5% accuracy drop
- Must pass evaluation suite before deployment

## Service Deployment

### Azure Functions
```bash
# Validate locally first
func host start
curl http://localhost:7071/api/ai/status | jq

# Deploy to Azure
func azure functionapp publish <app-name>
```

### Local Development
```bash
python local_dev_adapter.py  # Flask wrapper on port 5000
```

### Aria Character Server
```bash
cd apps/aria && python server.py  # Port 8080
```

### Dashboard
```bash
cd apps/dashboard && python serve.py  # Monitoring UI
```

## Pre-Deployment Checklist

- [ ] Run unit tests: `python scripts/test_runner.py --unit`
- [ ] Run fast validation: `python scripts/fast_validate.py`
- [ ] Check health: `curl http://localhost:7071/api/ai/status | jq`
- [ ] Verify no hardcoded secrets
- [ ] Review subscription gating for new endpoints
- [ ] Update `local.settings.json.example` if new env vars added

## Environment Variables

Never hardcode. Use:
- **Local dev**: `local.settings.json`
- **Production**: Azure App Settings
- **CI/CD**: GitHub Secrets

Deploy: {{input}}
