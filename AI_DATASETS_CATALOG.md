# AI Training Datasets Catalog
**Last Updated:** October 31, 2025

A comprehensive guide to datasets for all AI projects in this workspace:
- **Quantum AI**: Quantum machine learning and hybrid classifiers
- **Chat/LLM**: Fine-tuning conversational models (Phi-3.6, GPT, etc.)
- **General ML**: Traditional machine learning tasks

---

## Quick Start

### 1. Download Datasets
```powershell
# Run the dataset downloader
python .\scripts\download_datasets.py --category all
```

### 2. Storage Structure
```
AI/
├── datasets/                    # Centralized data storage
│   ├── raw/                     # Original downloaded data
│   ├── processed/               # Cleaned and preprocessed
│   ├── quantum/                 # Quantum ML datasets
│   ├── chat/                    # Conversational AI data
│   └── vision/                  # Image/video data
├── dataset_index.json          # Metadata and inventory
└── scripts/
    ├── download_datasets.py    # Automated downloader
    └── validate_datasets.py    # Data quality checks
```

---

## 🔬 Quantum AI Datasets

### Built-in Scikit-Learn Datasets
**Already Available** - No download needed

| Dataset | Samples | Features | Classes | Use Case |
|---------|---------|----------|---------|----------|
| Iris | 150 | 4 | 3 | Binary/multi-class classification |
| Wine | 178 | 13 | 3 | Quality classification |
| Breast Cancer | 569 | 30 | 2 | Medical diagnosis |
| Digits | 1,797 | 64 | 10 | Image classification |

**Training Command:**
```powershell
cd quantum-ai
python .\src\quantum_classifier.py --dataset iris
```

### UCI Machine Learning Repository
**Free, High-Quality Datasets for Quantum Experiments**

#### Heart Disease
- **URL**: https://archive.ics.uci.edu/ml/datasets/Heart+Disease
- **Size**: 303 samples, 14 features
- **Task**: Binary classification (disease presence)
- **Format**: CSV
- **Use**: Quantum medical diagnosis models

#### Ionosphere
- **URL**: https://archive.ics.uci.edu/ml/datasets/Ionosphere
- **Size**: 351 samples, 34 features
- **Task**: Binary classification
- **Format**: CSV
- **Use**: Quantum feature extraction

#### Sonar
- **URL**: https://archive.ics.uci.edu/ml/datasets/Connectionist+Bench+(Sonar,+Mines+vs.+Rocks)
- **Size**: 208 samples, 60 features
- **Task**: Binary classification (mines vs rocks)
- **Format**: CSV
- **Use**: Quantum signal processing

### Quantum-Specific Datasets

#### Quantum Many-Body Systems
- **Source**: TensorFlow Quantum datasets
- **URL**: https://www.tensorflow.org/quantum/tutorials/mnist
- **Format**: NumPy arrays
- **Use**: Quantum state preparation, VQE training

#### QMNIST (Quantum MNIST)
- **Source**: Modified MNIST for quantum circuits
- **Size**: 60,000 train, 10,000 test
- **Format**: 4x4 downsampled images (16 features → 4 qubits)
- **Use**: Quantum image classification

---

## 💬 Chat/LLM Fine-Tuning Datasets

### High-Quality Conversational Datasets

#### 1. ShareGPT Conversations
- **Source**: Hugging Face `shareGPT_vicuna_unfiltered`
- **Size**: 90,000+ multi-turn conversations
- **Format**: JSONL
- **Quality**: ⭐⭐⭐⭐⭐
- **Use**: General chatbot fine-tuning
- **Download**:
```python
from datasets import load_dataset
ds = load_dataset("anon8231489123/ShareGPT_Vicuna_unfiltered")
```

#### 2. OpenAssistant Conversations
- **Source**: Hugging Face `OpenAssistant/oasst1`
- **Size**: 161,000 messages across 35,000 conversations
- **Format**: Parquet/JSONL
- **Quality**: ⭐⭐⭐⭐⭐
- **Languages**: 35 languages
- **Use**: Instruction-following, multi-turn dialogue
- **Download**:
```python
from datasets import load_dataset
ds = load_dataset("OpenAssistant/oasst1")
```

#### 3. Alpaca Dataset
- **Source**: Stanford Alpaca
- **Size**: 52,000 instruction-response pairs
- **Format**: JSON
- **Quality**: ⭐⭐⭐⭐
- **Use**: Instruction tuning
- **URL**: https://github.com/tatsu-lab/stanford_alpaca

#### 4. Dolly 15k
- **Source**: Databricks
- **Size**: 15,000 instruction-response pairs
- **Format**: JSONL
- **Quality**: ⭐⭐⭐⭐⭐ (Human-generated)
- **License**: CC BY-SA 3.0 (Commercial use allowed)
- **Download**:
```python
from datasets import load_dataset
ds = load_dataset("databricks/databricks-dolly-15k")
```

#### 5. WizardLM Evol-Instruct
- **Source**: Microsoft Research
- **Size**: 70,000+ complex instructions
- **Format**: JSONL
- **Quality**: ⭐⭐⭐⭐⭐
- **Use**: Advanced reasoning, complex tasks
- **Download**:
```python
from datasets import load_dataset
ds = load_dataset("WizardLM/WizardLM_evol_instruct_70k")
```

### Domain-Specific Datasets

#### Medical/Healthcare
- **PubMedQA**: Medical question-answering (1,000 expert-annotated)
- **MedDialog**: Doctor-patient conversations (3.6M+ utterances)
- **MIMIC-III Notes**: Clinical notes (requires credentialing)

#### Legal
- **LegalBench**: Legal reasoning tasks
- **CaseHOLD**: Legal citation prediction
- **MultiLegalPile**: 689GB legal documents

#### Code/Programming
- **CodeAlpaca**: 20,000 code instruction pairs
- **Code Contests**: Programming competition problems
- **The Stack**: 3TB of permissively licensed code

#### Customer Support
- **MultiWOZ**: Multi-domain dialogue (10,000 conversations)
- **Ubuntu IRC**: Technical support logs
- **Coached Conversations**: Customer service training data

---

## 🎯 Dataset Selection Guide

### For Quantum AI (4-10 qubits):
- **Start with**: Iris, Wine, Breast Cancer (built-in)
- **Next**: UCI datasets (Heart Disease, Sonar)
- **Advanced**: Quantum Many-Body, QMNIST
- **Features**: Keep ≤ 10 features (or use PCA)
- **Samples**: 100-10,000 (quantum simulators are slow)

### For Phi-3.6 Fine-Tuning:
- **Small tests**: Dolly 15k (fits in memory, high quality)
- **Production**: ShareGPT or OpenAssistant (large, diverse)
- **Specialized**: Domain-specific datasets for targeted use cases
- **Format**: JSONL with `messages` field (Phi-3 chat template)
- **Streaming**: Use `datasets` library for >10GB files

### For Talk-to-AI Chat:
- **Logs**: Your own conversation history in `talk-to-ai/logs/*.jsonl`
- **Fine-tune on**: Personal assistant style from your interactions
- **Combine with**: OpenAssistant for general knowledge

---

## 📦 Automated Download Scripts

### Script 1: Quantum Datasets
**File**: `scripts/download_quantum_datasets.py`
```python
# Downloads UCI and quantum-specific datasets
# Saves to: datasets/quantum/
# Formats: CSV, NumPy, Parquet
```

### Script 2: Chat Datasets
**File**: `scripts/download_chat_datasets.py`
```python
# Downloads ShareGPT, OpenAssistant, Dolly, Alpaca
# Converts to Phi-3 JSONL format
# Saves to: datasets/chat/
```

### Script 3: Dataset Validator
**File**: `scripts/validate_datasets.py`
```python
# Checks file integrity
# Validates JSONL format
# Counts samples and features
# Reports quality metrics
```

---

## 🔐 License Considerations

### ✅ Safe for Commercial Use:
- Dolly 15k (CC BY-SA 3.0)
- OpenAssistant (Apache 2.0)
- UCI datasets (Attribution required)
- Scikit-learn datasets (BSD)

### ⚠️ Research/Non-Commercial Only:
- ShareGPT (No commercial license)
- Alpaca (Based on OpenAI data - terms unclear)

### 🔒 Requires Credentialing:
- MIMIC-III (Healthcare data - CITI training required)
- Clinical trial data (IRB approval)

---

## 💾 Storage Requirements

### Current Workspace Storage:
- **Quantum datasets**: ~50 MB (UCI + built-in)
- **Chat datasets (small)**: ~500 MB (Dolly 15k)
- **Chat datasets (large)**: ~5-10 GB (ShareGPT, OpenAssistant)
- **Code datasets**: ~50+ GB (The Stack)

### Recommended Setup:
```powershell
# Check available space
Get-PSDrive C | Select-Object Used,Free

# Allocate for datasets
# Minimum: 10 GB for chat fine-tuning
# Recommended: 50 GB for diverse datasets
# Optimal: 500 GB for large-scale training
```

---

## 🚀 Next Steps

1. **Run Dataset Downloader** (created below)
   ```powershell
   python .\scripts\download_datasets.py --category quantum
   python .\scripts\download_datasets.py --category chat --dataset dolly
   ```

2. **Validate Downloads**
   ```powershell
   python .\scripts\validate_datasets.py
   ```

3. **Train Models**
   ```powershell
   # Quantum AI
   cd quantum-ai
   python .\train_custom_dataset.py
   
   # Phi-3.6 Fine-tuning
   cd AI\microsoft_phi-silica-3.6_v1
   python .\scripts\train_lora.py --dataset ..\..\datasets\chat\dolly15k
   ```

4. **Monitor Storage**
   ```powershell
   # Track dataset sizes
   Get-ChildItem .\datasets -Recurse | Measure-Object -Property Length -Sum
   ```

---

## 📚 Additional Resources

### Data Sources:
- **Hugging Face Hub**: https://huggingface.co/datasets
- **Papers with Code**: https://paperswithcode.com/datasets
- **UCI ML Repository**: https://archive.ics.uci.edu/ml/
- **Kaggle Datasets**: https://www.kaggle.com/datasets
- **Google Dataset Search**: https://datasetsearch.research.google.com/

### Tools:
- **Hugging Face `datasets`**: Streaming, caching, auto-download
- **Pandas**: CSV/Excel processing
- **PyArrow**: Fast Parquet reading
- **DVC**: Dataset version control

### Tutorials:
- Quantum dataset preparation: `quantum-ai/notebooks/`
- JSONL conversion: `AI/microsoft_phi-silica-3.6_v1/scripts/prepare_dataset.py`
- Chat template formatting: Phi-3 documentation
