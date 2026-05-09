# Quantum AI Examples

This directory contains comprehensive examples demonstrating all capabilities of the Quantum AI project.

## 📁 Example Files

### 1. `create_circuits.py` - Creating Quantum Circuits

Demonstrates various quantum circuit creation patterns:

- **Bell State**: Maximally entangled 2-qubit state
- **GHZ State**: 3-qubit entanglement
- **Quantum Fourier Transform**: QFT for 3 qubits
- **Variational Quantum Circuit**: For machine learning
- **PennyLane Circuits**: Parameterized quantum circuits
- **Quantum Classifier Circuit**: From our QML model

**Run:**

```powershell
python .\examples\create_circuits.py
```

**Output:**

- Visual circuit diagrams in ASCII art
- Circuit configurations and parameters
- Demonstration of different entanglement patterns

---

### 2. `run_simulations.py` - Running Simulations Locally

Demonstrates local quantum simulation capabilities:

- **Bell State Simulation**: Tests quantum entanglement
- **Superposition Simulation**: Hadamard gate effects
- **PennyLane with Gradients**: Enables quantum ML
- **State Evolution**: Visualize quantum state changes
- **Scaling Analysis**: Performance across qubit counts
- **Noisy Simulation**: Realistic hardware imperfections

**Run:**

```powershell
python .\examples\run_simulations.py
```

**Output:**

- Measurement statistics (1000 shots)
- Gradient computation for QML
- State evolution plot (saved to `results/`)
- Noise modeling demonstration

**Generated Files:**

- `results/state_evolution.png` - Quantum state evolution visualization

---

### 3. `train_models.py` - Training Quantum ML Models

Demonstrates quantum machine learning on real datasets:

- **Moons Dataset**: Non-linear binary classification
- **Circles Dataset**: Challenging concentric patterns
- **Iris Dataset**: Multi-class problem (binary reduction)
- **Performance Comparison**: Across all datasets

**Run:**

```powershell
python .\examples\train_models.py
```

**Training Details:**

- 100 epochs per model
- Batch size: 32
- Learning rate: 0.01
- Hybrid quantum-classical architecture

**Output:**

- Training progress with loss/accuracy metrics
- Final validation accuracies
- Comparative analysis

**Generated Files:**

- `results/training_moons.png` - Loss and accuracy curves
- `results/model_comparison.png` - Performance comparison chart

**Results:**

- Moons: ~85% accuracy
- Circles: ~50% accuracy (challenging for current architecture)
- Iris: ~67% accuracy

---

### 4. `azure_integration.py` - Azure Quantum Integration

Complete guide for integrating with Azure Quantum:

- **Configuration Check**: Validates Azure setup
- **Circuit Preparation**: Creates Azure-ready circuits
- **Provider Overview**: IonQ, Quantinuum, Rigetti, Microsoft
- **Cost Estimation**: Pricing guide
- **Deployment Steps**: Full setup instructions
- **Security Best Practices**: Azure security guidelines

**Run:**

```powershell
python .\examples\azure_integration.py
```

**Prerequisites:**

- Azure subscription (optional for local simulation)
- Azure CLI installed
- Quantum workspace deployed

**Output:**

- Configuration status
- Available providers and features
- Cost estimates
- Step-by-step deployment guide
- Example code for Azure Quantum

---

## 🚀 Quick Start

### Run All Examples

```powershell
# Ensure you're in the quantum-ai directory with venv activated
cd c:\Users\Bryan\OneDrive\AI\quantum-ai
.\venv\Scripts\Activate.ps1

# Run examples in sequence
python .\examples\create_circuits.py
python .\examples\run_simulations.py
python .\examples\train_models.py
python .\examples\azure_integration.py
```

### View Results

```powershell
# All plots are saved to results/
explorer .\results\
```

---

## 📊 Expected Results

### Circuit Creation

- 6 different circuit types demonstrated
- Visual ASCII diagrams for each
- Parameter counts and configurations

### Simulations

- Bell state: ~50/50 split between |00⟩ and |11⟩
- Superposition: ~50/50 split between |0⟩ and |1⟩
- Noisy simulation: Small error rates (~1-2%)

### ML Training

- Convergence within 100 epochs
- Moons dataset: Best performance (~85%)
- Iris dataset: Moderate performance (~67%)
- Circles dataset: Challenging (~50% - needs architecture tuning)

### Azure Integration

- Configuration validation
- Provider comparison
- Cost breakdown
- Deployment roadmap

---

## 🎯 Learning Path

### Beginner

1. Start with `create_circuits.py` to understand quantum gates
2. Move to `run_simulations.py` to see quantum behavior
3. Try `train_models.py` to see quantum ML in action

### Intermediate

1. Modify circuit architectures in `create_circuits.py`
2. Experiment with different noise models in `run_simulations.py`
3. Try different hyperparameters in `train_models.py`

### Advanced

1. Follow `azure_integration.py` to deploy to real quantum hardware
2. Implement custom quantum algorithms
3. Optimize circuit depth for specific quantum processors

---

## 🔧 Customization

### Modify Circuit Parameters

Edit `config/quantum_config.yaml`:

```yaml
ml:
  model:
    n_qubits: 4      # Change to 6 or 8
    n_layers: 2      # Increase for more expressiveness
    entanglement: "linear"  # Try "circular" or "full"
```

### Change Training Settings

```yaml
ml:
  training:
    epochs: 100      # Increase for better convergence
    batch_size: 32   # Adjust based on dataset size
    learning_rate: 0.01  # Tune for optimization
```

### Test Different Datasets

In `train_models.py`, replace data generation:

```python
from sklearn.datasets import make_blobs, make_classification
X, y = make_blobs(n_samples=200, centers=2, random_state=42)
```

---

## 🐛 Troubleshooting

### "Device not found" Error

- Ensure PennyLane is installed: `pip install pennylane`
- Use `default.qubit` for universal compatibility

### Azure Connection Issues

1. Verify Azure CLI: `az --version`
2. Check login: `az account show`
3. Confirm workspace exists: `az quantum workspace list`

### Poor ML Performance

- Increase epochs (e.g., 200)
- Try different learning rates (0.001 - 0.1)
- Increase circuit layers (2 → 3 or 4)
- Change entanglement pattern

### Memory Issues

- Reduce qubit count (especially >10 qubits)
- Decrease batch size
- Use GPU if available: `device='cuda'`

---

## 📚 Additional Resources

### Documentation

- [PennyLane Docs](https://docs.pennylane.ai/)
- [Qiskit Tutorials](https://qiskit.org/learn/)
- [Azure Quantum Docs](https://learn.microsoft.com/azure/quantum/)

### Papers

- [Variational Quantum Eigensolver](https://arxiv.org/abs/1304.3061)
- [Quantum Machine Learning](https://arxiv.org/abs/1611.09347)
- [QAOA](https://arxiv.org/abs/1411.4028)

### Community

- [Qiskit Slack](https://qiskit.slack.com/)
- [PennyLane Forum](https://discuss.pennylane.ai/)
- [Azure Quantum Community](https://quantum.microsoft.com/)

---

## 🎓 Key Concepts Demonstrated

### Quantum Computing Fundamentals

- ✓ Superposition
- ✓ Entanglement
- ✓ Quantum gates (H, CNOT, RY, RZ)
- ✓ Measurement and collapse

### Quantum Machine Learning

- ✓ Variational quantum circuits
- ✓ Hybrid quantum-classical models
- ✓ Quantum gradients
- ✓ Parameter optimization

### Practical Quantum Computing

- ✓ Local simulation
- ✓ Noise modeling
- ✓ Cloud integration (Azure)
- ✓ Cost management

---

## 💡 Next Steps

1. **Experiment**: Modify parameters and observe changes
2. **Extend**: Add new datasets or circuit designs
3. **Deploy**: Set up Azure Quantum for real hardware access
4. **Optimize**: Tune models for better performance
5. **Research**: Implement quantum algorithms from papers

---

## 📝 Notes

- All examples are self-contained
- No Azure credentials needed for local simulation
- Results may vary slightly due to randomness
- Some datasets are harder than others (by design)
- Real quantum hardware will show different statistics

---

Happy Quantum Computing! 🌌
