# ⚛️ LLaMA 3 + Quantum ML: Quick Reference

## 🚀 TL;DR - Start Here (Quantum-Enabled Models)

```bash
# 1. Preview quantum training pipeline (no GPU required)
python scripts/gguf_training_automation.py --quick --dry-run

# 2. Train quick quantum LLaMA 3 (variational encoding + quantum attention)
python scripts/gguf_training_automation.py --quick --jobs llama3_quantum_quick

# 3. Train ALL quantum-enhanced models (8 qubit encoding + multi-head quantum attention)
python scripts/gguf_training_automation.py --full --quantum

# 4. Use quantum-enhanced trained model for inference
python talk-to-ai/src/chat_cli.py --model-path deployed_models/llama3_quantum_quick-latest.gguf
```

## ⚛️ What Makes These Models Quantum?

These LLaMA 3 models include **hybrid classical-quantum architecture**:
- **Quantum Encoding**: Classical tokens → quantum superposition states (8 qubits)
- **Quantum Attention**: Multi-head quantum attention with entangled gates (16 qubits)
- **Quantum Classifier**: Variational quantum circuit for predictions (8 qubits)
- All quantum parameters are learnable and trained via backpropagation

## Available Quantum Models

| Name | Base | Quant | ⚛️ Quantum Features | Size | Speed | Quality |
|------|------|-------|------------------|------|-------|---------|
| `llama3_quantum_quick` | LLaMA 3 8B | Q4 | Variational encoding + quantum attention + entanglement | ~2.5GB | ⚡⚡⚡ | ★★☆ |
| `llama3_quantum_prod` | LLaMA 3 8B | Q5 | Full quantum stack + classifier head | ~3.5GB | ⚡⚡ | ★★★ |
| `llama3_hq_quantum` | LLaMA 3 8B | F16 | Adaptive entanglement + multi-head quantum | ~16GB | ⚡ | ★★★★ |
| `llama3_light_quantum` | LLaMA 3 1B | Q4 | Lightweight quantum encoding + attention | ~0.4GB | ⚡⚡⚡ | ★★ |

## Common Commands

```bash
# Train single model
python scripts/gguf_training_automation.py --full --jobs llama3_quantum_prod

# Train multiple specific models
python scripts/gguf_training_automation.py --full --jobs llama3_quantum_quick llama3_quantum_prod

# Only quantum models
python scripts/gguf_training_automation.py --full --quantum

# Custom config
python scripts/gguf_training_automation.py --full --config my_config.yaml

# Dry-run (shows what will happen)
python scripts/gguf_training_automation.py --full --dry-run

# Convert existing LoRA to GGUF
python scripts/gguf_training_automation.py --convert-only /path/to/lora

# Validate GGUF file
python scripts/gguf_training_automation.py --validate /path/to/model.gguf
```

## Quantum Features

- **variational_encoding**: Amplitude-based feature encoding (8 qubits)
- **quantum_attention**: Multi-head quantum attention (4 heads × 4 qubits)
- **entanglement_layer**: Full qubit correlations (16 qubits)
- **quantum_classifier_head**: Variational task classifier (8 qubits, 3 layers)
- **full_quantum_stack**: Complete quantum ML integration (20 qubits)
- **multi_head_quantum_attention**: Enhanced attention (8 heads × 4 qubits)
- **adaptive_entanglement**: Dynamic circuit depth (8-20 qubits)
- **lightweight_quantum_attention**: Edge-optimized (4 qubits, 1 layer)

## Outputs

Training creates:
```
data_out/gguf_training/
  ├── llama3_quantum_quick/
  │   └── 2026-01-17T.../
  │       ├── status.json (results)
  │       ├── quantum_enhancements/quantum_config.json
  │       ├── llama3_quantum_quick-q4_0.gguf (final model)
  │       └── *.log (detailed logs)
  └── ...

deployed_models/
  ├── llama3_quantum_quick-latest.gguf
  ├── llama3_quantum_prod-latest.gguf
  └── ...
```

## Integration Points

```python
# With Chat CLI
python talk-to-ai/src/chat_cli.py \
  --model-path deployed_models/llama3_quantum_prod-latest.gguf

# With Aria Web Server
python aria_web/server.py \
  --model deployed_models/llama3_quantum_prod-latest.gguf

# With Azure Functions
curl http://localhost:7071/api/chat \
  -d '{"message": "Hello", "model": "llama3_quantum_prod"}'
```

## Configuration (config/training/gguf_training.yaml)

```yaml
jobs:
  - name: llama3_quantum_quick
    base_model: meta-llama/Llama-3-8B-Instruct
    quantization_type: q4_0
    validate: true
    deploy: false
    quantum_enhanced: true
    quantum_features:
      - variational_encoding
      - quantum_attention
      - entanglement_layer
    notes: "Quick testing"
```

## Typical Timings

- **Quick Training**: 5-10 min per model
- **Full Training**: 10-20 min per model
- **HQ Training**: 15-30 min per model
- **Total (all 4 models)**: ~40-60 min on GPU

## File Sizes

- LLaMA 3 8B (Q4): ~2-3 GB
- LLaMA 3 8B (Q5): ~3-4 GB
- LLaMA 3 8B (F16): ~15-16 GB
- LLaMA 3 1B (Q4): ~300-500 MB

## Status Check

```bash
# View latest results
cat data_out/gguf_training/llama3_quantum_quick/*/status.json | jq .

# Check deployed models
ls -lh deployed_models/*llama3*.gguf

# Read training logs
tail -f data_out/gguf_training/llama3_quantum_quick/*/status.log
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory | Use `q4_0` quantization or `llama3_light_quantum` |
| Model download fails | Run `huggingface-cli login` |
| Quantization slow | Skip with `quantization_type: f32` |
| GGUF validation fails | Check file size > 100MB |
| Model not in deployed_models | Set `deploy: true` in config |

## Next Steps

1. Run `--quick --dry-run` to understand the pipeline
2. Train with `--quick` to test on your GPU
3. Check results in `data_out/gguf_training/*/status.json`
4. Deploy with `--full` for production
5. Use deployed model in chat/Aria/functions

See [LLAMA3_QUANTUM_INTEGRATION.md](LLAMA3_QUANTUM_INTEGRATION.md) for detailed documentation.

