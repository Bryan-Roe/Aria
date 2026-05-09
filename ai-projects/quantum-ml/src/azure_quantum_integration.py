"""
Azure Quantum Integration Module
Provides integration with Azure Quantum services for running quantum circuits
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from azure.identity import DefaultAzureCredential
from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
from qiskit import QuantumCircuit, transpile

logger = logging.getLogger(__name__)


class AzureQuantumIntegration:
    """
    Manages connection and job submission to Azure Quantum workspace.
    """

    def __init__(self, config_path: str = "./config/quantum_config.yaml"):
        """
        Initialize Azure Quantum connection.

        Args:
            config_path: Path to configuration file
        """
        # Handle both relative and absolute paths, and resolve from script location
        config_file = Path(config_path)
        if not config_file.is_absolute():
            # Try relative to quantum-ai directory
            quantum_ai_dir = Path(__file__).parent.parent
            config_file = quantum_ai_dir / config_path

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        with open(config_file, "r") as f:
            self.config = yaml.safe_load(f)

        self.azure_config = self.config["azure"]
        self.quantum_config = self.config["quantum"]

        self.workspace: Optional[Workspace] = None
        self.provider: Optional[AzureQuantumProvider] = None

        logger.info("Azure Quantum Integration initialized")

    def connect(self, credential: Optional[Any] = None) -> Workspace:
        """
        Connect to Azure Quantum workspace.

        Args:
            credential: Azure credential (uses DefaultAzureCredential if None)

        Returns:
            Connected workspace
        """
        if credential is None:
            credential = DefaultAzureCredential()

        try:
            self.workspace = Workspace(
                subscription_id=self.azure_config["subscription_id"],
                resource_group=self.azure_config["resource_group"],
                name=self.azure_config["workspace_name"],
                location=self.azure_config["location"],
                credential=credential,
            )

            logger.info(
                f"Connected to Azure Quantum workspace: {self.azure_config['workspace_name']}"
            )

            # Initialize provider
            self.provider = AzureQuantumProvider(self.workspace)

            return self.workspace

        except Exception as e:
            logger.error(f"Failed to connect to Azure Quantum: {str(e)}")
            raise

    def list_backends(self) -> List[str]:
        """
        List available quantum backends in the workspace.

        Returns:
            List of backend names
        """
        if self.provider is None:
            raise RuntimeError("Not connected to Azure Quantum. Call connect() first.")

        backends = self.provider.backends()
        backend_names = [backend.name() for backend in backends]

        logger.info(f"Available backends: {', '.join(backend_names)}")
        return backend_names

    def get_backend(self, backend_name: Optional[str] = None):
        """
        Get a specific quantum backend.

        Args:
            backend_name: Name of the backend (uses config default if None)

        Returns:
            Quantum backend
        """
        if self.provider is None:
            raise RuntimeError("Not connected to Azure Quantum. Call connect() first.")

        if backend_name is None:
            # Use provider from config
            provider = self.quantum_config["provider"]
            backends = self.provider.backends()

            # Prefer simulators by default to avoid unintended costs
            preferred = None
            fallback = None
            for backend in backends:
                name = backend.name().lower()
                if provider.lower() in name:
                    if "sim" in name or "simulator" in name:
                        preferred = backend.name()
                        break
                    # Track first provider match as fallback (likely QPU)
                    if fallback is None:
                        fallback = backend.name()

            backend_name = preferred or fallback or backends[0].name()

        backend = self.provider.get_backend(backend_name)
        logger.info(f"Using backend: {backend_name}")

        return backend

    def submit_circuit(
        self,
        circuit: QuantumCircuit,
        backend_name: Optional[str] = None,
        shots: Optional[int] = None,
        job_name: Optional[str] = None,
    ) -> Any:
        """
        Submit a quantum circuit to Azure Quantum.

        Args:
            circuit: Qiskit quantum circuit
            backend_name: Target backend
            shots: Number of shots (uses config default if None)
            job_name: Optional job name

        Returns:
            Job object
        """
        if shots is None:
            shots = self.quantum_config["hardware"]["shots"]

        backend = self.get_backend(backend_name)

        # Transpile circuit for backend
        transpiled_circuit = transpile(
            circuit,
            backend=backend,
            optimization_level=self.quantum_config["hardware"]["optimization_level"],
        )

        # Submit job
        job = backend.run(transpiled_circuit, shots=shots)

        if job_name:
            logger.info(f"Submitted job '{job_name}': {job.id()}")
        else:
            logger.info(f"Submitted job: {job.id()}")

        return job

    def get_job_results(self, job) -> Dict:
        """
        Retrieve results from a completed job.

        Args:
            job: Job object

        Returns:
            Job results as dictionary
        """
        logger.info(f"Waiting for job {job.id()} to complete...")
        result = job.result()

        counts = result.get_counts()
        logger.info(f"Job completed. Results: {counts}")

        return {"job_id": job.id(), "counts": counts, "success": result.success}

    def save_results(self, results: Dict, filename: str):
        """
        Save job results to file.

        Args:
            results: Results dictionary
            filename: Output filename
        """
        results_dir = Path(self.config["logging"]["results_dir"])
        results_dir.mkdir(parents=True, exist_ok=True)

        filepath = results_dir / filename
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to {filepath}")

    def estimate_cost(
        self, circuit: QuantumCircuit, backend_name: str, shots: int = 100
    ) -> Dict:
        """
        Estimate the cost of running a circuit.

        Args:
            circuit: Quantum circuit
            backend_name: Target backend
            shots: Number of shots

        Returns:
            Cost estimation
        """
        backend = self.get_backend(backend_name)

        # Get pricing info from backend
        try:
            # This is a simplified estimation
            # Actual pricing depends on provider and may vary
            estimation = {
                "backend": backend_name,
                "shots": shots,
                "estimated_time_minutes": 5,  # Placeholder
                "note": "Actual cost depends on Azure Quantum pricing for the selected provider",
            }

            logger.info(f"Cost estimation: {estimation}")
            return estimation

        except Exception as e:
            logger.warning(f"Could not estimate cost: {str(e)}")
            return {"error": str(e)}


class QuantumJobManager:
    """
    Manages multiple quantum jobs and tracks their status.
    """

    def __init__(self, azure_integration: AzureQuantumIntegration):
        """
        Initialize job manager.

        Args:
            azure_integration: Azure Quantum integration instance
        """
        self.azure = azure_integration
        self.jobs: Dict[str, Any] = {}

    def submit_batch(
        self,
        circuits: List[QuantumCircuit],
        backend_name: Optional[str] = None,
        shots: Optional[int] = None,
        job_names: Optional[List[str]] = None,
    ) -> List[Any]:
        """
        Submit multiple circuits as a batch.

        Args:
            circuits: List of quantum circuits
            backend_name: Target backend
            shots: Number of shots per circuit
            job_names: Optional names for each job

        Returns:
            List of job objects
        """
        if job_names is None:
            job_names = [f"job_{i}" for i in range(len(circuits))]

        jobs = []
        for circuit, name in zip(circuits, job_names):
            job = self.azure.submit_circuit(circuit, backend_name, shots, name)
            self.jobs[name] = job
            jobs.append(job)

        logger.info(f"Submitted batch of {len(circuits)} circuits")
        return jobs

    def check_status(self, job_name: str) -> str:
        """
        Check the status of a job.

        Args:
            job_name: Name of the job

        Returns:
            Job status
        """
        if job_name not in self.jobs:
            raise ValueError(f"Job '{job_name}' not found")

        job = self.jobs[job_name]
        status = job.status()

        logger.info(f"Job '{job_name}' status: {status}")
        return status.name

    def get_all_results(self) -> Dict[str, Dict]:
        """
        Get results for all completed jobs.

        Returns:
            Dictionary mapping job names to results
        """
        results = {}

        for job_name, job in self.jobs.items():
            try:
                result = self.azure.get_job_results(job)
                results[job_name] = result
            except Exception as e:
                logger.warning(f"Could not get results for '{job_name}': {str(e)}")
                results[job_name] = {"error": str(e)}

        return results


def create_sample_circuit(n_qubits: int = 3) -> QuantumCircuit:
    """
    Create a sample quantum circuit for testing.

    Args:
        n_qubits: Number of qubits

    Returns:
        Quantum circuit
    """
    circuit = QuantumCircuit(n_qubits, n_qubits)

    # Create a simple entangled state
    circuit.h(0)
    for i in range(n_qubits - 1):
        circuit.cx(i, i + 1)

    # Measure all qubits
    circuit.measure(range(n_qubits), range(n_qubits))

    return circuit


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize Azure Quantum integration
    azure = AzureQuantumIntegration()

    try:
        # Connect to workspace
        workspace = azure.connect()

        # List available backends
        backends = azure.list_backends()

        # Create and submit a sample circuit
        circuit = create_sample_circuit(n_qubits=3)

        print("Sample quantum circuit created:")
        print(circuit)

        # Uncomment to actually submit (requires valid Azure credentials)
        # job = azure.submit_circuit(circuit, shots=100, job_name="test_job")
        # results = azure.get_job_results(job)
        # azure.save_results(results, "test_results.json")

    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        print("\nNote: To actually submit jobs, ensure you have:")
        print("1. Valid Azure credentials configured")
        print("2. An Azure Quantum workspace created")
        print("3. Updated config/quantum_config.yaml with your workspace details")
