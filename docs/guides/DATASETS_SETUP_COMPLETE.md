# AI Training Datasets - Setup Complete! ✅

**Status**: Ready for AI training
**Date**: October 31, 2025
**Location**: `C:\Users\Bryan\OneDrive\AI\datasets`

---

## 📦 What's Been Set Up

### 1. Directory Structure ✅
```
AI/
├── datasets/                    # Centralized data storage
│   ├── raw/                     # Original downloads
│   ├── processed/               # Cleaned data
│   ├── quantum/                 # ✅ 4 datasets downloaded (0.21 MB)
│   │   ├── heart_disease.csv   # 303 samples, 14 features
│   │   ├── ionosphere.csv      # 351 samples, 35 features
│   │   ├── sonar.csv           # 208 samples, 61 features
│   │   └── banknote.csv        # 1,372 samples, 5 features
│   ├── chat/                    # Ready for LLM datasets
│   ├── vision/                  # Ready for image data
│   ├── dataset_index.json      # Auto-updated inventory
│   └── README.md               # Full usage guide
├── scripts/                     # Automation tools
│   ├── download_datasets.py    # ✅ Tested & working
│   ├── validate_datasets.py    # ✅ Tested & working
│   └── quick_setup_datasets.py # One-command setup
├── AI_DATASETS_CATALOG.md       # Comprehensive dataset guide
├── DATASETS_QUICK_REF.md        # Quick command reference
└── dataset-requirements.txt     # Python dependencies
```

### 2. Automated Tools ✅
- **Downloader**: Downloads from UCI, Hugging Face, Kaggle
- **Validator**: Checks format, integrity, counts samples
- **Quick Setup**: One-command installation
- **Index Manager**: Tracks metadata automatically

### 3. Documentation ✅
- **AI_DATASETS_CATALOG.md**: 400+ line comprehensive guide
  - Dataset sources (Hugging Face, UCI, Kaggle)
  - License information
  - Quality ratings
  - Usage examples
- **datasets/README.md**: Full usage documentation
- **DATASETS_QUICK_REF.md**: Fast command reference

---

## 🚀 Next Steps - Start Training Now!

### Option 1: Train Quantum AI (Fastest - 2 minutes)
```powershell
cd quantum-ai
python .\train_custom_dataset.py
```

The script already uses the Wine dataset for demo. Modify `load_your_data()` to use downloaded datasets:

```python
# In train_custom_dataset.py, replace the demo code with:
df = pd.read_csv("../datasets/quantum/heart_disease.csv")
X = df.iloc[:, :-1].values  # All features except last
y = df.iloc[:, -1].values   # Last column as label
return X, y
```

### Option 2: Download Chat Dataset & Fine-tune Phi-3.6
```powershell
# Step 1: Download Dolly 15k (50 MB, 2 minutes)
python .\scripts\download_datasets.py --category chat --dataset dolly

# Step 2: Quick test (CPU-friendly, 10 minutes)
cd AI\microsoft_phi-silica-3.6_v1
python .\scripts\train_lora.py `
  --dataset ..\..\datasets\chat\dolly `
  --config .\lora\lora.yaml `
  --max-train-samples 64 `
  --max-eval-samples 32 `
  --no-stream

# Step 3: Full training (GPU required, hours)
python .\scripts\train_lora.py `
  --dataset ..\..\datasets\chat\dolly `
  --config .\lora\lora.yaml
```

### Option 3: One-Command Setup (Everything)
```powershell
# Downloads quantum + Dolly 15k + validates all
python .\scripts\quick_setup_datasets.py
```

---

## 📊 Currently Available

### Quantum Datasets (Downloaded ✅)
| Dataset | Size | Samples | Features | Use Case |
|---------|------|---------|----------|----------|
| Heart Disease | 20 KB | 303 | 14 | Medical diagnosis |
| Ionosphere | 70 KB | 351 | 35 | Radar signal classification |
| Sonar | 80 KB | 208 | 61 | Object detection (mines vs rocks) |
| Banknote | 40 KB | 1,372 | 5 | Authentication (fraud detection) |

**Total**: 4 datasets, 210 KB, 2,234 samples

### Built-in Datasets (No Download Needed)
- Iris (150 samples, 4 features) - via scikit-learn
- Wine (178 samples, 13 features) - via scikit-learn
- Breast Cancer (569 samples, 30 features) - via scikit-learn

### Chat Datasets (Ready to Download)
| Dataset | Size | Quality | License | Command |
|---------|------|---------|---------|---------|
| Dolly 15k | 50 MB | ⭐⭐⭐⭐⭐ | Commercial ✅ | `--dataset dolly` |
| OpenAssistant | 500 MB | ⭐⭐⭐⭐⭐ | Commercial ✅ | `--dataset openassistant` |
| Alpaca | 100 MB | ⭐⭐⭐⭐ | Non-commercial ⚠️ | `--dataset alpaca` |

---

## 🎯 Recommended Workflow

### For Quantum AI Development:
1. ✅ **Quantum datasets downloaded** - Ready to use!
2. Train on built-in datasets first (Iris, Wine)
3. Switch to UCI datasets for real-world testing
4. Use 4 qubits for Iris, 6-8 qubits for larger datasets
5. PCA recommended for >10 features

### For LLM Fine-tuning:
1. Download Dolly 15k (commercial-safe, high quality)
2. Test with `--max-train-samples 64` (quick iteration)
3. Scale up to full dataset when ready
4. Monitor GPU memory usage
5. Use streaming for >5GB datasets

### For Both:
1. Always validate after downloading
2. Check `dataset_index.json` for metadata
3. Monitor disk space (`Get-PSDrive C`)
4. Document your data sources
5. Respect dataset licenses

---

## 🔧 Maintenance Commands

### Check what's downloaded:
```powershell
python .\scripts\download_datasets.py --list
```

### Validate everything:
```powershell
python .\scripts\validate_datasets.py --verbose
```

### Download more datasets:
```powershell
# See full catalog
type AI_DATASETS_CATALOG.md

# Download specific dataset
python .\scripts\download_datasets.py --category chat --dataset dolly
```

### Check storage usage:
```powershell
Get-ChildItem .\datasets -Recurse | Measure-Object -Property Length -Sum
```

---

## 📚 Documentation Index

1. **AI_DATASETS_CATALOG.md** - Comprehensive guide
   - All available datasets
   - Sources and licenses
   - Quality ratings
   - Training examples

2. **datasets/README.md** - Usage documentation
   - Directory structure
   - Download instructions
   - Training commands
   - Troubleshooting

3. **DATASETS_QUICK_REF.md** - Fast reference
   - Common commands
   - Size/quality table
   - Quick tips

4. **dataset-requirements.txt** - Dependencies
   - `datasets` (Hugging Face)
   - `tqdm` (progress bars)
   - `pandas`, `numpy`, `scikit-learn`

---

## ✅ Verification Results

### Downloads: ✅ PASSED
- Heart Disease: 303 samples, 14 features
- Ionosphere: 351 samples, 35 features
- Sonar: 208 samples, 61 features
- Banknote: 1,372 samples, 5 features

### Validation: ✅ PASSED
- All CSV files valid
- No format errors
- Feature counts consistent
- Ready for training

### Scripts: ✅ TESTED
- `download_datasets.py --help` ✅
- `download_datasets.py --category quantum` ✅
- `validate_datasets.py --category quantum --verbose` ✅
- All 4 datasets downloaded and validated

---

## 🎓 Learning Resources

### Dataset Sources:
- **Hugging Face**: 100,000+ datasets for ML/NLP
- **UCI ML Repository**: Classic ML datasets (30+ years)
- **Kaggle**: Competitions and community datasets
- **Papers with Code**: Research-quality datasets

### Training Tutorials:
- Quantum AI: `ai-projects/quantum-ml/README.md`
- Phi-3.6 Fine-tuning: `AI/microsoft_phi-silica-3.6_v1/README.md`
- Custom datasets: `ai-projects/quantum-ml/train_custom_dataset.py`

### Tools:
- Hugging Face `datasets` library (streaming, caching)
- Pandas (CSV/Excel processing)
- Scikit-learn (built-in datasets, preprocessing)
- Azure ML (large-scale training)

---

## 🚨 Important Notes

### Licenses:
- **Commercial OK**: Dolly, OpenAssistant, UCI datasets
- **Non-commercial**: Alpaca, some Kaggle datasets
- Always check license before production use

### Storage:
- Current: ~0.21 MB (quantum datasets)
- Recommended: 10 GB for diverse datasets
- Large-scale: 50-500 GB for production

### Dependencies:
Some scripts require packages not in base environment:
```powershell
pip install -r dataset-requirements.txt
```

### Git:
Add to `.gitignore`:
```
datasets/raw/
datasets/chat/
datasets/vision/
*.csv
*.jsonl
```

Keep in Git:
```
datasets/README.md
datasets/dataset_index.json
```

---

## 🎉 You're All Set!

Your AI workspace now has:
- ✅ Centralized dataset storage
- ✅ Automated download tools
- ✅ Validation scripts
- ✅ 4 quantum datasets ready
- ✅ Comprehensive documentation
- ✅ Training examples

**Start training now!** Choose an option from "Next Steps" above.

For questions or issues, see the documentation files or run:
```powershell
python .\scripts\download_datasets.py --help
python .\scripts\validate_datasets.py --help
```

Happy training! 🚀
