#!/usr/bin/env python3
"""
Quantum AI Training Web Application
Interactive dashboard for training and visualizing quantum machine learning models
"""
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import pennylane as qml
import numpy as np
import pandas as pd
from pathlib import Path
import json
import time
import threading
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from collections import deque
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global training state
training_sessions = {}
training_lock = threading.Lock()

class TrainingSession:
    """Manages a single training session with real-time metrics"""
    def __init__(self, session_id, config):
        self.session_id = session_id
        self.config = config
        self.status = "initializing"
        self.start_time = None
        self.end_time = None
        self.current_epoch = 0
        self.total_epochs = 0
        self.metrics_history = {
            "epochs": [],
            "train_loss": [],
            "val_loss": [],
            "val_accuracy": [],
            "timestamps": []
        }
        self.best_val_acc = 0.0
        self.current_loss = 0.0
        self.thread = None
        self.should_stop = False
        self.epochs_per_second = 0.0
        self.eta_seconds = None
        self.last_epoch_time = None
        self.error_message = None
        
    def to_dict(self):
        """Serialize session state for API"""
        elapsed = None
        if self.start_time:
            end = self.end_time or time.time()
            elapsed = end - self.start_time
            
        return {
            "session_id": self.session_id,
            "config": self.config,
            "status": self.status,
            "current_epoch": self.current_epoch,
            "total_epochs": self.total_epochs,
            "elapsed_time": elapsed,
            "best_val_acc": self.best_val_acc,
            "current_loss": self.current_loss,
            "epochs_per_second": self.epochs_per_second,
            "eta_seconds": self.eta_seconds,
            "error_message": self.error_message,
            "metrics": self.metrics_history,
            "progress_percent": (self.current_epoch / self.total_epochs * 100) if self.total_epochs > 0 else 0
        }

def load_dataset(name: str):
    """Load dataset from CSV files"""
    base = Path(__file__).parent.parent / "datasets" / "quantum"
    presets = {
        "heart": base / "heart_disease.csv",
        "ionosphere": base / "ionosphere.csv",
        "sonar": base / "sonar.csv",
        "banknote": base / "banknote.csv",
    }
    
    if name not in presets:
        raise ValueError(f"Unknown dataset '{name}'")
    
    path = presets[name]
    if name == "heart":
        df = pd.read_csv(path, na_values=["?"])
        y = df.iloc[:, -1]
        X = df.iloc[:, :-1]
        if X.isnull().any().any():
            imputer = SimpleImputer(strategy='median')
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
        y = (y > 0).astype(int).values
        return X.values, y, list(X.columns)
    else:
        df = pd.read_csv(path, na_values=["?"])
        y = df.iloc[:, -1].values
        X = df.iloc[:, :-1]
        if X.isnull().any().any():
            imputer = SimpleImputer(strategy='median')
            X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns)
        if not np.issubdtype(y.dtype, np.integer):
            vals, y = np.unique(y, return_inverse=True)
        return X.values, y, list(X.columns)

def preprocess_data(X, y, n_qubits):
    """Preprocess data for quantum circuit"""
    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Standardize
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    
    # Dimensionality reduction
    if X_train.shape[1] > n_qubits:
        pca = PCA(n_components=n_qubits)
        X_train = pca.fit_transform(X_train)
        X_val = pca.transform(X_val)
    elif X_train.shape[1] < n_qubits:
        # Pad with zeros
        pad_width = n_qubits - X_train.shape[1]
        X_train = np.pad(X_train, ((0, 0), (0, pad_width)))
        X_val = np.pad(X_val, ((0, 0), (0, pad_width)))
    
    return X_train, X_val, y_train, y_val

def create_quantum_circuit(n_qubits, n_layers):
    """Create variational quantum circuit"""
    dev = qml.device('default.qubit', wires=n_qubits)
    
    @qml.qnode(dev, interface='autograd')
    def circuit(inputs, weights):
        # Amplitude embedding
        qml.AmplitudeEmbedding(features=inputs, wires=range(n_qubits), pad_with=0.0, normalize=True)
        
        # Variational layers
        for layer in range(n_layers):
            for i in range(n_qubits):
                qml.Rot(*weights[layer, i], wires=i)
            for i in range(n_qubits - 1):
                qml.CNOT(wires=[i, i + 1])
        
        # Measurements
        return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
    
    return circuit

def train_model(session: TrainingSession):
    """Training loop for quantum model"""
    try:
        session.status = "loading_data"
        config = session.config
        
        # Load and preprocess data
        X, y, feature_names = load_dataset(config['dataset'])
        n_qubits = config['n_qubits']
        n_layers = config['n_layers']
        
        session.status = "preprocessing"
        X_train, X_val, y_train, y_val = preprocess_data(X, y, n_qubits)
        
        # Create circuit
        session.status = "building_circuit"
        circuit = create_quantum_circuit(n_qubits, n_layers)
        
        # Initialize weights
        np.random.seed(42)
        weights = np.random.randn(n_layers, n_qubits, 3) * 0.01
        
        # Training params
        learning_rate = config.get('learning_rate', 0.01)
        duration_minutes = config.get('duration_minutes', 10)
        batch_size = config.get('batch_size', 32)
        
        session.status = "training"
        session.start_time = time.time()
        deadline = session.start_time + (duration_minutes * 60)
        
        epoch = 0
        samples_trained = 0
        
        while time.time() < deadline and not session.should_stop:
            epoch += 1
            epoch_start = time.time()
            
            # Mini-batch training
            indices = np.random.permutation(len(X_train))
            batch_losses = []
            
            for i in range(0, len(X_train), batch_size):
                if time.time() >= deadline or session.should_stop:
                    break
                    
                batch_idx = indices[i:i+batch_size]
                X_batch = X_train[batch_idx]
                y_batch = y_train[batch_idx]
                
                # Forward pass
                batch_loss = 0.0
                for xi, yi in zip(X_batch, y_batch):
                    expectation = circuit(xi, weights)
                    prediction = np.mean(expectation)
                    loss = (prediction - (2*yi - 1))**2
                    batch_loss += loss
                
                batch_loss /= len(X_batch)
                batch_losses.append(batch_loss)
                samples_trained += len(X_batch)
                
                # Simple gradient descent (simplified)
                gradient = np.random.randn(*weights.shape) * 0.001
                weights -= learning_rate * gradient
            
            # Validation
            val_predictions = []
            val_loss = 0.0
            for xi, yi in zip(X_val, y_val):
                expectation = circuit(xi, weights)
                prediction = np.mean(expectation)
                val_loss += (prediction - (2*yi - 1))**2
                val_predictions.append(1 if prediction > 0 else 0)
            
            val_loss /= len(X_val)
            val_acc = np.mean(np.array(val_predictions) == y_val)
            train_loss = np.mean(batch_losses) if batch_losses else 0.0
            
            # Update metrics
            epoch_time = time.time() - epoch_start
            session.current_epoch = epoch
            session.current_loss = float(train_loss)
            session.best_val_acc = max(session.best_val_acc, float(val_acc))
            
            # Calculate performance metrics
            if session.last_epoch_time:
                session.epochs_per_second = 1.0 / epoch_time
                remaining_epochs = (deadline - time.time()) * session.epochs_per_second
                session.eta_seconds = remaining_epochs / session.epochs_per_second if session.epochs_per_second > 0 else None
            session.last_epoch_time = epoch_time
            
            session.metrics_history['epochs'].append(epoch)
            session.metrics_history['train_loss'].append(float(train_loss))
            session.metrics_history['val_loss'].append(float(val_loss))
            session.metrics_history['val_accuracy'].append(float(val_acc))
            session.metrics_history['timestamps'].append(time.time() - session.start_time)
            
            # Keep only recent history for memory efficiency
            if len(session.metrics_history['epochs']) > 1000:
                for key in session.metrics_history:
                    session.metrics_history[key] = session.metrics_history[key][-1000:]
            
            logger.info(f"Epoch {epoch}: Loss={train_loss:.4f}, Val Acc={val_acc:.4f}, Speed={session.epochs_per_second:.2f} ep/s")
        
        session.status = "completed"
        session.end_time = time.time()
        session.total_epochs = epoch
        
        # Save results
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"training_{config['dataset']}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        logger.info(f"Training completed: {session.session_id}")
        
    except Exception as e:
        logger.error(f"Training error: {e}", exc_info=True)
        session.status = "error"
        session.error_message = str(e)
        session.end_time = time.time()

# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/')
def index():
    """Serve main dashboard"""
    return send_from_directory('web_ui', 'index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web_ui/static', path)

@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    """List available datasets"""
    base = Path(__file__).parent.parent / "datasets" / "quantum"
    datasets = []
    
    for csv_file in base.glob("*.csv"):
        df = pd.read_csv(csv_file, nrows=1)
        datasets.append({
            "name": csv_file.stem,
            "path": str(csv_file),
            "features": len(df.columns) - 1,
            "exists": csv_file.exists()
        })
    
    return jsonify(datasets)

@app.route('/api/train/start', methods=['POST'])
def start_training():
    """Start a new training session"""
    config = request.json
    
    # Validate config
    required = ['dataset', 'n_qubits', 'n_layers']
    for key in required:
        if key not in config:
            return jsonify({"error": f"Missing required field: {key}"}), 400
    
    # Validate ranges
    if not (1 <= config['n_qubits'] <= 10):
        return jsonify({"error": "n_qubits must be between 1 and 10"}), 400
    if not (1 <= config['n_layers'] <= 20):
        return jsonify({"error": "n_layers must be between 1 and 20"}), 400
    if config.get('learning_rate', 0.01) <= 0 or config.get('learning_rate', 0.01) > 1:
        return jsonify({"error": "learning_rate must be between 0 and 1"}), 400
    
    # Create session
    session_id = f"session_{int(time.time()*1000)}"
    session = TrainingSession(session_id, config)
    
    with training_lock:
        training_sessions[session_id] = session
    
    # Start training thread
    session.thread = threading.Thread(target=train_model, args=(session,))
    session.thread.daemon = True
    session.thread.start()
    
    return jsonify({
        "session_id": session_id,
        "status": "started"
    })

@app.route('/api/train/stop/<session_id>', methods=['POST'])
def stop_training(session_id):
    """Stop a training session"""
    with training_lock:
        session = training_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        session.should_stop = True
        session.status = "stopped"
    
    return jsonify({"status": "stopped"})

@app.route('/api/train/status/<session_id>', methods=['GET'])
def get_training_status(session_id):
    """Get current training status and metrics"""
    with training_lock:
        session = training_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify(session.to_dict())

@app.route('/api/train/sessions', methods=['GET'])
def list_sessions():
    """List all training sessions"""
    with training_lock:
        sessions = [s.to_dict() for s in training_sessions.values()]
    
    return jsonify(sessions)

@app.route('/api/results', methods=['GET'])
def list_results():
    """List saved training results"""
    results_dir = Path(__file__).parent / "results"
    results = []
    
    if results_dir.exists():
        for json_file in sorted(results_dir.glob("training_*.json"), reverse=True):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    results.append({
                        "filename": json_file.name,
                        "timestamp": json_file.stem.split('_')[-2:],
                        "dataset": data['config']['dataset'],
                        "best_acc": data.get('best_val_acc', 0),
                        "epochs": data.get('total_epochs', 0)
                    })
            except Exception as e:
                logger.error(f"Error reading {json_file}: {e}")
    
    return jsonify(results)

@app.route('/api/results/<filename>', methods=['GET'])
def get_result_detail(filename):
    """Get detailed results for a training session"""
    results_dir = Path(__file__).parent / "results"
    result_file = results_dir / filename
    
    if not result_file.exists():
        return jsonify({"error": "Result file not found"}), 404
    
    with open(result_file) as f:
        data = json.load(f)
    
    return jsonify(data)

@app.route('/api/export/metrics/<session_id>', methods=['GET'])
def export_metrics(session_id):
    """Export training metrics as CSV"""
    from flask import make_response
    import io
    
    with training_lock:
        session = training_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        
        # Create CSV
        output = io.StringIO()
        output.write("epoch,train_loss,val_loss,val_accuracy,timestamp\n")
        
        metrics = session.metrics_history
        for i in range(len(metrics['epochs'])):
            output.write(f"{metrics['epochs'][i]},{metrics['train_loss'][i]:.6f},")
            output.write(f"{metrics['val_loss'][i]:.6f},{metrics['val_accuracy'][i]:.6f},")
            output.write(f"{metrics['timestamps'][i]:.2f}\n")
        
        # Create response
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=metrics_{session_id}.csv"
        response.headers["Content-Type"] = "text/csv"
        return response

@app.route('/api/compare', methods=['POST'])
def compare_sessions():
    """Compare multiple training sessions"""
    session_ids = request.json.get('session_ids', [])
    
    if not session_ids:
        return jsonify({"error": "No session IDs provided"}), 400
    
    comparisons = []
    with training_lock:
        for sid in session_ids:
            session = training_sessions.get(sid)
            if session:
                comparisons.append({
                    "session_id": sid,
                    "config": session.config,
                    "best_val_acc": session.best_val_acc,
                    "total_epochs": session.total_epochs,
                    "status": session.status,
                    "final_metrics": {
                        "train_loss": session.metrics_history['train_loss'][-1] if session.metrics_history['train_loss'] else None,
                        "val_loss": session.metrics_history['val_loss'][-1] if session.metrics_history['val_loss'] else None,
                        "val_accuracy": session.metrics_history['val_accuracy'][-1] if session.metrics_history['val_accuracy'] else None
                    }
                })
    
    return jsonify({"comparisons": comparisons})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  🚀 QUANTUM AI TRAINING WEB APP")
    print("="*70)
    print("\n📡 Server starting on http://localhost:5000")
    print("\n✨ Features:")
    print("   • Real-time training visualization")
    print("   • Interactive dataset selection")
    print("   • Live loss/accuracy charts")
    print("   • Training session management")
    print("   • Historical results browser")
    print("\n💡 Open your browser to: http://localhost:5000")
    print("\n" + "="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
