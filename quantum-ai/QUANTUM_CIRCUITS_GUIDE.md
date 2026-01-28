# Quantum Circuit Tools - Quick Reference

🚀 **Four New Quantum Computing Capabilities**

---

## 📚 **Quick Start**

```bash
cd quantum-ai

# Run all demos
python demo_quantum_circuits.py

# Or test individual components
python -m src.grover_circuit
python -m src.enhanced_variational_circuit
python -m src.circuit_visualizer
```

---

## 1️⃣ **Grover's Search Algorithm**

**File:** [src/grover_circuit.py](src/grover_circuit.py)

### Basic Usage
```python
from src.grover_circuit import GroverCircuit

# Initialize (search space = 2^n_qubits)
grover = GroverCircuit(n_qubits=3, shots=1000)

# Search for item(s)
results = grover.search(marked_states=[5])
print(f"Success: {results['success_probability']:.1%}")

# Visualize amplitude amplification
grover.visualize_amplitudes(marked_states=[5])
```

### Key Features
- **Quantum speedup:** O(√N) vs O(N) classical search
- **Configurable:** Any search space size (2^n_qubits items)
- **Multiple targets:** Search for multiple items at once
- **Visualization:** See amplitude amplification in action

### Example Results
```
3 qubits = 8-item database
Optimal iterations: 2
Success probability: ~100% (perfect amplification)
```

---

## 2️⃣ **Enhanced Variational Circuits**

**File:** [src/enhanced_variational_circuit.py](src/enhanced_variational_circuit.py)

### Basic Usage
```python
from src.enhanced_variational_circuit import EnhancedVariationalCircuit
import torch

circuit = EnhancedVariationalCircuit(
    n_qubits=4,
    n_layers=3,
    encoding="hybrid",       # angle, amplitude, iqp, hybrid
    entanglement="pyramid",  # linear, circular, full, pyramid, alternating
    use_data_reuploading=True
)

# Forward pass
output = circuit(torch.randn(4))
```

### Encoding Strategies

| Encoding | Use Case | Features |
|----------|----------|----------|
| **angle** | Small feature spaces | RY/RZ rotations, simple |
| **amplitude** | Exponential efficiency | Encodes 2^n values in n qubits |
| **iqp** | Classically hard to simulate | Diagonal unitaries, entangling |
| **hybrid** | Complex data | Combines angle + amplitude |

### Entanglement Patterns

| Pattern | Description | Depth |
|---------|-------------|-------|
| **linear** | Nearest-neighbor only | O(n) |
| **circular** | Ring topology | O(n) |
| **full** | All-to-all coupling | O(n²) |
| **pyramid** | Hierarchical (recommended) | O(log n) |
| **alternating** | Even-odd pairs | O(n) |

### Integration with PyTorch
```python
import torch.nn as nn

class HybridModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.quantum = EnhancedVariationalCircuit(n_qubits=4, n_layers=2)
        self.classical = nn.Linear(4, 2)
    
    def forward(self, x):
        x = self.quantum(x)
        return self.classical(x)
```

---

## 3️⃣ **Circuit Visualization**

**File:** [src/circuit_visualizer.py](src/circuit_visualizer.py)

### Basic Usage
```python
from src.circuit_visualizer import CircuitVisualizer

viz = CircuitVisualizer(output_dir="circuit_visualizations")

# PennyLane circuits
viz.visualize_pennylane(qnode, sample_input=[0.5, 1.0, 0.3])

# Qiskit circuits (requires: pip install qiskit)
viz.visualize_qiskit(qiskit_circuit, style="mpl")

# Export to HTML
viz.export_html(circuit, title="My Circuit", filename="circuit.html")
```

### Features
- **Multi-format:** PNG, HTML, LaTeX, text
- **Framework agnostic:** Works with PennyLane and Qiskit
- **Interactive HTML:** Beautiful web exports
- **Comparison:** Side-by-side circuit comparison

### Output Examples
```
circuit_visualizations/
├── demo_pennylane.png
├── demo_qiskit.png
├── circuit_comparison.png
└── circuit.html
```

---

## 4️⃣ **Azure Quantum Testing**

**File:** [src/azure_quantum_tester.py](src/azure_quantum_tester.py)

### Prerequisites
```bash
# Install Azure Quantum SDK
pip install azure-quantum qiskit qiskit-qir

# Configure in config/quantum_config.yaml
azure:
  subscription_id: "your-subscription-id"
  resource_group: "rg-quantum-ai"
  workspace_name: "quantum-ai-workspace"
  location: "eastus"
```

### Basic Usage
```python
from src.azure_quantum_tester import AzureQuantumTester

tester = AzureQuantumTester()

# List available quantum hardware
targets = tester.list_targets()
for t in targets:
    print(f"{t['id']} - {t['status']}")

# Submit a circuit
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

result = tester.submit_circuit(
    circuit=qc,
    target_name='ionq.simulator',
    shots=100,
    wait=True
)

print(f"Results: {result['counts']}")
```

### Run Full Test Suite
```python
# Test multiple circuits automatically
results = tester.run_test_suite(
    target_name='ionq.simulator',
    shots=100
)

# Includes: Bell state, GHZ state, VQC, Deutsch-Jozsa
```

### Available Targets
- **ionq.simulator** - Free IonQ simulator
- **ionq.qpu** - IonQ trapped-ion hardware (paid)
- **quantinuum.sim.h1-1sc** - Quantinuum syntax checker (free)
- **quantinuum.qpu.h1-1** - Quantinuum hardware (paid)
- **rigetti.sim.qvm** - Rigetti simulator

---

## 🔬 **Complete Demo**

```python
#!/usr/bin/env python3
"""Complete quantum circuit demo"""

# 1. Grover's Algorithm
from src.grover_circuit import GroverCircuit
grover = GroverCircuit(n_qubits=3, shots=1000)
results = grover.search(marked_states=[5, 7])
print(f"Grover found items: {results['success_probability']:.1%}")

# 2. Enhanced VQC
from src.enhanced_variational_circuit import EnhancedVariationalCircuit
import torch

circuit = EnhancedVariationalCircuit(
    n_qubits=4,
    encoding="hybrid",
    entanglement="pyramid"
)
output = circuit(torch.randn(4))
print(f"VQC output: {output}")

# 3. Visualization
from src.circuit_visualizer import CircuitVisualizer
import pennylane as qml

viz = CircuitVisualizer()
dev = qml.device('lightning.qubit', wires=2)

@qml.qnode(dev)
def my_circuit(x):
    qml.RY(x[0], wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.PauliZ(0))

viz.visualize_pennylane(my_circuit, sample_input=[1.0])
print("✓ Circuit visualized!")

# 4. Azure Quantum (requires credentials)
try:
    from src.azure_quantum_tester import AzureQuantumTester
    tester = AzureQuantumTester()
    targets = tester.list_targets()
    print(f"Azure targets: {len(targets)}")
except:
    print("⚠️ Azure Quantum requires configuration")
```

---

## 📦 **Dependencies**

### Core (Required)
```bash
pip install pennylane torch numpy matplotlib
```

### Optional (Azure Quantum)
```bash
pip install azure-quantum qiskit qiskit-qir
```

### Optional (Qiskit Visualization)
```bash
pip install qiskit qiskit-aer
```

---

## 🎯 **Use Cases**

| Tool | Best For |
|------|----------|
| **Grover** | Search problems, database queries, optimization |
| **Enhanced VQC** | ML classification, regression, pattern recognition |
| **Visualizer** | Debugging, documentation, education |
| **Azure Tester** | Real quantum hardware testing, benchmarking |

---

## 📊 **Performance Tips**

### Grover's Algorithm
- Use optimal iterations: `int(π/4 * √N)`
- Multiple targets reduce success probability
- Visualize before submitting to hardware

### Variational Circuits
- Start with `pyramid` entanglement (best depth/expressivity)
- Use `hybrid` encoding for complex data
- Enable data reuploading for better expressivity
- Batch process for efficiency

### Azure Quantum
- Test on simulators first (free)
- Use syntax checkers before hardware (quantinuum.sim.h1-1sc)
- Monitor costs in Azure Portal
- Small circuits first (<10 qubits)

---

## 🐛 **Troubleshooting**

### Import Errors
```bash
# If you see "No module named 'qiskit'"
pip install qiskit qiskit-aer

# If you see "No module named 'azure.quantum'"
pip install azure-quantum qiskit-qir
```

### Azure Quantum Connection
- Verify credentials in `config/quantum_config.yaml`
- Check subscription has Azure Quantum workspace
- Ensure workspace is in supported region (eastus, westus)

### Visualization Not Showing
- Check matplotlib backend: `import matplotlib; matplotlib.use('Agg')`
- Use `show=False` to save without displaying
- Check output directory permissions

---

## 📚 **Further Reading**

- **Grover's Algorithm:** [quantum-ai/src/grover_circuit.py](src/grover_circuit.py)
- **Enhanced VQC:** [quantum-ai/src/enhanced_variational_circuit.py](src/enhanced_variational_circuit.py)
- **Visualizer:** [quantum-ai/src/circuit_visualizer.py](src/circuit_visualizer.py)
- **Azure Tester:** [quantum-ai/src/azure_quantum_tester.py](src/azure_quantum_tester.py)
- **Main README:** [quantum-ai/README.md](README.md)

---

**Need help?** Check the docstrings in each module or run with `--help`
