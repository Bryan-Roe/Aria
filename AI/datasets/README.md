# AI Training Datasets

Centralized storage for all AI training datasets across workspace projects.

## Quick Start

```powershell
# One-command setup (recommended for first time)
python .\scripts\quick_setup_datasets.py

# Or manually download specific datasets
python .\scripts\download_datasets.py --category quantum
python .\scripts\download_datasets.py --category chat --dataset dolly
```

## Directory Structure

```
datasets/
├── raw/              # Original downloaded data (untouched)
├── processed/        # Cleaned and preprocessed data
├── quantum/          # Quantum ML datasets (UCI, specialized)
├── chat/             # Chat/LLM fine-tuning datasets
├── vision/           # Image/video datasets
└── dataset_index.json  # Metadata and inventory
```

## Available Datasets

### Quantum AI (Ready to Use)

| Dataset | Samples | Features | Type | Location |
|---------|---------|----------|------|----------|
| Heart Disease | 303 | 14 | CSV | `quantum/heart_disease.csv` |
| Ionosphere | 351 | 34 | CSV | `quantum/ionosphere.csv` |
| Sonar | 208 | 60 | CSV | `quantum/sonar.csv` |
| Banknote | 1,372 | 5 | CSV | `quantum/banknote.csv` |

**Built-in** (via scikit-learn - no download needed):
- Iris (150 samples, 4 features)
- Wine (178 samples, 13 features)
- Breast Cancer (569 samples, 30 features)

### Chat/LLM Fine-Tuning

| Dataset | Size | License | Quality | Location |
|---------|------|---------|---------|----------|
| Dolly 15k | ~50 MB | CC BY-SA 3.0 ✅ | ⭐⭐⭐⭐⭐ | `chat/dolly/` |
| OpenAssistant | ~500 MB | Apache 2.0 ✅ | ⭐⭐⭐⭐⭐ | `chat/openassistant/` |
| Alpaca | ~100 MB | CC BY-NC 4.0 ⚠️ | ⭐⭐⭐⭐ | `chat/alpaca/` |

✅ = Commercial use allowed  
⚠️ = Non-commercial only

## Usage Examples

### 1. Train Quantum Model on Downloaded Dataset

```powershell
cd quantum-ai

# Train on downloaded UCI dataset
python .\train_custom_dataset.py

# Modify train_custom_dataset.py to load your data:
# df = pd.read_csv("../datasets/quantum/heart_disease.csv")
```

### 2. Fine-tune Phi-3.6 on Chat Dataset

```powershell
cd AI\microsoft_phi-silica-3.6_v1

# Small test (CPU-friendly)
python .\scripts\train_lora.py `
  --dataset ..\..\datasets\chat\dolly `
  --config .\lora\lora.yaml `
  --max-train-samples 64 `
  --max-eval-samples 32 `
  --no-stream

# Full training (GPU required)
python .\scripts\train_lora.py `
  --dataset ..\..\datasets\chat\dolly `
  --config .\lora\lora.yaml
```

### 3. Convert Your Own Data

```powershell
# Prepare custom dataset for Phi-3.6
cd AI\microsoft_phi-silica-3.6_v1
python .\scripts\prepare_dataset.py `
  --input C:\path\to\your\data `
  --output-dir ..\..\datasets\chat\my_dataset `
  --train-ratio 0.9
```

## Dataset Management

### Download More Datasets

```powershell
# List available datasets
python .\scripts\download_datasets.py --help

# Download all quantum datasets
python .\scripts\download_datasets.py --category quantum

# Download specific chat dataset
python .\scripts\download_datasets.py --category chat --dataset dolly

# Download all chat datasets under 5GB
python .\scripts\download_datasets.py --category chat --dataset all --max-size 5
```

### Validate Datasets

```powershell
# Validate all datasets
python .\scripts\validate_datasets.py

# Validate specific category
python .\scripts\validate_datasets.py --category quantum --verbose

# Validate specific dataset
python .\scripts\validate_datasets.py --category chat --dataset dolly --verbose
```

### List Downloaded Datasets

```powershell
python .\scripts\download_datasets.py --list
```

## Storage Management

### Check Dataset Sizes

```powershell
# Get total size
Get-ChildItem .\datasets -Recurse | Measure-Object -Property Length -Sum

# Size by category
Get-ChildItem .\datasets\quantum | Measure-Object -Property Length -Sum
Get-ChildItem .\datasets\chat -Recurse | Measure-Object -Property Length -Sum
```

### Clean Up

```powershell
# Remove specific dataset
Remove-Item -Recurse .\datasets\chat\alpaca

# Remove all raw downloads (keep processed)
Remove-Item -Recurse .\datasets\raw\*

# Clear entire cache (re-download needed)
Remove-Item -Recurse .\datasets\*
```

## Data Formats

### JSONL (Chat Datasets)

Phi-3 chat template format:
```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### CSV (Quantum Datasets)

Standard CSV format:
```csv
feature1,feature2,feature3,label
1.2,3.4,5.6,0
2.3,4.5,6.7,1
```

## Finding More Datasets

See **AI_DATASETS_CATALOG.md** for comprehensive list including:

- **Hugging Face Hub**: https://huggingface.co/datasets
- **UCI ML Repository**: https://archive.ics.uci.edu/ml/
- **Kaggle**: https://www.kaggle.com/datasets
- **Papers with Code**: https://paperswithcode.com/datasets

## Troubleshooting

### Import Errors

If you see "Import 'datasets' could not be resolved":

```powershell
pip install -r dataset-requirements.txt
```

### Download Failures

Check internet connection and retry:
```powershell
python .\scripts\download_datasets.py --category chat --dataset dolly
```

### JSONL Format Errors

Validate and fix:
```powershell
python .\scripts\validate_datasets.py --category chat --verbose
```

Common issues:
- Trailing blank lines (remove with text editor)
- Invalid JSON syntax (check with JSON validator)
- Missing required fields (ensure "messages" array exists)

### Out of Disk Space

Check available space:
```powershell
Get-PSDrive C | Select-Object Used,Free
```

Download smaller datasets or increase storage.

## Best Practices

1. **Start Small**: Use Dolly 15k (50 MB) before downloading large datasets
2. **Validate**: Always run `validate_datasets.py` after downloading
3. **Version Control**: Add `datasets/` to `.gitignore` (data is large)
4. **Backup Index**: Keep `dataset_index.json` in version control
5. **Document Sources**: Track dataset origins for licensing/citation

## License Information

Each dataset has its own license. Check `dataset_index.json` or the catalog for details.

**Commercial-safe datasets in this workspace:**
- Dolly 15k (CC BY-SA 3.0)
- OpenAssistant (Apache 2.0)
- UCI datasets (Attribution required)

## Support

- See: `AI_DATASETS_CATALOG.md` for full dataset documentation
- Scripts: `scripts/download_datasets.py`, `scripts/validate_datasets.py`
- Issues: Check validation output for specific errors
