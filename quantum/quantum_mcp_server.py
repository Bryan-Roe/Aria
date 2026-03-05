"""
Quantum AI MCP Server (Optimized)
Exposes quantum computing and quantum machine learning capabilities via Model Context Protocol
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
from collections import OrderedDict
import tempfile

# Add src directory to path before importing local modules
import sys
from pathlib import Path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Verify src directory exists
if not src_path.exists():
    print(f"Error: src/ directory not found at {src_path}")
    print("Please ensure the following directory structure exists:")
    print("  quantum/")
    print("    ├── quantum_mcp_server.py")
    print("    └── src/")
    print("        ├── quantum_classifier.py")
    print("        └── azure_quantum_integration.py")
    sys.exit(1)

# Import MCP dependencies
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError as e:
    print("Error: MCP package not installed or incompatible version.")
    print("\nTo install MCP dependencies, run:")
    print("  pip install -r mcp-requirements.txt")
    print("\nOr install directly:")
    print("  pip install 'mcp>=0.9.0'")
    print("\nIf you're using a virtual environment, ensure it's activated:")
    print("  .\\venv\\Scripts\\Activate.ps1")
    print(f"\nDetails: {e}")
    sys.exit(1)

# Import quantum modules
try:
    from quantum_classifier import QuantumClassifier, HybridQuantumClassifier, train_quantum_model
    from azure_quantum_integration import AzureQuantumIntegration, create_sample_circuit
except ImportError as e:
    print(f"Error: Could not import quantum modules from {src_path}/")
    print("\nEnsure the following files exist:")
    print(f"  - {src_path / 'quantum_classifier.py'}")
    print(f"  - {src_path / 'azure_quantum_integration.py'}")
    print("\nMissing files should contain:")
    print("  quantum_classifier.py:")
    print("    - class QuantumClassifier")
    print("    - class HybridQuantumClassifier")
    print("    - def train_quantum_model()")
    print("  azure_quantum_integration.py:")
    print("    - class AzureQuantumIntegration")
    print("    - def create_sample_circuit()")
    print(f"\nDetails: {e}")
    sys.exit(1)

import numpy as np
from qiskit import QuantumCircuit

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("quantum-ai-mcp")

# Thread pool for CPU-bound operations
cpu_executor = ProcessPoolExecutor(max_workers=2)
io_executor = ThreadPoolExecutor(max_workers=4)
EXECUTOR_TIMEOUT_SECONDS = 60


class CircuitCache:
    """LRU cache with TTL for quantum circuits"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps = {}

    def get(self, key: str) -> Optional[QuantumCircuit]:
        if key not in self.cache:
            return None

        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self._evict(key)
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, circuit: QuantumCircuit):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            self.cache[key] = circuit
            self.timestamps[key] = time.time()

        # Evict oldest if over size limit
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            self._evict(oldest_key)

    def _evict(self, key: str):
        del self.cache[key]
        del self.timestamps[key]

    def clear_expired(self):
        """Remove all expired entries"""
        current_time = time.time()
        expired = [
            key for key, timestamp in self.timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        for key in expired:
            self._evict(key)


# Global state for quantum resources
quantum_state = {
    "azure_integration": None,
    "quantum_classifier": None,
    "circuit_cache": CircuitCache(max_size=100, ttl_seconds=3600),
    "config_cache": {},  # Cache YAML configs to avoid repeated temp file creation
}


def _is_paid_qpu_backend(backend_name: Optional[str]) -> bool:
    """Return True when backend target appears to be paid hardware (QPU)."""
    if not backend_name:
        return False

    normalized = backend_name.lower()
    return "qpu" in normalized and "sim" not in normalized


def _coerce_bool(value: Any) -> bool:
    """Safely coerce bool-like values from MCP arguments."""
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False

    if isinstance(value, (int, float)):
        return value != 0

    return bool(value)


def initialize_quantum_resources():
    """Initialize quantum computing resources"""
    try:
        quantum_state["quantum_classifier"] = QuantumClassifier()
        logger.info("Quantum classifier initialized")
    except Exception as e:
        logger.warning(f"Could not initialize quantum classifier: {e}")


def _resolve_azure_location(args: Dict[str, Any]) -> str:
    """Resolve Azure location safely from args/env with a stable default."""
    location = args.get("location") if isinstance(args, dict) else None
    if isinstance(location, str) and location.strip():
        return location.strip()

    env_location = os.getenv("AZURE_QUANTUM_LOCATION", "")
    if env_location.strip():
        return env_location.strip()

    return "eastus"


async def _run_executor_with_timeout(
    executor: Any,
    func: Any,
    *args: Any,
    operation: str,
):
    """Run blocking executor work with a timeout guard."""
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(executor, func, *args),
            timeout=EXECUTOR_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise TimeoutError(
            f"{operation} timed out after {EXECUTOR_TIMEOUT_SECONDS} seconds"
        ) from exc


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available quantum computing tools"""
    return [
        Tool(
            name="create_quantum_circuit",
            description="Create a quantum circuit with specified parameters. Returns circuit description and QASM representation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "n_qubits": {
                        "type": "integer",
                        "description": "Number of qubits in the circuit",
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "circuit_type": {
                        "type": "string",
                        "description": "Type of circuit to create",
                        "enum": ["entanglement", "ghz", "bell", "random", "custom"],
                    },
                    "gates": {
                        "type": "array",
                        "description": "Custom gates for 'custom' circuit type. Format: [{'gate': 'h', 'qubit': 0}, {'gate': 'cx', 'qubits': [0,1]}]",
                        "items": {"type": "object"},
                    },
                },
                "required": ["n_qubits", "circuit_type"],
            },
        ),
        Tool(
            name="simulate_quantum_circuit",
            description="Simulate a quantum circuit locally using Qiskit Aer simulator. Returns measurement results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "circuit_id": {
                        "type": "string",
                        "description": "ID of a previously created circuit",
                    },
                    "shots": {
                        "type": "integer",
                        "description": "Number of measurement shots",
                        "minimum": 1,
                        "maximum": 100000,
                        "default": 1024,
                    },
                },
                "required": ["circuit_id"],
            },
        ),
        Tool(
            name="connect_azure_quantum",
            description="Connect to Azure Quantum workspace. Required before submitting jobs to Azure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "subscription_id": {
                        "type": "string",
                        "description": "Azure subscription ID",
                    },
                    "resource_group": {
                        "type": "string",
                        "description": "Azure resource group name",
                    },
                    "workspace_name": {
                        "type": "string",
                        "description": "Azure Quantum workspace name",
                    },
                    "location": {
                        "type": "string",
                        "description": "Azure region for the Quantum workspace (optional, defaults to AZURE_QUANTUM_LOCATION or eastus)",
                    },
                },
                "required": ["subscription_id", "resource_group", "workspace_name"],
            },
        ),
        Tool(
            name="list_quantum_backends",
            description="List available quantum backends in the Azure Quantum workspace. Must be connected first.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="submit_quantum_job",
            description="Submit a quantum circuit to Azure Quantum for execution on real quantum hardware or cloud simulators.",
            inputSchema={
                "type": "object",
                "properties": {
                    "circuit_id": {
                        "type": "string",
                        "description": "ID of a previously created circuit",
                    },
                    "backend_name": {
                        "type": "string",
                        "description": "Backend to run on (from list_quantum_backends)",
                    },
                    "shots": {
                        "type": "integer",
                        "description": "Number of measurement shots",
                        "minimum": 1,
                        "maximum": 10000,
                        "default": 500,
                    },
                    "confirm_cost": {
                        "type": "boolean",
                        "description": "Required for paid QPU targets. Set true only after reviewing expected cost.",
                        "default": False,
                    },
                },
                "required": ["circuit_id"],
            },
        ),
        Tool(
            name="train_quantum_classifier",
            description="Train a hybrid quantum-classical classifier on provided data. Returns training metrics and accuracy.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dataset": {
                        "type": "string",
                        "description": "Dataset to use for training",
                        "enum": ["iris", "wine", "breast_cancer", "synthetic"],
                    },
                    "n_qubits": {
                        "type": "integer",
                        "description": "Number of qubits in quantum circuit",
                        "minimum": 2,
                        "maximum": 10,
                        "default": 4,
                    },
                    "n_layers": {
                        "type": "integer",
                        "description": "Number of variational layers",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 2,
                    },
                    "epochs": {
                        "type": "integer",
                        "description": "Number of training epochs",
                        "minimum": 1,
                        "maximum": 200,
                        "default": 50,
                    },
                    "entanglement": {
                        "type": "string",
                        "description": "Entanglement pattern for quantum circuit",
                        "enum": ["linear", "circular", "full"],
                        "default": "linear",
                    },
                },
                "required": ["dataset"],
            },
        ),
        Tool(
            name="estimate_quantum_cost",
            description="Estimate the cost of running a quantum job on Azure Quantum hardware.",
            inputSchema={
                "type": "object",
                "properties": {
                    "circuit_id": {
                        "type": "string",
                        "description": "ID of the circuit to estimate",
                    },
                    "backend_name": {
                        "type": "string",
                        "description": "Backend to estimate cost for",
                    },
                    "shots": {
                        "type": "integer",
                        "description": "Number of shots",
                        "default": 100,
                    },
                },
                "required": ["circuit_id", "backend_name"],
            },
        ),
        Tool(
            name="get_quantum_circuit_properties",
            description="Get properties of a quantum circuit including depth, gate count, and topology.",
            inputSchema={
                "type": "object",
                "properties": {
                    "circuit_id": {
                        "type": "string",
                        "description": "ID of the circuit to analyze",
                    },
                },
                "required": ["circuit_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""

    try:
        if name == "create_quantum_circuit":
            return await create_circuit_handler(arguments)
        elif name == "simulate_quantum_circuit":
            return await simulate_circuit_handler(arguments)
        elif name == "connect_azure_quantum":
            return await connect_azure_handler(arguments)
        elif name == "list_quantum_backends":
            return await list_backends_handler(arguments)
        elif name == "submit_quantum_job":
            return await submit_job_handler(arguments)
        elif name == "train_quantum_classifier":
            return await train_classifier_handler(arguments)
        elif name == "estimate_quantum_cost":
            return await estimate_cost_handler(arguments)
        elif name == "get_quantum_circuit_properties":
            return await circuit_properties_handler(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error executing {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def create_circuit_handler(args: Dict) -> List[TextContent]:
    """Create a quantum circuit based on parameters (optimized with async execution)"""
    n_qubits = args["n_qubits"]
    circuit_type = args["circuit_type"]

    # Offload circuit creation to thread pool for CPU-intensive operations
    circuit = await _run_executor_with_timeout(
        io_executor,
        _create_circuit_sync,
        n_qubits,
        circuit_type,
        args.get("gates"),
        operation="create_quantum_circuit",
    )

    if circuit is None:
        return [TextContent(type="text", text="Invalid circuit type or missing gates for custom type")]

    # Generate circuit ID using SHA-256 (MD5 is weak for security)
    import hashlib
    circuit_id = hashlib.sha256(str(circuit).encode()).hexdigest()[:12]

    # Cache the circuit with TTL
    quantum_state["circuit_cache"].put(circuit_id, circuit)

    result = {
        "circuit_id": circuit_id,
        "n_qubits": n_qubits,
        "circuit_type": circuit_type,
        "depth": circuit.depth(),
        "gate_count": sum(circuit.count_ops().values()),
        "qasm": circuit.qasm(),
        "diagram": str(circuit.draw(output='text')),
    }

    return [TextContent(
        type="text",
        text=f"Created quantum circuit:\n\n```\n{result['diagram']}\n```\n\nCircuit ID: {circuit_id}\nDepth: {result['depth']}, Gates: {result['gate_count']}"
    )]


def _create_circuit_sync(n_qubits: int, circuit_type: str, gates: Optional[List] = None) -> Optional[QuantumCircuit]:
    """Synchronous circuit creation (runs in thread pool)"""
    if circuit_type == "entanglement":
        return create_sample_circuit(n_qubits)
    elif circuit_type == "bell":
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
        return circuit
    elif circuit_type == "ghz":
        circuit = QuantumCircuit(n_qubits, n_qubits)
        circuit.h(0)
        for i in range(n_qubits - 1):
            circuit.cx(i, i + 1)
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    elif circuit_type == "random":
        circuit = QuantumCircuit(n_qubits, n_qubits)
        import random
        for _ in range(n_qubits * 2):
            gate = random.choice(['h', 'x', 'y', 'z', 'rx', 'ry', 'rz'])
            qubit = random.randint(0, n_qubits - 1)
            if gate == 'h':
                circuit.h(qubit)
            elif gate == 'x':
                circuit.x(qubit)
            elif gate == 'y':
                circuit.y(qubit)
            elif gate == 'z':
                circuit.z(qubit)
            else:
                circuit.rx(np.pi / 4, qubit)
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    elif circuit_type == "custom" and gates:
        circuit = QuantumCircuit(n_qubits, n_qubits)
        for gate_spec in gates:
            gate_name = gate_spec["gate"].lower()
            if "qubit" in gate_spec:
                qubit = gate_spec["qubit"]
                if gate_name == "h":
                    circuit.h(qubit)
                elif gate_name == "x":
                    circuit.x(qubit)
                elif gate_name == "y":
                    circuit.y(qubit)
                elif gate_name == "z":
                    circuit.z(qubit)
            elif "qubits" in gate_spec:
                qubits = gate_spec["qubits"]
                if gate_name in ["cx", "cnot"]:
                    circuit.cx(qubits[0], qubits[1])
                elif gate_name == "cz":
                    circuit.cz(qubits[0], qubits[1])
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    return None


async def simulate_circuit_handler(args: Dict) -> List[TextContent]:
    """Simulate a quantum circuit locally (optimized with async execution)"""
    circuit_id = args["circuit_id"]
    shots = args.get("shots", 1024)

    # Clean expired cache entries periodically
    quantum_state["circuit_cache"].clear_expired()

    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired. Create a circuit first.")]

    # Offload simulation to thread pool (CPU-intensive)
    counts = await _run_executor_with_timeout(
        cpu_executor,
        _simulate_circuit_sync,
        circuit,
        shots,
        operation="simulate_quantum_circuit",
    )

    # Format results
    sorted_counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    total_shots = sum(sorted_counts.values())

    result_text = f"Simulation results for circuit {circuit_id} ({shots} shots):\n\n"
    for state, count in list(sorted_counts.items())[:10]:  # Top 10 states
        probability = count / total_shots
        result_text += f"  |{state}⟩: {count} ({probability:.3%})\n"

    if len(sorted_counts) > 10:
        result_text += f"\n  ... and {len(sorted_counts) - 10} more states"

    return [TextContent(type="text", text=result_text)]


def _simulate_circuit_sync(circuit: QuantumCircuit, shots: int) -> Dict:
    """Synchronous circuit simulation (runs in process pool)"""
    from qiskit_aer import AerSimulator
    simulator = AerSimulator()
    job = simulator.run(circuit, shots=shots)
    result = job.result()
    return result.get_counts()


async def connect_azure_handler(args: Dict) -> List[TextContent]:
    """Connect to Azure Quantum workspace (optimized with config caching)"""
    try:
        # Check config cache to avoid repeated temp file creation
        location = _resolve_azure_location(args)
        config_key = f"{args['subscription_id']}_{args['resource_group']}_{args['workspace_name']}_{location}"

        if config_key not in quantum_state["config_cache"]:
            # Create config in-memory instead of temp file
            config = {
                "azure": {
                    "subscription_id": args["subscription_id"],
                    "resource_group": args["resource_group"],
                    "workspace_name": args["workspace_name"],
                    "location": location,
                },
                "quantum": {"provider": "ionq", "hardware": {"shots": 500, "optimization_level": 2}},
                "ml": {"model": {"n_qubits": 4, "n_layers": 2, "entanglement": "linear"}},
                "logging": {"level": "INFO", "results_dir": "./results"},
            }
            quantum_state["config_cache"][config_key] = config

        # Offload Azure connection to thread pool (I/O bound)
        azure_int = await _run_executor_with_timeout(
            io_executor,
            _connect_azure_sync,
            quantum_state["config_cache"][config_key],
            operation="connect_azure_quantum",
        )
        quantum_state["azure_integration"] = azure_int

        return [TextContent(
            type="text",
            text=f"✓ Connected to Azure Quantum workspace: {args['workspace_name']}\nResource Group: {args['resource_group']}\nLocation: {location}"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to connect to Azure Quantum: {str(e)}")]


def _connect_azure_sync(config: Dict) -> AzureQuantumIntegration:
    """Synchronous Azure connection (runs in thread pool)"""
    import yaml

    config_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        azure_int = AzureQuantumIntegration(config_path=config_path)
        azure_int.connect()
        return azure_int
    finally:
        if config_path:
            try:
                Path(config_path).unlink()
            except FileNotFoundError:
                pass


async def list_backends_handler(args: Dict) -> List[TextContent]:
    """List available quantum backends (optimized with async I/O)"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum. Use connect_azure_quantum first.")]

    try:
        # Offload to thread pool
        backends = await _run_executor_with_timeout(
            io_executor,
            quantum_state["azure_integration"].list_backends,
            operation="list_quantum_backends",
        )
        backend_list = "\n".join(f"  • {backend}" for backend in backends)
        return [TextContent(type="text", text=f"Available quantum backends:\n\n{backend_list}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing backends: {str(e)}")]


async def submit_job_handler(args: Dict) -> List[TextContent]:
    """Submit a quantum job to Azure Quantum (optimized)"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum. Use connect_azure_quantum first.")]

    circuit_id = args["circuit_id"]
    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired.")]

    backend_name = args.get("backend_name")
    shots = args.get("shots", 500)
    confirm_cost = _coerce_bool(args.get("confirm_cost", False))

    if _is_paid_qpu_backend(backend_name) and not confirm_cost:
        return [TextContent(
            type="text",
            text=(
                "Refusing paid QPU submission without explicit cost confirmation.\n"
                "Set confirm_cost=true after reviewing estimate_quantum_cost output.\n"
                "Tip: validate first on FREE simulators (ionq.simulator, quantinuum.sim.*)."
            ),
        )]

    try:
        # Offload job submission to thread pool
        job = await _run_executor_with_timeout(
            io_executor,
            quantum_state["azure_integration"].submit_circuit,
            circuit,
            backend_name,
            shots,
            f"mcp_{circuit_id}",
            operation="submit_quantum_job",
        )
        return [TextContent(
            type="text",
            text=f"✓ Job submitted to Azure Quantum\nJob ID: {job.id()}\nBackend: {backend_name or 'default'}\nShots: {shots}\n\nNote: Job execution may take several minutes depending on queue."
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error submitting job: {str(e)}")]


async def train_classifier_handler(args: Dict) -> List[TextContent]:
    """Train a quantum classifier (optimized with process pool for CPU-intensive training)"""
    dataset_name = args["dataset"]
    n_qubits = args.get("n_qubits", 4)
    n_layers = args.get("n_layers", 2)
    epochs = args.get("epochs", 50)
    entanglement = args.get("entanglement", "linear")

    # Offload data loading and training to process pool
    result_text = await _run_executor_with_timeout(
        cpu_executor,
        _train_classifier_sync,
        dataset_name,
        n_qubits,
        n_layers,
        epochs,
        entanglement,
        operation="train_quantum_classifier",
    )

    return [TextContent(type="text", text=result_text)]


def _train_classifier_sync(dataset_name: str, n_qubits: int, n_layers: int, epochs: int, entanglement: str) -> str:
    """Synchronous training (runs in process pool)"""
    from sklearn.datasets import load_iris, load_wine, load_breast_cancer, make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import yaml
    config_path: Optional[str] = None

    # Load dataset
    if dataset_name == "iris":
        data = load_iris()
        X, y = data.data, (data.target > 0).astype(int)
    elif dataset_name == "wine":
        data = load_wine()
        X, y = data.data, (data.target > 0).astype(int)
    elif dataset_name == "breast_cancer":
        data = load_breast_cancer()
        X, y = data.data, data.target
    elif dataset_name == "synthetic":
        X, y = make_classification(n_samples=200, n_features=4, n_classes=2, random_state=42)
    else:
        return f"Unknown dataset: {dataset_name}"

    # Prepare data
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    try:
        # Create config
        config = {
            "quantum": {"simulator": {"backend": "qiskit_aer", "shots": 1024}},
            "ml": {
                "model": {"n_qubits": n_qubits, "n_layers": n_layers, "entanglement": entanglement},
                "training": {"epochs": epochs, "batch_size": 16, "learning_rate": 0.01, "validation_split": 0.2},
            },
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name

        qc = QuantumClassifier(config_path=config_path)
        model = HybridQuantumClassifier(input_dim=X.shape[1], quantum_classifier=qc)

        history = train_quantum_model(model, X_train, y_train, X_val, y_val, config_path=config_path)

        final_acc = history["val_acc"][-1]
        final_loss = history["val_loss"][-1]

        return f"""✓ Quantum classifier training completed!

Dataset: {dataset_name}
Architecture:
  - Qubits: {n_qubits}
  - Layers: {n_layers}
  - Entanglement: {entanglement}
  - Epochs: {epochs}

Results:
  - Final Validation Accuracy: {final_acc:.2%}
  - Final Validation Loss: {final_loss:.4f}

Training History:
  - Best Accuracy: {max(history['val_acc']):.2%}
  - Best Loss: {min(history['val_loss']):.4f}
"""

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        return f"Training failed: {str(e)}"
    finally:
        if config_path:
            try:
                Path(config_path).unlink()
            except FileNotFoundError:
                pass


async def estimate_cost_handler(args: Dict) -> List[TextContent]:
    """Estimate quantum job cost (optimized)"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum.")]

    circuit_id = args["circuit_id"]
    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired.")]

    backend_name = args["backend_name"]
    shots = args.get("shots", 100)

    try:
        estimate = await _run_executor_with_timeout(
            io_executor,
            quantum_state["azure_integration"].estimate_cost,
            circuit,
            backend_name,
            shots,
            operation="estimate_quantum_cost",
        )

        cost_info = f"""Cost Estimate for {backend_name}:

Shots: {shots}
Estimated Time: {estimate.get('estimated_time_minutes', 'N/A')} minutes

{estimate.get('note', '')}

Note: Actual costs vary by provider:
  - IonQ: ~$0.00003 per gate-shot
  - Quantinuum: ~$0.00015 per circuit execution
  - Microsoft simulators: Free
"""
        return [TextContent(type="text", text=cost_info)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error estimating cost: {str(e)}")]


async def circuit_properties_handler(args: Dict) -> List[TextContent]:
    """Get circuit properties (optimized with caching)"""
    circuit_id = args["circuit_id"]

    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired.")]

    gate_counts = circuit.count_ops()

    properties = f"""Circuit Properties for {circuit_id}:

Basic Info:
  - Qubits: {circuit.num_qubits}
  - Classical Bits: {circuit.num_clbits}
  - Depth: {circuit.depth()}
  - Size (total gates): {circuit.size()}

Gate Breakdown:
"""
    for gate, count in gate_counts.items():
        properties += f"  - {gate}: {count}\n"

    return [TextContent(type="text", text=properties)]


async def main():
    """Run the MCP server"""
    logger.info("Starting Quantum AI MCP Server (Optimized)...")
    initialize_quantum_resources()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


async def cleanup():
    """Cleanup resources on shutdown"""
    cpu_executor.shutdown(wait=True)
    io_executor.shutdown(wait=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(cleanup())
