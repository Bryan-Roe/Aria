# Advanced Training - Quick Reference

## 🚀 One-Command Pipeline

```bash
# Full pipeline (optimize → prune → train → evaluate → RAG)
python scripts\run_pipeline.py --input-dataset ..\..\datasets\chat\dolly\train.jsonl --test-dataset ..\..\datasets\chat\dolly\test.jsonl --rag-docs ..\..\datasets

# Quick test (64 samples, skip RAG)
python scripts\run_pipeline.py --input-dataset ..\..\datasets\chat\dolly\train.jsonl --max-train-samples 64 --skip-rag
```

## 📊 Individual Tools


### GPU Optimizer

```bash
# Auto-optimize config
python scripts\gpu_optimizer.py --update-config lora\lora.yaml

# Custom settings
python scripts\gpu_optimizer.py --model-size 7.0 --memory-usage 0.8
```


### Semantic Pruning

```bash
# Prune dataset
python scripts\semantic_pruning.py --input raw.jsonl --output clean.jsonl

# Aggressive pruning
python scripts\semantic_pruning.py --input raw.jsonl --output clean.jsonl --similarity-threshold 0.90 --quality-threshold 0.5
```


### Auto Evaluation

```bash
# Evaluate model
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl

# Full metrics
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --metrics perplexity inference_time bleu rouge
```







#### Quality Metrics (BLEU / ROUGE)

BLEU and ROUGE are optional; they require extra packages. If the libraries are not installed the script will gracefully skip them and report `null`.

Install (recommended):


```bash
pip install rouge-score sacrebleu
```

Usage examples:


```bash
# Minimal (only speed + perplexity)
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --metrics perplexity inference_time

# Add BLEU
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --metrics perplexity bleu

# Add ROUGE (averages rouge1/rouge2/rougeL)
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --metrics perplexity rouge



- Perplexity ↓: Lower is better (model assigns higher probability to test tokens).
- Inference Time ↓: Lower latency per prompt.
- Tokens/sec ↑: Throughput; combine with latency for capacity planning.
- BLEU ↑: N‑gram precision vs. reference responses (sensitive to exact wording).
- ROUGE‑L ↑: Longest common subsequence overlap (better for summarization / longer answers).

Best practices:

- Keep evaluation sample size modest during iteration (10–20) then scale to 100–500.
- Never select training checkpoints solely on one metric—track multiple to avoid overfitting.
- For chat datasets, ensure reference = last assistant message; prompt = last user message.

  
### RAG Pipeline
  
```bash
# Build index
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --rebuild-index

# Interactive Q&A
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --interactive

#### RAG Tuning Tips

- Chunk Size: Smaller chunks (400–800 chars) increase recall; larger chunks (1200–1600) improve coherence.
- Embeddings: Install `sentence-transformers` for semantic retrieval; otherwise keyword fallback is used.
- Similarity Threshold: Raise above 0.75 to filter loosely related documents.
- Hybrid Strategy: Retrieve top-k semantic → enrich with one keyword‑matched chunk for breadth.

Example with semantic retrieval (after installing sentence-transformers):

```bash
pip install sentence-transformers
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --rebuild-index --interactive
```

## 📁 Output Structure

```text
data_out/
├── lora_training/          # Trained model
├── evaluation_results/     # JSON evaluation results
│   └── experiment_YYYYMMDD_HHMMSS.json
├── rag_index/             # RAG document index
│   ├── documents.json
│   └── embeddings.npy
├── gpu_profile.yaml       # Hardware profile

└── pipeline_results.json  # Full pipeline results
```

## 💡 Common Patterns

  
### Pattern 1: Quick Iteration
  
```bash

# Test on 64 samples
python scripts\gpu_optimizer.py --update-config lora\lora.yaml
python scripts\train_lora.py --dataset data --config lora\lora.yaml --max-train-samples 64
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --num-samples 10
```

  
### Pattern 2: Production Training
  
```bash

# Full quality pipeline
python scripts\semantic_pruning.py --input raw.jsonl --output clean.jsonl --similarity-threshold 0.95
python scripts\gpu_optimizer.py --update-config lora\lora.yaml --model-size 7.0
python scripts\train_lora.py --dataset data --config lora\lora.yaml
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --num-samples 500 --metrics perplexity inference_time bleu rouge
```

  
### Pattern 3: RAG Deployment

  
```bash
# Train + RAG
python scripts\train_lora.py --dataset data --config lora\lora.yaml
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --rebuild-index
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --interactive
```

  
### Pattern 4: Full Orchestrated Pipeline With Metrics
  
```bash
python scripts\run_pipeline.py \
  --input-dataset ..\..\datasets\chat\dolly\train.jsonl \
  --test-dataset ..\..\datasets\chat\dolly\test.jsonl \
  --rag-docs ..\..\datasets \
  --eval-metrics perplexity inference_time bleu rouge \
  --experiment-name prod_eval
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Out of memory | `python scripts\gpu_optimizer.py --memory-usage 0.6` |
| Slow training | Check GPU profile, enable BF16/FP16 |
| Poor eval scores | More aggressive pruning, longer training |
| RAG not working | `pip install sentence-transformers` |

## 📦 Optional Dependencies

```bash
# For semantic features
pip install sentence-transformers

# For quality metrics  
pip install rouge-score sacrebleu

# For quantization
pip install bitsandbytes

# For flash attention (Linux only)
pip install flash-attn --no-build-isolation
```

## 🎯 Performance Targets

|-----|------------|------------|--------|
| RTX 4090 | 4 | ~2000 | 18GB |
| RTX 3090 | 2 | ~1000 | 20GB |
| RTX 3060 | 1 | ~400 | 10GB |
| T4 | 1 | ~300 | 12GB |

## 📖 Full Documentation

See `ADVANCED_TRAINING_GUIDE.md` for complete details.

---
Last updated: (auto) Added BLEU/ROUGE guidance, RAG tuning tips, pipeline metrics examples.
