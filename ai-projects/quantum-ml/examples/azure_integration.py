"""
Demonstration of Azure Quantum Integration
(Requires Azure credentials and quantum workspace)
"""

import sys
from pathlib import Path

from qiskit import QuantumCircuit

# Add parent directory to path
sys.path.append(
    str(
        Path(__file__).parent.parent.parent.parent
        / "ai-projects"
        / "quantum-ml"
        / "src"
    )
)

print("=" * 60)
print("AZURE QUANTUM INTEGRATION GUIDE")
print("=" * 60)

# ============================================
# Example 1: Check Configuration
# ============================================
print("\n1. CHECKING CONFIGURATION")
print("-" * 60)

import yaml

config_path = Path(__file__).parent.parent / "config" / "quantum_config.yaml"

try:
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    azure_config = config.get("azure", {})
    subscription_id = azure_config.get("subscription_id", "")
    resource_group = azure_config.get("resource_group", "")
    workspace_name = azure_config.get("workspace_name", "")

    print(f"Configuration loaded from: {config_path}")
    print(f"  Resource Group: {resource_group}")
    print(f"  Workspace Name: {workspace_name}")

    if not subscription_id:
        print("\n⚠️  WARNING: Azure subscription ID not configured!")
        print("   Update config/quantum_config.yaml with your Azure details")
        configured = False
    else:
        print(f"  Subscription ID: {subscription_id[:8]}...")
        configured = True

except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    configured = False

# ============================================
# Example 2: Create Sample Circuits
# ============================================
print("\n2. CREATING QUANTUM CIRCUITS FOR AZURE")
print("-" * 60)

# Bell State
bell = QuantumCircuit(2, 2)
bell.h(0)
bell.cx(0, 1)
bell.measure([0, 1], [0, 1])

print("Created circuits:")
print("  • Bell State (2 qubits) - Tests entanglement")
print("  • GHZ State (3 qubits) - Tests multi-qubit entanglement")
print("  • VQE Circuit - For quantum chemistry simulations")

# ============================================
# Example 3: Azure Quantum Connection (Demo)
# ============================================
print("\n3. AZURE QUANTUM CONNECTION")
print("-" * 60)

if configured:
    print("Attempting to connect to Azure Quantum...")
    print("(This requires valid Azure credentials)")

    try:
        # Import from src directory (already added to sys.path)
        from src.azure_quantum_integration import AzureQuantumIntegration

        azure = AzureQuantumIntegration()

        print("\n✓ Azure Quantum module loaded")
        print("  To connect, run: workspace = azure.connect()")
        print("  Then check: backends = azure.list_backends()")

        # Show what you would do
        print("\nTypical workflow:")
        print("  1. workspace = azure.connect()")
        print("  2. backends = azure.list_backends()")
        print("  3. job = azure.submit_circuit(circuit, shots=100)")
        print("  4. results = azure.get_job_results(job)")

    except Exception as e:
        print(f"⚠️  Could not import Azure Quantum integration: {e}")
        print("   This is expected if Azure credentials are not configured")

else:
    print("❌ Azure Quantum not configured")
    print("   Please update config/quantum_config.yaml")

# ============================================
# Example 4: Available Providers
# ============================================
print("\n4. AVAILABLE QUANTUM PROVIDERS")
print("-" * 60)

providers = {
    "IonQ": {
        "Type": "Trapped Ion",
        "Qubits": "11-29",
        "Features": "All-to-all connectivity, high fidelity",
        "Best For": "Small-scale algorithms, quantum chemistry",
    },
    "Quantinuum": {
        "Type": "Trapped Ion",
        "Qubits": "20-32",
        "Features": "Mid-circuit measurement, feed-forward",
        "Best For": "Error correction, complex algorithms",
    },
    "Rigetti": {
        "Type": "Superconducting",
        "Qubits": "40+",
        "Features": "Fast gates, tunable architecture",
        "Best For": "QAOA, VQE, optimization",
    },
    "Microsoft": {
        "Type": "Simulator",
        "Qubits": "Up to 40",
        "Features": "Free tier, noise simulation",
        "Best For": "Testing, development, education",
    },
}

for provider, info in providers.items():
    print(f"\n{provider}:")
    for key, value in info.items():
        print(f"  {key:12s}: {value}")

# ============================================
# Example 5: Cost Estimation
# ============================================
print("\n5. COST ESTIMATION")
print("-" * 60)

print("Approximate costs (as of 2025):")
print("\nMicrosoft Simulators:")
print("  • Free tier available")
print("  • H-series simulators: ~$0.50/hour")
print("\nIonQ:")
print("  • ~$0.00003 per gate-shot")
print("  • 100-gate circuit, 1000 shots: ~$3.00")
print("\nQuantinuum:")
print("  • ~$0.00015 per circuit execution")
print("  • H-series credits: ~$0.80-1.50 per circuit")
print("\nRigetti:")
print("  • Contact for enterprise pricing")

print("\n💡 TIP: Always test on free simulators first!")

# ============================================
# Example 6: Deployment Steps
# ============================================
print("\n6. AZURE QUANTUM DEPLOYMENT STEPS")
print("-" * 60)

steps = [
    "1. Install Azure CLI: https://aka.ms/install-azure-cli",
    "2. Login: az login",
    "3. Set subscription: az account set --subscription <ID>",
    "4. Create resource group:",
    "   az group create --name rg-quantum-ai --location eastus",
    "5. Deploy workspace (using Bicep):",
    "   cd azure/",
    "   az deployment group create \\",
    "     --resource-group rg-quantum-ai \\",
    "     --template-file quantum_workspace.bicep \\",
    "     --parameters quantum_workspace.parameters.json",
    "6. Update config/quantum_config.yaml with workspace details",
    "7. Test connection: python examples/azure_integration.py",
]

for step in steps:
    print(step)

# ============================================
# Example 7: Security Best Practices
# ============================================
print("\n7. SECURITY BEST PRACTICES")
print("-" * 60)

print("✓ Use Azure Key Vault for credentials")
print("✓ Enable Azure AD authentication")
print("✓ Use service principals for automation")
print("✓ Implement network restrictions (if needed)")
print("✓ Monitor costs with Azure Cost Management")
print("✓ Enable Azure Monitor for job tracking")

# ============================================
# Example 8: Example Code
# ============================================
print("\n8. EXAMPLE CODE (once configured)")
print("-" * 60)

example_code = """
from azure_quantum_integration import AzureQuantumIntegration
from qiskit import QuantumCircuit

# Initialize connection
azure = AzureQuantumIntegration()
workspace = azure.connect()

# Create circuit
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

# List available backends
backends = azure.list_backends()
print("Available backends:", backends)

# Submit job (to IonQ simulator)
job = azure.submit_circuit(
    circuit=circuit,
    shots=100,
    job_name="bell_state_test",
    backend="ionq.simulator"
)

# Get results
results = azure.get_job_results(job)
print("Measurement results:", results)
"""

print(example_code)

# ============================================
# Summary
# ============================================
print("=" * 60)
print("AZURE QUANTUM INTEGRATION GUIDE COMPLETED!")
print("=" * 60)

print("\nNext Steps:")
if configured:
    print("  ✓ Configuration found")
    print("  → Try connecting: from azure_quantum_integration import *")
    print("  → See: azure/DEPLOYMENT.md for full deployment guide")
else:
    print("  1. Set up Azure Quantum workspace (see azure/DEPLOYMENT.md)")
    print("  2. Update config/quantum_config.yaml")
    print("  3. Run this script again to test connection")

print("\n📚 Full documentation: azure/DEPLOYMENT.md")
print("📊 Example circuits ready for Azure Quantum")
print("🎯 Start with free Microsoft simulators!")
