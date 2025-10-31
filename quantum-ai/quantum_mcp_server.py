"""
Quantum AI MCP Server
Exposes quantum computing and quantum machine learning capabilities via Model Context Protocol
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import quantum modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from quantum_classifier import QuantumClassifier, HybridQuantumClassifier
from azure_quantum_integration import AzureQuantumIntegration, create_sample_circuit
import numpy as np
import torch
from qiskit import QuantumCircuit

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("quantum-ai-mcp")

# Global state for quantum resources
quantum_state = {
    "azure_integration": None,
    "quantum_classifier": None,
    "circuit_cache": {},
}


def initialize_quantum_resources():
    """Initialize quantum computing resources"""
    try:
        quantum_state["quantum_classifier"] = QuantumClassifier()
        logger.info("Quantum classifier initialized")
    except Exception as e:
        logger.warning(f"Could not initialize quantum classifier: {e}")


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
    """Create a quantum circuit based on parameters"""
    n_qubits = args["n_qubits"]
    circuit_type = args["circuit_type"]
    
    if circuit_type == "entanglement":
        circuit = create_sample_circuit(n_qubits)
    elif circuit_type == "bell":
        circuit = QuantumCircuit(2, 2)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.measure([0, 1], [0, 1])
    elif circuit_type == "ghz":
        circuit = QuantumCircuit(n_qubits, n_qubits)
        circuit.h(0)
        for i in range(n_qubits - 1):
            circuit.cx(i, i + 1)
        circuit.measure(range(n_qubits), range(n_qubits))
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
    elif circuit_type == "custom" and "gates" in args:
        circuit = QuantumCircuit(n_qubits, n_qubits)
        for gate_spec in args["gates"]:
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
                if gate_name == "cx" or gate_name == "cnot":
                    circuit.cx(qubits[0], qubits[1])
                elif gate_name == "cz":
                    circuit.cz(qubits[0], qubits[1])
        circuit.measure(range(n_qubits), range(n_qubits))
    else:
        return [TextContent(type="text", text="Invalid circuit type or missing gates for custom type")]
    
    # Generate circuit ID
    import hashlib
    circuit_id = hashlib.md5(str(circuit).encode()).hexdigest()[:12]
    
    # Cache the circuit
    quantum_state["circuit_cache"][circuit_id] = circuit
    
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


async def simulate_circuit_handler(args: Dict) -> List[TextContent]:
    """Simulate a quantum circuit locally"""
    circuit_id = args["circuit_id"]
    shots = args.get("shots", 1024)
    
    if circuit_id not in quantum_state["circuit_cache"]:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found. Create a circuit first.")]
    
    circuit = quantum_state["circuit_cache"][circuit_id]
    
    # Simulate using Qiskit Aer
    from qiskit_aer import AerSimulator
    simulator = AerSimulator()
    job = simulator.run(circuit, shots=shots)
    result = job.result()
    counts = result.get_counts()
    
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


async def connect_azure_handler(args: Dict) -> List[TextContent]:
    """Connect to Azure Quantum workspace"""
    try:
        # Create temporary config
        import yaml
        import tempfile
        
        config = {
            "azure": {
                "subscription_id": args["subscription_id"],
                "resource_group": args["resource_group"],
                "workspace_name": args["workspace_name"],
            },
            "quantum": {"provider": "ionq", "hardware": {"shots": 500, "optimization_level": 2}},
            "ml": {"model": {"n_qubits": 4, "n_layers": 2, "entanglement": "linear"}},
            "logging": {"level": "INFO", "results_dir": "./results"},
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        azure_int = AzureQuantumIntegration(config_path=config_path)
        workspace = azure_int.connect()
        quantum_state["azure_integration"] = azure_int
        
        return [TextContent(
            type="text",
            text=f"✓ Connected to Azure Quantum workspace: {args['workspace_name']}\nResource Group: {args['resource_group']}"
        )]
        
    except Exception as e:
        return [TextContent(type="text", text=f"Failed to connect to Azure Quantum: {str(e)}")]


async def list_backends_handler(args: Dict) -> List[TextContent]:
    """List available quantum backends"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum. Use connect_azure_quantum first.")]
    
    try:
        backends = quantum_state["azure_integration"].list_backends()
        backend_list = "\n".join(f"  • {backend}" for backend in backends)
        return [TextContent(type="text", text=f"Available quantum backends:\n\n{backend_list}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error listing backends: {str(e)}")]


async def submit_job_handler(args: Dict) -> List[TextContent]:
    """Submit a quantum job to Azure Quantum"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum. Use connect_azure_quantum first.")]
    
    circuit_id = args["circuit_id"]
    if circuit_id not in quantum_state["circuit_cache"]:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found.")]
    
    circuit = quantum_state["circuit_cache"][circuit_id]
    backend_name = args.get("backend_name")
    shots = args.get("shots", 500)
    
    try:
        job = quantum_state["azure_integration"].submit_circuit(
            circuit, backend_name=backend_name, shots=shots, job_name=f"mcp_{circuit_id}"
        )
        return [TextContent(
            type="text",
            text=f"✓ Job submitted to Azure Quantum\nJob ID: {job.id()}\nBackend: {backend_name or 'default'}\nShots: {shots}\n\nNote: Job execution may take several minutes depending on queue."
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Error submitting job: {str(e)}")]


async def train_classifier_handler(args: Dict) -> List[TextContent]:
    """Train a quantum classifier"""
    dataset_name = args["dataset"]
    n_qubits = args.get("n_qubits", 4)
    n_layers = args.get("n_layers", 2)
    epochs = args.get("epochs", 50)
    entanglement = args.get("entanglement", "linear")
    
    # Load dataset
    from sklearn.datasets import load_iris, load_wine, load_breast_cancer, make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    if dataset_name == "iris":
        data = load_iris()
        X, y = data.data, (data.target > 0).astype(int)  # Binary classification
    elif dataset_name == "wine":
        data = load_wine()
        X, y = data.data, (data.target > 0).astype(int)
    elif dataset_name == "breast_cancer":
        data = load_breast_cancer()
        X, y = data.data, data.target
    elif dataset_name == "synthetic":
        X, y = make_classification(n_samples=200, n_features=4, n_classes=2, random_state=42)
    else:
        return [TextContent(type="text", text=f"Unknown dataset: {dataset_name}")]
    
    # Prepare data
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train model
    try:
        from quantum_classifier import train_quantum_model
        
        # Update config temporarily
        import yaml
        import tempfile
        
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
        
        result_text = f"""✓ Quantum classifier training completed!

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
        
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        return [TextContent(type="text", text=f"Training failed: {str(e)}")]


async def estimate_cost_handler(args: Dict) -> List[TextContent]:
    """Estimate quantum job cost"""
    if quantum_state["azure_integration"] is None:
        return [TextContent(type="text", text="Not connected to Azure Quantum.")]
    
    circuit_id = args["circuit_id"]
    if circuit_id not in quantum_state["circuit_cache"]:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found.")]
    
    circuit = quantum_state["circuit_cache"][circuit_id]
    backend_name = args["backend_name"]
    shots = args.get("shots", 100)
    
    try:
        estimate = quantum_state["azure_integration"].estimate_cost(circuit, backend_name, shots)
        
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
    """Get circuit properties"""
    circuit_id = args["circuit_id"]
    
    if circuit_id not in quantum_state["circuit_cache"]:
        return [TextContent(type="text", text=f"Circuit ID '{circuit_id}' not found.")]
    
    circuit = quantum_state["circuit_cache"][circuit_id]
    
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
    logger.info("Starting Quantum AI MCP Server...")
    initialize_quantum_resources()
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
