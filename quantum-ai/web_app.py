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
import re
import time
import threading
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_auc_score
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
        self.samples_trained = 0
        self.current_val_acc = 0.0
        self.learning_rate = config.get('learning_rate', 0.01)
        self.checkpoint_path = None
        self.gradient_norm = 0.0
        self.optimizer_type = config.get('optimizer', 'adam')
        self.epochs_without_improvement = 0
        
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
            "samples_trained": self.samples_trained,
            "current_val_acc": self.current_val_acc,
            "current_learning_rate": self.learning_rate,
            "gradient_norm": self.gradient_norm,
            "checkpoint_path": self.checkpoint_path,
            "optimizer": self.optimizer_type,
            "epochs_without_improvement": self.epochs_without_improvement,
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

def compute_loss(circuit, X, y, weights):
    """Compute loss with proper gradient tracking"""
    total_loss = 0.0
    for xi, yi in zip(X, y):
        expectation = circuit(xi, weights)
        prediction = np.mean(expectation)
        target = 2 * yi - 1  # Map {0,1} to {-1,1}
        loss = (prediction - target) ** 2
        total_loss += loss
    return total_loss / len(X)

def compute_gradient(circuit, X, y, weights, use_parameter_shift=True):
    """Compute gradient using parameter-shift rule or finite differences"""
    grad = np.zeros_like(weights)
    
    if use_parameter_shift:
        # Parameter-shift rule: more accurate for quantum circuits
        shift = np.pi / 2
        for i in range(weights.shape[0]):
            for j in range(weights.shape[1]):
                for k in range(weights.shape[2]):
                    weights_plus = weights.copy()
                    weights_minus = weights.copy()
                    weights_plus[i, j, k] += shift
                    weights_minus[i, j, k] -= shift
                    loss_plus = compute_loss(circuit, X, y, weights_plus)
                    loss_minus = compute_loss(circuit, X, y, weights_minus)
                    grad[i, j, k] = (loss_plus - loss_minus) / 2
    else:
        # Finite differences fallback
        epsilon = 1e-4
        base_loss = compute_loss(circuit, X, y, weights)
        for i in range(weights.shape[0]):
            for j in range(weights.shape[1]):
                for k in range(weights.shape[2]):
                    weights_plus = weights.copy()
                    weights_plus[i, j, k] += epsilon
                    loss_plus = compute_loss(circuit, X, y, weights_plus)
                    grad[i, j, k] = (loss_plus - base_loss) / epsilon
    
    return grad

class AdamOptimizer:
    """Adam optimizer for quantum circuit training"""
    def __init__(self, learning_rate=0.01, beta1=0.9, beta2=0.999, epsilon=1e-8):
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon
        self.m = None  # First moment
        self.v = None  # Second moment
        self.t = 0     # Timestep
    
    def update(self, weights, gradient):
        """Apply Adam update"""
        if self.m is None:
            self.m = np.zeros_like(weights)
            self.v = np.zeros_like(weights)
        
        self.t += 1
        
        # Update biased first moment estimate
        self.m = self.beta1 * self.m + (1 - self.beta1) * gradient
        
        # Update biased second moment estimate
        self.v = self.beta2 * self.v + (1 - self.beta2) * (gradient ** 2)
        
        # Compute bias-corrected moment estimates
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)
        
        # Update weights
        weights_new = weights - self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
        
        return weights_new

class MomentumOptimizer:
    """SGD with momentum optimizer"""
    def __init__(self, learning_rate=0.01, momentum=0.9):
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.velocity = None
    
    def update(self, weights, gradient):
        """Apply momentum update"""
        if self.velocity is None:
            self.velocity = np.zeros_like(weights)
        
        self.velocity = self.momentum * self.velocity - self.learning_rate * gradient
        weights_new = weights + self.velocity
        
        return weights_new

def learning_rate_schedule(epoch, initial_lr, decay_rate=0.95, decay_every=50):
    """Learning rate decay schedule"""
    return initial_lr * (decay_rate ** (epoch // decay_every))

def warmup_lr_schedule(epoch, initial_lr, warmup_epochs=10):
    """Linear warmup for learning rate"""
    if epoch < warmup_epochs:
        return initial_lr * (epoch + 1) / warmup_epochs
    return initial_lr

def clip_gradient(gradient, max_norm=1.0):
    """Clip gradient by global norm"""
    grad_norm = np.linalg.norm(gradient)
    if grad_norm > max_norm:
        return gradient * (max_norm / grad_norm)
    return gradient

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
        initial_lr = learning_rate
        duration_minutes = config.get('duration_minutes', 10)
        batch_size = config.get('batch_size', 32)
        use_lr_decay = config.get('use_lr_decay', True)
        checkpoint_every = config.get('checkpoint_every', 100)
        optimizer_type = config.get('optimizer', 'adam')  # 'adam', 'momentum', or 'sgd'
        early_stopping_patience = config.get('early_stopping_patience', 20)
        use_parameter_shift = config.get('use_parameter_shift', True)
        use_gradient_clipping = config.get('use_gradient_clipping', True)
        max_grad_norm = config.get('max_grad_norm', 1.0)
        use_warmup = config.get('use_warmup', True)
        warmup_epochs = config.get('warmup_epochs', 10)
        
        # Initialize optimizer
        if optimizer_type == 'adam':
            optimizer = AdamOptimizer(learning_rate=learning_rate)
        elif optimizer_type == 'momentum':
            optimizer = MomentumOptimizer(learning_rate=learning_rate, momentum=0.9)
        else:
            optimizer = None  # Plain SGD
        
        session.status = "training"
        session.start_time = time.time()
        deadline = session.start_time + (duration_minutes * 60)
        
        epoch = 0
        samples_trained = 0
        best_weights = weights.copy()
        best_val_loss = float('inf')
        epochs_without_improvement = 0
        
        # Create checkpoints directory
        checkpoint_dir = Path(__file__).parent / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)
        
        while time.time() < deadline and not session.should_stop:
            epoch += 1
            epoch_start = time.time()
            
            # Apply warmup schedule
            if use_warmup and epoch <= warmup_epochs:
                current_lr = warmup_lr_schedule(epoch, initial_lr, warmup_epochs)
                session.learning_rate = current_lr
                if optimizer is not None:
                    optimizer.learning_rate = current_lr
            # Apply learning rate decay after warmup
            elif use_lr_decay:
                current_lr = learning_rate_schedule(epoch, initial_lr)
                session.learning_rate = current_lr
                if optimizer is not None:
                    optimizer.learning_rate = current_lr
            
            # Mini-batch training with proper gradients
            indices = np.random.permutation(len(X_train))
            batch_losses = []
            epoch_gradients = []
            
            for i in range(0, len(X_train), batch_size):
                if time.time() >= deadline or session.should_stop:
                    break
                    
                batch_idx = indices[i:i+batch_size]
                X_batch = X_train[batch_idx]
                y_batch = y_train[batch_idx]
                
                # Compute gradient for this batch
                gradient = compute_gradient(circuit, X_batch, y_batch, weights, use_parameter_shift=use_parameter_shift)
                
                # Apply gradient clipping
                if use_gradient_clipping:
                    gradient = clip_gradient(gradient, max_norm=max_grad_norm)
                
                epoch_gradients.append(gradient)
                
                # Compute batch loss
                batch_loss = compute_loss(circuit, X_batch, y_batch, weights)
                batch_losses.append(batch_loss)
                samples_trained += len(X_batch)
                
                # Apply optimizer update
                if optimizer is not None:
                    weights = optimizer.update(weights, gradient)
                else:
                    # Plain SGD
                    weights -= session.learning_rate * gradient
            
            # Track gradient norm
            if epoch_gradients:
                avg_gradient = np.mean([np.linalg.norm(g) for g in epoch_gradients])
                session.gradient_norm = float(avg_gradient)
            
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
            
            # Early stopping check
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_weights = weights.copy()
                epochs_without_improvement = 0
            else:
                epochs_without_improvement += 1
            
            session.epochs_without_improvement = epochs_without_improvement
            
            # Stop if no improvement for patience epochs
            if epochs_without_improvement >= early_stopping_patience:
                logger.info(f"Early stopping triggered after {epoch} epochs (no improvement for {early_stopping_patience} epochs)")
                session.status = "early_stopped"
                break
            
            # Save best weights based on validation accuracy
            if val_acc > session.best_val_acc:
                best_weights = weights.copy()
            
            # Checkpoint saving
            if epoch % checkpoint_every == 0:
                checkpoint_path = checkpoint_dir / f"checkpoint_{session.session_id}_epoch_{epoch}.npz"
                np.savez(checkpoint_path, 
                        weights=weights, 
                        epoch=epoch,
                        val_acc=val_acc,
                        config=config)
                session.checkpoint_path = str(checkpoint_path)
                logger.info(f"Checkpoint saved: {checkpoint_path}")
            
            # Update metrics
            epoch_time = time.time() - epoch_start
            session.current_epoch = epoch
            session.current_loss = float(train_loss)
            session.current_val_acc = float(val_acc)
            session.best_val_acc = max(session.best_val_acc, float(val_acc))
            session.samples_trained = samples_trained
            
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
            
            logger.info(f"Epoch {epoch}: Loss={train_loss:.4f}, Val Acc={val_acc:.4f}, Val Loss={val_loss:.4f}, Speed={session.epochs_per_second:.2f} ep/s, LR={session.learning_rate:.6f}, Grad Norm={session.gradient_norm:.6f}")
        
        # Use best weights for final model
        weights = best_weights
        
        session.status = "completed" if session.status != "early_stopped" else "early_stopped"
        session.end_time = time.time()
        session.total_epochs = epoch
        
        # Save final checkpoint with best weights
        final_checkpoint = checkpoint_dir / f"final_{session.session_id}.npz"
        np.savez(final_checkpoint,
                weights=best_weights,
                epoch=epoch,
                val_acc=session.best_val_acc,
                config=config,
                metrics=session.metrics_history)
        session.checkpoint_path = str(final_checkpoint)
        
        # Optional evaluation at end of training
        try:
            eval_result = evaluate_session_internal(config, best_weights)
        except Exception as _:
            eval_result = None
        
        # Save results
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"training_{config['dataset']}_{timestamp}.json"
        
        with open(result_file, 'w') as f:
            doc = session.to_dict()
            if eval_result is not None:
                doc['evaluation'] = eval_result
            json.dump(doc, f, indent=2)
        
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
    
    # Validate filename to prevent path traversal attacks
    # Only allow alphanumeric, underscores, dashes, and .json extension
    if not re.match(r'^[A-Za-z0-9_\-]+\.json$', filename):
        return jsonify({"error": "Invalid filename"}), 400
    
    result_file = results_dir / filename
    
    # Ensure path is within results directory (additional protection)
    try:
        resolved_path = result_file.resolve()
        allowed_dir = results_dir.resolve()
        # Verify the resolved path is within allowed_dir (path containment check)
        # Python 3.9+: use is_relative_to; fallback for earlier versions
        if hasattr(resolved_path, "is_relative_to"):
            if not resolved_path.is_relative_to(allowed_dir):
                return jsonify({"error": "Invalid file path"}), 403
        else:
            try:
                resolved_path.relative_to(allowed_dir)
            except ValueError:
                return jsonify({"error": "Invalid file path"}), 403
    except (OSError, RuntimeError):
        return jsonify({"error": "Invalid file path"}), 400
    
    if not resolved_path.exists():
        return jsonify({"error": "Result file not found"}), 404
    
    with open(resolved_path) as f:
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

def evaluate_session_internal(config, weights):
    """Compute evaluation metrics on the validation set given config and weights"""
    # Reload dataset and reproduce split (random_state fixed in preprocess_data)
    X, y, _ = load_dataset(config['dataset'])
    X_train, X_val, y_train, y_val = preprocess_data(X, y, config['n_qubits'])
    
    # Rebuild circuit
    circuit = create_quantum_circuit(config['n_qubits'], config['n_layers'])
    
    # Predictions
    y_scores = []
    y_pred = []
    for xi in X_val:
        expectation = circuit(xi, weights)
        score = float(np.mean(expectation))  # in [-1, 1]
        prob = (score + 1.0) / 2.0          # map to [0, 1]
        y_scores.append(prob)
        y_pred.append(1 if score > 0 else 0)
    
    y_scores = np.array(y_scores)
    y_pred = np.array(y_pred)
    
    # Metrics
    cm = confusion_matrix(y_val, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_val, y_pred, average='binary' if len(np.unique(y_val)) == 2 else 'macro', zero_division=0)
    accuracy = float(np.mean(y_pred == y_val))
    roc = None
    try:
        if len(np.unique(y_val)) == 2:
            roc = float(roc_auc_score(y_val, y_scores))
    except Exception:
        roc = None
    
    return {
        "confusion_matrix": cm.tolist(),
        "labels": sorted(list(map(int, np.unique(y_val)))),
        "metrics": {
            "accuracy": accuracy,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "roc_auc": roc
        }
    }

@app.route('/api/train/evaluate/<session_id>', methods=['GET'])
def evaluate_session(session_id):
    """Evaluate a completed training session using its final checkpoint"""
    with training_lock:
        session = training_sessions.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
        if not session.checkpoint_path or not Path(session.checkpoint_path).exists():
            return jsonify({"error": "No checkpoint available for this session yet"}), 400
        config = session.config
        checkpoint_path = session.checkpoint_path
    
    try:
        data = np.load(checkpoint_path, allow_pickle=True)
        weights = data['weights']
        result = evaluate_session_internal(config, weights)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/checkpoint/<session_id>', methods=['GET'])
def get_checkpoint(session_id):
    """Download checkpoint file for a session"""
    from flask import send_file
    
    with training_lock:
        session = training_sessions.get(session_id)
        if not session or not session.checkpoint_path:
            return jsonify({"error": "No checkpoint found"}), 404
        
        checkpoint_file = Path(session.checkpoint_path)
        if not checkpoint_file.exists():
            return jsonify({"error": "Checkpoint file not found"}), 404
        
        return send_file(checkpoint_file, as_attachment=True)

@app.route('/api/load_checkpoint', methods=['POST'])
def load_checkpoint():
    """Load a checkpoint and resume training"""
    checkpoint_path = request.json.get('checkpoint_path')
    
    if not checkpoint_path:
        return jsonify({"error": "No checkpoint path provided"}), 400
    
    try:
        # Validate path to prevent path traversal attacks
        checkpoint_path = Path(checkpoint_path)
        checkpoint_dir = Path(__file__).parent / "checkpoints"
        
        # Resolve to absolute paths to prevent traversal
        try:
            resolved_path = checkpoint_path.resolve()
            allowed_dir = checkpoint_dir.resolve()
        except (OSError, RuntimeError) as e:
            return jsonify({"error": "Invalid checkpoint path"}), 400
        
        # Verify the resolved path is within allowed_dir (path containment check)
        # Python 3.9+: use is_relative_to; fallback for earlier versions
        if hasattr(resolved_path, "is_relative_to"):
            if not resolved_path.is_relative_to(allowed_dir):
                return jsonify({"error": "Invalid checkpoint path: must be within checkpoints directory"}), 403
        else:
            try:
                resolved_path.relative_to(allowed_dir)
            except ValueError:
                return jsonify({"error": "Invalid checkpoint path: must be within checkpoints directory"}), 403
        
        if not resolved_path.exists():
            return jsonify({"error": "Checkpoint file not found"}), 404
        
        checkpoint = np.load(str(resolved_path), allow_pickle=True)
        weights = checkpoint['weights']
        epoch = int(checkpoint['epoch'])
        config = checkpoint['config'].item() if isinstance(checkpoint['config'], np.ndarray) else checkpoint['config']
        
        return jsonify({
            "success": True,
            "epoch": epoch,
            "config": config,
            "message": f"Checkpoint loaded from epoch {epoch}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_global_stats():
    """Get global statistics across all sessions"""
    with training_lock:
        total_sessions = len(training_sessions)
        active_sessions = sum(1 for s in training_sessions.values() if s.status == "training")
        completed_sessions = sum(1 for s in training_sessions.values() if s.status == "completed")
        total_epochs = sum(s.current_epoch for s in training_sessions.values())
        avg_accuracy = np.mean([s.best_val_acc for s in training_sessions.values() if s.best_val_acc > 0]) if training_sessions else 0
        
    return jsonify({
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "completed_sessions": completed_sessions,
        "total_epochs_trained": total_epochs,
        "average_best_accuracy": float(avg_accuracy),
        "server_uptime": time.time() - app.config.get('START_TIME', time.time())
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "active_sessions": sum(1 for s in training_sessions.values() if s.status == "training")
    })

if __name__ == '__main__':
    # Set start time for uptime tracking
    app.config['START_TIME'] = time.time()
    
    print("\n" + "="*70)
    print("  🚀 QUANTUM AI TRAINING WEB APP - ADVANCED ML ENGINE")
    print("="*70)
    print("\n📡 Server starting on http://localhost:5000")
    print("\n✨ Advanced Optimization Features:")
    print("   • Adam, Momentum, and SGD optimizers")
    print("   • Parameter-shift gradient rule (quantum-native)")
    print("   • Learning rate warmup and decay scheduling")
    print("   • Gradient clipping for training stability")
    print("   • Early stopping with patience monitoring")
    print("   • Automatic checkpoint saving")
    print("   • Model comparison & analytics")
    print("\n🔬 Training Enhancements:")
    print("   • Parameter-shift rule (π/2 shift)")
    print("   • Finite difference fallback")
    print("   • Adaptive learning rate warmup (10 epochs)")
    print("   • Exponential LR decay (0.95 every 50 epochs)")
    print("   • Gradient norm clipping (max_norm=1.0)")
    print("   • Best model checkpointing")
    print("   • Early stopping (patience=20)")
    print("\n📊 Available Optimizers:")
    print("   • Adam (default): Adaptive moment estimation")
    print("   • Momentum: SGD with momentum (β=0.9)")
    print("   • SGD: Vanilla stochastic gradient descent")
    print("\n💡 Open your browser to: http://localhost:5000")
    print("📊 API Documentation: http://localhost:5000/api/health")
    print("\n" + "="*70 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
