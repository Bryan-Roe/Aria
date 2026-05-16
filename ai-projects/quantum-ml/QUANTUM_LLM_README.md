# Quantum LLM - Advanced Components

**Quantum-Enhanced Language Model Training System**

Complete implementation of quantum-classical hybrid language model training with advanced features for circuit optimization, adaptive training, and real-time monitoring.

---

## 🚀 Quick Start

```bash
# Test with minimal training (2 epochs, 64-dim model)
python quantum_llm_quickstart.py --mode quick

# Full training with all features
python quantum_llm_quickstart.py --mode full --config config/quantum_llm_config.yaml

# Monitor ongoing training
python quantum_llm_quickstart.py --mode monitor --output-dir data_out/quantum_llm_quickstart

# Generate text with trained model
python quantum_llm_quickstart.py --mode generate --model data_out/quantum_llm_quickstart/final_model.pt --prompt "Quantum computing"
```

---

## 📦 Components

### Core Files

| File | Purpose | Features |
| ------ | --------- | ---------- |
| **quantum_llm_advanced.py** | Advanced quantum layers | Circuit caching, adaptive entanglement, multi-scale attention, prompt tuning, error mitigation |
| **quantum_circuit_optimizer.py** | Circuit optimization | Circuit compilation, batch execution, adaptive scheduling, quantum/classical partitioning |
| **quantum_llm_hybrid_trainer.py** | Hybrid training orchestration | Curriculum learning, adaptive routing, multi-stage training |
| **quantum_llm_monitor.py** | Training monitoring | Real-time dashboard, metrics aggregation, performance profiling, alert system |
| **quantum_llm_integrated.py** | Complete integration | Unified system combining all components |
| **quantum_llm_datasets.py** | Dataset utilities | Tokenization, data loading, augmentation |
| **quantum_llm_quickstart.py** | Quick start examples | Ready-to-run training examples |

---

## 🔬 Advanced Quantum Features

### 1. Multi-Scale Quantum Attention

**Purpose:** Capture information at different granularities using varying qubit counts.

```python
from quantum_llm_advanced import MultiScaleQuantumAttention

# Creates 4 attention heads with 2, 3, 4, and 6 qubits
attention = MultiScaleQuantumAttention(
    d_model=128,
    n_heads=4,
    n_qubits_per_head=[2, 3, 4, 6]
)
```

**Benefits:**
- Fine-grained patterns (2-3 qubits)
- Mid-level structures (4 qubits)
- Complex relationships (6 qubits)
- Adaptive computation based on complexity

### 2. Adaptive Quantum Layer

**Purpose:** Dynamically select quantum circuit topology based on input complexity.

```python
from quantum_llm_advanced import AdaptiveQuantumLayer

layer = AdaptiveQuantumLayer(d_model=128, n_qubits=4)
```

**Modes:**
- **Linear entanglement:** Simple inputs (low complexity)
- **Circular entanglement:** Moderate inputs (medium complexity)
- **Full entanglement:** Complex inputs (high complexity)

**Selector:** Learned neural network predicts optimal entanglement pattern.

### 3. Quantum Circuit Cache

**Purpose:** Cache repeated quantum circuit executions to reduce QPU calls.

```python
from quantum_llm_advanced import QuantumCircuitCache

cache = QuantumCircuitCache(cache_size=1000)
```

**Features:**
- LRU eviction policy
- Hit/miss tracking
- Cache statistics reporting
- Significant speedup for repeated patterns

### 4. Quantum Prompt Tuning

**Purpose:** Task-specific adaptation using quantum-parametrized soft prompts.

```python
from quantum_llm_advanced import QuantumPromptTuning

prompt_tuner = QuantumPromptTuning(
    d_model=128,
    n_qubits=4,
    n_prompts=10
)
```

**Benefits:**
- Few-shot learning capability
- Task adaptation without full retraining
- Quantum-enhanced prompt representation

### 5. Quantum Error Mitigation

**Purpose:** Reduce noise in quantum circuit outputs.

```python
from quantum_llm_advanced import QuantumErrorMitigation

error_mitigator = QuantumErrorMitigation(n_qubits=4)
```

**Techniques:**
- Zero-noise extrapolation
- Readout error correction
- Calibration matrix support

---

## ⚙️ Circuit Optimization

### Circuit Compiler

Optimizes quantum circuits for efficient execution.

```python
from quantum_circuit_optimizer import CircuitCompiler, OptimizationStrategy

strategy = OptimizationStrategy(
    compilation_level=2,  # 0=none, 1=light, 2=moderate, 3=aggressive
    enable_gate_fusion=True,
    enable_gate_cancellation=True,
)

compiler = CircuitCompiler(strategy)
```

**Optimization Passes:**
- Gate fusion (combine adjacent gates)
- Gate cancellation (remove redundant gates)
- Circuit depth reduction
- Parameter shift optimization

### Batch Circuit Executor

Executes multiple circuits efficiently with caching.

```python
from quantum_circuit_optimizer import BatchCircuitExecutor

executor = BatchCircuitExecutor(
    max_batch_size=10,
    enable_parallel=False,
    cache_size=1000,
)
```

**Features:**
- Batch processing
- Execution caching
- Cache hit rate tracking
- Reduced QPU load

### Adaptive Circuit Scheduler

Resource-aware quantum circuit scheduling.

```python
from quantum_circuit_optimizer import AdaptiveCircuitScheduler

scheduler = AdaptiveCircuitScheduler(
    max_concurrent_circuits=5,
    quantum_resource_limit=0.8,
)
```

**Capabilities:**
- Load-aware scheduling
- Priority-based execution
- Resource contention management

---

## 🎓 Curriculum Learning

### Training Stages

Progressive quantum integration through multiple training stages.

```python
from quantum_llm_hybrid_trainer import TrainingStage

stages = [
    TrainingStage(
        name="classical_warmup",
        quantum_ratio=0.0,
        num_epochs=2,
        learning_rate=1e-4,
        batch_size=16,
    ),
    TrainingStage(
        name="quantum_transition",
        quantum_ratio=0.3,
        num_epochs=3,
        learning_rate=5e-5,
        batch_size=16,
        enable_quantum_layers=["attention"],
    ),
    TrainingStage(
        name="full_quantum",
        quantum_ratio=0.7,
        num_epochs=10,
        learning_rate=1e-5,
        batch_size=8,
        enable_quantum_layers=["attention", "feedforward"],
    ),
]
```

**Stage Progression:**
1. **Classical Warmup:** Pure classical training to learn basic patterns
2. **Quantum Transition:** Gradual quantum integration (30% quantum)
3. **Full Quantum:** Maximize quantum usage (70% quantum)

### Adaptive Quantum Router

Learns optimal quantum/classical routing policy.

```python
from quantum_llm_hybrid_trainer import AdaptiveQuantumRouter

router = AdaptiveQuantumRouter(input_dim=64, learning_rate=0.001)
```

**Policy Learning:**
- Reinforcement learning based
- Context-aware decisions
- Performance-driven optimization

---

## 📊 Monitoring & Visualization

### Training Dashboard

Real-time training monitoring with alerts.

```python
from quantum_llm_monitor import TrainingDashboard

dashboard = TrainingDashboard(
    output_dir=Path("data_out/dashboard"),
    update_interval=10,  # seconds
    enable_alerts=True,
)
```

**Features:**
- Real-time metrics tracking
- Moving average computation
- Trend detection (improving/degrading/stable)
- Anomaly detection using z-scores
- Alert system for issues

**Metrics Tracked:**
- Loss and perplexity
- Quantum execution time
- Classical execution time
- CPU/memory/GPU usage
- Cache hit rates
- Circuit statistics

### Visualization Export

Export data for external visualization tools.

```python
from quantum_llm_monitor import VisualizationExporter

exporter = VisualizationExporter(output_dir=Path("visualizations"))
exporter.export_all(snapshots)
```

**Exported Data:**
- Loss curves
- Quantum metrics over time
- Resource utilization
- Circuit performance

---

## 🗂️ Dataset Utilities

### Character Tokenizer

Simple character-level tokenization.

```python
from quantum_llm_datasets import CharacterTokenizer

tokenizer = CharacterTokenizer(vocab_size=256)
text = "Hello, Quantum World!"
encoded = tokenizer.encode(text)
decoded = tokenizer.decode(encoded)
```

### Text Dataset

Handles tokenization and sequence windowing.

```python
from quantum_llm_datasets import TextDataset

dataset = TextDataset(
    texts=["sample text 1", "sample text 2"],
    tokenizer=tokenizer,
    max_seq_length=512,
    stride=256,
)
```

### Auto-Detection Loading

Automatically detect and load various dataset formats.

```python
from quantum_llm_datasets import DatasetBuilder

# Auto-detect: text, JSON, or chat format
dataset = DatasetBuilder.auto_detect_and_load(
    path=Path("datasets/chat/conversation.json"),
    tokenizer=tokenizer,
    max_seq_length=512,
)
```

**Supported Formats:**
- Plain text files
- JSON with "text" field
- Chat format with "messages" array

---

## 🔧 Configuration

### Example Configuration (YAML)

```yaml
# Model architecture
vocab_size: 256
d_model: 128
n_heads: 4
n_layers: 4
d_ff: 512
max_seq_length: 512

# Quantum configuration
n_qubits: 4
quantum_backend: "default.qubit"
quantum_shots: 1000
enable_quantum_attention: true
enable_quantum_ffn: true
enable_multi_scale_attention: true
enable_adaptive_entanglement: true
enable_circuit_caching: true
enable_error_mitigation: false

# Training
batch_size: 16
learning_rate: 1e-4
num_epochs: 10
enable_curriculum: true
enable_adaptive_routing: true

# Optimization
optimization_level: 2
enable_circuit_fusion: true
max_batch_circuits: 10

# Monitoring
enable_dashboard: true
dashboard_update_interval: 10
enable_alerts: true

# Output
output_dir: "data_out/quantum_llm"
save_checkpoints: true
checkpoint_interval: 100
```

---

## 📈 Performance Tips

### 1. Circuit Caching

**Enable for:** Training on repeated patterns (e.g., character-level language models)

```python
config["enable_circuit_caching"] = True
```

**Expected improvement:** 2-5x speedup on repeated inputs

### 2. Optimization Level

**Level 0:** No optimization (debugging)
**Level 1:** Light optimization (safe)
**Level 2:** Moderate optimization (recommended)
**Level 3:** Aggressive optimization (experimental)

```python
config["optimization_level"] = 2
```

### 3. Batch Size

**Quantum circuits:** Smaller batches (4-8) for complex circuits
**Classical layers:** Larger batches (16-32) for efficiency

```python
# Adaptive batch sizing across stages
stages = [
    TrainingStage(..., batch_size=16),  # Classical
    TrainingStage(..., batch_size=8),   # Transition
    TrainingStage(..., batch_size=4),   # Full quantum
]
```

### 4. Multi-Scale Attention

**Use when:** Capturing hierarchical patterns important

```python
config["enable_multi_scale_attention"] = True
config["n_qubits_per_head"] = [2, 3, 4, 6]
```

---

## 🔍 Monitoring Outputs

### Dashboard JSON

Location: `data_out/quantum_llm/dashboard/dashboard.json`

```json
{
  "timestamp": 1234567890.0,
  "metrics_summary": {
    "moving_avg_loss": 2.5,
    "loss_trend": "improving",
    "anomalies": []
  },
  "performance_report": {
    "avg_cpu_percent": 45.2,
    "max_memory_mb": 2048.5
  },
  "circuit_stats": {
    "attention_circuit_0": {
      "avg_time": 0.15,
      "executions": 1000
    }
  }
}
```

### Training Report

Location: `data_out/quantum_llm/training/training_report.json`

```json
{
  "total_stages": 3,
  "total_time": 3600.0,
  "total_steps": 10000,
  "best_loss": 1.85,
  "stage_metrics": [...],
  "routing_stats": {
    "quantum_ratio": 0.65
  }
}
```

---

## 🧪 Testing

### Quick Test

```bash
# Test all components with minimal example
python quantum_llm_quickstart.py --mode quick
```

### Component Tests

```bash
# Test advanced components
python ai-projects/quantum-ml/src/quantum_llm_advanced.py

# Test optimizer
python ai-projects/quantum-ml/src/quantum_circuit_optimizer.py

# Test monitor
python ai-projects/quantum-ml/src/quantum_llm_monitor.py

# Test datasets
python ai-projects/quantum-ml/src/quantum_llm_datasets.py
```

### Integration Test

```bash
# Test full integrated system
python ai-projects/quantum-ml/src/quantum_llm_integrated.py --dry-run
```

---

## 📚 Documentation Structure

```
ai-projects/quantum-ml/
├── src/
│   ├── quantum_llm_advanced.py          # Advanced quantum layers
│   ├── quantum_circuit_optimizer.py      # Circuit optimization
│   ├── quantum_llm_hybrid_trainer.py     # Training orchestration
│   ├── quantum_llm_monitor.py            # Monitoring & visualization
│   ├── quantum_llm_integrated.py         # Complete integration
│   └── quantum_llm_datasets.py           # Dataset utilities
├── quantum_llm_quickstart.py            # Quick start examples
├── QUANTUM_LLM_README.md                # This file
└── quantum_llm_config_example.yaml      # Example configuration
```

---

## 🎯 Use Cases

### 1. Research & Experimentation

Explore quantum advantages in language modeling:

```python
# Compare quantum vs classical attention
config["enable_multi_scale_attention"] = True
system = QuantumLLMSystem(config)
```

### 2. Curriculum Training

Progressive quantum integration for stable training:

```python
config["enable_curriculum"] = True
stages = create_curriculum_stages()
```

### 3. Resource-Constrained Training

Optimize for limited quantum resources:

```python
config["optimization_level"] = 3
config["enable_circuit_caching"] = True
config["max_batch_circuits"] = 5
```

### 4. Production Monitoring

Real-time training monitoring and alerts:

```python
config["enable_dashboard"] = True
config["enable_alerts"] = True
config["dashboard_update_interval"] = 5
```

---

## 🚧 Limitations & Future Work

### Current Limitations

1. **Quantum Backend:** Simulation-based (no real QPU integration yet)
2. **Tokenization:** Character-level only (subword/BPE planned)
3. **Model Size:** Limited by quantum circuit depth
4. **Training Speed:** Quantum simulation slower than classical

### Planned Enhancements

1. **Azure Quantum Integration:** Real QPU execution
2. **Subword Tokenization:** BPE/WordPiece support
3. **Distributed Training:** Multi-GPU/multi-QPU
4. **Advanced Error Correction:** Full QEC implementation
5. **Model Compression:** Quantum-aware pruning/quantization

---

## 📖 References

- **Quantum Machine Learning:** Quantum circuits for ML tasks
- **Curriculum Learning:** Progressive training strategies
- **Circuit Optimization:** Gate-level quantum optimizations
- **Error Mitigation:** Noise reduction techniques

---

## ✨ Key Innovation

**Hybrid Quantum-Classical Training:** Seamlessly integrates quantum circuits into transformer architecture with adaptive routing, curriculum learning, and comprehensive monitoring - the first complete quantum LLM training system.

---

## 🤝 Contributing

Improvements welcome! Focus areas:
- Real QPU backend integration
- Advanced error correction
- Distributed training
- Performance optimizations

---

**Author:** Quantum AI Workspace
**Date:** March 9, 2026
**License:** MIT
