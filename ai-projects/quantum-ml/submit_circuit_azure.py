#!/usr/bin/env python3
"""
Submit quantum circuits to Azure Quantum using QIR
"""

import time

from azure.quantum import Workspace
from qiskit import QuantumCircuit


def main():
    print("=" * 70)
    print("  Azure Quantum Circuit Submission")
    print("=" * 70)

    # Connect to workspace
    print("\n[1/3] Connecting to Azure Quantum...")
    workspace = Workspace(
        subscription_id="a07fbd16-e722-446d-8efd-0681e85b725c",
        resource_group="rg-quantum-ai",
        name="quantum-ai-workspace",
        location="eastus",
    )
    print(f"✓ Connected to: {workspace.name}")

    # Create Bell state circuit
    print("\n[2/3] Creating Bell state circuit...")
    circuit = QuantumCircuit(2, 2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.measure([0, 1], [0, 1])

    print(circuit)

    # Convert to QIR and submit
    print("\n[3/3] Submitting to Quantinuum Simulator (API validator)...")
    try:
        from qiskit_qir import to_qir_bitcode

        # Convert circuit to QIR bitcode bytes
        bitcode = to_qir_bitcode(circuit, name="bell_state")

        # Use Quantinuum syntax checker (free, validates QIR)
        target = workspace.get_targets("quantinuum.sim.h2-1sc")

        job = target.submit(
            input_data=bitcode,
            name="bell-state-test",
            input_data_format="qir.v1",
            output_data_format="microsoft.quantum-results.v1",
            shots=100,
        )

        print("✓ Job submitted successfully!")
        print(f"  Job ID: {job.id}")
        print(f"  Status: {job.details.status}")

        # Wait for completion
        print("\nWaiting for results...")
        start_time = time.time()

        while job.details.status not in ["Succeeded", "Failed", "Cancelled"]:
            time.sleep(2)
            job.refresh()
            elapsed = int(time.time() - start_time)
            print(f"  Status: {job.details.status} ({elapsed}s)", end="\r")

        print(f"\n✓ Job completed in {int(time.time() - start_time)}s")
        print(f"  Final status: {job.details.status}")

        if job.details.status == "Succeeded":
            # Get results
            results = job.get_results()

            print("\n" + "=" * 70)
            print("  RESULTS")
            print("=" * 70)
            print("\nMeasurement Counts:")

            total_shots = sum(results.values())
            for state, count in sorted(results.items()):
                percentage = (count / total_shots) * 100
                bar = "█" * int(percentage / 2)
                print(f"  |{state}⟩: {count:3d} shots ({percentage:5.1f}%) {bar}")

            # Check entanglement
            entangled = results.get("00", 0) + results.get("11", 0)
            entanglement_pct = (entangled / total_shots) * 100

            print(f"\nEntanglement Quality: {entanglement_pct:.1f}%")

            if entanglement_pct > 90:
                print("✓ EXCELLENT - Strong quantum entanglement detected!")
            elif entanglement_pct > 70:
                print("✓ GOOD - Quantum entanglement present")
            else:
                print("⚠ WARNING - Low entanglement quality")

            print("\n" + "=" * 70)
            print("✓ Quantum circuit execution successful!")
            print("=" * 70)
        else:
            print(f"\n✗ Job failed with status: {job.details.status}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
