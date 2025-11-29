# Quantum AI Benchmark Report

**Date:** 2025-11-16 21:21:52

## Model Configuration
- **Architecture:** Hybrid Quantum-Classical Neural Network
- **Quantum Circuit:** 4 qubits, 2 variational layers
- **Classical Layers:** 16-node hidden layer with dropout (0.2)
- **Training:** 25 epochs, batch size 16, learning rate 0.001
- **Optimizer:** Adam

## Results Summary

| Dataset | Samples | Features | Best Accuracy | Final Accuracy | Grade |
|---------|---------|----------|---------------|----------------|-------|
| ionosphere | 351 | 34 | 90.14% | 90.14% | 🏆 Excellent |
| banknote | 1372 | 4 | 100.00% | 100.00% | 🏆 Excellent |
| heart_disease | 303 | 13 | 85.25% | 80.33% | 🏆 Excellent |
| sonar | 208 | 60 | 83.33% | 80.95% | ⭐ Very Good |
| breast_cancer | 569 | 29 | 96.49% | 95.61% | 🏆 Excellent |
| diabetes | 768 | 8 | 73.38% | 70.13% | ✅ Good |
| blood_transfusion | 747 | 4 | 83.33% | 82.00% | ⭐ Very Good |
| wine_red | 1599 | 11 | 99.38% | 99.38% | 🏆 Excellent |
| wine_white | 4898 | 11 | 99.59% | 99.59% | 🏆 Excellent |
| magic_gamma | 19020 | 10 | 78.15% | 77.84% | ⭐ Very Good |
| iris | 150 | 4 | 100.00% | 100.00% | 🏆 Excellent |
| wheat_seeds | 210 | 7 | 97.62% | 97.62% | 🏆 Excellent |
| glass | 214 | 10 | 93.02% | 86.05% | 🏆 Excellent |

## Detailed Results


### Ionosphere

**Description:** Radar returns classification

**Task:** Binary classification: Good vs Bad radar signals

**Metrics:**
- Best Validation Accuracy: **90.14%**
- Final Training Loss: 0.3908
- Training Samples: 280
- Validation Samples: 71

### Banknote

**Description:** Banknote authentication

**Task:** Binary classification: Genuine vs Forged banknotes

**Metrics:**
- Best Validation Accuracy: **100.00%**
- Final Training Loss: 0.0785
- Training Samples: 1097
- Validation Samples: 275

### Heart_Disease

**Description:** Heart disease diagnosis

**Task:** Binary classification: Disease present vs absent

**Metrics:**
- Best Validation Accuracy: **85.25%**
- Final Training Loss: 0.4144
- Training Samples: 242
- Validation Samples: 61

### Sonar

**Description:** Sonar returns classification

**Task:** Binary classification: Mine vs Rock detection

**Metrics:**
- Best Validation Accuracy: **83.33%**
- Final Training Loss: 0.4968
- Training Samples: 166
- Validation Samples: 42

### Breast_Cancer

**Description:** Wisconsin Breast Cancer Diagnostic

**Task:** Binary classification: Malignant vs Benign

**Metrics:**
- Best Validation Accuracy: **96.49%**
- Final Training Loss: 0.1681
- Training Samples: 455
- Validation Samples: 114

### Diabetes

**Description:** Pima Indians Diabetes

**Task:** Binary classification: Diabetes onset prediction

**Metrics:**
- Best Validation Accuracy: **73.38%**
- Final Training Loss: 0.5143
- Training Samples: 614
- Validation Samples: 154

### Blood_Transfusion

**Description:** Blood Transfusion Service Center

**Task:** Binary: Blood donation prediction

**Metrics:**
- Best Validation Accuracy: **83.33%**
- Final Training Loss: 0.4811
- Training Samples: 597
- Validation Samples: 150

### Wine_Red

**Description:** Red Wine Quality

**Task:** Multi-class: Wine quality rating (3-8)

**Metrics:**
- Best Validation Accuracy: **99.38%**
- Final Training Loss: 0.0332
- Training Samples: 1279
- Validation Samples: 320

### Wine_White

**Description:** White Wine Quality

**Task:** Multi-class: Wine quality rating (3-9)

**Metrics:**
- Best Validation Accuracy: **99.59%**
- Final Training Loss: 0.0226
- Training Samples: 3918
- Validation Samples: 980

### Magic_Gamma

**Description:** MAGIC Gamma Telescope

**Task:** Binary: Gamma signal vs Hadron background

**Metrics:**
- Best Validation Accuracy: **78.15%**
- Final Training Loss: 0.4975
- Training Samples: 15216
- Validation Samples: 3804

### Iris

**Description:** Iris Flower Species

**Task:** Multi-class: Iris species (setosa, versicolor, virginica)

**Metrics:**
- Best Validation Accuracy: **100.00%**
- Final Training Loss: 0.1334
- Training Samples: 120
- Validation Samples: 30

### Wheat_Seeds

**Description:** Wheat Seeds Classification

**Task:** Multi-class: Wheat variety classification

**Metrics:**
- Best Validation Accuracy: **97.62%**
- Final Training Loss: 0.3036
- Training Samples: 168
- Validation Samples: 42

### Glass

**Description:** Glass Identification

**Task:** Multi-class: Glass type classification

**Metrics:**
- Best Validation Accuracy: **93.02%**
- Final Training Loss: 0.2632
- Training Samples: 171
- Validation Samples: 43

## Conclusions

- **Best Performance:** banknote (100.00%)
- **Average Accuracy:** 90.74%
- **Total Datasets Tested:** 13

✅ **Overall Assessment:** The quantum AI model demonstrates strong performance across all datasets!