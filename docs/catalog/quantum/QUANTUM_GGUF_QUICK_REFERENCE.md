# Quantum GGUF Infrastructure - Quick Reference

## 🎯 One-Line Commands

```bash
# Validate setup
python scripts/quantum_gguf_quickstart.py

# Dry-run (test without execution)
python scripts/quantum_gguf/gguf_orchestrator.py --dry-run

# Run full pipeline
python scripts/quantum_gguf/gguf_orchestrator.py --full

# Quick test mode
python scripts/quantum_gguf/gguf_orchestrator.py --quick

# Check model registry
python scripts/quantum_gguf/gguf_orchestrator.py --registry

# View orchestration status
python scripts/quantum_gguf/gguf_orchestrator.py --status

# Monitor dashboard (one-time)
python scripts/quantum_gguf/gguf_monitor.py

# Monitor dashboard (live, auto-refresh)
python scripts/quantum_gguf/gguf_monitor.py --watch --interval 10

# Export metrics to JSON
python scripts/quantum_gguf/gguf_monitor.py --export metrics.json

# Test quantum integration
python scripts/quantum_gguf/quantum_gguf_integration.py

# Validate GGUF model
python scripts/quantum_gguf/gguf_validation.py

# Test model serving
python scripts/quantum_gguf/gguf_serving.py
```

## 📂 Key Files

| File | Purpose |
|------|---------|
| `config/training/quantum_gguf.yaml` | Main configuration |
| `scripts/quantum_gguf/gguf_orchestrator.py` | Pipeline orchestrator |
| `scripts/quantum_gguf/gguf_registry.py` | Model registry |
| `scripts/quantum_gguf/quantum_gguf_integration.py` | Quantum circuits |
| `scripts/quantum_gguf/gguf_serving.py` | Model serving |
| `scripts/quantum_gguf/gguf_validation.py` | Testing/benchmarking |
| `scripts/quantum_gguf/gguf_monitor.py` | Monitoring |
| `data_out/quantum_gguf_training/status.json` | Current status |
| `data_out/quantum_gguf_training/gguf_registry.json` | Models metadata |

## 🔧 Configuration Quick Edit

```bash
# Edit main config
nano config/training/quantum_gguf.yaml

# Edit training jobs
# Look for "training.configs" section

# Edit quantization strategies
# Look for "conversion.quantization_strategies" section

# Edit quantum features
# Look for "quantum_enhancement.features" section
```

## 💻 Python Usage Examples

### Create Quantum Dataset
```python
from scripts.quantum_gguf.quantum_gguf_integration import create_quantum_enhanced_dataset
from pathlib import Path

output = create_quantum_enhanced_dataset(
    input_dataset=Path('datasets/chat/train.jsonl'),
    output_dir=Path('data_out/quantum_datasets'),
    quantum_features=['entanglement_patterns', 'amplitude_encoding']
)
```

### Query Model Registry
```python
from scripts.quantum_gguf.gguf_registry import GGUFRegistry

registry = GGUFRegistry()

# List all quantum-enhanced models
quantum_models = registry.list_models(quantum_enhanced=True)

# Get best model by speed
best = registry.get_best_model(metric="inference_speed_tokens_per_sec")

# Export summary
summary = registry.export_summary()
registry.print_summary()
```

### Serve Model
```python
from scripts.quantum_gguf.gguf_serving import create_server
from pathlib import Path

server = create_server("llama-cpp", Path("deployed_models/best_model.gguf"))
server.start()

result = server.inference("Hello world", max_tokens=256)
print(result)

server.stop()
```

### Validate & Benchmark
```python
from scripts.quantum_gguf.gguf_validation import GGUFValidator, GGUFBenchmark
from pathlib import Path

model = Path("deployed_models/best_model.gguf")

# Validate
validator = GGUFValidator(model)
validator.run_all_validations()

# Benchmark
benchmark = GGUFBenchmark(model)
result = benchmark.run_full_benchmark()
print(f"Speed: {result.inference_speed_tokens_per_sec} tok/s")
```

## 📊 Pipeline Phases

```
Phase 1: TRAINING
  Input: Base model + dataset + LoRA config
  Output: HF checkpoint with quantum enhancements
  
Phase 2: CONVERSION
  Input: HF checkpoint
  Output: GGUF files (q4_0, q5_0, q8_0, f16)
  
Phase 3: QUANTUM ENHANCEMENT
  Input: GGUF files
  Output: Quantum-enhanced embeddings + circuit data
  
Phase 4: VALIDATION
  Input: GGUF files + test datasets
  Output: Performance metrics + validation reports
  
Phase 5: DEPLOYMENT
  Input: Validated GGUF files
  Output: Production-ready models + serving configs
```

## 🎛️ Configuration Sections

### Quantum Features Available
- `entanglement_patterns` - Create quantum entanglement (linear/circular/full)
- `amplitude_encoding` - Convert classical data to quantum states
- `vqe_embeddings` - Variational quantum eigensolver patterns
- `qaoa_patterns` - Quantum approximate optimization patterns
- `quantum_gates_optimization` - Optimize quantum gate circuits

### Quantization Types
- `q4_0` - 4-bit (most compact)
- `q5_0` - 5-bit (balanced)
- `q8_0` - 8-bit (high precision)
- `f16` - 16-bit float (reference)

### Serving Platforms
- `llama-cpp` - Local CPU/GPU inference
- `vllm` - High-performance batched serving
- `azure_inference` - Cloud deployment

## 📈 Monitoring

```bash
# Watch-mode dashboard (updates every 10s)
watch -n 10 'python scripts/quantum_gguf/gguf_monitor.py'

# Tail logs
tail -f data_out/quantum_gguf_training/orchestrator.log

# Check status
cat data_out/quantum_gguf_training/status.json | python -m json.tool

# List models
cat data_out/quantum_gguf_training/gguf_registry.json | python -m json.tool
```

## 🚨 Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | `pip install pennylane numpy pyyaml` |
| `No models in registry` | Check `status.json` - ensure training phase completed |
| `Port 8000 in use` | Kill: `lsof -ti:8000 \| xargs kill -9` |
| `CUDA out of memory` | Reduce `max_train_samples` in config |
| `Dataset not found` | Verify `datasets/{chat,quantum}/` exist |
| `GGUF validation fails` | Use `gguf_validation.py` to diagnose |

## 🔗 Integration

### With Aria Character
```python
# aria_web/server.py
from scripts.quantum_gguf.gguf_serving import create_server
model = create_server("llama-cpp", Path("deployed_models/best_model.gguf"))
```

### With Azure Functions
```python
# function_app.py
from scripts.quantum_gguf.gguf_registry import GGUFRegistry

@app.route('api/gguf/models')
def list_gguf_models(req):
    registry = GGUFRegistry()
    return func.HttpResponse(json.dumps([...]))
```

### With Chat CLI
```bash
# Use GGUF model provider
python talk-to-ai/src/chat_cli.py --provider gguf \
  --model deployed_models/best_model.gguf \
  --once "Hello"
```

## 📚 Documentation

- Full guide: `docs/QUANTUM_GGUF_INFRASTRUCTURE.md`
- Setup status: `QUANTUM_GGUF_SETUP_COMPLETE.md`
- Config file: `config/training/quantum_gguf.yaml`

## ✅ Validation Checklist

- [ ] Quickstart passes: `python scripts/quantum_gguf_quickstart.py`
- [ ] Config is readable: `cat config/training/quantum_gguf.yaml`
- [ ] Dry-run succeeds: `python scripts/quantum_gguf/gguf_orchestrator.py --dry-run`
- [ ] Datasets exist: `ls -la datasets/`
- [ ] Python packages installed: `pip list | grep -E "(pennylane|numpy|pyyaml)"`

## 🎯 Typical Workflow

```bash
# 1. Validate setup
python scripts/quantum_gguf_quickstart.py

# 2. Edit config if needed
nano config/training/quantum_gguf.yaml

# 3. Test with dry-run
python scripts/quantum_gguf/gguf_orchestrator.py --dry-run

# 4. Run full pipeline
python scripts/quantum_gguf/gguf_orchestrator.py --full

# 5. Monitor progress
python scripts/quantum_gguf/gguf_monitor.py --watch

# 6. Check results
python scripts/quantum_gguf/gguf_orchestrator.py --registry

# 7. Deploy best model
# (Models auto-deployed to: deployed_models/)
```

---

**For detailed information**, see `docs/QUANTUM_GGUF_INFRASTRUCTURE.md`
