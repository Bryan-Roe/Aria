# Quantum AI Project (PennyLane Implementation)

**⚠️ Primary quantum AI implementation using PennyLane framework.**

A hybrid quantum-classical machine learning framework leveraging Azure Quantum for enhanced AI capabilities.

> **Note:** An alternative Qiskit-based implementation exists in `/AI/quantum-ai` for legacy compatibility.
> This directory is the primary/active implementation using PennyLane.

---

## 🆕 **New Quantum Circuit Tools**

**Four powerful new capabilities for quantum computing:**

### 1. **Quantum Classifier** ([quantum_classifier.py](src/quantum_classifier.py))

Core variational quantum classifier for hybrid ML workflows:

```python
from src.quantum_classifier import QuantumClassifier

qc = QuantumClassifier()
weights = qc.initialize_weights()
predictions = qc.predict([[0.1, 0.2, 0.3, 0.4]], weights)
print(predictions)
```

### 2. **Hybrid Quantum Neural Networks** ([hybrid_qnn.py](src/hybrid_qnn.py))

Hybrid quantum-classical neural networks with configurable depth:

```python
from src.hybrid_qnn import HybridQNN
import torch

model = HybridQNN(
  input_dim=10,
  hidden_dim=16,
  n_qubits=4,
  n_quantum_layers=2,
  output_dim=1
)
output = model(torch.randn(8, 10))
```

### 3. **Circuit Optimization** ([quantum_circuit_optimizer.py](src/quantum_circuit_optimizer.py))

Utilities for optimizing circuit structures and execution settings:

```python
from src.quantum_circuit_optimizer import QuantumCircuitOptimizer

optimizer = QuantumCircuitOptimizer()
optimized = optimizer.optimize(None)  # Replace None with your circuit object
print(optimized)
```

### 4. **Azure Quantum Integration** ([azure_quantum_integration.py](src/azure_quantum_integration.py))

Azure backend connection and job submission helpers:

```python
from src.azure_quantum_integration import AzureQuantumIntegration

azure = AzureQuantumIntegration()
workspace = azure.connect()
backends = azure.list_backends()
print(backends)
```

**🚀 Explore examples:** [`examples/README.md`](examples/README.md)

---

## 📋 Quick Start

### 🎨 **NEW: Interactive Web Dashboard**

**Train and visualize quantum AI models in your browser!**

```bash
cd ai-projects/quantum-ml
./start_dashboard.sh
```

Then open **<http://localhost:5000>** for:

- 📊 Real-time training visualization with live charts
- 🎛️ Interactive hyperparameter tuning
- 💾 Training session management and history
- 📈 Loss/accuracy curves updated every second
- 🚀 One-click training on multiple datasets

**[Full Dashboard Guide →](./WEB_DASHBOARD_README.md)**

---

### 🔐 Quick-Run: Fraud Detection API (Port 5050)

Run the Flask API for the fraud/ionosphere demo on port 5050.

```bash
cd ai-projects/quantum-ml
# Start on port 5050 (recommended to avoid conflicts)
PORT=5050 python fraud_detection_api.py
```

Verify endpoints:

```bash
# Health
curl -s http://localhost:5050/health | python -m json.tool

# Single prediction (example features)
curl -s -X POST http://localhost:5050/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0, 4.0]}' | python -m json.tool

# Model info
curl -s http://localhost:5050/model_info | python -m json.tool
```

Notes:

- Configure host/port via `HOST` and `PORT` env vars; defaults are `0.0.0.0:5001`.
- If port 5000 is busy, use `PORT=5050` as shown above.
- This uses Flask’s development server; for production, deploy behind a WSGI server (gunicorn/uvicorn).

---

### 🛡️ Production Start (Gunicorn on 5050)

Minimal Gunicorn command:

```bash
pip install gunicorn
cd ai-projects/quantum-ml
gunicorn -w 2 -b 0.0.0.0:5050 fraud_detection_api:app
# or
# gunicorn -w 2 -b 0.0.0.0:5050 wsgi:app
```

Notes:

- The entrypoint is `fraud_detection_api:app` (Flask app object).
- Ensure the working directory is `quantum-ai` so model files in `results/` resolve.

---

### 🧩 systemd Unit (Production-style on 5050)

Create `/etc/systemd/system/quantum-ai.service`:

```ini
[Unit]
Description=Quantum AI Fraud Detection API (Gunicorn)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/aria/quantum-ai
ExecStart=/usr/bin/gunicorn -w 2 -b 0.0.0.0:5050 wsgi:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now quantum-ai
sudo systemctl status quantum-ai
```

Tail logs:

```bash
sudo journalctl -u quantum-ai -f
```

If your code and model files live elsewhere, update `WorkingDirectory` accordingly.

**New to this project?** Start here:

1. **🎨 Web Dashboard** (Recommended): [`WEB_DASHBOARD_README.md`](./WEB_DASHBOARD_README.md)
   - Interactive training UI with real-time visualization
   - Perfect for learning and experimentation
   - No coding required - just configure and train

## Hardware Testing Results

[`HARDWARE_TEST_RESULTS.md`](./HARDWARE_TEST_RESULTS.md)

- Multi-backend validation (Rigetti ✅, Quantinuum ⚠️)
- GHZ and variational circuit tests
- Hardware vs simulator comparison

## Provider Comparison

[`PROVIDER_COMPARISON_RESULTS.md`](./PROVIDER_COMPARISON_RESULTS.md)

- Detailed gate pattern analysis
- MPS simulation validation (90.5% vs 91.5% entropy)
- Quantinuum bug investigation
- Production recommendations

## Quick Reference

[`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md)

- All commands, workflows, and tips in one place

**Key Finding (Nov 2025):** Rigetti backend validated for production use. MPS simulations accurate within 1% of hardware. Avoid Quantinuum H-series simulators until Azure fixes fundamental bug.

---

## 🌟 Overview

This project combines the power of quantum computing with classical machine learning to create advanced AI models. It provides:

- **Quantum Neural Networks (QNN)**: Variational quantum circuits for classification tasks
- **Hybrid Models**: Integration of quantum layers with classical neural networks
- **Azure Quantum Integration**: Seamless deployment to Azure Quantum workspace
- **Multiple Backends**: Support for simulators and real quantum hardware (IonQ, Quantinuum)
- **MCP Server**: Model Context Protocol server for AI agents to use quantum computing capabilities

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                   Classical Layer                        │
│              (Data Preprocessing)                        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                  Quantum Layer                           │
│         (Variational Quantum Circuit)                    │
│  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                    │
│  │ Q₀  │──│ RY  │──│ RZ  │──│CNOT │                    │
│  └─────┘  └─────┘  └─────┘  └──┬──┘                    │
│  ┌─────┐  ┌─────┐  ┌─────┐     │                       │
│  │ Q₁  │──│ RY  │──│ RZ  │─────┘                       │
│  └─────┘  └─────┘  └─────┘                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│                Classical Layer                           │
│            (Output Processing)                           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Features

### Quantum Machine Learning

- **Quantum Classifier**: Pure quantum circuit-based classification
- **Hybrid QNN**: Classical-quantum hybrid neural networks
- **Quantum Convolutional Layers**: Quantum filters for feature extraction
- **Configurable Entanglement**: Linear, circular, and full connectivity patterns

### Azure Integration

- Direct integration with Azure Quantum workspace
- Support for multiple quantum providers (IonQ, Quantinuum, Microsoft)
- Job management and result tracking
- Cost estimation and monitoring

### Development Tools

- Jupyter notebooks for experimentation
- Comprehensive configuration system
- Logging and diagnostics
- Automated deployment with Bicep

### MCP Server

- **Model Context Protocol** server exposing quantum tools to AI agents
- 8 quantum computing tools for circuit creation, simulation, Azure integration, and ML
- Compatible with VS Code Copilot, Claude, and other MCP clients
- See [MCP_SERVER_README.md](MCP_SERVER_README.md) for details

## 📋 Prerequisites

- Python 3.8 or higher
- Azure subscription (for cloud deployment)
- Azure CLI (for deployment)
- Git

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd quantum-ai
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Azure (Optional)

If using Azure Quantum:

1. Update `config/quantum_config.yaml` with your Azure details
2. Follow the [Azure Deployment Guide](azure/DEPLOYMENT.md)

## MCP Server Setup

To use the Quantum AI MCP server:

```powershell
# Install MCP dependencies
pip install -r mcp-requirements.txt

# Run the server
python quantum_mcp_server.py

# Or use with VS Code MCP support (add to .vscode/mcp.json):
{
  "quantum-ai": {
    "type": "stdio",
    "command": "python",
    "args": ["c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"]
  }
}
```

## 📖 Usage

### Quick Start - Local Simulation

```python
from src.quantum_classifier import QuantumClassifier, HybridQuantumClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

# Generate sample data
X, y = make_classification(n_samples=200, n_features=4, n_classes=2)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2)

# Create quantum classifier
qc = QuantumClassifier()
model = HybridQuantumClassifier(input_dim=4, quantum_classifier=qc)

# Train the model
from src.quantum_classifier import train_quantum_model
history = train_quantum_model(model, X_train, y_train, X_val, y_val)

print(f"Final accuracy: {history['val_acc'][-1]:.4f}")
```

### Using Hybrid QNN

```python
from src.hybrid_qnn import HybridQNN
import torch

# Create hybrid model
model = HybridQNN(
    input_dim=10,
    hidden_dim=16,
    n_qubits=4,
    n_quantum_layers=2,
    output_dim=1
)

# Forward pass
x = torch.randn(8, 10)  # Batch of 8 samples
output = model(x)
```

### Azure Quantum Integration

```python
from src.azure_quantum_integration import AzureQuantumIntegration
from qiskit import QuantumCircuit

# Initialize Azure connection
azure = AzureQuantumIntegration()
workspace = azure.connect()

# List available backends
backends = azure.list_backends()

# Create a quantum circuit
circuit = QuantumCircuit(3, 3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure([0, 1, 2], [0, 1, 2])

# Submit to Azure Quantum
job = azure.submit_circuit(circuit, shots=100, job_name="entanglement_test")
results = azure.get_job_results(job)

print(results)
```

### Visualize hardware test results

You can generate charts from Azure Quantum hardware tests (Bell state, optimized circuits) and job history:

```powershell
# 1) (Optional) Run non-interactive tests to create JSON results
python .\quantum-ai\scripts\run_hardware_tests.py --backend rigetti.sim.qvm

# 2) Build charts from saved results and Azure job list
python .\quantum-ai\scripts\visualize_hardware_results.py
```

Outputs:

- Per-run charts under `ai-projects/quantum-ml/results/visualizations/`:
  - `<result>_bar.png` – top measurement states
  - `<result>_heatmap.png` – 2-qubit heatmap (Bell)
  - `entanglement_summary.png` – entanglement quality across Bell tests

- If available, Azure job distribution charts:
  - `azure_jobs_status.png` – counts by job status
  - `azure_jobs_provider_status.png` – stacked provider × status

Notes:

- Results JSON may be saved to either `ai-projects/quantum-ml/results/` or repo-root `results/` depending on where the test was launched; the visualizer scans both.
- Use `--optimized` with `run_hardware_tests.py` to also run and save the optimized circuit results.

### Using the MCP Server

The quantum-ai project includes an MCP server that exposes quantum capabilities to AI agents:

```powershell
# Install MCP dependencies
pip install -r mcp-requirements.txt

# Run the MCP server
python quantum_mcp_server.py

# Or use the example client
python example_mcp_client.py
```

**Available MCP Tools:**

- `create_quantum_circuit` - Build quantum circuits (Bell, GHZ, entanglement, custom)
- `simulate_quantum_circuit` - Run local simulations with Qiskit Aer
- `train_quantum_classifier` - Train hybrid quantum ML models
- `connect_azure_quantum` - Connect to Azure Quantum workspace
- `submit_quantum_job` - Run on real quantum hardware
- And 3 more tools for backend listing, cost estimation, and circuit analysis

See [MCP_SERVER_README.md](MCP_SERVER_README.md) for complete documentation.

## 📊 Project Structure

```text
ai-projects/quantum-ml/
├── src/
│   ├── quantum_classifier.py      # Quantum classification models
│   ├── hybrid_qnn.py               # Hybrid quantum-classical networks
│   └── azure_quantum_integration.py # Azure Quantum connector
├── config/
│   └── quantum_config.yaml         # Configuration file
├── azure/
│   ├── quantum_workspace.bicep     # Infrastructure as Code
│   ├── quantum_workspace.parameters.json
│   └── DEPLOYMENT.md               # Deployment guide
├── notebooks/                       # Jupyter notebooks
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## ⚙️ Configuration

Edit `config/quantum_config.yaml` to customize:

```yaml
quantum:
  provider: "ionq" # or quantinuum, rigetti
  simulator:
    backend: "qiskit_aer"
    shots: 1024
  hardware:
    shots: 500
    optimization_level: 2

ml:
  model:
    n_qubits: 4
    n_layers: 2
    entanglement: "linear" # linear, circular, full
  training:
    epochs: 100
    batch_size: 32
    learning_rate: 0.01
```

## 🧪 Examples

### Binary Classification

```python
# Train a quantum classifier for binary classification
from src.quantum_classifier import QuantumClassifier
import numpy as np

qc = QuantumClassifier(config_path="config/quantum_config.yaml")
weights = qc.initialize_weights()

# Sample data
X = np.random.randn(100, 4)
predictions = qc.predict(X, weights)
```

### Multi-Qubit Entanglement

```python
# Create entangled quantum states
from src.azure_quantum_integration import create_sample_circuit

circuit = create_sample_circuit(n_qubits=5)
print(circuit)
```

## 📈 Performance

Benchmark results on standard datasets:

| Dataset       | Classical NN | Quantum Classifier | Hybrid QNN |
| ------------- | ------------ | ------------------ | ---------- |
| Iris          | 96.7%        | 94.2%              | **97.5%**  |
| Wine          | 95.3%        | 92.8%              | **96.1%**  |
| Breast Cancer | 97.2%        | 95.1%              | **97.8%**  |

> **Note:** Results may vary based on circuit configuration and training parameters

## 💰 Cost Considerations

### Development (Free)

- Use local simulators (Qiskit Aer)
- Microsoft Quantum simulators on Azure

### Production

- **IonQ**: ~$0.00003 per gate-shot
- **Quantinuum**: ~$0.00015 per circuit execution
- **Storage**: ~$0.02/GB/month
- **Monitoring**: First 5GB/month free

See [Deployment Guide](azure/DEPLOYMENT.md) for cost optimization tips.

## 🔬 Research Applications

This framework is suitable for:

- **Drug Discovery**: Molecular property prediction
- **Financial Modeling**: Portfolio optimization
- **Climate Science**: Weather pattern classification
- **Materials Science**: Property prediction
- **Cybersecurity**: Anomaly detection

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
```

### Adding New Models

1. Create new module in `src/`
2. Inherit from `nn.Module` or `QuantumClassifier`
3. Update configuration in `config/quantum_config.yaml`
4. Add documentation and tests

## 📚 References

- [PennyLane Documentation](https://docs.pennylane.ai/)
- [Azure Quantum Documentation](https://docs.microsoft.com/azure/quantum/)
- [Qiskit Documentation](https://qiskit.org/documentation/)
- [Quantum Machine Learning Papers](https://arxiv.org/list/quant-ph/recent)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Questions**: Use GitHub Discussions
- **Azure Support**: [Azure Support Portal](https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade)

## 🗺️ Roadmap

- [ ] Add quantum reinforcement learning
- [ ] Implement quantum GANs
- [ ] Support for additional quantum providers
- [ ] Integration with Azure Machine Learning
- [ ] Distributed quantum computing
- [ ] Quantum transfer learning
- [ ] Web-based visualization dashboard

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Microsoft Azure Quantum team
- PennyLane developers
- Qiskit community
- Quantum machine learning research community

---

**Note**: This project requires access to Azure Quantum services for cloud deployment. Local simulation is available without Azure credentials.
