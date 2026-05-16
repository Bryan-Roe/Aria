# Quantum AI Project (Qiskit Implementation)

**⚠️ NOTE: This is an alternative Qiskit-based implementation.**

The primary quantum AI implementation is in `/quantum-ai` and uses **PennyLane**.
This directory (`/AI/quantum-ai`) contains an older **Qiskit-based** implementation
that uses different quantum computing frameworks.

## Key Differences

| Feature | This Directory (AI/quantum-ai) | Main Directory (quantum-ai) |
| --------- | ------------------------------- | --------------------------- |
| Framework | **Qiskit** | **PennyLane** |
| Backend | Qiskit Aer, IBM Quantum | PennyLane, Azure Quantum |
| Status | Legacy/Alternative | Primary/Active |

For new development, use the **PennyLane-based** implementation in `/quantum-ai`.

---

# Original Documentation

A comprehensive quantum machine learning framework combining **quantum computing** with **classical AI**, powered by **Azure Quantum** and **Qiskit**.

## 🌟 Features

- **Quantum Machine Learning**: Variational Quantum Classifiers (VQC) and Quantum Neural Networks (QNN)
- **Hybrid Models**: Quantum-classical neural networks combining the best of both worlds
- **Azure Quantum Integration**: Seamless integration with Azure Quantum services
- **Multiple Backends**: Support for simulators and real quantum hardware (IonQ, Quantinuum, Rigetti)
- **Production Ready**: Scalable architecture with logging, monitoring, and batch processing

## 🏗️ Architecture

```text
Classical Input → Classical Preprocessing → Quantum Layer → Classical Postprocessing → Output
```

### Components

1. **Quantum Classifier** (`quantum_classifier.py`)
   - Variational Quantum Classifier (VQC)
   - Quantum Neural Network (QNN)
   - Built-in data preprocessing and scaling

2. **Hybrid QNN** (`hybrid_qnn.py`)
   - PyTorch-based hybrid architecture
   - Quantum layers integrated into classical networks
   - Full gradient-based training

3. **Azure Quantum Integration** (`azure_quantum_integration.py`)
   - Workspace connection management
   - Job submission and monitoring
   - Backend selection and cost estimation

## 📋 Prerequisites

- Python 3.8 or higher
- Azure subscription (for Azure Quantum)
- Basic understanding of quantum computing and machine learning

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd quantum-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Azure Quantum (Optional but recommended)

Create an Azure Quantum workspace:

```bash
# Using Azure CLI
az quantum workspace create \
    --resource-group <your-resource-group> \
    --name <workspace-name> \
    --location eastus \
    --storage-account <storage-account-name>
```

Set environment variables:

```bash
# Windows PowerShell
$env:AZURE_QUANTUM_RESOURCE_ID = "/subscriptions/.../resourceGroups/.../providers/Microsoft.Quantum/Workspaces/..."
$env:AZURE_QUANTUM_LOCATION = "eastus"

# Linux/Mac
export AZURE_QUANTUM_RESOURCE_ID="/subscriptions/.../resourceGroups/.../providers/Microsoft.Quantum/Workspaces/..."
export AZURE_QUANTUM_LOCATION="eastus"
```

## 💻 Quick Start

### Example 1: Quantum Classifier

```python
from src.quantum_classifier import QuantumClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Generate data
X, y = make_classification(n_samples=100, n_features=4, n_classes=2, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Create and train quantum classifier
qc = QuantumClassifier(num_features=4, num_qubits=4, reps=2)
qc.fit(X_train, y_train)

# Evaluate
accuracy = qc.score(X_test, y_test)
print(f"Accuracy: {accuracy:.4f}")
```

### Example 2: Hybrid Quantum-Classical Neural Network

```python
from src.hybrid_qnn import HybridQNN, QuantumClassicalTrainer
import torch
from torch.utils.data import DataLoader, TensorDataset

# Create hybrid model
model = HybridQNN(
    input_dim=8,
    hidden_dim=16,
    num_qubits=4,
    quantum_layers=2,
    output_dim=3
)

# Prepare data loaders
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16)

# Train
trainer = QuantumClassicalTrainer(model, learning_rate=0.01)
trainer.train(train_loader, val_loader, num_epochs=10)
```

### Example 3: Azure Quantum Integration

```python
from src.azure_quantum_integration import AzureQuantumManager
from qiskit import QuantumCircuit

# Create quantum circuit
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

# Connect to Azure Quantum
azure_qm = AzureQuantumManager()
azure_qm.connect()

# List available backends
backends = azure_qm.list_backends()
print(f"Available backends: {backends}")

# Run on quantum hardware/simulator
result = azure_qm.run_circuit(qc, shots=1000, backend_name='ionq.simulator')
print(f"Results: {result['counts']}")
```

## 📊 Jupyter Notebooks

Explore interactive examples in the `notebooks/` directory:

- `01_quantum_basics.ipynb` - Introduction to quantum circuits
- `02_quantum_ml.ipynb` - Quantum machine learning fundamentals
- `03_hybrid_models.ipynb` - Building hybrid quantum-classical models
- `04_azure_quantum.ipynb` - Using Azure Quantum services

## 🛠️ Project Structure

```text
quantum-ai/
├── src/
│   ├── quantum_classifier.py      # Quantum ML classifiers
│   ├── hybrid_qnn.py              # Hybrid quantum-classical models
│   └── azure_quantum_integration.py # Azure Quantum connection
├── notebooks/
│   ├── 01_quantum_basics.ipynb
│   ├── 02_quantum_ml.ipynb
│   ├── 03_hybrid_models.ipynb
│   └── 04_azure_quantum.ipynb
├── config/
│   └── quantum_config.yaml        # Configuration file
├── azure/
│   └── quantum_workspace.bicep    # Azure infrastructure
├── requirements.txt
└── README.md
```

## ⚙️ Configuration

Edit `config/quantum_config.yaml` to customize:

```yaml
quantum:
  num_qubits: 4
  circuit_depth: 3
  optimizer: COBYLA
  shots: 1024

azure:
  location: eastus
  default_backend: ionq.simulator

training:
  learning_rate: 0.001
  batch_size: 16
  epochs: 10
```

## 🔬 Supported Quantum Backends

### Simulators (Free)

- **Qiskit Aer** - Local quantum simulator
- **IonQ Simulator** - Cloud-based ion trap simulator
- **Quantinuum Simulator** - Trapped-ion quantum simulator

### Real Quantum Hardware (Requires Azure Quantum credits)

- **IonQ Quantum Computer** - Ion trap quantum computer
- **Quantinuum H1** - Trapped-ion quantum processor
- **Rigetti** - Superconducting quantum processors

## 📈 Performance Tips

1. **Start with simulators** before moving to real hardware
2. **Use fewer qubits** for faster training (4-6 qubits is optimal)
3. **Batch processing** for multiple circuits
4. **Cost estimation** before running on real hardware
5. **Hybrid models** often outperform pure quantum models

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_quantum_classifier.py

# With coverage
pytest --cov=src tests/
```

## 📚 Resources

- [Qiskit Documentation](https://qiskit.org/documentation/)
- [Azure Quantum Documentation](https://learn.microsoft.com/azure/quantum/)
- [Quantum Machine Learning Papers](https://arxiv.org/list/quant-ph/recent)
- [PennyLane QML](https://pennylane.ai/qml/)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Troubleshooting

### Import errors

```bash
pip install --upgrade qiskit qiskit-machine-learning qiskit-algorithms
```

### Azure authentication issues

```bash
az login
az account set --subscription <subscription-id>
```

### Quantum backend not found

Check available backends:

```python
azure_qm.list_backends()
```

## 🌐 Future Enhancements

- [ ] Quantum Generative Adversarial Networks (QGAN)
- [ ] Quantum Reinforcement Learning
- [ ] Quantum Natural Language Processing
- [ ] Integration with TensorFlow Quantum
- [ ] Automated hyperparameter tuning
- [ ] Distributed quantum computing

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with** ⚛️ **Quantum Computing** | 🧠 **Machine Learning** | ☁️ **Azure Quantum**
