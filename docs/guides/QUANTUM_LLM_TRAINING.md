# Quantum-Enhanced Passive LLM Training

## Overview

This feature integrates quantum computing capabilities into passive LLM training, enabling continuous background training with quantum-enhanced optimization. The system combines classical LLM fine-tuning with quantum circuits for improved performance and novel optimization strategies.

## Key Features

### 🔬 Quantum Computing Integration
- **Quantum Attention Optimization**: Uses quantum circuits to optimize attention weight distributions in transformer models
- **Quantum Feature Encoding**: Encodes classical features into quantum states for enhanced representation learning
- **Hybrid Quantum-Classical Architecture**: Seamlessly integrates quantum layers with classical neural networks

### 🤖 Passive Training Mode
- **Continuous Background Training**: Runs autonomously in the background with configurable intervals
- **Integration with Autonomous Orchestrator**: Works seamlessly with the existing autonomous training system
- **Resource-Aware Execution**: Intelligently manages quantum circuit executions to balance performance and cost

### ⚛️ Quantum Backends
- **Local Simulator**: Fast quantum simulation using PennyLane's default.qubit (free, unlimited use)
- **Azure Quantum**: Production quantum computing via Azure Quantum service
  - Free simulators: `ionq.simulator`, `quantinuum.sim.*`
  - Paid QPU hardware: `ionq.qpu`, `quantinuum.qpu.*` (requires cost confirmation)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Autonomous Training Orchestrator                             │
│  ├── Data Discovery & Collection                             │
│  ├── Classical Training Cycles                               │
│  ├── Quantum-Enhanced LLM Training (NEW) ◄────────────────┐ │
│  ├── Performance Analysis                                  │ │
│  └── Optimization & Deployment                             │ │
└──────────────────────────────────────────┬──────────────────┘ │
                                           │                    │
                                           ▼                    │
┌─────────────────────────────────────────────────────────────┴─┐
│ Quantum-Enhanced LLM Trainer                                  │
│  ├── Quantum Attention Optimizer                              │
│  │   └── Optimizes attention weight distributions             │
│  ├── Quantum Feature Encoder                                  │
│  │   └── Encodes features into quantum states                 │
│  ├── Training Pipeline                                        │
│  │   ├── Load dataset (JSON/JSONL)                            │
│  │   ├── Apply quantum enhancement every N steps              │
│  │   └── Track quantum metrics                                │
│  └── Passive Mode Controller                                  │
│      └── Manages continuous background training               │
└───────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Quantum Computing Layer (ai-projects/quantum-ml/)                        │
│  ├── QuantumClassifier (variational circuits)                │
│  ├── HybridQNN (quantum-classical hybrid)                    │
│  ├── QuantumLayer (PennyLane integration)                    │
│  └── Azure Quantum Integration                               │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Basic Usage (Active Training)

Train a model with quantum enhancement on a specific dataset:

```bash
# Using local quantum simulator (free, fast)
python scripts/quantum_llm_trainer.py \
  --dataset datasets/chat/aria_chat \
  --quantum-backend local \
  --n-qubits 4 \
  --epochs 3

# Using Azure Quantum simulator (free, requires Azure setup)
python scripts/quantum_llm_trainer.py \
  --dataset datasets/chat/aria_chat \
  --quantum-backend azure \
  --config config/quantum_llm_config.yaml
```

### 2. Passive Training Mode

Enable continuous background training:

```bash
# Run in passive mode - trains every hour
python scripts/quantum_llm_trainer.py \
  --passive \
  --interval 3600 \
  --config config/quantum_llm_config.yaml
```

### 3. Integration with Autonomous Orchestrator

The quantum LLM training is automatically integrated into the autonomous training orchestrator:

```bash
# Start autonomous training (includes quantum LLM training)
python scripts/autonomous_training_orchestrator.py

# Or use the full repo automation
python scripts/repo_automation.py --start
```

The orchestrator will automatically run quantum-enhanced LLM training based on the schedule configured in `config/autonomous_training.yaml`.

## Configuration

### Main Configuration File: `config/quantum_llm_config.yaml`

```yaml
quantum_settings:
  backend: "local"  # or "azure"
  n_qubits: 4
  n_quantum_layers: 2
  entanglement: "circular"

passive_training:
  enabled: true
  interval_seconds: 3600  # Run every hour
  epochs_per_cycle: 1

llm_training:
  model_name: "microsoft/phi-2"
  learning_rate: 0.0001
  batch_size: 4

  lora:
    enabled: true
    r: 8
    alpha: 16

quantum_enhancement:
  optimize_attention: true
  attention_optimization_frequency: 10
  quantum_feature_encoding: true
```

### Autonomous Integration: `config/autonomous_training.yaml`

```yaml
# Enable quantum-enhanced LLM training
quantum_llm:
  enabled: true
  passive_mode: true
  backend: "local"
  n_qubits: 4
  training_interval_minutes: 60
  optimize_attention: true
  quantum_feature_encoding: true
```

## How It Works

### Quantum Attention Optimization

The quantum attention optimizer uses quantum circuits to enhance attention mechanisms:

1. **Encoding**: Attention scores are encoded into quantum states
2. **Processing**: Quantum gates apply transformations (superposition, entanglement)
3. **Measurement**: Quantum measurements produce optimized attention weights
4. **Interference**: Quantum interference patterns enhance attention distribution

**Benefits**:
- More diverse attention patterns
- Better capture of long-range dependencies
- Potential for quantum speedup on quantum hardware

### Quantum Feature Encoding

Classical features are encoded into quantum states using amplitude encoding:

1. **Normalization**: Features are normalized to unit vectors
2. **Amplitude Encoding**: Classical values become quantum amplitudes
3. **Variational Circuit**: Parameterized quantum gates process the encoded state
4. **Measurement**: Results are decoded back to classical features

**Benefits**:
- Exponential feature space (2^n for n qubits)
- Quantum entanglement captures feature correlations
- Novel feature representations

### Passive Training Workflow

```
┌──────────────────────────────────────────────────────────┐
│ Passive Training Cycle (runs every interval)             │
├──────────────────────────────────────────────────────────┤
│ 1. Scan datasets/chat/ for available datasets            │
│ 2. Select random dataset                                 │
│ 3. Load and prepare data                                 │
│ 4. Initialize quantum components                         │
│ 5. Training loop:                                        │
│    ├── Forward pass                                      │
│    ├── Apply quantum optimization (every N steps)        │
│    ├── Backward pass                                     │
│    └── Update weights                                    │
│ 6. Save results and metrics                              │
│ 7. Update status file                                    │
│ 8. Sleep until next cycle                                │
└──────────────────────────────────────────────────────────┘
```

## Quantum Backends

### Local Simulator (Recommended for Development)

- **Backend**: `default.qubit` (PennyLane)
- **Cost**: Free, unlimited
- **Speed**: Fast (CPU-based)
- **Use Case**: Development, testing, experimentation

```yaml
quantum_settings:
  backend: "local"
```

### Azure Quantum

- **Free Simulators**:
  - `ionq.simulator` - IonQ quantum simulator
  - `quantinuum.sim.h1-1e` - Quantinuum H1 emulator
- **Paid QPU Hardware**:
  - `ionq.qpu` - IonQ trapped-ion quantum computer
  - `quantinuum.qpu.h1-1` - Quantinuum H1-1 quantum computer

```yaml
quantum_settings:
  backend: "azure"
  azure:
    resource_id: "your-azure-quantum-workspace-id"
    target_backend: "ionq.simulator"
    shots: 100
    confirm_cost: false  # Must be true for QPU
```

## Monitoring and Metrics

### Status File: `data_out/quantum_llm_training/status.json`

```json
{
  "status": "success",
  "epochs_completed": 3,
  "final_loss": 1.234,
  "quantum_metrics": {
    "circuit_executions": 150,
    "optimization_steps": 15,
    "quantum_advantage_ratio": 1.05
  },
  "started_at": "2025-12-08T10:00:00",
  "completed_at": "2025-12-08T10:15:00"
}
```

### Training Results: `data_out/quantum_llm_training/quantum_training_results.json`

Detailed results including:
- Loss history per epoch
- Quantum circuit execution counts
- Optimization metrics
- Training timestamps

### Logs

Logs are written to:
- Console output (INFO level)
- Autonomous training log: `data_out/autonomous_training.log` (when integrated)

## Performance Considerations

### Resource Usage

- **CPU**: Quantum simulation is CPU-intensive (1-4 cores recommended)
- **Memory**: ~2-4 GB per training cycle
- **Disk**: ~100 MB per cycle for checkpoints and results
- **GPU**: Optional (for classical neural network components)

### Optimization Tips

1. **Start Small**: Begin with 4 qubits, 2 layers
2. **Tune Frequency**: Adjust `attention_optimization_frequency` (higher = less quantum overhead)
3. **Batch Size**: Use smaller batches (4-8) for faster quantum circuits
4. **Cache Circuits**: Enable circuit caching to avoid recomputation

### Cost Management (Azure Quantum)

- Always test with FREE simulators first
- Set `confirm_cost: false` to prevent accidental QPU usage
- Monitor costs in Azure portal
- Start with low shot counts (100-500)

## Testing

### Run Unit Tests

```bash
# Test quantum LLM trainer
pytest tests/test_quantum_llm_trainer.py -v

# Run all quantum tests
pytest tests/ -k quantum -v

# Integration tests
pytest tests/test_quantum_llm_trainer.py::TestQuantumLLMIntegration -v
```

### Validate Configuration

```bash
# Test with dry-run
python scripts/quantum_llm_trainer.py \
  --dataset datasets/chat/aria_chat \
  --epochs 1 \
  --quantum-backend local
```

## Troubleshooting

### Quantum Modules Not Available

If you see warnings about quantum modules:

```bash
# Install quantum-ai dependencies
cd quantum-ai
pip install -r requirements.txt

# Or install specific packages
pip install pennylane qiskit torch
```

### Azure Quantum Connection Issues

1. Verify workspace credentials in `config/quantum_llm_config.yaml`
2. Check Azure login: `az login`
3. Verify workspace access: `az quantum workspace list`
4. Try free simulator first: `target_backend: "ionq.simulator"`

### Performance Issues

- Reduce `n_qubits` (try 3-4 instead of 8+)
- Reduce `n_quantum_layers` (try 1-2 instead of 3+)
- Increase `attention_optimization_frequency` (apply quantum less often)
- Disable quantum feature encoding temporarily

### Passive Mode Not Running

1. Check `config/autonomous_training.yaml`: `quantum_llm.enabled: true`
2. Verify `scripts/quantum_llm_trainer.py` exists
3. Check logs: `tail -f data_out/autonomous_training.log`
4. Verify datasets exist: `ls datasets/chat/*/train.json`

## Examples

### Example 1: Quick Test

```bash
# 1-minute test with local simulator
python scripts/quantum_llm_trainer.py \
  --dataset datasets/chat/aria_chat \
  --quantum-backend local \
  --n-qubits 3 \
  --n-quantum-layers 1 \
  --epochs 1
```

### Example 2: Production Passive Training

```bash
# Run continuous training in background
nohup python scripts/quantum_llm_trainer.py \
  --passive \
  --interval 3600 \
  --config config/quantum_llm_config.yaml \
  > data_out/quantum_llm_training.log 2>&1 &

# Monitor
tail -f data_out/quantum_llm_training.log
```

### Example 3: Azure Quantum Integration

```bash
# Configure Azure Quantum
cat > config/quantum_llm_config.yaml << EOF
quantum_settings:
  backend: "azure"
  n_qubits: 4
  azure:
    resource_id: "/subscriptions/.../quantumWorkspaces/my-workspace"
    target_backend: "ionq.simulator"
    shots: 200
EOF

# Run with Azure
python scripts/quantum_llm_trainer.py \
  --dataset datasets/chat/aria_chat \
  --config config/quantum_llm_config.yaml
```

## Future Enhancements

- [ ] Quantum-assisted hyperparameter optimization using QAOA
- [ ] Quantum circuit architecture search (quantum NAS)
- [ ] Multi-qubit entanglement patterns for attention heads
- [ ] Quantum error mitigation for QPU execution
- [ ] Distributed quantum training across multiple backends
- [ ] Quantum-classical co-training strategies

## References

- [PennyLane Documentation](https://pennylane.ai/)
- [Azure Quantum Documentation](https://learn.microsoft.com/en-us/azure/quantum/)
- [Quantum Machine Learning Papers](https://arxiv.org/list/quant-ph/recent)
- [Variational Quantum Algorithms](https://arxiv.org/abs/2012.09265)

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review logs in `data_out/quantum_llm_training.log`
3. Test with local simulator first
4. Check ai-projects/quantum-ml/ module is properly configured

## License

This module is part of the Aria project and follows the same license.
