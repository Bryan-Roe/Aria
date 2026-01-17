# Quantum AI Benchmark Report

**Date:** 2025-11-16 22:12:44

## Model Configuration
- **Architecture:** Hybrid Quantum-Classical Neural Network
- **Quantum Circuit:** 4 qubits, 2 variational layers
- **Classical Layers:** 16-node hidden layer with dropout (0.2)
- **Training:** 25 epochs, batch size 16, learning rate 0.001
- **Optimizer:** Adam

## Results Summary

| Dataset | Samples | Features | Best Accuracy | Final Accuracy | Grade |
|---------|---------|----------|---------------|----------------|-------|
| ionosphere | 351 | 34 | 88.73% | 88.73% | 🏆 Excellent |
| banknote | 1372 | 4 | 100.00% | 100.00% | 🏆 Excellent |
| heart_disease | 303 | 13 | 88.52% | 88.52% | 🏆 Excellent |
| sonar | 208 | 60 | 80.95% | 80.95% | ⭐ Very Good |
| breast_cancer | 569 | 29 | 96.49% | 92.98% | 🏆 Excellent |
| diabetes | 768 | 8 | 72.08% | 70.13% | ✅ Good |
| blood_transfusion | 747 | 4 | 80.00% | 78.67% | ⭐ Very Good |
| wine_red | 1599 | 11 | 99.38% | 99.38% | 🏆 Excellent |
| wine_white | 4898 | 11 | 99.59% | 99.59% | 🏆 Excellent |
| magic_gamma | 19020 | 10 | 78.18% | 77.68% | ⭐ Very Good |
| iris | 150 | 4 | 100.00% | 100.00% | 🏆 Excellent |
| wheat_seeds | 210 | 7 | 95.24% | 95.24% | 🏆 Excellent |
| glass | 214 | 10 | 93.02% | 86.05% | 🏆 Excellent |
| parkinsons | 195 | 22 | 79.49% | 74.36% | ⭐ Very Good |
| dermatology | 366 | 34 | 100.00% | 100.00% | 🏆 Excellent |
| thyroid | 215 | 5 | 97.67% | 97.67% | 🏆 Excellent |
| wine_quality_combined | 6497 | 12 | 98.69% | 97.77% | 🏆 Excellent |
| optical_recognition | 3823 | 64 | 99.74% | 99.61% | 🏆 Excellent |
| pendigits | 7494 | 16 | 99.40% | 99.27% | 🏆 Excellent |
| statlog_australian | 690 | 14 | 86.23% | 84.78% | 🏆 Excellent |
| balance_scale | 625 | 4 | 92.00% | 92.00% | 🏆 Excellent |
| contraceptive | 1473 | 9 | 66.78% | 63.05% | ✅ Good |

## Detailed Results


### Ionosphere

**Description:** Radar returns classification

**Task:** Binary classification: Good vs Bad radar signals

**Metrics:**
- Best Validation Accuracy: **88.73%**
- Final Training Loss: 0.3984
- Training Samples: 280
- Validation Samples: 71

### Banknote

**Description:** Banknote authentication

**Task:** Binary classification: Genuine vs Forged banknotes

**Metrics:**
- Best Validation Accuracy: **100.00%**
- Final Training Loss: 0.0627
- Training Samples: 1097
- Validation Samples: 275

### Heart_Disease

**Description:** Heart disease diagnosis

**Task:** Binary classification: Disease present vs absent

**Metrics:**
- Best Validation Accuracy: **88.52%**
- Final Training Loss: 0.4065
- Training Samples: 242
- Validation Samples: 61

### Sonar

**Description:** Sonar returns classification

**Task:** Binary classification: Mine vs Rock detection

**Metrics:**
- Best Validation Accuracy: **80.95%**
- Final Training Loss: 0.4821
- Training Samples: 166
- Validation Samples: 42

### Breast_Cancer

**Description:** Wisconsin Breast Cancer Diagnostic

**Task:** Binary classification: Malignant vs Benign

**Metrics:**
- Best Validation Accuracy: **96.49%**
- Final Training Loss: 0.2399
- Training Samples: 455
- Validation Samples: 114

### Diabetes

**Description:** Pima Indians Diabetes

**Task:** Binary classification: Diabetes onset prediction

**Metrics:**
- Best Validation Accuracy: **72.08%**
- Final Training Loss: 0.5310
- Training Samples: 614
- Validation Samples: 154

### Blood_Transfusion

**Description:** Blood Transfusion Service Center

**Task:** Binary: Blood donation prediction

**Metrics:**
- Best Validation Accuracy: **80.00%**
- Final Training Loss: 0.5014
- Training Samples: 597
- Validation Samples: 150

### Wine_Red

**Description:** Red Wine Quality

**Task:** Multi-class: Wine quality rating (3-8)

**Metrics:**
- Best Validation Accuracy: **99.38%**
- Final Training Loss: 0.0317
- Training Samples: 1279
- Validation Samples: 320

### Wine_White

**Description:** White Wine Quality

**Task:** Multi-class: Wine quality rating (3-9)

**Metrics:**
- Best Validation Accuracy: **99.59%**
- Final Training Loss: 0.0278
- Training Samples: 3918
- Validation Samples: 980

### Magic_Gamma

**Description:** MAGIC Gamma Telescope

**Task:** Binary: Gamma signal vs Hadron background

**Metrics:**
- Best Validation Accuracy: **78.18%**
- Final Training Loss: 0.4949
- Training Samples: 15216
- Validation Samples: 3804

### Iris

**Description:** Iris Flower Species

**Task:** Multi-class: Iris species (setosa, versicolor, virginica)

**Metrics:**
- Best Validation Accuracy: **100.00%**
- Final Training Loss: 0.1281
- Training Samples: 120
- Validation Samples: 30

### Wheat_Seeds

**Description:** Wheat Seeds Classification

**Task:** Multi-class: Wheat variety classification

**Metrics:**
- Best Validation Accuracy: **95.24%**
- Final Training Loss: 0.3510
- Training Samples: 168
- Validation Samples: 42

### Glass

**Description:** Glass Identification

**Task:** Multi-class: Glass type classification

**Metrics:**
- Best Validation Accuracy: **93.02%**
- Final Training Loss: 0.3770
- Training Samples: 171
- Validation Samples: 43

### Parkinsons

**Description:** Parkinsons Disease Detection

**Task:** Binary: Parkinsons presence prediction

**Metrics:**
- Best Validation Accuracy: **79.49%**
- Final Training Loss: 0.4395
- Training Samples: 156
- Validation Samples: 39

### Dermatology

**Description:** Dermatology Disease Classification

**Task:** Multi-class: 6 dermatology conditions

**Metrics:**
- Best Validation Accuracy: **100.00%**
- Final Training Loss: 0.1004
- Training Samples: 292
- Validation Samples: 74

### Thyroid

**Description:** Thyroid Disease Classification

**Task:** Multi-class: 3 thyroid conditions

**Metrics:**
- Best Validation Accuracy: **97.67%**
- Final Training Loss: 0.3275
- Training Samples: 172
- Validation Samples: 43

### Wine_Quality_Combined

**Description:** Combined Wine Quality Dataset

**Task:** Multi-class: Wine quality with type feature

**Metrics:**
- Best Validation Accuracy: **98.69%**
- Final Training Loss: 0.1115
- Training Samples: 5197
- Validation Samples: 1300

### Optical_Recognition

**Description:** Optical Recognition of Handwritten Digits

**Task:** Multi-class: 10 digit classification

**Metrics:**
- Best Validation Accuracy: **99.74%**
- Final Training Loss: 0.0552
- Training Samples: 3058
- Validation Samples: 765

### Pendigits

**Description:** Pen-Based Recognition of Handwritten Digits

**Task:** Multi-class: 10 digit classification

**Metrics:**
- Best Validation Accuracy: **99.40%**
- Final Training Loss: 0.0816
- Training Samples: 5995
- Validation Samples: 1499

### Statlog_Australian

**Description:** Australian Credit Approval

**Task:** Binary: Credit approval prediction

**Metrics:**
- Best Validation Accuracy: **86.23%**
- Final Training Loss: 0.4023
- Training Samples: 552
- Validation Samples: 138

### Balance_Scale

**Description:** Balance Scale Weight & Distance

**Task:** Multi-class: 3 balance classes

**Metrics:**
- Best Validation Accuracy: **92.00%**
- Final Training Loss: 0.2378
- Training Samples: 500
- Validation Samples: 125

### Contraceptive

**Description:** Contraceptive Method Choice

**Task:** Multi-class: 3 contraceptive methods

**Metrics:**
- Best Validation Accuracy: **66.78%**
- Final Training Loss: 0.6467
- Training Samples: 1178
- Validation Samples: 295

## Conclusions

- **Best Performance:** banknote (100.00%)
- **Average Accuracy:** 90.55%
- **Total Datasets Tested:** 22

✅ **Overall Assessment:** The quantum AI model demonstrates strong performance across all datasets!