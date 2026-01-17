# Quantum AI MCP Server

An MCP (Model Context Protocol) server that exposes quantum computing and quantum machine learning capabilities to AI agents and LLMs.

## Features

The Quantum AI MCP server provides 8 powerful tools:

### Quantum Circuit Creation & Simulation

- **create_quantum_circuit** - Build quantum circuits (entanglement, GHZ, Bell states, random, or custom)
- **simulate_quantum_circuit** - Simulate circuits locally with Qiskit Aer
- **get_quantum_circuit_properties** - Analyze circuit depth, gates, and topology

### Azure Quantum Integration

- **connect_azure_quantum** - Connect to Azure Quantum workspace
- **list_quantum_backends** - See available quantum hardware (IonQ, Quantinuum, etc.)
- **submit_quantum_job** - Run circuits on real quantum computers
- **estimate_quantum_cost** - Get cost estimates before running on hardware

### Quantum Machine Learning

- **train_quantum_classifier** - Train hybrid quantum-classical ML models on standard datasets

## Installation

```powershell
cd quantum-ai

# Install base dependencies
pip install -r requirements.txt

# Install MCP dependencies
pip install -r mcp-requirements.txt
```

## Usage

### As a Standalone MCP Server

Run the server directly:

```powershell
python quantum_mcp_server.py
```

### In VS Code with MCP Configuration

Add to your `mcp.json` (in VS Code settings):

```json
{
  "servers": {
    "quantum-ai": {
      "type": "stdio",
      "command": "python",
      "args": [
        "c:\\Users\\Bryan\\OneDrive\\AI\\quantum-ai\\quantum_mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}\\quantum-ai"
      }
    }
  }
}
```

### With Python MCP Client

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["quantum_mcp_server.py"],
        env={}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Create a Bell state circuit
            result = await session.call_tool(
                "create_quantum_circuit",
                {"n_qubits": 2, "circuit_type": "bell"}
            )
            print(result.content[0].text)
            
            # Simulate it
            circuit_id = "..."  # Extract from result
            sim_result = await session.call_tool(
                "simulate_quantum_circuit",
                {"circuit_id": circuit_id, "shots": 1024}
            )
            print(sim_result.content[0].text)

asyncio.run(main())
```

## Example Workflows

### 1. Create and Simulate a Quantum Circuit

```python
# Create a GHZ state (3-qubit entanglement)
result = await session.call_tool(
    "create_quantum_circuit",
    {
        "n_qubits": 3,
        "circuit_type": "ghz"
    }
)

# Extract circuit ID from result
# Then simulate with 10,000 shots
sim_result = await session.call_tool(
    "simulate_quantum_circuit",
    {
        "circuit_id": "<circuit-id>",
        "shots": 10000
    }
)
```

### 2. Train a Quantum Machine Learning Model

```python
# Train on the Iris dataset with quantum circuit
result = await session.call_tool(
    "train_quantum_classifier",
    {
        "dataset": "iris",
        "n_qubits": 4,
        "n_layers": 2,
        "epochs": 100,
        "entanglement": "linear"
    }
)
```

### 3. Run on Azure Quantum Hardware

```python
# Connect to Azure
await session.call_tool(
    "connect_azure_quantum",
    {
        "subscription_id": "<your-sub-id>",
        "resource_group": "rg-quantum-ai",
        "workspace_name": "quantum-ai-workspace"
    }
)

# List available backends
backends = await session.call_tool("list_quantum_backends", {})

# Estimate cost
cost = await session.call_tool(
    "estimate_quantum_cost",
    {
        "circuit_id": "<circuit-id>",
        "backend_name": "ionq.simulator",
        "shots": 100
    }
)

# Submit job
job = await session.call_tool(
    "submit_quantum_job",
    {
        "circuit_id": "<circuit-id>",
        "backend_name": "ionq.simulator",
        "shots": 500
    }
)
```

## Tool Reference

### create_quantum_circuit

**Parameters:**

- `n_qubits` (int, required) - Number of qubits (1-20)
- `circuit_type` (string, required) - Type: "entanglement", "ghz", "bell", "random", "custom"
- `gates` (array, optional) - For custom circuits: `[{"gate": "h", "qubit": 0}, {"gate": "cx", "qubits": [0,1]}]`

**Returns:** Circuit ID, diagram, QASM, depth, and gate count

### simulate_quantum_circuit

**Parameters:**

- `circuit_id` (string, required) - ID from create_quantum_circuit
- `shots` (int, optional, default=1024) - Number of measurements (1-100,000)

**Returns:** Measurement probability distribution

### train_quantum_classifier

**Parameters:**

- `dataset` (string, required) - "iris", "wine", "breast_cancer", or "synthetic"
- `n_qubits` (int, optional, default=4) - Quantum circuit qubits (2-10)
- `n_layers` (int, optional, default=2) - Variational layers (1-5)
- `epochs` (int, optional, default=50) - Training epochs (1-200)
- `entanglement` (string, optional, default="linear") - "linear", "circular", or "full"

**Returns:** Training metrics, final accuracy, and loss

### connect_azure_quantum

**Parameters:**

- `subscription_id` (string, required) - Azure subscription ID
- `resource_group` (string, required) - Resource group name
- `workspace_name` (string, required) - Quantum workspace name

**Returns:** Connection confirmation

**Note:** Requires Azure credentials configured via `az login` or environment variables.

## Prerequisites for Azure Quantum

1. **Azure subscription** with Quantum workspace deployed
2. **Azure CLI authentication**: Run `az login` before using Azure tools
3. **Workspace configuration**: Update `config/quantum_config.yaml` with your Azure details

See `azure/DEPLOYMENT.md` for full deployment guide.

## Cost Considerations

- **Local simulation** (Qiskit Aer): **Free**
- **Microsoft simulators** on Azure: **Free**
- **IonQ hardware**: ~$0.00003 per gate-shot
- **Quantinuum hardware**: ~$0.00015 per circuit execution

Always use `estimate_quantum_cost` before submitting to paid hardware!

## Architecture

The MCP server maintains:

- **Circuit cache**: Stores created circuits by ID for reuse
- **Azure connection**: Persistent connection to Azure Quantum workspace
- **Quantum classifier**: Pre-initialized for ML training

All operations are stateful within a session.

## Troubleshooting

**"Circuit ID not found"**: Create a circuit with `create_quantum_circuit` first, then use the returned ID.

**"Not connected to Azure Quantum"**: Call `connect_azure_quantum` before using Azure tools.

**Import errors**: Ensure you've installed both `requirements.txt` and `mcp-requirements.txt`.

**Authentication errors**: Run `az login` and verify your Azure subscription has access to the Quantum workspace.

## Development

To extend the MCP server:

1. Add new tool definitions to `list_tools()`
2. Implement handler functions (e.g., `async def my_tool_handler(args)`)
3. Register handler in `call_tool()` dispatcher
4. Update this README with usage examples

## License

Same as parent quantum-ai project (MIT).
