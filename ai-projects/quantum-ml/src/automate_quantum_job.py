"""
Automated Azure Quantum job submission, monitoring, and hybrid experiment runner
- Submits a Bell state circuit to IonQ hardware
- Monitors job status and retrieves results
- Can be adapted for hybrid/classical-quantum experiments
"""

import time

from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit

# Load workspace config
ws = Workspace(
    subscription_id="a07fbd16-e722-446d-8efd-0681e85b725c",
    resource_group="rg-quantum-ai",
    workspace_name="quantum-ai-workspace",
    location="eastus",
)

provider = AzureQuantumProvider(ws)
print("Available targets:", [b.name for b in provider.backends()])

# Choose IonQ hardware backend
backend = provider.get_backend("ionq.qpu")

# Create a Bell state circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()

print("Submitting job to IonQ hardware...")
job = backend.run(qc, shots=100)
print(f"Job ID: {job.id()}")

# Monitor job status
TERMINAL_STATUSES = {"Succeeded", "Failed", "Cancelled"}  # O(1) set lookup
while True:
    status = job.status()
    print(f"Job status: {status}")
    if status in TERMINAL_STATUSES:
        break
    time.sleep(10)

if status == "Succeeded":
    result = job.result()
    print("Measurement counts:", result.get_counts())
else:
    print(f"Job did not complete successfully. Status: {status}")

# For hybrid experiments, adapt this script to submit parameterized circuits or use your hybrid model code.
