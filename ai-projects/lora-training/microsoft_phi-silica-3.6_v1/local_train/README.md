# Local LoRA Fine-Tuning - Quick Start

Train Phi-3.5 locally on your own data with LoRA, optimized for consumer hardware (single GPU or CPU).

## Features

- **No Azure dependencies** - runs completely offline after model download
- **Memory efficient** - optimized for consumer GPUs (RTX 3060, M1/M2, etc.)
- **Quantization support** - 4-bit and 8-bit training (QLoRA) for limited VRAM
- **Simple configuration** - single YAML file for all settings
- **Resume from checkpoint** - continue training if interrupted

## Quick Setup

### 1. Create Virtual Environment

```powershell
# Navigate to local_train directory
cd AI\microsoft_phi-silica-3.6_v1\local_train

# Create and activate venv
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt

# Optional: For 4-bit/8-bit quantization (saves VRAM)
pip install bitsandbytes
```

### 3. Prepare Your Data

Create `data/train.json` and `data/test.json` in JSONL format:

```jsonl
{"messages": [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "Artificial Intelligence..."}]}
{"messages": [{"role": "user", "content": "Explain LoRA"}, {"role": "assistant", "content": "LoRA is a technique..."}]}
```

**Sample data is included** in `../data/` for testing.

### 4. Train the Model

```powershell
# Quick test (10 samples, fast iteration)
python train_local.py --config local_config.yaml --max-samples 10

# Full training
python train_local.py --config local_config.yaml

# With 4-bit quantization (for limited VRAM)
python train_local.py --config local_config.yaml --use-4bit

# Resume from checkpoint
python train_local.py --config local_config.yaml --resume-from outputs/checkpoint-500
```

### 5. Evaluate the Model

```powershell
# Evaluate trained model on test set
python train_local.py --config local_config.yaml --eval-only --resume-from outputs/final_model
```

## Configuration

Edit `local_config.yaml` to customize training:

```yaml
# Model
model_id: "microsoft/Phi-3.5-mini-instruct"

# Data
train_file: "train.json"
eval_file: "test.json"

# Training
num_epochs: 3
batch_size: 1
gradient_accumulation_steps: 4
learning_rate: 0.0002
max_seq_length: 512

# LoRA
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05

# Memory optimization
use_bf16: true
gradient_checkpointing: true
use_4bit: false  # Enable for QLoRA (saves VRAM)
```

## Common Scenarios

### Limited VRAM (< 8GB)

```yaml
# local_config.yaml
use_4bit: true
max_seq_length: 256
gradient_checkpointing: true
batch_size: 1
gradient_accumulation_steps: 8
```

```powershell
python train_local.py --config local_config.yaml --use-4bit
```

### CPU-Only Training

```yaml
# local_config.yaml
use_fp16: false
use_bf16: false
batch_size: 1
gradient_accumulation_steps: 16
```

```powershell
python train_local.py --config local_config.yaml
```

### Quick Experimentation

```powershell
# Train on small subset (fast iteration)
python train_local.py --config local_config.yaml --max-samples 100

# Single epoch test
python train_local.py --config local_config.yaml --num-epochs 1 --max-samples 50
```

## CLI Reference

```
python train_local.py [OPTIONS]

Required:
  --config PATH              Path to local_config.yaml

Optional:
  --data-dir PATH            Directory with train/eval files (default: ../data)
  --num-epochs N             Override config num_epochs
  --max-samples N            Limit dataset size (for testing)
  --resume-from PATH         Resume from checkpoint
  --eval-only                Only run evaluation (requires --resume-from)
  --use-4bit                 Enable 4-bit quantization (QLoRA)
  --use-8bit                 Enable 8-bit quantization
```

## Output Structure

```
outputs/
├── checkpoint-100/        # Intermediate checkpoints
├── checkpoint-200/
├── final_model/           # Final LoRA adapter
│   ├── adapter_config.json
│   ├── adapter_model.bin
│   └── tokenizer files
└── training_metrics.json  # Loss and perplexity per step
```

## Tips

1. **Start small**: Use `--max-samples 10` for quick validation
2. **Monitor VRAM**: Watch `nvidia-smi` (GPU) or Task Manager (CPU)
3. **Adjust batch size**: If OOM, reduce `batch_size` and increase `gradient_accumulation_steps`
4. **Use quantization**: Enable `--use-4bit` for low VRAM (< 8GB)
5. **Check perplexity**: Lower is better - look for decreasing trend in logs

## Troubleshooting

### Out of Memory (OOM)

```yaml
# Reduce memory footprint
use_4bit: true
max_seq_length: 256
batch_size: 1
gradient_accumulation_steps: 16
```

### Slow Training

```yaml
# Speed up at cost of VRAM
gradient_checkpointing: false
batch_size: 2
gradient_accumulation_steps: 2
```

### Model Not Learning

- Increase `lora_r` (16 → 32)
- Check learning rate (try 1e-4 to 5e-4)
- Verify data quality (check tokenization)
- Increase `num_epochs` or dataset size

## Next Steps

- **Use the model**: Load adapter with `PeftModel.from_pretrained()`
- **Merge adapter**: Merge LoRA weights into base model for deployment
- **Experiment**: Try different `lora_r`, learning rates, datasets
- **Scale up**: Move to Azure for multi-GPU training (see `../scripts/train_lora.py`)

## Differences from Azure Setup

| Feature | Local Setup | Azure Setup (../scripts/) |
| --------- | ------------- | --------------------------- |
| Dependencies | Minimal (no Azure SDKs) | Full (Azure Blob, Log Analytics, App Insights) |
| Data Loading | Local files only | Blob Storage manifests, streaming |
| Multi-GPU | Manual Accelerate launch | Built-in DeepSpeed support |
| Observability | File logging only | OpenTelemetry, App Insights, Log Analytics |
| Deployment | Local use | Container Apps Jobs |

For production-scale training with multi-GPU, observability, and cloud storage, use the Azure setup in `../scripts/`.
