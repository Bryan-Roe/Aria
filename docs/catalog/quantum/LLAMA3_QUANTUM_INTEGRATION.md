# LLaMA 3 + Quantum ML Integration Guide

**⚛️ Quantum Machine Learning Integration for LLaMA 3 Models**

This guide describes how to train and deploy **hybrid classical-quantum LLaMA 3 models** with integrated quantum machine learning capabilities including variational quantum circuits, multi-qubit entanglement, and quantum classifiers.

## Overview

You can now train and export **LLaMA 3 models enhanced with quantum ML**. The quantum enhancements include:

- **Variational Encoding**: Amplitude-based quantum encoding of input features
- **Quantum Attention**: Multi-head quantum attention layers with entanglement
- **Entanglement Layers**: Full quantum circuit entanglement patterns
- **Quantum Classifier Heads**: Variational quantum classifiers for task-specific outputs
- **Adaptive Entanglement**: Dynamically adjusting quantum circuit depth

## Available LLaMA 3 Quantum Models

### 1. `llama3_quantum_quick` (Quick Testing)
- **Base**: `meta-llama/Llama-3-8B-Instruct`
- **Quantization**: Q4 (highest compression)
- **Quantum Features**: Variational encoding + Quantum attention + Entanglement layer
- **Use Case**: Quick experimentation, testing quantum features

```bash
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick --dry-run
```

### 2. `llama3_quantum_prod` (Production Ready)
- **Base**: `meta-llama/Llama-3-8B-Instruct`
- **Quantization**: Q5 (balanced quality/size)
- **Quantum Features**: Full quantum attention + Classifier head
- **Use Case**: Production deployments with quantum enhancements

```bash
python scripts/gguf_training_automation.py --full --jobs llama3_quantum_prod
```

### 3. `llama3_hq_quantum` (High Quality)
- **Base**: `meta-llama/Llama-3-8B-Instruct`
- **Quantization**: F16 (high precision)
- **Quantum Features**: Full quantum stack with adaptive entanglement
- **Use Case**: Research, fine-grained quantum ML integration

```bash
python scripts/gguf_training_automation.py --full --jobs llama3_hq_quantum
```

### 4. `llama3_light_quantum` (Lightweight)
- **Base**: `meta-llama/Llama-3-1B-Instruct`
- **Quantization**: Q4
- **Quantum Features**: Lightweight quantum encoding + efficient attention
- **Use Case**: Fast inference on edge devices, resource-constrained environments

```bash
python scripts/gguf_training_automation.py --full --jobs llama3_light_quantum
```

## Quantum Features Explained

### Variational Encoding
```json
{
  "type": "amplitude_encoding",
  "n_qubits": 8,
  "encoding_layers": 2
}
```
Encodes classical features into quantum amplitudes using RY and RZ rotations.

### Quantum Attention
```json
{
  "type": "multi_head_quantum_attention",
  "n_heads": 4,
  "n_qubits_per_head": 4,
  "entanglement": "linear"
}
```
Implements multi-head attention using quantum circuits with entanglement.

### Entanglement Layer
```json
{
  "type": "full_entanglement",
  "n_qubits": 16,
  "pattern": "fully_connected"
}
```
Creates quantum correlations across all qubits for improved expressiveness.

### Quantum Classifier Head
```json
{
  "type": "variational_classifier",
  "n_qubits": 8,
  "layers": 3
}
```
Adds a quantum classifier layer for task-specific predictions.

## Training Workflow

### Step 1: Quick Validation (Dry-Run)

```bash
# Preview what will be trained without executing
python scripts/gguf_training_automation.py --quick --dry-run
```

Output shows:
- Jobs to be executed
- Quantum features per job
- Configuration details

### Step 2: Train Single Quantum Model

```bash
# Train just LLaMA 3 quick quantum
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick
```

Pipeline phases:
1. **Quantum Enhancement**: Generate quantum config with feature specifications
2. **Training**: Train LoRA adapter on base LLaMA 3 model
3. **Conversion**: Convert trained model to GGUF format
4. **Quantization**: Apply selected quantization (Q4/Q5/F16)
5. **Validation**: Verify GGUF integrity and format
6. **Deployment**: Copy to `deployed_models/` (if `deploy: true`)

### Step 3: Train All Quantum LLaMA 3 Models

```bash
# Filter to only quantum-enhanced models
python scripts/gguf_training_automation.py --full --quantum
```

### Step 4: Train All Models (Including Non-Quantum Baselines)

```bash
# Full pipeline: Phi-3.5, Qwen 2.5, LLaMA 3 variants, etc.
python scripts/gguf_training_automation.py --full
```

## Output Directory Structure

```
data_out/gguf_training/
├── llama3_quantum_quick/
│   └── 2026-01-17T...
│       ├── status.log                    # Training logs
│       ├── status.json                   # Machine-readable results
│       ├── quantum_enhancements/
│       │   └── quantum_config.json       # Quantum feature config
│       ├── training.log                  # LoRA training phase
│       ├── conversion.log                # GGUF conversion phase
│       ├── quantization.log              # Quantization phase
│       ├── validation.log                # Validation phase
│       ├── llama3_quantum_quick.gguf     # Raw GGUF file
│       └── llama3_quantum_quick-q4_0.gguf  # Quantized GGUF
│
├── llama3_quantum_prod/
│   └── 2026-01-17T...
│       ├── (similar structure)
│       └── llama3_quantum_prod-q5_0.gguf
│
└── llama3_hq_quantum/
    └── 2026-01-17T...
        ├── (similar structure)
        └── llama3_hq_quantum-f16.gguf
```

Deployed models:
```
deployed_models/
├── llama3_quantum_quick-latest.gguf
├── llama3_quantum_prod-latest.gguf
├── llama3_hq_quantum-latest.gguf
└── llama3_light_quantum-latest.gguf
```

## Configuration Details

Edit `config/training/gguf_training.yaml` to customize:

```yaml
jobs:
  - name: llama3_quantum_custom
    base_model: meta-llama/Llama-3-8B-Instruct
    quantization_type: q5_0
    validate: true
    deploy: true
    quantum_enhanced: true
    quantum_features:
      - variational_encoding
      - quantum_attention
      - entanglement_layer
      - quantum_classifier_head
    notes: "Custom LLaMA 3 with full quantum stack"
```

## Quantum Feature Layers

### Architecture Overview

```
LLaMA 3 Base Model
        ↓
   [Quantum Enhancement]
        ↓
   ┌─────────────────────┐
   │  Variational Layer  │  ← Input encoding to quantum states
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Multi-Head Quantum  │  ← Entangled attention mechanisms
   │     Attention       │
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Entanglement Layer  │  ← Correlations across qubits
   └─────────────────────┘
        ↓
   ┌─────────────────────┐
   │ Quantum Classifier  │  ← Task-specific quantum head
   └─────────────────────┘
        ↓
    Output Tokens (GGUF)
```

## API Reference

### Training Command Options

```bash
# Run specific model by name
python scripts/gguf_training_automation.py --full \
  --jobs llama3_quantum_quick llama3_quantum_prod

# Use custom config
python scripts/gguf_training_automation.py --full \
  --config /path/to/custom_gguf_training.yaml

# Filter to quantum models
python scripts/gguf_training_automation.py --full --quantum

# Dry-run first
python scripts/gguf_training_automation.py --full --dry-run

# Convert existing LoRA to GGUF
python scripts/gguf_training_automation.py \
  --convert-only /path/to/lora_adapter

# Validate GGUF file
python scripts/gguf_training_automation.py \
  --validate /path/to/model.gguf
```

## Quantum Enhancement Config (Auto-Generated)

When you train a quantum-enhanced model, it creates `quantum_enhancements/quantum_config.json`:

```json
{
  "enabled": true,
  "features": [
    "variational_encoding",
    "quantum_attention",
    "entanglement_layer",
    "quantum_classifier_head"
  ],
  "base_model": "meta-llama/Llama-3-8B-Instruct",
  "timestamp": "2026-01-17T10:30:45.123456+00:00",
  "feature_configs": {
    "variational_encoding": {
      "type": "amplitude_encoding",
      "n_qubits": 8,
      "encoding_layers": 2
    },
    "quantum_attention": {
      "type": "multi_head_quantum_attention",
      "n_heads": 4,
      "n_qubits_per_head": 4,
      "entanglement": "linear"
    },
    "entanglement_layer": {
      "type": "full_entanglement",
      "n_qubits": 16,
      "pattern": "fully_connected"
    },
    "quantum_classifier_head": {
      "type": "variational_classifier",
      "n_qubits": 8,
      "layers": 3
    }
  }
}
```

## Quick Start Examples

### Example 1: Train and Deploy Production Model

```bash
# 1. Dry-run to verify config
python scripts/gguf_training_automation.py --full --dry-run

# 2. Train production quantum LLaMA 3
python scripts/gguf_training_automation.py --full \
  --jobs llama3_quantum_prod

# 3. Check results
ls -lh deployed_models/llama3_quantum_prod-latest.gguf
cat data_out/gguf_training/llama3_quantum_prod/*/status.json | jq .
```

### Example 2: Compare Quantum vs Non-Quantum

```bash
# Train non-quantum baseline
python scripts/gguf_training_automation.py --quick \
  --jobs phi35_quick_gguf

# Train quantum-enhanced variant
python scripts/gguf_training_automation.py --quick \
  --jobs llama3_quantum_quick

# Compare outputs
diff <(cat data_out/gguf_training/phi35_quick_gguf/*/status.json | jq .) \
     <(cat data_out/gguf_training/llama3_quantum_quick/*/status.json | jq .)
```

### Example 3: Lightweight Edge Deployment

```bash
# Train small quantum-enhanced LLaMA 3 (1B) for edge
python scripts/gguf_training_automation.py --full \
  --jobs llama3_light_quantum

# Result: ~400MB GGUF file suitable for mobile/IoT
ls -lh deployed_models/llama3_light_quantum-latest.gguf
```

## Integration with Existing Tools

### Using with Chat CLI

```bash
# Chat with quantum-enhanced LLaMA 3 GGUF
python talk-to-ai/src/chat_cli.py \
  --provider local \
  --model-path deployed_models/llama3_quantum_prod-latest.gguf \
  "Explain quantum computing"
```

### Using with Azure Functions

The models in `deployed_models/` are automatically available to the `/api/chat` endpoint:

```bash
# Chat via HTTP
curl -X POST http://localhost:7071/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from quantum LLaMA",
    "model": "llama3_quantum_prod"
  }'
```

### Using with Aria Character

The quantum-enhanced models can be used for Aria's natural language understanding:

```bash
# Configure Aria web server to use quantum model
python aria_web/server.py \
  --model deployed_models/llama3_quantum_prod-latest.gguf
```

## Troubleshooting

### Issue: Out of Memory During Quantum Feature Generation

**Solution**: Use lighter quantum features or reduce `n_qubits`:
```yaml
quantum_features:
  - quantum_encoding              # Lightweight (4 qubits)
  - lightweight_quantum_attention # Lightweight (4 qubits)
```

### Issue: LLaMA 3 Model Download Fails

**Solution**: Download manually and cache:
```bash
huggingface-cli download meta-llama/Llama-3-8B-Instruct \
  --cache-dir ~/.cache/huggingface/hub
```

### Issue: Quantization Too Slow

**Solution**: Skip quantization (use F32 in config):
```yaml
quantization_type: f32  # No compression, fast export
```

## Performance Metrics

Typical training times (per model, on GPU):
- **Quantum Quick**: 5-10 minutes
- **Quantum Prod**: 10-20 minutes
- **Quantum HQ**: 15-30 minutes
- **Quantum Light**: 3-5 minutes

GGUF file sizes:
- **Q4 Quantization**: ~2-3 GB (8B model)
- **Q5 Quantization**: ~3-4 GB (8B model)
- **F16 Precision**: ~15-16 GB (8B model)
- **Light (1B, Q4)**: ~300-500 MB

## References

- **Base Model**: [LLaMA 3 on Hugging Face](https://huggingface.co/meta-llama/Llama-3-8B-Instruct)
- **Quantum ML**: [PennyLane Documentation](https://pennylane.ai/)
- **GGUF Format**: [GGML Project](https://github.com/ggerganov/ggml)
- **LoRA Fine-tuning**: [QLoRA Paper](https://arxiv.org/abs/2305.14314)

## Next Steps

1. **Start with `--quick` training**: Test quantum features without full training
2. **Inspect quantum config**: Check generated `quantum_config.json` for details
3. **Deploy to production**: Use `deploy: true` models in `deployed_models/`
4. **Monitor performance**: Compare quantum vs non-quantum benchmarks
5. **Customize features**: Edit `config/training/gguf_training.yaml` for your needs

## Support

For issues or questions:
- Check `data_out/gguf_training/<job_name>/*/status.log` for detailed logs
- Review `status.json` files for structured results
- Run with `--dry-run` to validate configuration before executing

