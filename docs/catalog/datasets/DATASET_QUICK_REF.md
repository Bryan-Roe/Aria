# Dataset Collection - Quick Reference

## 🚀 One-Line Commands

```bash
# Quick test (30 sec) - sklearn only
python scripts/dataset_automation.py --quick

# Full collection (5-10 min) - multiple sources
python scripts/dataset_automation.py --sources sklearn openml uci --limit 30

# Validate all datasets (1-2 min)
python scripts/dataset_automation.py --validate-only

# View statistics
python scripts/data_collection/dataset_statistics.py

# Specific source only
python scripts/data_collection/comprehensive_dataset_collector.py --sources sklearn

# Validate one category
python scripts/data_collection/dataset_validator.py --category quantum
```

## 📦 Data Sources

| Source | Speed | Auth | Command |
|--------|-------|------|---------|
| sklearn | ⚡ Fast | No | `--sources sklearn` |
| openml | 🐢 Slow | No | `--sources openml` |
| huggingface | 🐌 Very Slow | No | `--sources huggingface` |
| kaggle | 🐢 Slow | Yes | `--sources kaggle` (needs API key) |
| uci | 🚀 Fast | No | `--sources uci` |

## 📊 Reports Location

```
data_out/
├── data_collection/collection_report.json
├── validation/validation_report.json
└── reports/dataset_statistics.json
```

## 🎯 Quality Thresholds

- Minimum samples: 10
- Minimum features: 2
- Max missing: 50%
- Quality score: ≥60

## 🔧 Config File

`config/autonomous_training.yaml`

## 📚 Full Docs

`docs/DATASET_COLLECTION_GUIDE.md`

## ✅ Workflow

1. Collect: `python scripts/dataset_automation.py --quick`
2. Validate: `python scripts/dataset_automation.py --validate-only`
3. Stats: `python scripts/data_collection/dataset_statistics.py`
4. Train: `python scripts/training/autonomous_training_orchestrator.py`
