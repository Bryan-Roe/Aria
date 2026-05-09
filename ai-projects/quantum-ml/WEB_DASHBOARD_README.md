# 🚀 Quantum AI Training Web Dashboard

Interactive web application for training and visualizing quantum machine learning models with real-time metrics.

![Dashboard Preview](https://via.placeholder.com/800x400/667eea/ffffff?text=Quantum+AI+Training+Dashboard)

## ✨ Features

- **🎨 Beautiful UI**: Modern, responsive design with gradient themes
- **📊 Real-time Visualization**: Live training/validation loss and accuracy charts
- **⚡ Interactive Training**: Start/stop training sessions with custom hyperparameters
- **📈 Live Metrics**: Real-time epoch progress, loss values, and accuracy tracking
- **💾 Session Management**: Save and review historical training results
- **🎛️ Hyperparameter Tuning**: Adjust qubits, layers, learning rate, batch size, and duration
- **📚 Dataset Selection**: Train on heart disease, ionosphere, sonar, or banknote datasets
- **🔄 Background Training**: Non-blocking training with threaded execution

## 🚀 Quick Start

### Option 1: Using the Launch Script (Recommended)

```bash
cd quantum-ai
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### Option 2: Manual Setup

```bash
cd quantum-ai

# Install dependencies
pip install -r web-requirements.txt

# Start the dashboard
python web_app.py
```

Then open your browser to: **<http://localhost:5000>**

## 📖 How to Use

### 1. Configure Training

- **Dataset**: Select from available quantum datasets (heart, ionosphere, sonar, banknote)
- **Qubits**: Number of quantum qubits (2-8, determines feature dimensionality)
- **Layers**: Variational circuit depth (1-5)
- **Learning Rate**: Gradient descent step size (0.001-0.1)
- **Duration**: Training time limit in minutes (1-120)
- **Batch Size**: Samples per training batch (8-128)

### 2. Start Training

Click **"🚀 Start Training"** to begin. The dashboard will:

1. Load and preprocess the selected dataset
2. Build a quantum variational circuit
3. Train the model with real-time metric updates
4. Display live charts showing loss and accuracy
5. Save results when complete

### 3. Monitor Progress

Watch real-time metrics:

- Current epoch number
- Elapsed training time
- Training/validation loss
- Best validation accuracy
- Progress bar showing % complete

### 4. View Results

The **Training History** panel shows:

- All completed training sessions
- Dataset used and final accuracy
- Timestamp and total epochs
- Click any result to view detailed metrics

### 5. Stop Training

Click **"⏹️ Stop Training"** to halt the current session early.

## 🏗️ Architecture

### Backend (Flask)

**File**: `web_app.py`

API Endpoints:

- `GET /` - Serve main dashboard UI
- `GET /api/datasets` - List available datasets
- `POST /api/train/start` - Start training session
- `POST /api/train/stop/<id>` - Stop training session
- `GET /api/train/status/<id>` - Get real-time training status
- `GET /api/train/sessions` - List all sessions
- `GET /api/results` - List saved training results
- `GET /api/results/<file>` - Get detailed results

Features:

- Threaded training execution (non-blocking)
- Real-time metric streaming
- Session state management
- Automatic result persistence

### Frontend (HTML/CSS/JS)

**Files**: `web_ui/index.html`, `web_ui/static/styles.css`, `web_ui/static/app.js`

Features:

- Chart.js for real-time visualization
- Polling-based status updates (1s interval)
- Responsive design (mobile-friendly)
- Gradient color themes
- Interactive training controls

### Quantum Training Pipeline

**Flow**:

1. Load CSV dataset → pandas
2. Preprocess (StandardScaler + PCA) → scikit-learn
3. Build quantum circuit (AmplitudeEmbedding + Variational layers) → PennyLane
4. Train with mini-batch gradient descent
5. Validate on held-out test set
6. Save metrics to JSON

**Quantum Circuit**:

- **Encoding**: AmplitudeEmbedding (maps classical data to quantum states)
- **Variational Layers**: Rot gates (RX, RY, RZ) + CNOT entanglement
- **Measurement**: PauliZ expectation values
- **Backend**: default.qubit (CPU simulator)

## 📊 Datasets

Located in `../datasets/quantum/*.csv`:

| Dataset       | Samples | Features | Task   | Best Accuracy |
| ------------- | ------- | -------- | ------ | ------------- |
| heart_disease | 302     | 13       | Binary | ~85%          |
| ionosphere    | 351     | 34       | Binary | ~90%          |
| sonar         | 208     | 60       | Binary | ~80%          |
| banknote      | 1,372   | 4        | Binary | ~95%          |

All datasets automatically:

- Handle missing values (median imputation)
- Normalize features (StandardScaler)
- Reduce dimensions (PCA to match qubit count)

## 🎛️ Hyperparameter Guide

### Qubits (n_qubits)

- **Range**: 2-8
- **Impact**: Higher = more features retained, slower training
- **Recommendation**: Start with 4, increase if accuracy plateaus

### Layers (n_layers)

- **Range**: 1-5
- **Impact**: Higher = more expressiveness, risk of overfitting
- **Recommendation**: 2-3 layers for most datasets

### Learning Rate

- **Range**: 0.001-0.1
- **Impact**: Higher = faster convergence, risk of instability
- **Recommendation**: 0.01 (default), reduce if loss oscillates

### Duration

- **Range**: 1-120 minutes
- **Impact**: Longer = more epochs, better convergence
- **Recommendation**: 10-30 minutes for initial experiments

### Batch Size

- **Range**: 8-128
- **Impact**: Larger = smoother gradients, more memory
- **Recommendation**: 32 (default)

## 📁 File Structure

```text
ai-projects/quantum-ml/
├── web_app.py                    # Flask backend
├── start_dashboard.sh            # Launch script
├── web-requirements.txt          # Python dependencies
├── web_ui/
│   ├── index.html               # Main dashboard UI
│   └── static/
│       ├── styles.css           # Styling
│       └── app.js               # Frontend logic
├── results/
│   └── training_*.json          # Saved session results
└── ../datasets/quantum/
    ├── heart_disease.csv
    ├── ionosphere.csv
    ├── sonar.csv
    └── banknote.csv
```

## 🔧 Troubleshooting

### Port Already in Use

If port 5000 is busy:

```python
# Edit web_app.py, change last line:
app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
```

### Dependencies Not Found

```bash
# Ensure virtual environment is active
source ./venv/bin/activate

# Reinstall dependencies
pip install -r web-requirements.txt
```

### Charts Not Updating

- Check browser console for errors
- Verify training is running: `GET /api/train/status/<session_id>`
- Refresh the page

### Training Crashes

- Reduce qubits (8→4) or layers (5→2)
- Lower batch size (128→32)
- Check error in console logs

## 🚀 Advanced Usage

### Custom Datasets

Add your own CSV to `../datasets/quantum/`:

1. Last column must be the label (0/1 for binary classification)
2. All other columns are features
3. Missing values are automatically handled
4. Refresh the dashboard to see it in the dataset list

### Modify Quantum Circuit

Edit `create_quantum_circuit()` in `web_app.py`:

```python
def create_quantum_circuit(n_qubits, n_layers):
    dev = qml.device('default.qubit', wires=n_qubits)

    @qml.qnode(dev, interface='autograd')
    def circuit(inputs, weights):
        # Your custom circuit here
        # Example: Add RX rotation layer
        for i in range(n_qubits):
            qml.RX(inputs[i], wires=i)

        # Variational layers
        for layer in range(n_layers):
            for i in range(n_qubits):
                qml.Rot(*weights[layer, i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]

    return circuit
```

### API Integration

Use the REST API programmatically:

```python
import requests

# Start training
response = requests.post('http://localhost:5000/api/train/start', json={
    'dataset': 'heart',
    'n_qubits': 4,
    'n_layers': 2,
    'learning_rate': 0.01,
    'duration_minutes': 10,
    'batch_size': 32
})
session_id = response.json()['session_id']

# Poll status
status = requests.get(f'http://localhost:5000/api/train/status/{session_id}').json()
print(f"Epoch {status['current_epoch']}, Accuracy: {status['best_val_acc']}")
```

## 📈 Metrics Explained

### Training Loss

- **What**: Mean squared error on training data
- **Goal**: Should decrease over time
- **Typical Range**: 0.1-0.8

### Validation Loss

- **What**: Mean squared error on held-out validation set
- **Goal**: Should track training loss closely
- **Warning**: If much higher than training loss → overfitting

### Validation Accuracy

- **What**: Classification accuracy on validation set
- **Goal**: Should increase over time
- **Range**: 0.0-1.0 (0%-100%)

## 🎯 Performance Tips

1. **Start Small**: Test with 1-minute duration first
2. **Monitor Charts**: Look for convergence (loss plateaus)
3. **Adjust Learning Rate**: If loss oscillates, reduce LR
4. **Increase Duration**: If accuracy still improving at timeout, train longer
5. **Try Different Datasets**: Some are easier to learn than others

## 📝 Example Workflows

### Quick Test Run

```text
Dataset: heart
Qubits: 4
Layers: 2
Learning Rate: 0.01
Duration: 2 minutes
Batch Size: 32

Expected: ~70-80% accuracy in 10-20 epochs
```

### High-Accuracy Training

```text
Dataset: banknote
Qubits: 4
Layers: 3
Learning Rate: 0.005
Duration: 20 minutes
Batch Size: 64

Expected: ~90-95% accuracy in 50-100 epochs
```

### Fast Iteration

```text
Dataset: any
Qubits: 3
Layers: 1
Learning Rate: 0.02
Duration: 1 minute
Batch Size: 16

Expected: Quick results for hyperparameter tuning
```

## 🔗 Related Documentation

- [PennyLane Quantum Training](https://pennylane.ai/)
- [Quantum ML Tutorial](INDEX.md)
- [Dataset Catalog](../../docs/guides/AI_DATASETS_CATALOG.md)
- [Azure Quantum Integration](AZURE_QUANTUM_QUICKSTART.md)

## 📄 License

Same as parent repository. See root LICENSE file.

## 🙏 Credits

Built with:

- **PennyLane**: Quantum machine learning framework
- **Flask**: Python web framework
- **Chart.js**: JavaScript charting library
- **scikit-learn**: Classical ML preprocessing

---

**Ready to explore quantum machine learning?** 🚀

Run `./start_dashboard.sh` and open <http://localhost:5000> to get started!
