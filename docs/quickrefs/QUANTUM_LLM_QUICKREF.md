# Quantum LLM Quick Reference

## Fast reference for daily quantum LLM development

---

## 🚀 Quick Commands

```bash
# Test system (5 min)
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode quick

# Full training
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode full

# With custom config
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode full --config config/my_config.yaml

# Monitor training
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode monitor --output-dir data_out/quantum_llm_quickstart

# Generate text
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode generate --model model.pt --prompt "Hello"

# Validate system
python ai-projects/quantum-ml/validate_quantum_llm.py --full

# Chat with trained quantum LLM (CLI)
python ai-projects/chat-cli/src/chat_cli.py --provider quantum --model data_out/quantum_llm_chat --once "Hello quantum"

# Chat via API payload (when function host is running)
# provider=quantum and model points to trained checkpoint directory
# {"messages":[{"role":"user","content":"Hello"}],"provider":"quantum","model":"data_out/quantum_llm_chat"}

# Compare old vs new
python ai-projects/quantum-ml/quantum_llm_integration.py --mode compare

# Component tests
python ai-projects/quantum-ml/src/quantum_llm_advanced.py
python ai-projects/quantum-ml/src/quantum_circuit_optimizer.py
python ai-projects/quantum-ml/src/quantum_llm_monitor.py
```

---

## 📦 Components at a Glance

| Component      | What It Does                                   | Import                                     |
| -------------- | ---------------------------------------------- | ------------------------------------------ |
| **advanced**   | Cache, multi-scale attention, error mitigation | `from quantum_llm_advanced import *`       |
| **optimizer**  | Circuit compilation, batch execution           | `from quantum_circuit_optimizer import *`  |
| **trainer**    | Curriculum learning, orchestration             | `from quantum_llm_hybrid_trainer import *` |
| **monitor**    | Dashboard, alerts, profiling                   | `from quantum_llm_monitor import *`        |
| **integrated** | Complete system                                | `from quantum_llm_integrated import *`     |
| **datasets**   | Tokenizer, data loading                        | `from quantum_llm_datasets import *`       |

---

## ⚙️ Key Configuration Options

```yaml
# Essential settings
vocab_size: 256 # Character vocab
d_model: 128 # Model dimension
n_qubits: 4 # Qubits per layer
enable_multi_scale_attention: true # Use 2-6 qubits
enable_circuit_caching: true # 2-5x speedup
enable_curriculum: true # Stable training
optimization_level: 2 # 0=none, 3=max
batch_size: 16 # Training batch
learning_rate: 0.0001 # LR
num_epochs: 10 # Training epochs
```

---

## 🔬 Advanced Features

### Multi-Scale Attention

```python
from quantum_llm_advanced import MultiScaleQuantumAttention

attention = MultiScaleQuantumAttention(
    d_model=128,
    n_heads=4,
    n_qubits_per_head=[2, 3, 4, 6]  # Different scales
)
```

### Circuit Caching

```python
from quantum_llm_advanced import QuantumCircuitCache

cache = QuantumCircuitCache(cache_size=1000)
cache.put("circuit_key", result)
cached_result = cache.get("circuit_key")
```

### Curriculum Training

```python
from quantum_llm_hybrid_trainer import TrainingStage

stages = [
    TrainingStage("warmup", quantum_ratio=0.0, num_epochs=2),
    TrainingStage("transition", quantum_ratio=0.3, num_epochs=3),
    TrainingStage("full", quantum_ratio=0.7, num_epochs=10),
]
```

### Real-time Monitoring

```python
from quantum_llm_monitor import TrainingDashboard

dashboard = TrainingDashboard(
    output_dir=Path("data_out/dashboard"),
    update_interval=10,
    enable_alerts=True
)
```

---

## 📊 Performance Tips

1. **Enable caching** for character-level: `enable_circuit_caching: true`
2. **Use curriculum** for stable training: `enable_curriculum: true`
3. **Optimize circuits** for speed: `optimization_level: 2`
4. **Smaller batches** for quantum: `batch_size: 4-8`
5. **Multi-scale** for accuracy: `enable_multi_scale_attention: true`

---

## 🐛 Troubleshooting

### Import errors

```bash
cd ai-projects/quantum-ml
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Missing dependencies

```bash
pip install torch pennylane pyyaml numpy
```

### Training instability

- Enable curriculum learning
- Reduce learning rate
- Increase warmup epochs
- Lower quantum ratio initially

### Slow training

- Enable circuit caching
- Increase optimization level
- Reduce circuit depth
- Use adaptive entanglement

---

## 📁 Output Structure

```text
data_out/quantum_llm_quickstart/
├── final_model.pt                 # Trained model
├── config.yaml                    # Used configuration
├── system_report.json             # System metrics
├── dashboard/
│   └── dashboard.json             # Live dashboard
├── training/
│   ├── training_report.json       # Training summary
│   └── checkpoint_*.pt            # Checkpoints
└── visualizations/
    ├── loss_curve.json            # Loss data
    └── quantum_metrics.json       # Quantum data
```

---

## 🔗 Documentation Links

- **Complete Guide:** `ai-projects/quantum-ml/QUANTUM_LLM_README.md`
- **Config Example:** `config/quantum_llm_config_example.yaml`
- **Development Summary:** `docs/QUANTUM_LLM_DEVELOPMENT_SUMMARY.md`
- **Build Complete:** `QUANTUM_LLM_BUILD_COMPLETE.md`

---

## 💡 Common Workflows

### Quick Test

```bash
python quantum_llm_quickstart.py --mode quick
# Output: data_out/quantum_llm_quickstart/
```

### Research Experiment

```bash
# 1. Copy config template
cp config/quantum_llm_config_example.yaml config/my_experiment.yaml

# 2. Edit configuration
nano config/my_experiment.yaml

# 3. Run training
python quantum_llm_quickstart.py --mode full --config config/my_experiment.yaml

# 4. Monitor results
python quantum_llm_quickstart.py --mode monitor --output-dir data_out/quantum_llm_full
```

### Production Training

```bash
# With comprehensive monitoring
python quantum_llm_quickstart.py --mode full \
    --config config/production_config.yaml \
    > data_out/training.log 2>&1 &

# Monitor in real-time
watch -n 5 'cat data_out/quantum_llm_full/dashboard/dashboard.json | python -m json.tool'
```

---

## 🎯 One-Liners

```bash
# Quick test
python ai-projects/quantum-ml/quantum_llm_quickstart.py --mode quick

# Validate
python ai-projects/quantum-ml/validate_quantum_llm.py --full

# Compare systems
python ai-projects/quantum-ml/quantum_llm_integration.py --mode compare

# Test tokenizer
python -c "from quantum_llm_datasets import CharacterTokenizer; t=CharacterTokenizer(); print(t.decode(t.encode('Hello')))"

# Check config
python -c "from quantum_llm_integrated import QuantumLLMConfig; c=QuantumLLMConfig(); print(f\"Model: {c['d_model']}d, {c['n_qubits']}q\")"
```

---

**Last Updated:** March 9, 2026
**Version:** 1.0.0
