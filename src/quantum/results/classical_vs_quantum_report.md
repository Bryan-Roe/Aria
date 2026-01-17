# Classical vs Quantum ML - Benchmark Report

**Generated:** 2025-11-01 18:34:12

## Executive Summary

This report compares quantum hybrid neural networks against classical ML baselines 
across four quantum-classical datasets: banknote authentication, ionosphere radar, 
sonar detection, and heart disease diagnosis.

**🏆 Best Overall Model:** SVM (RBF) (92.04% average accuracy)

**⚛️ Quantum Model:** Ranked #4 with 89.13% average accuracy


## Detailed Results by Dataset


### Banknote

| Rank | Model | Test Accuracy | vs Quantum |
|------|-------|---------------|------------|
| 1 | 🥇 SVM (RBF) | 100.00% | +0.00% |
| 2 |  Random Forest | 100.00% | +0.00% |
| 3 |  Neural Network | 100.00% | +0.00% |
| 4 | ⚛️ Quantum Hybrid QNN | 100.00% | BASELINE |
| 5 |  SVM (Linear) | 97.45% | -2.55% |


### Ionosphere

| Rank | Model | Test Accuracy | vs Quantum |
|------|-------|---------------|------------|
| 1 | 🥇 SVM (RBF) | 97.18% | +11.47% |
| 2 |  Neural Network | 92.96% | +7.25% |
| 3 |  SVM (Linear) | 91.55% | +5.84% |
| 4 |  Random Forest | 90.14% | +4.43% |
| 5 | ⚛️ Quantum Hybrid QNN | 85.71% | BASELINE |


### Sonar

| Rank | Model | Test Accuracy | vs Quantum |
|------|-------|---------------|------------|
| 1 | 🥇 SVM (RBF) | 85.71% | +9.52% |
| 2 |  SVM (Linear) | 85.71% | +9.52% |
| 3 |  Random Forest | 83.33% | +7.14% |
| 4 |  Neural Network | 83.33% | +7.14% |
| 5 | ⚛️ Quantum Hybrid QNN | 76.19% | BASELINE |


### Heart Disease

| Rank | Model | Test Accuracy | vs Quantum |
|------|-------|---------------|------------|
| 1 | ⚛️ Quantum Hybrid QNN | 94.64% | BASELINE |
| 2 |  Neural Network | 86.89% | -7.75% |
| 3 |  SVM (RBF) | 85.25% | -9.39% |
| 4 |  SVM (Linear) | 85.25% | -9.39% |
| 5 |  Random Forest | 73.77% | -20.87% |


## Average Performance Across All Datasets

| Rank | Model | Average Accuracy |
|------|-------|------------------|
| 1 | 🥇 SVM (RBF) | 92.04% |
| 2 | 🥈 Neural Network | 90.79% |
| 3 | 🥉 SVM (Linear) | 89.99% |
| 4 |  ⚛️ Quantum Hybrid QNN | 89.13% |
| 5 |  Random Forest | 86.81% |

## Key Insights

- **Quantum Model Won:** 2/4 datasets

- **Best Quantum Performance:** Banknote (100.00%)

- **Best Classical Model:** SVM (RBF) (92.04% average)

- **Classical Advantage:** 2.90% over quantum


## Recommendations

- ✅ **Quantum models show promise** on these datasets

- 🚀 **Next step:** Deploy to Azure Quantum hardware for validation

- 📊 **Hyperparameter tuning** could improve both classical and quantum models

- 🔄 **Cross-validation** would provide more robust estimates
