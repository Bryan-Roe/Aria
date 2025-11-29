# Advanced Training Pipeline Guide

Complete guide for automatic evaluation, RAG pipeline, semantic pruning, and GPU optimization.

## 🚀 Quick Start

```bash
cd AI\microsoft_phi-silica-3.6_v1

# 1. Optimize for your GPU
python scripts\gpu_optimizer.py --update-config lora\lora.yaml

# 2. Prune your training data
python scripts\semantic_pruning.py --input ..\..\datasets\chat\dolly\train.jsonl --output data\pruned_train.jsonl

# 3. Train with optimized settings
python scripts\train_lora.py --dataset data --config lora\lora.yaml

# 4. Evaluate the model
python scripts\auto_eval.py --model data_out\lora_training --dataset ..\..\datasets\chat\dolly\test.jsonl

# 5. Use with RAG
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --interactive
```

## 📊 1. Automatic Evaluation

Automatically evaluate fine-tuned models with multiple metrics.

### Features
- **Perplexity**: Language model quality metric
- **Inference Speed**: Tokens per second, latency
- **Memory Usage**: GPU memory consumption
- **Quality Metrics**: BLEU, ROUGE scores (optional)
- **Model Comparison**: Benchmark multiple models

### Basic Usage

```bash
# Evaluate single model
python scripts\auto_eval.py \
  --model data_out\lora_training \
  --dataset ..\..\datasets\chat\dolly\test.jsonl \
  --num-samples 100

# Compare multiple models
python scripts\auto_eval.py \
  --model data_out\lora_training \
  --dataset ..\..\datasets\chat\dolly\test.jsonl \
  --metrics perplexity inference_time bleu \
  --output-name model_v1
```

### Output

Results saved to `data_out/evaluation_results/`:
```json
{
  "perplexity": 12.34,
  "inference_time_ms": 45.67,
  "tokens_per_second": 89.12,
  "memory_usage_mb": 6789.0
}
```

### Integration with Training

```python
from scripts.auto_eval import AutomaticEvaluator

evaluator = AutomaticEvaluator()
metrics = evaluator.evaluate_model(
    model_path="data_out/lora_training",
    test_dataset="test.jsonl",
    num_samples=100
)
print(f"Perplexity: {metrics.perplexity:.2f}")
```

## 🔍 2. RAG Pipeline Setup

Retrieval-Augmented Generation for enhanced model responses.

### Features
- **Document Indexing**: Load documents from any directory
- **Semantic Search**: Find relevant context using embeddings
- **Context Integration**: Inject retrieved docs into prompts
- **Interactive Mode**: Question-answering interface
- **Persistent Index**: Save/load document embeddings

### Setup

```bash
# Install optional dependencies
pip install sentence-transformers

# Build document index
python scripts\rag_pipeline.py \
  --model data_out\lora_training \
  --docs ..\..\datasets \
  --rebuild-index

# Interactive mode
python scripts\rag_pipeline.py \
  --model data_out\lora_training \
  --docs ..\..\datasets \
  --interactive
```

### Document Structure

```
datasets/
├── quantum/           # Will be indexed
│   ├── README.md
│   └── data.csv
├── chat/              # Will be indexed
│   └── dolly/
└── processed/         # Will be indexed
```

### Configuration

Edit `scripts/rag_pipeline.py` or create `rag_config.yaml`:

```yaml
embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
chunk_size: 512          # Tokens per chunk
chunk_overlap: 50        # Overlap between chunks
top_k_retrieval: 3       # Number of docs to retrieve
retrieval_threshold: 0.7 # Minimum similarity score
```

### Programmatic Usage

```python
from scripts.rag_pipeline import RAGPipeline, DocumentStore, RAGConfig

# Setup
config = RAGConfig(top_k_retrieval=5)
doc_store = DocumentStore(config)
doc_store.load_from_directory("../../datasets")
doc_store.build_index()

# Create pipeline
rag = RAGPipeline("data_out/lora_training", doc_store, config)

# Query
result = rag.query("What are quantum circuits?")
print(result["answer"])
```

## 🧹 3. Semantic Pruning

Remove redundant and low-quality training samples to improve efficiency.

### Features
- **Exact Deduplication**: Remove identical samples
- **Semantic Deduplication**: Remove similar samples via embeddings
- **Quality Filtering**: Score and filter low-quality data
- **Length Filtering**: Remove outliers
- **Diversity Preservation**: Ensure varied training set

### Basic Usage

```bash
# Prune dataset with defaults
python scripts\semantic_pruning.py \
  --input ..\..\datasets\chat\dolly\train.jsonl \
  --output data\pruned_train.jsonl

# Custom thresholds
python scripts\semantic_pruning.py \
  --input ..\..\datasets\chat\dolly\train.jsonl \
  --output data\pruned_train.jsonl \
  --similarity-threshold 0.90 \
  --quality-threshold 0.4
```

### Pruning Strategies

1. **Exact Duplicates**: Hash-based removal (fast)
2. **Length Outliers**: Remove samples outside 10-2048 tokens
3. **Quality Scoring**: Based on:
   - Length appropriateness
   - Character diversity
   - Word diversity
   - Punctuation presence
4. **Semantic Similarity**: Embedding-based (requires sentence-transformers)
5. **Diversity Sampling**: Keep highest quality from each cluster

### Configuration Options

```python
from scripts.semantic_pruning import PruningConfig, SemanticPruner

config = PruningConfig(
    similarity_threshold=0.95,   # Higher = more aggressive
    min_length=10,               # Minimum words
    max_length=2048,             # Maximum words
    quality_threshold=0.3,       # 0.0-1.0 scale
    target_reduction=0.3         # Target 30% reduction
)

pruner = SemanticPruner(config)
stats = pruner.prune_dataset("input.jsonl", "output.jsonl")
stats.print_summary()
```

### Expected Results

```
=== Semantic Pruning Results ===
Original samples: 15,000
Final samples: 10,500 (30.0% reduction)

Breakdown:
  - Duplicates: 1,200
  - Low quality: 2,100
  - Outliers: 450
  - Redundant: 750
```

### Integration with Training

```bash
# Full pipeline: Prune → Train → Evaluate
python scripts\semantic_pruning.py --input data\raw.jsonl --output data\clean.jsonl
python scripts\train_lora.py --dataset data --config lora\lora.yaml
python scripts\auto_eval.py --model data_out\lora_training --dataset data\test.jsonl
```

## ⚡ 4. GPU Training Optimization Profile

Automatically configure optimal training settings for your hardware.

### Features
- **Hardware Detection**: Automatic GPU capability detection
- **Memory Optimization**: Configure batch size, quantization
- **Precision Selection**: FP16/BF16/8-bit/4-bit based on VRAM
- **Advanced Features**: Flash Attention, compiled models
- **Multi-GPU Support**: Automatic scaling
- **Config Updates**: Direct YAML file modification

### Quick Setup

```bash
# Detect hardware and create profile
python scripts\gpu_optimizer.py

# Update existing config
python scripts\gpu_optimizer.py --update-config lora\lora.yaml

# Specify model size
python scripts\gpu_optimizer.py --model-size 7.0 --memory-usage 0.8
```

### Hardware Profiles

#### High-End GPU (A100 80GB, RTX 4090 24GB)
```yaml
batch_size: 4
gradient_accumulation_steps: 1
gradient_checkpointing: false
bf16: true
max_seq_length: 2048
lora_rank: 32
flash_attention: true
compile_model: true
```

#### Mid-Range GPU (RTX 3090 24GB, V100 16GB)
```yaml
batch_size: 2
gradient_accumulation_steps: 2
gradient_checkpointing: true
fp16: true
max_seq_length: 1024
lora_rank: 16
```

#### Budget GPU (RTX 3060 12GB, T4 16GB)
```yaml
batch_size: 1
gradient_accumulation_steps: 4
gradient_checkpointing: true
use_8bit: true
max_seq_length: 512
lora_rank: 8
```

#### Limited VRAM (GTX 1080 Ti 11GB)
```yaml
batch_size: 1
gradient_accumulation_steps: 8
gradient_checkpointing: true
use_4bit: true
cpu_offload: true
max_seq_length: 256
lora_rank: 4
```

### Output

```
=== GPU Hardware Detection ===
GPU Name: NVIDIA GeForce RTX 4090
GPU Count: 1
Total Memory: 24.00 GB
Available Memory: 22.50 GB
Compute Capability: 8.9
CUDA Version: 12.1

=== Optimization Profile Creation ===
Model size: 7.00 GB
Available memory: 18.00 GB
Profile: Performance (BF16 + optimizations)

=== Recommended Settings ===
Batch Size: 4
Gradient Accumulation: 1
Effective Batch Size: 4
Max Sequence Length: 2048
LoRA Rank: 32
Precision: BF16
Gradient Checkpointing: False
Flash Attention: True
Compiled Model: True

Estimated tokens/step: 8,192
```

### Environment Variables

```bash
# Export optimized environment
python scripts\gpu_optimizer.py --export-env > gpu_env.sh

# Windows (PowerShell)
$env:CUDA_VISIBLE_DEVICES = "0"
$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:512"
$env:TOKENIZERS_PARALLELISM = "false"

# Linux/Mac
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
export TOKENIZERS_PARALLELISM=false
```

### Multi-GPU Training

```bash
# Automatic multi-GPU detection
python scripts\gpu_optimizer.py --update-config lora\lora.yaml

# Manual DeepSpeed config (for 2+ GPUs)
python scripts\train_lora.py \
  --dataset data \
  --config lora\lora.yaml \
  --deepspeed scripts\deepspeed_zero3.json
```

## 🔄 Complete Workflow

### End-to-End Pipeline

```bash
# Step 1: Optimize for hardware
python scripts\gpu_optimizer.py --update-config lora\lora.yaml --model-size 7.0

# Step 2: Prune training data
python scripts\semantic_pruning.py \
  --input ..\..\datasets\chat\dolly\train.jsonl \
  --output data\pruned_train.jsonl \
  --similarity-threshold 0.95

# Step 3: Train with optimized settings
python scripts\train_lora.py \
  --dataset data \
  --config lora\lora.yaml

# Step 4: Evaluate model
python scripts\auto_eval.py \
  --model data_out\lora_training \
  --dataset ..\..\datasets\chat\dolly\test.jsonl \
  --metrics perplexity inference_time \
  --output-name experiment_1

# Step 5: Setup RAG for deployment
python scripts\rag_pipeline.py \
  --model data_out\lora_training \
  --docs ..\..\datasets \
  --rebuild-index

# Step 6: Test RAG interactively
python scripts\rag_pipeline.py \
  --model data_out\lora_training \
  --docs ..\..\datasets \
  --interactive
```

### Master Orchestration Script

See `scripts\run_pipeline.py` for automated orchestration.

## 📦 Dependencies

### Core Requirements (already installed)
```
torch>=2.0.0
transformers>=4.36.0
datasets>=2.14.0
pyyaml>=6.0
numpy>=1.24.0
```

### Optional Requirements

```bash
# For semantic search and pruning
pip install sentence-transformers

# For quality metrics
pip install rouge-score sacrebleu

# For 4-bit/8-bit quantization
pip install bitsandbytes

# For flash attention (Linux only)
pip install flash-attn --no-build-isolation
```

## 🎯 Performance Tips

### Training Speed
1. Use GPU optimizer to find best batch size
2. Enable gradient checkpointing only if OOM
3. Use BF16 on Ampere+ GPUs (A100, RTX 30xx+)
4. Enable flash attention on supported GPUs
5. Use compiled models (PyTorch 2.0+)

### Memory Efficiency
1. Start with 4-bit quantization on limited VRAM
2. Use gradient accumulation to simulate larger batches
3. Reduce sequence length if still OOM
4. Enable CPU offload as last resort
5. Prune dataset to reduce training time

### Data Quality
1. Always prune training data first
2. Use similarity threshold 0.90-0.95 for deduplication
3. Set quality threshold based on your domain
4. Keep test set unpruned for fair evaluation
5. Monitor perplexity during evaluation

### RAG Performance
1. Build index once, reuse across runs
2. Use smaller embedding models for speed
3. Adjust chunk size based on your documents
4. Lower top_k for faster retrieval
5. Cache embeddings on SSD

## 🐛 Troubleshooting

### Out of Memory
```bash
# Run optimizer with conservative settings
python scripts\gpu_optimizer.py --memory-usage 0.6

# Or manually reduce batch size
python scripts\train_lora.py --batch-size 1 --gradient-accumulation 8
```

### Slow Training
```bash
# Check if using optimal settings
python scripts\gpu_optimizer.py

# Profile training
python -m torch.utils.bottleneck scripts\train_lora.py ...
```

### Poor Evaluation Scores
```bash
# Prune more aggressively
python scripts\semantic_pruning.py --quality-threshold 0.5

# Check data quality
python scripts\semantic_pruning.py --input data.jsonl --output /dev/null
```

### RAG Not Finding Context
```bash
# Rebuild index with lower threshold
python scripts\rag_pipeline.py --rebuild-index

# Check document loading
python -c "from scripts.rag_pipeline import DocumentStore, RAGConfig; ds = DocumentStore(RAGConfig()); ds.load_from_directory('docs'); print(len(ds.documents))"
```

## 📚 API Reference

See individual script files for detailed API documentation:
- `scripts/auto_eval.py` - Evaluation framework
- `scripts/rag_pipeline.py` - RAG components
- `scripts/semantic_pruning.py` - Data pruning
- `scripts/gpu_optimizer.py` - Hardware optimization

## 🎓 Examples

### Example 1: Quick Training
```bash
python scripts\gpu_optimizer.py --update-config lora\lora.yaml
python scripts\train_lora.py --dataset data --config lora\lora.yaml --max-train-samples 1000
python scripts\auto_eval.py --model data_out\lora_training --dataset data\test.jsonl
```

### Example 2: Production Pipeline
```bash
# Full quality training
python scripts\semantic_pruning.py --input raw.jsonl --output clean.jsonl --similarity-threshold 0.95
python scripts\gpu_optimizer.py --update-config lora\lora.yaml
python scripts\train_lora.py --dataset data --config lora\lora.yaml
python scripts\auto_eval.py --model data_out\lora_training --dataset test.jsonl --metrics perplexity inference_time
```

### Example 3: RAG Deployment
```bash
# Index all docs
python scripts\rag_pipeline.py --model data_out\lora_training --docs ..\..\datasets --rebuild-index --index-dir data_out\rag_index

# Query API
python -c "
from scripts.rag_pipeline import RAGPipeline, DocumentStore, RAGConfig
doc_store = DocumentStore(RAGConfig())
doc_store.load_index('data_out/rag_index')
rag = RAGPipeline('data_out/lora_training', doc_store)
print(rag.query('What is quantum computing?')['answer'])
"
```

## 📈 Monitoring

All tools output results to `data_out/`:
```
data_out/
├── lora_training/           # Trained model
├── evaluation_results/      # Evaluation JSONs
├── rag_index/              # RAG document index
├── gpu_profile.yaml        # Hardware profile
└── pruned_stats.json       # Pruning statistics
```

## 🔗 Integration

These tools integrate seamlessly with existing training scripts:

```python
# In your training script
from scripts.gpu_optimizer import GPUOptimizer
from scripts.auto_eval import AutomaticEvaluator

# Optimize before training
optimizer = GPUOptimizer()
profile = optimizer.create_optimization_profile()
# Use profile.batch_size, profile.learning_rate, etc.

# Evaluate after training
evaluator = AutomaticEvaluator()
metrics = evaluator.evaluate_model(model_path, test_data)
```

---

**🎉 You're all set!** Run the pipeline and optimize your training workflow.
