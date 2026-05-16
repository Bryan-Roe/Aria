# Quick Reference: AI Training Datasets

## 🚀 One-Command Setup

```powershell
python .\scripts\quick_setup_datasets.py
```

Downloads quantum datasets + Dolly 15k (~500 MB, 5 minutes)

---

## 📥 Download Commands

### Quantum ML Datasets

```powershell
python .\scripts\download_datasets.py --category quantum
```

### Chat Datasets

```powershell
# Small, high-quality (recommended first)
python .\scripts\download_datasets.py --category chat --dataset dolly

# Large, multi-turn conversations
python .\scripts\download_datasets.py --category chat --dataset openassistant

# All datasets under size limit
python .\scripts\download_datasets.py --category chat --dataset all --max-size 5
```

---

## ✅ Validate & Check

```powershell
# Validate all
python .\scripts\validate_datasets.py

# List downloaded
python .\scripts\download_datasets.py --list

# Check sizes
Get-ChildItem .\datasets -Recurse | Measure-Object -Property Length -Sum
```

---

## 🎯 Training Commands

### Quantum AI

```powershell
cd quantum-ai
python .\train_custom_dataset.py
```

### Phi-3.6 Fine-tuning (Small Test)

```powershell
cd AI\microsoft_phi-silica-3.6_v1
python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config .\lora\lora.yaml --max-train-samples 64 --no-stream
```

### Phi-3.6 Fine-tuning (Full)

```powershell
cd AI\microsoft_phi-silica-3.6_v1
python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly --config .\lora\lora.yaml
```

---

## 📊 Dataset Sizes & Quality

| Dataset | Size | Samples | Quality | License |
| --------- | ------ | --------- | --------- | --------- |
| **Quantum** | | | | |
| Heart Disease | <1 MB | 303 | ⭐⭐⭐⭐ | Free |
| Ionosphere | <1 MB | 351 | ⭐⭐⭐⭐ | Free |
| Sonar | <1 MB | 208 | ⭐⭐⭐⭐ | Free |
| **Chat/LLM** | | | | |
| Dolly 15k | 50 MB | 15,000 | ⭐⭐⭐⭐⭐ | Commercial ✅ |
| OpenAssistant | 500 MB | 161,000 | ⭐⭐⭐⭐⭐ | Commercial ✅ |
| Alpaca | 100 MB | 52,000 | ⭐⭐⭐⭐ | Non-commercial ⚠️ |

---

## 📁 Storage Locations

```text
datasets/
├── quantum/          # UCI ML datasets (CSV)
├── chat/             # LLM datasets (JSONL)
│   ├── dolly/       # Instruction pairs
│   └── openassistant/  # Multi-turn conversations
├── raw/             # Original downloads
└── processed/       # Cleaned data
```

---

## 🔧 Install Dependencies

```powershell
pip install -r dataset-requirements.txt
```

Includes: `datasets`, `tqdm`, `pandas`, `numpy`, `scikit-learn`

---

## 📚 Full Documentation

- **Comprehensive Catalog**: `AI_DATASETS_CATALOG.md`
- **Dataset Directory README**: `datasets/README.md`
- **Scripts Help**: `python .\scripts\download_datasets.py --help`

---

## 💡 Tips

1. **Start with Dolly 15k** - Small, high-quality, commercial-safe
2. **Validate after download** - Catch format errors early
3. **Test with --max-train-samples 64** - Quick iteration
4. **Monitor disk space** - Large datasets can be 10+ GB
5. **Check licenses** - Some datasets are non-commercial only
