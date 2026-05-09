"""
Example MCP Client for Quantum AI
Demonstrates how to use the Quantum AI MCP server from Python
"""

import asyncio
import os
from contextlib import AsyncExitStack
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Optional: Azure AI for chat with tools
try:
    from azure.ai.inference import ChatCompletionsClient  # type: ignore
    from azure.ai.inference.models import AssistantMessage  # type: ignore
    from azure.ai.inference.models import (SystemMessage, ToolMessage,
                                           UserMessage)
    from azure.core.credentials import AzureKeyCredential  # type: ignore

    HAS_AZURE_AI = True
except ImportError:
    HAS_AZURE_AI = False
    # Note: azure-ai-inference is optional for basic MCP client usage
    # Install if you want to use Azure AI chat features:
    # pip install azure-ai-inference azure-core


class QuantumMCPClient:
    """Client for interacting with Quantum AI MCP server"""

    def __init__(self, server_script_path: str = "quantum_mcp_server.py"):
        self.server_script_path = server_script_path
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Connect to the Quantum AI MCP server"""
        server_params = StdioServerParameters(
            command="python", args=[self.server_script_path], env=os.environ.copy()
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )
        await self.session.initialize()

        print("✓ Connected to Quantum AI MCP server")

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(f"✓ Available tools: {[tool.name for tool in tools]}\n")

    async def create_circuit(self, n_qubits: int, circuit_type: str, **kwargs) -> str:
        """Create a quantum circuit"""
        args = {"n_qubits": n_qubits, "circuit_type": circuit_type}
        args.update(kwargs)

        result = await self.session.call_tool("create_quantum_circuit", args)
        print(result.content[0].text)

        # Extract circuit ID from response
        text = result.content[0].text
        for line in text.split("\n"):
            if "Circuit ID:" in line:
                return line.split("Circuit ID:")[1].strip().split()[0]
        return None

    async def simulate_circuit(self, circuit_id: str, shots: int = 1024):
        """Simulate a quantum circuit"""
        result = await self.session.call_tool(
            "simulate_quantum_circuit", {"circuit_id": circuit_id, "shots": shots}
        )
        print(result.content[0].text)

    async def train_classifier(self, dataset: str, **kwargs):
        """Train a quantum classifier"""
        args = {"dataset": dataset}
        args.update(kwargs)

        result = await self.session.call_tool("train_quantum_classifier", args)
        print(result.content[0].text)

    async def connect_azure(
        self, subscription_id: str, resource_group: str, workspace_name: str
    ):
        """Connect to Azure Quantum"""
        result = await self.session.call_tool(
            "connect_azure_quantum",
            {
                "subscription_id": subscription_id,
                "resource_group": resource_group,
                "workspace_name": workspace_name,
            },
        )
        print(result.content[0].text)

    async def list_backends(self):
        """List available quantum backends"""
        result = await self.session.call_tool("list_quantum_backends", {})
        print(result.content[0].text)

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def example_basic_workflow():
    """Example: Create and simulate a Bell state"""
    print("=" * 60)
    print("Example 1: Create and Simulate a Bell State")
    print("=" * 60 + "\n")

    client = QuantumMCPClient()

    try:
        await client.connect()

        # Create a Bell state circuit
        circuit_id = await client.create_circuit(n_qubits=2, circuit_type="bell")

        print("\n" + "-" * 60 + "\n")

        # Simulate with 10,000 shots
        await client.simulate_circuit(circuit_id, shots=10000)

    finally:
        await client.cleanup()


async def example_ghz_state():
    """Example: Create and simulate a 5-qubit GHZ state"""
    print("\n" + "=" * 60)
    print("Example 2: 5-Qubit GHZ State (Maximally Entangled)")
    print("=" * 60 + "\n")

    client = QuantumMCPClient()

    try:
        await client.connect()

        # Create GHZ state
        circuit_id = await client.create_circuit(n_qubits=5, circuit_type="ghz")

        print("\n" + "-" * 60 + "\n")

        # Simulate
        await client.simulate_circuit(circuit_id, shots=5000)

    finally:
        await client.cleanup()


async def example_quantum_ml():
    """Example: Train a quantum classifier on Iris dataset"""
    print("\n" + "=" * 60)
    print("Example 3: Quantum Machine Learning on Iris Dataset")
    print("=" * 60 + "\n")

    client = QuantumMCPClient()

    try:
        await client.connect()

        # Train quantum classifier
        await client.train_classifier(
            dataset="iris", n_qubits=4, n_layers=2, epochs=30, entanglement="linear"
        )

    finally:
        await client.cleanup()


async def example_custom_circuit():
    """Example: Build a custom circuit with specific gates"""
    print("\n" + "=" * 60)
    print("Example 4: Custom Quantum Circuit")
    print("=" * 60 + "\n")

    client = QuantumMCPClient()

    try:
        await client.connect()

        # Create custom circuit
        circuit_id = await client.create_circuit(
            n_qubits=3,
            circuit_type="custom",
            gates=[
                {"gate": "h", "qubit": 0},
                {"gate": "h", "qubit": 1},
                {"gate": "h", "qubit": 2},
                {"gate": "cx", "qubits": [0, 1]},
                {"gate": "cx", "qubits": [1, 2]},
                {"gate": "x", "qubit": 0},
            ],
        )

        print("\n" + "-" * 60 + "\n")

        # Simulate
        await client.simulate_circuit(circuit_id, shots=2048)

    finally:
        await client.cleanup()


async def example_azure_quantum():
    """Example: Connect to Azure Quantum (requires credentials)"""
    print("\n" + "=" * 60)
    print("Example 5: Azure Quantum Connection")
    print("=" * 60 + "\n")

    # Check for Azure credentials
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        print("⚠ Skipping Azure example - AZURE_SUBSCRIPTION_ID not set")
        print("Set environment variables to run this example:")
        print("  $env:AZURE_SUBSCRIPTION_ID = '<your-subscription-id>'")
        return

    client = QuantumMCPClient()

    try:
        await client.connect()

        # Connect to Azure Quantum
        await client.connect_azure(
            subscription_id=subscription_id,
            resource_group="rg-quantum-ai",
            workspace_name="quantum-ai-workspace",
        )

        print("\n" + "-" * 60 + "\n")

        # List available backends
        await client.list_backends()

    except Exception as e:
        print(f"Azure connection failed: {e}")
        print("\nMake sure you have:")
        print("  1. Run 'az login'")
        print("  2. Deployed Azure Quantum workspace (see azure/DEPLOYMENT.md)")
        print("  3. Updated environment variables")

    finally:
        await client.cleanup()


async def main():
    """Run all examples"""
    print("\n🔬 Quantum AI MCP Client Examples\n")

    # Run examples
    await example_basic_workflow()
    await example_ghz_state()
    await example_quantum_ml()
    await example_custom_circuit()
    await example_azure_quantum()

    print("\n" + "=" * 60)
    print("✓ All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
