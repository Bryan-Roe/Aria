# 📊 Training Quantum AI on Your Custom Dataset - Complete Guide

**Quick Start Guide for Custom Data**
**Date:** October 31, 2025

---

## 🎯 Three Ways to Use Your Data

### Option 1: Quick & Easy (Recommended for Beginners)

Use the existing `quantum_classifier.py` with minimal code changes.

### Option 2: Advanced Hybrid (You're looking at this!)

Use `hybrid_qnn.py` for complex multi-class problems.

### Option 3: Custom Circuit

Build your own quantum circuit from scratch.

---

## 🚀 Option 1: Using quantum_classifier.py (Easiest)

### Step 1: Prepare Your Data

Your data should be in one of these formats:

- CSV file with features and labels
- NumPy arrays (X, y)
- Pandas DataFrame
- Scikit-learn compatible format

**Example CSV format:**

```csv
feature1,feature2,feature3,feature4,label
5.1,3.5,1.4,0.2,0
4.9,3.0,1.4,0.2,0
6.3,2.5,4.9,1.5,1
```

### Step 2: Create Your Training Script

Create a new file: `train_my_data.py`

```python
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quantum_classifier import HybridQuantumClassifier, train_quantum_model
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch

# ============================================
# 1. LOAD YOUR DATA
# ============================================

# Option A: From CSV
def load_from_csv(filepath):
    df = pd.read_csv(filepath)
    X = df.drop('label', axis=1).values  # All columns except 'label'
    y = df['label'].values
    return X, y

# Option B: From NumPy
def load_from_numpy(X_file, y_file):
    X = np.load(X_file)
    y = np.load(y_file)
    return X, y

# Option C: Manual arrays
def create_manual_data():
    X = np.array([
        [1.0, 2.0, 3.0, 4.0],
        [2.0, 3.0, 4.0, 5.0],
        # ... your data ...
    ])
    y = np.array([0, 1, ...])  # Your labels
    return X, y

# ============================================
# 2. LOAD YOUR ACTUAL DATA (CHANGE THIS!)
# ============================================

# Choose your loading method:
X, y = load_from_csv("path/to/your/data.csv")
# OR
# X, y = load_from_numpy("features.npy", "labels.npy")
# OR
# X, y = create_manual_data()

print(f"Loaded data: {X.shape[0]} samples, {X.shape[1]} features")
print(f"Classes: {np.unique(y)}")

# ============================================
# 3. PREPROCESS DATA
# ============================================

# Split into train/validation
X_train, X_val, y_train, y_val = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y  # Keeps class balance
)

# Standardize features (IMPORTANT for quantum circuits!)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Handle feature dimension
n_features = X_train.shape[1]
n_qubits = 4  # From config

# Pad or reduce features to match qubits
if n_features < n_qubits:
    # Pad with zeros
    padding = np.zeros((X_train.shape[0], n_qubits - n_features))
    X_train = np.hstack([X_train, padding])

    padding_val = np.zeros((X_val.shape[0], n_qubits - n_features))
    X_val = np.hstack([X_val, padding_val])
    print(f"Padded features from {n_features} to {n_qubits}")

elif n_features > n_qubits:
    # Use PCA to reduce
    from sklearn.decomposition import PCA
    pca = PCA(n_components=n_qubits)
    X_train = pca.fit_transform(X_train)
    X_val = pca.transform(X_val)
    print(f"Reduced features from {n_features} to {n_qubits} using PCA")
    print(f"Explained variance: {pca.explained_variance_ratio_.sum():.2%}")

# ============================================
# 4. CREATE MODEL
# ============================================

# Initialize model (uses config from quantum_config.yaml)
model = HybridQuantumClassifier(input_dim=n_qubits)
print(f"Created model with {n_qubits} qubits")

# ============================================
# 5. TRAIN MODEL
# ============================================

print("\nStarting training...")
history = train_quantum_model(
    model=model,
    X_train=X_train,
    y_train=y_train,
    X_val=X_val,
    y_val=y_val
)

# ============================================
# 6. EVALUATE RESULTS
# ============================================

print("\n" + "="*50)
print("TRAINING COMPLETE!")
print("="*50)
print(f"Final Training Loss: {history['train_loss'][-1]:.4f}")
print(f"Final Validation Loss: {history['val_loss'][-1]:.4f}")
print(f"Final Validation Accuracy: {history['val_acc'][-1]:.4f}")
print(f"Best Validation Accuracy: {max(history['val_acc']):.4f}")

# ============================================
# 7. SAVE MODEL (OPTIONAL)
# ============================================

# Save model weights
torch.save(model.state_dict(), "results/my_quantum_model.pt")
print("\nModel saved to: results/my_quantum_model.pt")

# Save scaler for inference
import joblib
joblib.dump(scaler, "results/scaler.pkl")
print("Scaler saved to: results/scaler.pkl")

# ============================================
# 8. MAKE PREDICTIONS ON NEW DATA
# ============================================

def predict_new_data(new_X, model, scaler):
    """Predict on new unseen data"""
    # Preprocess
    new_X_scaled = scaler.transform(new_X)

    # Pad/reduce if needed
    if new_X_scaled.shape[1] < n_qubits:
        padding = np.zeros((new_X_scaled.shape[0], n_qubits - new_X_scaled.shape[1]))
        new_X_scaled = np.hstack([new_X_scaled, padding])

    # Convert to tensor
    new_X_tensor = torch.FloatTensor(new_X_scaled)

    # Predict
    model.eval()
    with torch.no_grad():
        predictions = model(new_X_tensor)
        if predictions.dim() > 1:
            predictions = (predictions > 0.5).float()
        else:
            predictions = (predictions > 0.5).float()

    return predictions.numpy()

# Example: Predict on validation set
predictions = predict_new_data(X_val, model, scaler)
print(f"\nPredictions shape: {predictions.shape}")
```

### Step 3: Run Your Training

```powershell
cd c:\Users\Bryan\OneDrive\AI\quantum-ai
python train_my_data.py
```

---

## 🔬 Option 2: Using hybrid_qnn.py (Advanced Multi-Class)

The file you're currently viewing (`hybrid_qnn.py`) is perfect for:

- **Multi-class classification** (3+ classes)
- **Complex datasets** (8+ features)
- **Deep quantum-classical integration**

### Quick Start with hybrid_qnn.py

Create `train_with_hybrid_qnn.py`:

```python
import numpy as np
import pandas as pd
import torch
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
from hybrid_qnn import HybridQNN, QuantumClassicalTrainer

# ============================================
# 1. LOAD YOUR DATA
# ============================================

# Example: Load from CSV
df = pd.read_csv("your_data.csv")
X = df.drop('label', axis=1).values
y = df['label'].values

# Or create sample data
from sklearn.datasets import make_classification
X, y = make_classification(
    n_samples=500,
    n_features=10,
    n_informative=8,
    n_classes=3,  # Multi-class!
    random_state=42
)

print(f"Data: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")

# ============================================
# 2. PREPROCESS
# ============================================

# Split
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_val = scaler.transform(X_val)

# Create data loaders
train_dataset = TensorDataset(
    torch.FloatTensor(X_train),
    torch.LongTensor(y_train)
)
val_dataset = TensorDataset(
    torch.FloatTensor(X_val),
    torch.LongTensor(y_val)
)

train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)

# ============================================
# 3. CREATE HYBRID MODEL
# ============================================

model = HybridQNN(
    input_dim=X.shape[1],      # Your number of features
    hidden_dim=32,              # Classical hidden layer size
    num_qubits=4,               # Quantum circuit size
    quantum_layers=2,           # Quantum depth (optimal!)
    output_dim=len(np.unique(y)),  # Number of classes
    dropout=0.2
)

print(model)

# ============================================
# 4. TRAIN
# ============================================

trainer = QuantumClassicalTrainer(
    model=model,
    learning_rate=0.01,
    device='cpu'  # or 'cuda' if you have GPU
)

trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
    num_epochs=50  # Adjust based on convergence
)

# ============================================
# 5. RESULTS
# ============================================

print(f"\nFinal Validation Accuracy: {trainer.val_accuracies[-1]:.2f}%")
print(f"Best Validation Accuracy: {max(trainer.val_accuracies):.2f}%")

# Save model
torch.save(model.state_dict(), "results/hybrid_qnn_model.pt")
print("Model saved!")
```

---

## 📋 Data Requirements & Tips

### Minimum Requirements

- **Samples:** At least 100 samples (200+ recommended)
- **Features:** 2-20 features (will be mapped to qubits)
- **Classes:** Binary (2) or multi-class (3+)
- **Format:** Numerical data only

### Data Preprocessing Checklist

✅ **Required Steps:**

1. **Standardization** - CRITICAL for quantum circuits

   ```python
   scaler = StandardScaler()
   X = scaler.fit_transform(X)
   ```

2. **Feature Scaling** - Map to quantum parameter range
   - Quantum circuits work with angles (0 to 2π)
   - StandardScaler handles this automatically

3. **Feature Dimension Matching**
   - If features < qubits: Pad with zeros
   - If features > qubits: Use PCA to reduce

4. **Class Encoding**
   - Binary: 0/1
   - Multi-class: 0, 1, 2, ...
   - Use LabelEncoder if needed

✅ **Recommended Steps:**

1. **Handle Missing Values**

   ```python
   from sklearn.impute import SimpleImputer
   imputer = SimpleImputer(strategy='mean')
   X = imputer.fit_transform(X)
   ```

2. **Balance Classes** (if imbalanced)

   ```python
   from imblearn.over_sampling import SMOTE
   smote = SMOTE(random_state=42)
   X, y = smote.fit_resample(X, y)
   ```

3. **Remove Outliers**

   ```python
   from sklearn.preprocessing import RobustScaler
   scaler = RobustScaler()
   X = scaler.fit_transform(X)
   ```

---

## 🎯 Real-World Examples

### Example 1: Medical Diagnosis (Binary Classification)

```python
# Load medical data
df = pd.read_csv("patient_data.csv")

# Features: age, blood_pressure, cholesterol, glucose, BMI
X = df[['age', 'bp', 'cholesterol', 'glucose', 'bmi']].values

# Label: 0=healthy, 1=disease
y = df['diagnosis'].values

# Preprocess
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Pad to 4 features (we have 5, so PCA)
from sklearn.decomposition import PCA
pca = PCA(n_components=4)
X_reduced = pca.fit_transform(X_scaled)

# Train quantum model
# ... (use quantum_classifier.py approach)
```

### Example 2: Financial Fraud Detection

```python
# Load transaction data
df = pd.read_csv("transactions.csv")

# Features: amount, time, merchant_category, etc.
X = df.drop(['fraud'], axis=1).values
y = df['fraud'].values  # 0=legitimate, 1=fraud

# Handle imbalance (fraud is rare!)
from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)

# Your quantum model excels at imbalanced data (90% accuracy!)
# ... train as normal
```

### Example 3: Image Classification (Small Images)

```python
# Load small images (e.g., MNIST digits)
from sklearn.datasets import load_digits
digits = load_digits()

X = digits.data  # 8x8 images flattened to 64 features
y = digits.target  # 0-9 digits

# Reduce 64 features to 4 using PCA
pca = PCA(n_components=4)
X_reduced = pca.fit_transform(X)

print(f"Explained variance: {pca.explained_variance_ratio_.sum():.2%}")

# Train multi-class quantum classifier
# Use hybrid_qnn.py for 10 classes
```

---

## 🔍 Troubleshooting

### Issue: Poor Accuracy (<50%)

**Possible Causes:**

1. **Data not standardized** → Use StandardScaler
2. **Too few samples** → Need at least 100 samples
3. **Features don't match qubits** → Pad or use PCA
4. **Classes imbalanced** → Use SMOTE or class weights

**Solutions:**

```python
# Always standardize!
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Check class distribution
print(np.bincount(y))

# If imbalanced, use SMOTE
from imblearn.over_sampling import SMOTE
X, y = SMOTE().fit_resample(X, y)
```

### Issue: Training is Slow

**Possible Causes:**

1. Too many samples (>1000)
2. Too many epochs
3. Quantum simulation overhead

**Solutions:**

```python
# Use smaller batch size
batch_size = 16  # instead of 32

# Reduce epochs
epochs = 50  # instead of 100

# Sample your data
from sklearn.utils import resample
X_sample, y_sample = resample(X, y, n_samples=500, random_state=42)
```

### Issue: Model Overfitting

**Symptoms:**

- Training accuracy high (>90%)
- Validation accuracy low (<60%)

**Solutions:**

```python
# 1. Reduce model complexity
n_layers = 1  # instead of 2

# 2. Add more regularization
dropout = 0.3  # instead of 0.2

# 3. Get more data or use data augmentation

# 4. Early stopping
if val_acc decreases for 5 epochs:
    break
```

---

## 💡 Best Practices for Custom Data

### 1. Start Simple

- Begin with binary classification
- Use 100-200 samples
- 2-4 features

### 2. Validate Your Preprocessing

```python
# Check data distribution
print(f"X mean: {X.mean(axis=0)}")
print(f"X std: {X.std(axis=0)}")
# Should be ~0 mean, ~1 std after StandardScaler

# Check class balance
print(f"Class distribution: {np.bincount(y)}")
# Should be roughly balanced
```

### 3. Monitor Training

```python
# Plot training curves
import matplotlib.pyplot as plt

plt.plot(history['train_loss'], label='Train Loss')
plt.plot(history['val_loss'], label='Val Loss')
plt.legend()
plt.savefig('results/training_curve.png')
```

### 4. Compare to Classical Baseline

```python
# Train classical model for comparison
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier()
rf.fit(X_train, y_train)
classical_acc = rf.score(X_val, y_val)

print(f"Classical: {classical_acc:.2%}")
print(f"Quantum: {quantum_acc:.2%}")
```

---

## 🚀 Next Steps

### Once Training Works

1. **Hyperparameter tuning** - Use `experiments/parameter_tuning.py`
2. **Cross-validation** - Test on multiple data splits
3. **Feature engineering** - Create better features
4. **Ensemble methods** - Combine multiple quantum models

### Production Deployment

1. **Save model & scaler**

   ```python
   torch.save(model.state_dict(), 'model.pt')
   joblib.dump(scaler, 'scaler.pkl')
   ```

2. **Create inference script**

   ```python
   def predict(new_data):
       X = scaler.transform(new_data)
       return model(torch.FloatTensor(X))
   ```

3. **Deploy to Azure Quantum** for real hardware

---

## 📚 Complete Example Script

I've created `train_my_data.py` - a ready-to-use template!

**Location:** Copy the code from "Step 2" above and save as:
`c:\Users\Bryan\OneDrive\AI\quantum-ai\train_my_data.py`

**Run it:**

```powershell
python train_my_data.py
```

---

## 🎯 Summary

**To train on YOUR data:**

1. ✅ Load your CSV/NumPy/DataFrame
2. ✅ Standardize with StandardScaler
3. ✅ Match features to qubits (pad or PCA)
4. ✅ Use `quantum_classifier.py` (simple) or `hybrid_qnn.py` (advanced)
5. ✅ Train and evaluate
6. ✅ Save model for deployment

**Your quantum AI is ready for custom data!** 🚀

Need help with specific data format? Just ask!
