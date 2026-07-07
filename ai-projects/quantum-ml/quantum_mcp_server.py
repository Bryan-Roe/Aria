"""
Quantum AI MCP Server (Optimized)
Exposes quantum computing and quantum machine learning capabilities via Model Context Protocol
"""

import asyncio
import logging
import re

# Add src directory to path before importing local modules
import sys
import time
from collections import OrderedDict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

try:
    import qiskit
except ImportError:
    print("Error: qiskit package not installed or incompatible version.")
    print("\nTo install qiskit, run:")
    print("  pip install qiskit")
    sys.exit(1)

try:
    from qiskit import qasm2 as qiskit_qasm2
except ImportError:
    qiskit_qasm2 = None

src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Verify src directory exists
if not src_path.exists():
    print(f"Error: src/ directory not found at {src_path}")
    print("Please ensure the following directory structure exists:")
    print("  ai-projects/quantum-ml/")
    print("    ├── quantum_mcp_server.py")
    print("    └── src/")
    print("        ├── quantum_classifier.py")
    print("        └── azure_quantum_integration.py")
    sys.exit(1)

# Import MCP dependencies
try:
    import mcp.server  # type: ignore
    from mcp.server.stdio import stdio_server  # type: ignore
    from mcp.types import TextContent, Tool  # type: ignore
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
    from azure_quantum_integration import AzureQuantumIntegration, create_sample_circuit
    from quantum_classifier import HybridQuantumClassifier, QuantumClassifier, train_quantum_model
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


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = mcp.server.Server("quantum-ai-mcp")

# Thread pool for CPU-bound operations
cpu_executor = ProcessPoolExecutor(max_workers=2)
io_executor = ThreadPoolExecutor(max_workers=4)


class CircuitCache:
    """LRU cache with TTL for quantum circuits"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.timestamps = {}

    def get(self, key: str) -> qiskit.QuantumCircuit | None:
        if key not in self.cache:
            return None

        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl_seconds:
            self._evict(key)
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, circuit: qiskit.QuantumCircuit):
        if key in self.cache:
            self.cache[key] = circuit
            self.cache.move_to_end(key)
        else:
            self.cache[key] = circuit
        # Refresh TTL on every put, including updates.
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
        expired = [key for key, timestamp in self.timestamps.items() if current_time - timestamp > self.ttl_seconds]
        for key in expired:
            self._evict(key)
        return len(expired)  # Return count for logging


# Cost-gating configuration to prevent Azure billing DoS
MAX_COST_PER_JOB_USD = 10.0  # Max cost per single job submission ($)
# Max cumulative cost per session ($)
MAX_CUMULATIVE_COST_PER_SESSION_USD = 100.0
COST_ESTIMATE_MULTIPLIER = 1.2  # Apply 20% margin to estimated costs for safety

# Cost provider rates (empirically based, in USD per gate-shot)
COST_RATES = {
    "ionq": 0.00003,  # IonQ: ~$0.00003 per gate-shot
    "quantinuum": 0.00015,  # Quantinuum: ~$0.00015 per circuit execution
    "microsoft": 0.0,  # Microsoft simulators: free
    "simulator": 0.0,  # Local simulator: free
}

# How long a cached backend list is considered fresh (seconds)
BACKEND_CACHE_TTL_SECONDS = 3600

# Safety limits (simulator-first, bounded resource usage)
MAX_LOCAL_QUBITS = 10
MAX_SHOTS_PER_CALL = 1000
OPERATION_TIMEOUT_SECONDS = 60.0

FREE_BACKEND_KEYWORDS = (
    "simulator",
    "resource_estimator",
    "resource-estimator",
    "aer",
    "local",
)

PAID_BACKEND_KEYWORDS = (
    "ionq",
    "quantinuum",
    "rigetti",
    "pasqal",
    "qpu",
)

# Global state for quantum resources
quantum_state = {
    "azure_integration": None,
    "quantum_classifier": None,
    "circuit_cache": CircuitCache(max_size=100, ttl_seconds=3600),
    "config_cache": {},  # Cache YAML configs to avoid repeated temp file creation
    "last_cache_cleanup": time.time(),  # Track last cleanup time
    "cumulative_cost_usd": 0.0,  # Track cumulative cost across session
    "known_backends": [],  # Cached allowlist from Azure workspace
    "known_backends_refreshed_at": 0.0,
}


def _cleanup_cache_if_needed():
    """Periodically clean expired circuits from cache (called before operations)"""
    current_time = time.time()
    # Run cleanup every 10 minutes
    if current_time - quantum_state["last_cache_cleanup"] > 600:
        expired_count = quantum_state["circuit_cache"].clear_expired()
        if expired_count > 0:
            logging.info(f"[quantum_mcp] Cleaned {expired_count} expired circuits from cache")
        quantum_state["last_cache_cleanup"] = current_time


def _normalize_backend_name(backend_name: str | None) -> str:
    """Normalize backend names for matching and pricing."""
    return (backend_name or "").strip().lower()


def _normalize_required_string(value: Any) -> str | None:
    """Return a trimmed non-empty string, or None when invalid."""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _text_response(message: str) -> list[TextContent]:
    """Return a standard text response payload."""
    return [TextContent(type="text", text=message)]


def _export_circuit_qasm(circuit: qiskit.QuantumCircuit) -> str:
    """Export a circuit to OpenQASM with compatibility across Qiskit versions."""
    if qiskit_qasm2 is not None and hasattr(qiskit_qasm2, "dumps"):
        try:
            return qiskit_qasm2.dumps(circuit)
        except Exception as exc:
            logger.warning("QASM2 export via qiskit.qasm2.dumps failed: %s", exc)

    qasm_method = getattr(circuit, "qasm", None)
    if callable(qasm_method):
        try:
            return qasm_method()
        except Exception as exc:
            logger.warning("QASM export via QuantumCircuit.qasm failed: %s", exc)

    raise RuntimeError("OpenQASM export is unavailable for this Qiskit installation")


def _require_string_arg(args: dict, key: str) -> tuple[str | None, list[TextContent] | None]:
    """Validate a required string argument from tool args."""
    value = _normalize_required_string(args.get(key))
    if value is None:
        return None, _text_response(f"{key} is required")
    return value, None


def _parse_shots_arg(args: dict, *, default: int) -> tuple[int | None, list[TextContent] | None]:
    """Validate and normalize shots argument for bounded execution safety."""
    shots = args.get("shots", default)
    if isinstance(shots, bool) or not isinstance(shots, int) or not (1 <= shots <= MAX_SHOTS_PER_CALL):
        return (
            None,
            _text_response(f"shots must be an integer between 1 and {MAX_SHOTS_PER_CALL}"),
        )
    return shots, None


def _is_free_backend(backend_name: str | None) -> bool:
    """Return True when the backend is simulator-like and should not incur cost."""
    normalized = _normalize_backend_name(backend_name)
    if not normalized:
        return False

    # Token-level "sim" match to avoid accidental substring matches.
    tokens = [t for t in re.split(r"[^a-z0-9]+", normalized) if t]
    if "sim" in tokens:
        return True

    return any(keyword in normalized for keyword in FREE_BACKEND_KEYWORDS)


def _requires_cost_confirmation(backend_name: str | None) -> bool:
    """Paid or unknown non-simulator backends require explicit confirmation."""
    normalized = _normalize_backend_name(backend_name)
    if not normalized:
        return False
    # Simulators are free even when provider-qualified (e.g., ionq.simulator).
    if _is_free_backend(normalized):
        return False
    # Everything else is gated. This covers known paid QPUs (see
    # PAID_BACKEND_KEYWORDS) *and* unrecognized backends: an unknown backend may
    # be paid, so as a deliberate fail-safe we never auto-approve it.
    return True


def _estimate_job_cost_sync(circuit, backend_name: str, shots: int) -> float:
    """Estimate job cost synchronously (runs in thread pool).

    Returns estimated cost in USD.
    """
    # Normalize backend name for cost lookup
    backend_key = _normalize_backend_name(backend_name)

    if _is_free_backend(backend_key):
        rate = 0.0
    elif "ionq" in backend_key:
        rate = COST_RATES["ionq"]
    elif "quantinuum" in backend_key:
        rate = COST_RATES["quantinuum"]
    else:
        # Unknown non-simulator backend: use the most conservative known paid rate.
        rate = max(rate for rate in COST_RATES.values() if rate > 0)

    # Estimate gates in circuit
    gate_ops = circuit.count_ops()
    total_gates = sum(gate_ops.values())

    # Cost = (gates * shots * rate)
    estimated_cost = total_gates * shots * rate

    return max(0.0, estimated_cost)  # Never negative


def _normalize_backend_allowlist(backends: list[str]) -> set[str]:
    """Normalize allowlist for membership checks."""
    return {
        _normalize_backend_name(name) for name in backends if isinstance(name, str) and _normalize_backend_name(name)
    }


def _backend_in_allowlist(normalized_backend: str, normalized_backends: set[str]) -> bool:
    """Return True when backend is directly allowed or accepted via simulator aliases."""
    if normalized_backend in normalized_backends:
        return True

    # Accept common simulator aliases (e.g., "simulator") when the workspace
    # exposes a provider-qualified simulator backend such as "microsoft.simulator".
    if _is_free_backend(normalized_backend) and normalized_backend == "simulator":
        return any("simulator" in backend for backend in normalized_backends)

    return False


async def _validate_backend_against_allowlist(backend_name: str) -> str | None:
    """Ensure a backend exists in the cached workspace allowlist, refreshing as needed."""
    loop = asyncio.get_event_loop()

    # Backend allowlist enforcement — refresh when empty or stale.
    known_backends = quantum_state.get("known_backends") or []
    cache_age = time.time() - quantum_state.get("known_backends_refreshed_at", 0.0)
    cache_stale = cache_age > BACKEND_CACHE_TTL_SECONDS
    did_refresh_allowlist = False
    if not known_backends or cache_stale:
        try:
            known_backends = await loop.run_in_executor(
                io_executor,
                quantum_state["azure_integration"].list_backends,
            )
            quantum_state["known_backends"] = list(known_backends)
            quantum_state["known_backends_refreshed_at"] = time.time()
            did_refresh_allowlist = True
        except Exception as e:
            return (
                f"Unable to verify backend '{backend_name}' against workspace backends ({e}). "
                "Run list_quantum_backends first, then retry submission."
            )

    normalized_backends = _normalize_backend_allowlist(known_backends)
    normalized_backend = _normalize_backend_name(backend_name)
    refresh_error = None
    if not _backend_in_allowlist(normalized_backend, normalized_backends) and not did_refresh_allowlist:
        # One-time recheck: backend inventories can change between cached refreshes.
        try:
            refreshed_backends = await loop.run_in_executor(
                io_executor,
                quantum_state["azure_integration"].list_backends,
            )
            quantum_state["known_backends"] = list(refreshed_backends)
            quantum_state["known_backends_refreshed_at"] = time.time()
            normalized_backends = _normalize_backend_allowlist(refreshed_backends)
        except Exception as e:
            refresh_error = str(e)

    if not _backend_in_allowlist(normalized_backend, normalized_backends):
        allowed_sample = ", ".join(sorted(normalized_backends)[:12])
        refresh_note = f" Backend list refresh failed: {refresh_error}." if refresh_error else ""
        return (
            f"Backend '{backend_name}' is not in the workspace allowlist. "
            f"Allowed backends: {allowed_sample or '(none)'}"
            f"{refresh_note}"
        )

    return None


def initialize_quantum_resources():
    """Initialize quantum computing resources"""
    try:
        quantum_state["quantum_classifier"] = QuantumClassifier()
        logger.info("Quantum classifier initialized")
    except Exception as e:
        logger.warning(f"Could not initialize quantum classifier: {e}")


@app.list_tools()
async def list_tools() -> list[Tool]:
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
                        "maximum": MAX_LOCAL_QUBITS,
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
                        "maximum": MAX_SHOTS_PER_CALL,
                        "default": MAX_SHOTS_PER_CALL,
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
                    "confirm_cost": {
                        "type": "boolean",
                        "description": "Required for paid or unknown non-simulator backends. Confirm that cost has been reviewed.",
                        "default": False,
                    },
                    "shots": {
                        "type": "integer",
                        "description": "Number of measurement shots",
                        "minimum": 1,
                        "maximum": MAX_SHOTS_PER_CALL,
                        "default": 500,
                    },
                },
                "required": ["circuit_id", "backend_name"],
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
                        "minimum": 1,
                        "maximum": MAX_SHOTS_PER_CALL,
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
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    try:
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            return [TextContent(type="text", text="Invalid arguments: expected an object")]

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


async def create_circuit_handler(args: dict) -> list[TextContent]:
    """Create a quantum circuit based on parameters (optimized with async execution)"""
    # Periodic cache cleanup to prevent memory leaks
    _cleanup_cache_if_needed()

    n_qubits = args.get("n_qubits")
    circuit_type = args.get("circuit_type")

    # Runtime validation (do not rely only on tool schema).
    if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or not (1 <= n_qubits <= MAX_LOCAL_QUBITS):
        return [
            TextContent(
                type="text",
                text=f"n_qubits must be an integer between 1 and {MAX_LOCAL_QUBITS}",
            )
        ]
    if circuit_type not in {"entanglement", "ghz", "bell", "random", "custom"}:
        return [
            TextContent(
                type="text",
                text="circuit_type must be one of: entanglement, ghz, bell, random, custom",
            )
        ]

    # Offload circuit creation to thread pool for CPU-intensive operations
    loop = asyncio.get_event_loop()
    try:
        # Add timeout to prevent hanging (CRITICAL FIX)
        circuit = await asyncio.wait_for(
            loop.run_in_executor(
                io_executor,
                _create_circuit_sync,
                n_qubits,
                circuit_type,
                args.get("gates"),
            ),
            timeout=OPERATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return [
            TextContent(
                type="text",
                text=f"Circuit creation timed out after {int(OPERATION_TIMEOUT_SECONDS)}s",
            )
        ]

    if circuit is None:
        return [
            TextContent(
                type="text",
                text="Invalid circuit type or missing gates for custom type",
            )
        ]

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
        "qasm": _export_circuit_qasm(circuit),
        "diagram": str(circuit.draw(output="text")),
    }

    return [
        TextContent(
            type="text",
            text=f"Created quantum circuit:\n\n```\n{result['diagram']}\n```\n\nCircuit ID: {circuit_id}\nDepth: {result['depth']}, Gates: {result['gate_count']}",
        )
    ]


def _create_circuit_sync(n_qubits: int, circuit_type: str, gates: list | None = None) -> qiskit.QuantumCircuit | None:
    """Synchronous circuit creation (runs in thread pool)"""
    if circuit_type == "entanglement":
        return create_sample_circuit(n_qubits)
    elif circuit_type == "bell":
        circuit = qiskit.QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
        return circuit
    elif circuit_type == "ghz":
        circuit = qiskit.QuantumCircuit(n_qubits, n_qubits)
        circuit.h(0)
        for i in range(n_qubits - 1):
            circuit.cx(i, i + 1)
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    elif circuit_type == "random":
        circuit = qiskit.QuantumCircuit(n_qubits, n_qubits)
        import random

        for _ in range(n_qubits * 2):
            gate = random.choice(["h", "x", "y", "z", "rx", "ry", "rz"])  # noqa: S311
            qubit = random.randint(0, n_qubits - 1)  # noqa: S311
            if gate == "h":
                circuit.h(qubit)
            elif gate == "x":
                circuit.x(qubit)
            elif gate == "y":
                circuit.y(qubit)
            elif gate == "z":
                circuit.z(qubit)
            else:
                circuit.rx(np.pi / 4, qubit)
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    elif circuit_type == "custom" and gates:
        circuit = qiskit.QuantumCircuit(n_qubits, n_qubits)
        for gate_spec in gates:
            if not isinstance(gate_spec, dict):
                continue
            gate_name = str(gate_spec.get("gate", "")).lower()
            if not gate_name:
                continue
            if "qubit" in gate_spec:
                qubit = gate_spec["qubit"]
                # Validate qubit index is within circuit bounds.
                if not isinstance(qubit, int) or not (0 <= qubit < n_qubits):
                    continue
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
                # Validate both qubit indices and require two distinct qubits.
                if (
                    not isinstance(qubits, list)
                    or len(qubits) < 2
                    or not all(isinstance(q, int) and 0 <= q < n_qubits for q in qubits[:2])
                    or qubits[0] == qubits[1]
                ):
                    continue
                if gate_name in ["cx", "cnot"]:
                    circuit.cx(qubits[0], qubits[1])
                elif gate_name == "cz":
                    circuit.cz(qubits[0], qubits[1])
        circuit.measure(range(n_qubits), range(n_qubits))
        return circuit
    return None


async def simulate_circuit_handler(args: dict) -> list[TextContent]:
    """Simulate a quantum circuit locally (optimized with async execution)"""
    circuit_id, circuit_id_error = _require_string_arg(args, "circuit_id")
    if circuit_id_error:
        return circuit_id_error

    shots, shots_error = _parse_shots_arg(args, default=MAX_SHOTS_PER_CALL)
    if shots_error:
        return shots_error

    # Narrow optional helper outputs for static typing.
    assert circuit_id is not None
    assert shots is not None

    # Clean expired cache entries periodically
    _cleanup_cache_if_needed()

    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [
            TextContent(
                type="text",
                text=f"Circuit ID '{circuit_id}' not found or expired. Create a circuit first.",
            )
        ]

    # Offload simulation (process pool first; thread fallback if process execution fails)
    loop = asyncio.get_event_loop()
    try:
        counts = await asyncio.wait_for(
            loop.run_in_executor(cpu_executor, _simulate_circuit_sync, circuit, shots),
            timeout=OPERATION_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return [
            TextContent(
                type="text",
                text=f"Circuit simulation timed out after {int(OPERATION_TIMEOUT_SECONDS)}s",
            )
        ]
    except Exception as exc:
        logger.warning("Process-pool simulation failed (%s). Retrying in thread pool.", exc)
        try:
            counts = await asyncio.wait_for(
                loop.run_in_executor(io_executor, _simulate_circuit_sync, circuit, shots),
                timeout=OPERATION_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return [
                TextContent(
                    type="text",
                    text=f"Circuit simulation timed out after {int(OPERATION_TIMEOUT_SECONDS)}s",
                )
            ]
        except Exception as fallback_exc:
            return [TextContent(type="text", text=f"Error running circuit simulation: {fallback_exc}")]

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


def _simulate_circuit_sync(circuit: qiskit.QuantumCircuit, shots: int) -> dict:
    """Synchronous circuit simulation (runs in process pool)"""
    from qiskit_aer import AerSimulator

    simulator = AerSimulator()
    job = simulator.run(circuit, shots=shots)
    result = job.result()
    return result.get_counts()


async def connect_azure_handler(args: dict) -> list[TextContent]:
    """Connect to Azure Quantum workspace (optimized with config caching)"""
    subscription_id = _normalize_required_string(args.get("subscription_id"))
    resource_group = _normalize_required_string(args.get("resource_group"))
    workspace_name = _normalize_required_string(args.get("workspace_name"))

    if subscription_id is None:
        return [TextContent(type="text", text="subscription_id is required")]
    if resource_group is None:
        return [TextContent(type="text", text="resource_group is required")]
    if workspace_name is None:
        return [TextContent(type="text", text="workspace_name is required")]

    try:
        # Check config cache to avoid repeated temp file creation
        config_key = f"{subscription_id}_{resource_group}_{workspace_name}"

        if config_key not in quantum_state["config_cache"]:
            # Create config in-memory instead of temp file
            config = {
                "azure": {
                    "subscription_id": subscription_id,
                    "resource_group": resource_group,
                    "workspace_name": workspace_name,
                },
                "quantum": {
                    "provider": "ionq",
                    "hardware": {"shots": 500, "optimization_level": 2},
                },
                "ml": {"model": {"n_qubits": 4, "n_layers": 2, "entanglement": "linear"}},
                "logging": {"level": "INFO", "results_dir": "./results"},
            }
            quantum_state["config_cache"][config_key] = config

        # Offload Azure connection to thread pool (I/O bound)
        loop = asyncio.get_event_loop()
        azure_int = await loop.run_in_executor(
            io_executor, _connect_azure_sync, quantum_state["config_cache"][config_key]
        )
        quantum_state["azure_integration"] = azure_int
        quantum_state["cumulative_cost_usd"] = 0.0
        quantum_state["known_backends"] = []
        quantum_state["known_backends_refreshed_at"] = 0.0

        return [
            TextContent(
                type="text",
                text=f"✓ Connected to Azure Quantum workspace: {workspace_name}\nResource Group: {resource_group}\nCost budget reset: ${quantum_state['cumulative_cost_usd']:.2f}",
            )
        ]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to connect to Azure Quantum: {str(e)}")]


def _connect_azure_sync(config: dict) -> AzureQuantumIntegration:
    """Synchronous Azure connection (runs in thread pool)"""
    import os
    import tempfile

    import yaml

    # Write config to a temp file; always clean it up regardless of success/failure
    # to prevent credentials lingering on disk.
    fd, config_path = tempfile.mkstemp(suffix=".yaml")
    try:
        with os.fdopen(fd, "w") as f:
            yaml.safe_dump(config, f)
        azure_int = AzureQuantumIntegration(config_path=config_path)
        azure_int.connect()
        return azure_int
    finally:
        try:
            os.unlink(config_path)
        except OSError:
            pass


async def list_backends_handler(args: dict) -> list[TextContent]:
    """List available quantum backends (optimized with async I/O)"""
    if quantum_state["azure_integration"] is None:
        return [
            TextContent(
                type="text",
                text="Not connected to Azure Quantum. Use connect_azure_quantum first.",
            )
        ]

    try:
        # Offload to thread pool
        loop = asyncio.get_event_loop()
        backends = await loop.run_in_executor(io_executor, quantum_state["azure_integration"].list_backends)
        quantum_state["known_backends"] = list(backends)
        quantum_state["known_backends_refreshed_at"] = time.time()
        backend_list = "\n".join(f"  • {backend}" for backend in backends)
        return [TextContent(type="text", text=f"Available quantum backends:\n\n{backend_list}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing backends: {str(e)}")]


async def submit_job_handler(args: dict) -> list[TextContent]:
    """Submit a quantum job to Azure Quantum with cost-gating (optimized)"""
    circuit_id, circuit_id_error = _require_string_arg(args, "circuit_id")
    if circuit_id_error:
        return circuit_id_error

    backend_name, backend_name_error = _require_string_arg(args, "backend_name")
    if backend_name_error:
        return backend_name_error

    confirm_cost = args.get("confirm_cost", False)
    shots, shots_error = _parse_shots_arg(args, default=500)

    if not isinstance(confirm_cost, bool):
        return _text_response("confirm_cost must be a boolean")
    if shots_error:
        return shots_error

    # Narrow optional helper outputs for static typing.
    assert circuit_id is not None
    assert backend_name is not None
    assert shots is not None

    if quantum_state["azure_integration"] is None:
        return [
            TextContent(
                type="text",
                text="Not connected to Azure Quantum. Use connect_azure_quantum first.",
            )
        ]

    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired.")]

    allowlist_error = await _validate_backend_against_allowlist(backend_name)
    if allowlist_error:
        return [TextContent(type="text", text=allowlist_error)]

    loop = asyncio.get_event_loop()

    # Cost-gating: estimate cost and validate against budget limits
    try:
        estimated_cost = await loop.run_in_executor(io_executor, _estimate_job_cost_sync, circuit, backend_name, shots)

        if _requires_cost_confirmation(backend_name) and not confirm_cost:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"Paid-backend confirmation required for '{backend_name}'. "
                        f"Review the estimated cost with estimate_quantum_cost first, then resubmit with confirm_cost=true. "
                        f"Estimated cost before safety margin: ${estimated_cost:.2f}."
                    ),
                )
            ]

        # Apply safety multiplier and check against limits
        safeguarded_cost = estimated_cost * COST_ESTIMATE_MULTIPLIER
        if safeguarded_cost > MAX_COST_PER_JOB_USD:
            return [
                TextContent(
                    type="text",
                    text=f"Cost limit exceeded: Estimated cost ${safeguarded_cost:.2f} exceeds max ${MAX_COST_PER_JOB_USD:.2f} per job. Reduce shots or use a simulator backend.",
                )
            ]
        if quantum_state["cumulative_cost_usd"] + safeguarded_cost > MAX_CUMULATIVE_COST_PER_SESSION_USD:
            return [
                TextContent(
                    type="text",
                    text=f"Session budget exceeded: Current cost ${quantum_state['cumulative_cost_usd']:.2f} + this job ${safeguarded_cost:.2f} would exceed max ${MAX_CUMULATIVE_COST_PER_SESSION_USD:.2f} per session.",
                )
            ]

        # Cost gates passed, proceed with submission
        job = await loop.run_in_executor(
            io_executor,
            quantum_state["azure_integration"].submit_circuit,
            circuit,
            backend_name,
            shots,
            f"mcp_{circuit_id}",
        )
        quantum_state["cumulative_cost_usd"] += safeguarded_cost
        return [
            TextContent(
                type="text",
                text=f"✓ Job submitted to Azure Quantum\nJob ID: {job.id()}\nBackend: {backend_name or 'default'}\nShots: {shots}\nEstimated Cost: ${safeguarded_cost:.2f}\nSession Total: ${quantum_state['cumulative_cost_usd']:.2f}\n\nNote: Job execution may take several minutes depending on queue.",
            )
        ]
    except Exception as e:
        return [TextContent(type="text", text=f"Error submitting job: {str(e)}")]


async def train_classifier_handler(args: dict) -> list[TextContent]:
    """Train a quantum classifier (optimized with process pool for CPU-intensive training)"""
    dataset_name = args.get("dataset")
    n_qubits = args.get("n_qubits", 4)
    n_layers = args.get("n_layers", 2)
    epochs = args.get("epochs", 50)
    entanglement = args.get("entanglement", "linear")

    if dataset_name not in {"iris", "wine", "breast_cancer", "synthetic"}:
        return [
            TextContent(
                type="text",
                text="dataset must be one of: iris, wine, breast_cancer, synthetic",
            )
        ]
    if isinstance(n_qubits, bool) or not isinstance(n_qubits, int) or not (2 <= n_qubits <= 10):
        return [TextContent(type="text", text="n_qubits must be an integer between 2 and 10")]
    if isinstance(n_layers, bool) or not isinstance(n_layers, int) or not (1 <= n_layers <= 5):
        return [TextContent(type="text", text="n_layers must be an integer between 1 and 5")]
    if isinstance(epochs, bool) or not isinstance(epochs, int) or not (1 <= epochs <= 200):
        return [TextContent(type="text", text="epochs must be an integer between 1 and 200")]
    if entanglement not in {"linear", "circular", "full"}:
        return [TextContent(type="text", text="entanglement must be one of: linear, circular, full")]

    # Offload data loading and training to process pool
    loop = asyncio.get_event_loop()
    result_text = await loop.run_in_executor(
        cpu_executor,
        _train_classifier_sync,
        dataset_name,
        n_qubits,
        n_layers,
        epochs,
        entanglement,
    )

    return [TextContent(type="text", text=result_text)]


def _train_classifier_sync(dataset_name: str, n_qubits: int, n_layers: int, epochs: int, entanglement: str) -> str:
    """Synchronous training (runs in process pool)"""
    import tempfile

    import yaml
    from sklearn.datasets import load_breast_cancer, load_iris, load_wine, make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

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
            "quantum": {
                "simulator": {
                    "backend": "qiskit_aer",
                    "shots": MAX_SHOTS_PER_CALL,
                }
            },
            "ml": {
                "model": {
                    "n_qubits": n_qubits,
                    "n_layers": n_layers,
                    "entanglement": entanglement,
                },
                "training": {
                    "epochs": epochs,
                    "batch_size": 16,
                    "learning_rate": 0.01,
                    "validation_split": 0.2,
                },
            },
        }

        import os

        fd, config_path = tempfile.mkstemp(suffix=".yaml")
        try:
            with os.fdopen(fd, "w") as f:
                yaml.safe_dump(config, f)
            qc = QuantumClassifier(config_path=config_path)
            model = HybridQuantumClassifier(input_dim=X.shape[1], quantum_classifier=qc)
            history = train_quantum_model(model, X_train, y_train, X_val, y_val, config_path=config_path)
        finally:
            try:
                os.unlink(config_path)
            except OSError:
                pass

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
  - Best Accuracy: {max(history["val_acc"]):.2%}
  - Best Loss: {min(history["val_loss"]):.4f}
"""

    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        return f"Training failed: {str(e)}"


async def estimate_cost_handler(args: dict) -> list[TextContent]:
    """Estimate quantum job cost (optimized)"""
    circuit_id, circuit_id_error = _require_string_arg(args, "circuit_id")
    if circuit_id_error:
        return circuit_id_error

    backend_name, backend_name_error = _require_string_arg(args, "backend_name")
    if backend_name_error:
        return backend_name_error

    shots, shots_error = _parse_shots_arg(args, default=100)
    if shots_error:
        return shots_error

    # Narrow optional helper outputs for static typing.
    assert circuit_id is not None
    assert backend_name is not None
    assert shots is not None

    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum.")]

    circuit = quantum_state["circuit_cache"].get(circuit_id)
    if circuit is None:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found or expired.")]

    allowlist_error = await _validate_backend_against_allowlist(backend_name)
    if allowlist_error:
        return [TextContent(type="text", text=allowlist_error)]

    try:
        heuristic_cost = _estimate_job_cost_sync(circuit, backend_name, shots)
        safeguarded_cost = heuristic_cost * COST_ESTIMATE_MULTIPLIER
        loop = asyncio.get_event_loop()
        estimate = await loop.run_in_executor(
            io_executor,
            quantum_state["azure_integration"].estimate_cost,
            circuit,
            backend_name,
            shots,
        )

        cost_info = f"""Cost Estimate for {backend_name}:

Shots: {shots}
Estimated Time: {estimate.get("estimated_time_minutes", "N/A")} minutes
    Heuristic Price Estimate: ${heuristic_cost:.2f}
    Submission Guardrail Ceiling: ${safeguarded_cost:.2f}

{estimate.get("note", "")}

Note: Actual costs vary by provider:
  - IonQ: ~$0.00003 per gate-shot
  - Quantinuum: ~$0.00015 per circuit execution
  - Microsoft simulators: Free
"""
        return [TextContent(type="text", text=cost_info)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error estimating cost: {str(e)}")]


async def circuit_properties_handler(args: dict) -> list[TextContent]:
    """Get circuit properties (optimized with caching)"""
    circuit_id = _normalize_required_string(args.get("circuit_id"))

    if circuit_id is None:
        return [TextContent(type="text", text="circuit_id is required")]

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
