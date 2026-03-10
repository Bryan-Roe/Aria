# Scripts Directory - Advanced Training Tools

This directory contains all training and optimization scripts for the Phi-3.6 fine-tuning project.

## 📁 Script Overview

| Script | Purpose | Usage |
|--------|---------|-------|
| `train_lora.py` | LoRA fine-tuning | `python train_lora.py --dataset data --config ../lora/lora.yaml` |
| `auto_eval.py` | Automatic evaluation | `python auto_eval.py --model path/to/model --dataset test.jsonl` |
| `rag_pipeline.py` | RAG setup | `python rag_pipeline.py --model model --docs docs --interactive` |
| `semantic_pruning.py` | Data pruning | `python semantic_pruning.py --input in.jsonl --output out.jsonl` |
| `gpu_optimizer.py` | Hardware optimization | `python gpu_optimizer.py --update-config ../lora/lora.yaml` |
| `run_pipeline.py` | Master orchestrator | `python run_pipeline.py --input-dataset train.jsonl` |
| `prepare_dataset.py` | Dataset preparation | Helper for data formatting |
| `metrics_logger.py` | Training metrics | Used by train_lora.py |
| `otel_callback.py` | Telemetry | Optional observability |

## 🚀 Quick Commands

### One-Line Training
```bash
# Full pipeline
python run_pipeline.py --input-dataset ..\..\datasets\chat\dolly\train.jsonl --test-dataset ..\..\datasets\chat\dolly\test.jsonl

# Quick test
python run_pipeline.py --input-dataset ..\..\datasets\chat\dolly\train.jsonl --max-train-samples 64 --skip-rag
```

### Individual Tools
```bash
# Optimize GPU settings
python gpu_optimizer.py --update-config ..\lora\lora.yaml

# Prune dataset
python semantic_pruning.py --input raw.jsonl --output clean.jsonl

# Train model
python train_lora.py --dataset data --config ..\lora\lora.yaml

# Evaluate
python auto_eval.py --model ..\data_out\lora_training --dataset test.jsonl

# RAG
python rag_pipeline.py --model ..\data_out\lora_training --docs ..\..\..\datasets --interactive
```

## 📊 Output Directories

All scripts output to structured directories:

```
../data_out/
├── lora_training/          # Trained models (from train_lora.py)
├── evaluation_results/     # Eval JSONs (from auto_eval.py)
├── rag_index/             # RAG index (from rag_pipeline.py)
├── gpu_profile.yaml       # Hardware profile (from gpu_optimizer.py)
└── pipeline_results.json  # Pipeline results (from run_pipeline.py)
```

## 🔧 Configuration Files

Scripts use these config files:

- `../lora/lora.yaml` - LoRA training config
- `../soft_prompt/soft_prompt.yaml` - Soft prompt config
- `deepspeed_zero3.json` - DeepSpeed config (multi-GPU)

## 📖 Documentation

For detailed documentation:
- **Complete Guide**: `../ADVANCED_TRAINING_GUIDE.md`
- **Quick Reference**: `../ADVANCED_TRAINING_QUICKREF.md`
- **Setup Summary**: `../ADVANCED_TRAINING_SETUP_COMPLETE.md`

## 💻 Examples

### Example 1: CPU Test Run
```bash
python gpu_optimizer.py  # Detect hardware
python train_lora.py --dataset data --config ..\lora\lora.yaml --max-train-samples 64
```

### Example 2: GPU Production
```bash
python semantic_pruning.py --input ..\..\datasets\chat\dolly\train.jsonl --output ..\data\clean.jsonl
python gpu_optimizer.py --update-config ..\lora\lora.yaml --model-size 7.0
python train_lora.py --dataset ..\data --config ..\lora\lora.yaml
python auto_eval.py --model ..\data_out\lora_training --dataset ..\..\datasets\chat\dolly\test.jsonl
```

### Example 3: RAG Deployment
```bash
python train_lora.py --dataset data --config ..\lora\lora.yaml
python rag_pipeline.py --model ..\data_out\lora_training --docs ..\..\..\datasets --rebuild-index
python rag_pipeline.py --model ..\data_out\lora_training --docs ..\..\..\datasets --query "What is quantum computing?"
```

## 🎯 Workflow Recommendations

### For Quick Experiments
1. `gpu_optimizer.py` - Get optimal settings
2. `train_lora.py --max-train-samples 100` - Quick train
3. `auto_eval.py` - Verify quality

### For Production
1. `semantic_pruning.py` - Clean data
2. `gpu_optimizer.py` - Optimize config
3. `train_lora.py` - Full training
4. `auto_eval.py` - Comprehensive evaluation
5. `rag_pipeline.py` - Production deployment

### For Research
1. `run_pipeline.py` - Automated experiments
2. Monitor `../data_out/pipeline_results.json`
3. Compare multiple runs via `auto_eval.py`

## 🛠️ Advanced Usage

### Custom Pipeline
```python
# In your script
from auto_eval import AutomaticEvaluator
from rag_pipeline import RAGPipeline, DocumentStore
from gpu_optimizer import GPUOptimizer
from semantic_pruning import SemanticPruner

# Use the APIs programmatically
```

### Environment Variables
```bash
# Set before running
set CUDA_VISIBLE_DEVICES=0
set PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
set TOKENIZERS_PARALLELISM=false
```

## 📦 Dependencies

Core (already installed):
- torch, transformers, peft, accelerate

Optional (for advanced features):
```bash
pip install -r ..\requirements-advanced.txt
```

## ✅ Testing

Verify installation:
```bash
python gpu_optimizer.py  # Should detect hardware
python auto_eval.py --help  # Should show usage
python rag_pipeline.py --help  # Should show usage
python semantic_pruning.py --help  # Should show usage
```

---

**All scripts support `--help` for detailed usage information.**
