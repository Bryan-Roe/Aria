# Dataset Collection and Management System

Comprehensive automated system for discovering, downloading, validating, and managing datasets for AI training.

## 🚀 Quick Start

### Quick Mode (Fastest - sklearn only)
```bash
python scripts/dataset_automation.py --quick
```

### Full Collection (All Sources)
```bash
python scripts/dataset_automation.py --sources sklearn openml huggingface
```

### Validation Only
```bash
python scripts/dataset_automation.py --validate-only
```

## 📦 Available Data Sources

| Source | Type | Speed | Requires Auth | Description |
|--------|------|-------|---------------|-------------|
| **sklearn** | Built-in | ⚡ Fast | ❌ No | Scikit-learn datasets (iris, wine, breast_cancer, digits) |
| **openml** | Public API | 🐢 Slow | ❌ No | OpenML repository (1000+ datasets) |
| **huggingface** | Public API | 🐌 Very Slow | ❌ No | High-quality chat/instruction datasets |
| **kaggle** | Public API | 🐢 Slow | ✅ Yes | Community datasets (requires API key) |
| **uci** | Direct Download | 🚀 Fast | ❌ No | UCI ML Repository datasets |

## 🛠️ Scripts

### 1. Main Automation Pipeline
**File:** `scripts/dataset_automation.py`

Orchestrates collection, validation, and preparation.

**Usage:**
```bash
# Quick test (sklearn only, ~10 seconds)
python scripts/dataset_automation.py --quick

# Specific sources with limit
python scripts/dataset_automation.py --sources sklearn openml --limit 50

# Collection only (skip validation)
python scripts/dataset_automation.py --collect-only

# Validation only (skip collection)
python scripts/dataset_automation.py --validate-only
```

### 2. Dataset Collector
**File:** `scripts/data_collection/comprehensive_dataset_collector.py`

Core collection engine supporting multiple sources.

**Usage:**
```bash
# Direct usage
cd scripts/data_collection
python comprehensive_dataset_collector.py --sources sklearn openml --limit 20

# Quick mode
python comprehensive_dataset_collector.py --quick
```

**Features:**
- ✅ Multi-source collection (5 sources)
- ✅ Automatic augmentation (adds noise variations)
- ✅ Format conversion (standardizes to CSV/JSONL)
- ✅ Parallel downloads (configurable workers)
- ✅ Quality validation during download

### 3. Dataset Validator
**File:** `scripts/data_collection/dataset_validator.py`

Validates dataset quality and integrity.

**Usage:**
```bash
# Validate all datasets
python scripts/data_collection/dataset_validator.py

# Validate specific category
python scripts/data_collection/dataset_validator.py --category quantum
```

**Validation Checks:**
- ✅ Minimum sample count (≥10)
- ✅ Minimum feature count (≥2)
- ✅ Missing value ratio (<50%)
- ✅ Duplicate detection
- ✅ Data variance checks
- ✅ Format compliance (JSONL chat format)

**Quality Score:** 0-100 scale
- **90-100:** Excellent
- **70-89:** Good
- **50-69:** Acceptable
- **<50:** Poor (flagged)

### 4. Dataset Statistics
**File:** `scripts/data_collection/dataset_statistics.py`

Generates comprehensive dataset inventory and statistics.

**Usage:**
```bash
python scripts/data_collection/dataset_statistics.py
```

**Output:**
- Total files by category
- Sample counts
- File sizes
- Top datasets by size
- JSON report in `data_out/reports/`

## 📁 Directory Structure

```
datasets/
├── quantum/              # Quantum ML datasets (CSV)
│   ├── *.csv            # Raw datasets
│   └── *_aug.csv        # Augmented versions
├── chat/                 # Chat/instruction datasets (JSONL)
│   ├── dolly/
│   ├── aria_movement/
│   └── app_repo/
├── vision/              # Vision datasets (future)
├── massive_quantum/     # Large quantum dataset collection
└── dataset_index.json   # Master index

data_out/
├── data_collection/
│   └── collection_report.json      # Collection results
├── validation/
│   ├── validation_report.json      # Validation results
│   └── validation_issues.txt       # Issues found
└── reports/
    └── dataset_statistics.json     # Statistics report
```

## 🔧 Configuration

Edit `config/autonomous_training.yaml`:

```yaml
data_collection:
  auto_discover: true
  min_datasets: 500
  quality_threshold: 60        # Minimum quality score (0-100)
  categories:
    - quantum
    - chat
    - vision
  sources:
    - sklearn
    - openml
    - huggingface
    - kaggle
    - uci
  parallel_downloads: 15
  auto_augment: true
  validate_on_download: true
```

## 📊 Dataset Categories

### Quantum Datasets (CSV)
Small to medium classification datasets suitable for quantum ML:
- Medical: breast_cancer, diabetes, heart_disease
- Science: ionosphere, sonar, glass
- General: iris, wine, banknote

**Format:** CSV with numeric features and target column

### Chat Datasets (JSONL)
Instruction/response pairs for chat model training:
- dolly: Databricks 15k instruction pairs
- aria_movement: Synthetic movement commands
- app_repo: Repository-aware Q&A

**Format:** JSONL with `{"messages": [{"role": "user|assistant", "content": "..."}]}`

## 🎯 Quality Thresholds

| Metric | Minimum | Recommended |
|--------|---------|-------------|
| Samples | 10 | 100+ |
| Features | 2 | 5+ |
| Missing ratio | <50% | <20% |
| Duplicate ratio | <50% | <10% |
| Quality score | 50 | 70+ |

## 📈 Output Reports

### Collection Report
**Location:** `data_out/data_collection/collection_report.json`

Contains:
- Downloaded dataset list
- Source breakdown
- Category breakdown
- Augmentation count
- Validation results

### Validation Report
**Location:** `data_out/validation/validation_report.json`

Contains:
- Total datasets validated
- Valid/invalid counts
- Quality scores per dataset
- Issue descriptions
- Metadata (samples, features, size)

### Statistics Report
**Location:** `data_out/reports/dataset_statistics.json`

Contains:
- Per-category statistics
- File counts (CSV/JSONL)
- Sample counts
- Size metrics
- Top datasets

## 🔑 API Keys (Optional)

Some sources require authentication:

### Kaggle
1. Create account at kaggle.com
2. Go to Account → API → Create New Token
3. Save `kaggle.json` to `~/.kaggle/kaggle.json`

### HuggingFace (Optional)
```bash
export HF_TOKEN=your_token_here
```

## 🚨 Troubleshooting

### ImportError: No module named 'openml'
```bash
pip install openml
```

### ImportError: No module named 'datasets'
```bash
pip install datasets
```

### Kaggle API not configured
```bash
pip install kaggle
# Place kaggle.json in ~/.kaggle/
```

### Low disk space
Check available space:
```bash
df -h
```

Dataset location: `/workspaces/AI/datasets/`

## 🔄 Integration with Training

After collection, datasets are automatically available for:
- **Autonomous Training:** `scripts/training/autonomous_training_orchestrator.py`
- **AutoTrain:** `scripts/training/autotrain.py`
- **Progressive Training:** `scripts/training/progressive_training.py`

The training orchestrators automatically discover and use validated datasets.

## 📝 Best Practices

1. **Start with Quick Mode:** Test with `--quick` before full collection
2. **Validate First:** Run validation before training to catch issues
3. **Monitor Disk Space:** Large collections can use significant space
4. **Review Reports:** Check quality scores in validation reports
5. **Incremental Collection:** Collect in batches rather than all at once
6. **Set Quality Threshold:** Adjust `quality_threshold` in config based on needs

## 🎓 Examples

### Complete Workflow
```bash
# 1. Quick test collection
python scripts/dataset_automation.py --quick

# 2. View statistics
python scripts/data_collection/dataset_statistics.py

# 3. Full collection (more sources)
python scripts/dataset_automation.py --sources sklearn openml uci --limit 30

# 4. Validate everything
python scripts/dataset_automation.py --validate-only

# 5. Ready for training!
python scripts/training/autonomous_training_orchestrator.py
```

### Targeted Collection
```bash
# Only get quantum datasets from sklearn and UCI
python scripts/data_collection/comprehensive_dataset_collector.py \
  --sources sklearn uci \
  --limit 50

# Validate quantum datasets only
python scripts/data_collection/dataset_validator.py --category quantum
```

## 🤝 Contributing

To add a new data source:

1. Add collector function to `comprehensive_dataset_collector.py`:
```python
async def collect_from_newsource(self, category: str, limit: int) -> List[Dict]:
    # Your collection logic
    pass
```

2. Register in `self.sources`:
```python
self.sources = {
    # ... existing sources
    "newsource": self.collect_from_newsource
}
```

3. Update config and documentation

## 📚 Related Documentation

- [Training Guide](../QUANTUM_TRAINING_QUICK_START.md)
- [Autonomous Training](autonomous_training.md)
- [Dataset Requirements](dataset-requirements.txt)
