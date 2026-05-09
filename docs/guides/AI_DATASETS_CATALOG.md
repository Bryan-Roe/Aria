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
**29 Datasets (27 Working) - Free, High-Quality Datasets for Quantum Experiments**

#### Medical Domain (8 datasets)
Healthcare applications for quantum machine learning

**Heart Disease**
- **Size**: 303 samples, 14 features, 2 classes
- **Task**: Binary classification (disease presence/absence)
- **Use**: Quantum medical diagnosis, feature entanglement analysis
- **Training**: `python train_custom_dataset.py --dataset heart_disease --qubits 5 --layers 2`

**Parkinson's Disease Detection**
- **Size**: 195 samples, 22 features, 2 classes
- **Task**: Binary classification from voice measurements
- **Use**: Quantum voice biomarker analysis, high-dimensional feature processing
- **Training**: `python train_custom_dataset.py --dataset parkinsons --qubits 6 --layers 3`

**Dermatology**
- **Size**: 366 samples, 34 features, 6 classes
- **Task**: Multi-class skin disease classification
- **Use**: Quantum multi-class medical diagnosis
- **Training**: `python train_custom_dataset.py --dataset dermatology --qubits 6 --layers 3`

**Liver Disorders**
- **Size**: 345 samples, 6 features, 2 classes
- **Task**: Binary classification from blood tests
- **Use**: Quantum medical screening, low-dimensional quantum circuits
- **Training**: `python train_custom_dataset.py --dataset liver_disorders --qubits 4 --layers 2`

**Thyroid Conditions**
- **Size**: 215 samples, 5 features, 3 classes
- **Task**: Multi-class endocrine disorder classification
- **Use**: Quantum medical diagnostics with limited features
- **Training**: `python train_custom_dataset.py --dataset thyroid --qubits 4 --layers 2`

**Statlog Heart Disease**
- **Size**: 270 samples, 13 features, 2 classes
- **Task**: Binary cardiac disease classification
- **Use**: Quantum cardiology models, alternative heart disease dataset
- **Training**: `python train_custom_dataset.py --dataset statlog_heart --qubits 5 --layers 2`

**Breast Cancer**
- **Size**: 569 samples, 30 features, 2 classes (built-in)
- **Task**: Binary malignant/benign classification
- **Use**: Quantum cancer diagnosis benchmark
- **Training**: `python src/quantum_classifier.py --dataset breast_cancer`

**Diabetes**
- **Size**: 768 samples, 8 features, 2 classes
- **Task**: Binary diabetes prediction
- **Use**: Quantum metabolic disease screening
- **Training**: `python train_custom_dataset.py --dataset diabetes --qubits 5 --layers 2`

#### Biology Domain (4 datasets)
Biological sequence and protein classification

**E. coli Protein Localization**
- **Size**: 336 samples, 7 features, 8 classes
- **Task**: Multi-class protein cellular location prediction
- **Use**: Quantum bioinformatics, protein targeting analysis
- **Training**: `python train_custom_dataset.py --dataset ecoli --qubits 5 --layers 3`

**Yeast Protein Localization**
- **Size**: 1,484 samples, 8 features, 10 classes
- **Task**: 10-class protein location classification (challenging)
- **Use**: Large-scale quantum multi-class classification
- **Training**: `python train_custom_dataset.py --dataset yeast --qubits 5 --layers 4`

**Ionosphere**
- **Size**: 351 samples, 34 features, 2 classes
- **Task**: Binary classification of radar returns
- **Use**: Quantum signal processing, feature entanglement
- **Training**: `python train_custom_dataset.py --dataset ionosphere --qubits 6 --layers 2`

**Sonar**
- **Size**: 208 samples, 60 features, 2 classes
- **Task**: Binary classification (mines vs rocks from sonar signals)
- **Use**: Quantum signal processing, high-dimensional feature space
- **Training**: `python train_custom_dataset.py --dataset sonar --qubits 6 --layers 2`

#### Image Features Domain (4 datasets)
Computer vision feature-based classification

**Optical Recognition of Handwritten Digits**
- **Size**: 3,823 samples, 64 features, 10 classes
- **Task**: 10-class digit recognition (0-9)
- **Use**: Large-scale quantum image classification, PCA testing (64→6 qubits)
- **Note**: Requires aggressive dimensionality reduction
- **Training**: `python train_custom_dataset.py --dataset optical_recognition --qubits 6 --layers 4`

**Pen-Based Handwritten Digits**
- **Size**: 7,494 samples, 16 features, 10 classes (largest dataset)
- **Task**: 10-class digit recognition from pen trajectories
- **Use**: Large-scale quantum ML scalability testing
- **Training**: `python train_custom_dataset.py --dataset pendigits --qubits 6 --layers 4 --batch 32`

**Iris**
- **Size**: 150 samples, 4 features, 3 classes (built-in)
- **Task**: Multi-class flower species classification
- **Use**: Quantum ML benchmark, classic test case
- **Training**: `python src/quantum_classifier.py --dataset iris`

**Digits**
- **Size**: 1,797 samples, 64 features, 10 classes (built-in)
- **Task**: 10-class digit image classification
- **Use**: Quantum image classification benchmark
- **Training**: `python src/quantum_classifier.py --dataset digits`

#### Chemistry/Materials Domain (3 datasets)

**Wine Quality (Combined Red+White)**
- **Size**: 6,497 samples, 12 features, 7 classes
- **Task**: Multi-class wine quality rating (3-9 scale)
- **Use**: Largest quantum chemistry dataset, quality regression
- **Note**: Combined 1,599 red + 4,898 white wines with wine_type feature
- **Training**: `python train_custom_dataset.py --dataset wine_quality_combined --qubits 5 --layers 3`

**Wine (Red)**
- **Size**: 1,599 samples, 11 features, 6 classes
- **Task**: Red wine quality classification
- **Use**: Quantum chemistry, quality prediction
- **Training**: `python train_custom_dataset.py --dataset wine_red --qubits 5 --layers 2`

**Wine (White)**
- **Size**: 4,898 samples, 11 features, 7 classes
- **Task**: White wine quality classification
- **Use**: Large-scale quantum chemistry
- **Training**: `python train_custom_dataset.py --dataset wine_white --qubits 5 --layers 3`

#### Agriculture Domain (2 datasets)

**Wheat Seeds**
- **Size**: 210 samples, 7 features, 3 classes
- **Task**: Multi-class wheat variety classification
- **Use**: Quantum agriculture, seed quality analysis
- **Training**: `python train_custom_dataset.py --dataset wheat_seeds --qubits 5 --layers 2`

**Seeds (Alternative)**
- **Size**: 210 samples, 7 features, 3 classes
- **Task**: Wheat kernel variety classification
- **Use**: Alternative agriculture dataset for cross-validation
- **Training**: `python train_custom_dataset.py --dataset seeds --qubits 5 --layers 2`

#### Finance Domain (1 dataset)

**Statlog Australian Credit Approval**
- **Size**: 690 samples, 14 features, 2 classes
- **Task**: Binary credit decision classification
- **Use**: Quantum finance, risk assessment models
- **Training**: `python train_custom_dataset.py --dataset statlog_australian --qubits 5 --layers 2`

#### Social Science Domain (1 dataset)

**Contraceptive Method Choice**
- **Size**: 1,473 samples, 9 features, 3 classes
- **Task**: Multi-class contraceptive preference prediction
- **Use**: Quantum social science, demographic analysis
- **Training**: `python train_custom_dataset.py --dataset contraceptive --qubits 5 --layers 2`

#### Physics Domain (1 dataset)

**Balance Scale**
- **Size**: 625 samples, 4 features, 3 classes
- **Task**: Multi-class balance tip direction prediction
- **Use**: Quantum physics modeling, equilibrium classification
- **Training**: `python train_custom_dataset.py --dataset balance_scale --qubits 4 --layers 2`

#### Forensics Domain (1 dataset)

**Banknote Authentication**
- **Size**: 1,372 samples, 4 features, 2 classes
- **Task**: Binary genuine/counterfeit classification
- **Use**: Quantum security, forensic analysis
- **Training**: `python train_custom_dataset.py --dataset banknote --qubits 4 --layers 2`

#### Other Domains

**Glass Identification**
- **Size**: 214 samples, 9 features, 6 classes
- **Task**: Multi-class glass type classification
- **Use**: Quantum forensics, materials analysis
- **Training**: `python train_custom_dataset.py --dataset glass --qubits 5 --layers 2`

**Blood Transfusion Service**
- **Size**: 748 samples, 4 features, 2 classes
- **Task**: Binary donation prediction
- **Use**: Quantum healthcare logistics
- **Training**: `python train_custom_dataset.py --dataset blood_transfusion --qubits 4 --layers 2`

**Haberman Survival**
- **Size**: 306 samples, 3 features, 2 classes
- **Task**: Binary cancer survival prediction
- **Use**: Quantum medical prognosis
- **Training**: `python train_custom_dataset.py --dataset haberman --qubits 4 --layers 2`

**Magic Gamma Telescope**
- **Size**: 19,020 samples, 10 features, 2 classes
- **Task**: Binary particle classification (gamma vs hadron)
- **Use**: Large-scale quantum physics simulation
- **Training**: `python train_custom_dataset.py --dataset magic_gamma --qubits 5 --layers 2`

**Vertebral Column (CORRUPTED - DO NOT USE)**
- **Status**: File corruption, unable to load
- **Note**: Excluded from all benchmarks

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

#### Internal Repository Corpus (Synthetic)
- **Source**: Local workspace files (code + markdown docs)
- **Location**: `datasets/chat/app_repo`
- **Format**: `train.json` / `test.json` newline-delimited JSON (each line has `messages` array)
- **Size**: Small (synthetic; generated on demand)
- **License**: Internal use only (do not distribute externally)
- **Use**: Fine-tune Phi-3.6 adapters to improve model awareness of project-specific patterns, configuration philosophy, and extension guidelines.
- **Generation Script**: `scripts/generate_repo_training_dataset.py`
- **Prompt Types**: Summary, functions/classes listing, safe extension guidance.

**Generate (PowerShell):**
```powershell
python .\scripts\generate_repo_training_dataset.py --max-records 300
```

**Dry-run validate:**
```powershell
python AI\microsoft_phi-silica-3.6_v1\scripts\train_lora.py --dataset .\datasets\chat\app_repo --dry-run
```

**Smoke-test training (CPU friendly):**
```powershell
python AI\microsoft_phi-silica-3.6_v1\scripts\train_lora.py --dataset .\datasets\chat\app_repo --max-train-samples 64 --max-eval-samples 16
```

> Tip: Re-run generation script after significant repository changes to refresh synthetic summaries. Keep max-records modest (≤500) to avoid overfitting and retain generalization from broader public datasets.

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
- **Logs**: Your own conversation history in `ai-projects/chat-cli/logs/*.jsonl`
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
- Quantum dataset preparation: `ai-projects/quantum-ml/notebooks/`
- JSONL conversion: `AI/microsoft_phi-silica-3.6_v1/scripts/prepare_dataset.py`
- Chat template formatting: Phi-3 documentation
