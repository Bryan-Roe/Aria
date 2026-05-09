#!/usr/bin/env python3
"""
Submit Q# quantum circuit to Azure Quantum
"""

import time

from azure.quantum import Workspace

# Simple Q# Bell state program
QSHARP_BELL_STATE = """
namespace AzureQuantumTest {
    @EntryPoint()
    operation BellState() : (Result, Result) {
        use (q1, q2) = (Qubit(), Qubit());
        H(q1);
        CNOT(q1, q2);
        let r1 = M(q1);
        let r2 = M(q2);
        Reset(q1);
        Reset(q2);
        return (r1, r2);
    }
}
"""


def main():
    print("=" * 70)
    print("  Azure Quantum Q# Circuit Submission")
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

    # Show Q# program
    print("\n[2/3] Q# Bell State Program:")
    print(QSHARP_BELL_STATE)

    # Submit to Quantinuum syntax checker (free)
    print("\n[3/3] Submitting to Quantinuum Syntax Checker (FREE)...")
    try:
        target = workspace.get_targets("quantinuum.sim.h2-1sc")

        job = target.submit(
            input_data=QSHARP_BELL_STATE,
            name="qsharp-bell-test",
            input_data_format="qsharp.v1",
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

            # Count classical bit patterns
            counts = {}
            for result in results:
                # Q# returns tuples of Results
                key = str(result)
                counts[key] = counts.get(key, 0) + 1

            total_shots = sum(counts.values())
            for state, count in sorted(counts.items()):
                percentage = (count / total_shots) * 100
                bar = "█" * int(percentage / 2)
                print(f"  {state}: {count:3d} shots ({percentage:5.1f}%) {bar}")

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
