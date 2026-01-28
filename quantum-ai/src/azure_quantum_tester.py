"""
Azure Quantum Testing Framework
Unified tool for submitting and monitoring quantum circuits on Azure
"""
try:
    from azure.quantum import Workspace
    from azure.quantum.job import Job
    from qiskit import QuantumCircuit, transpile
    from qiskit_qir import to_qir_bitcode
    AZURE_QUANTUM_AVAILABLE = True
except ImportError:
    AZURE_QUANTUM_AVAILABLE = False
    Workspace = None
    QuantumCircuit = None

import time
import yaml
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class AzureQuantumTester:
    """
    Simplified interface for testing circuits on Azure Quantum.
    Supports multiple providers: IonQ, Quantinuum, Rigetti.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Azure Quantum connection.
        
        Args:
            config_path: Path to quantum config YAML
        """
        if not AZURE_QUANTUM_AVAILABLE:
            raise ImportError("Azure Quantum SDK not installed. Install with: pip install azure-quantum qiskit qiskit-qir")
        
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "quantum_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        azure_config = self.config['azure']
        
        self.workspace = Workspace(
            subscription_id=azure_config['subscription_id'],
            resource_group=azure_config['resource_group'],
            name=azure_config['workspace_name'],
            location=azure_config['location']
        )
        
        logger.info(f"Connected to Azure Quantum workspace: {azure_config['workspace_name']}")
    
    def list_targets(self, provider: Optional[str] = None) -> List[Dict]:
        """
        List available quantum targets.
        
        Args:
            provider: Filter by provider (ionq, quantinuum, rigetti, None for all)
            
        Returns:
            List of target information
        """
        targets = self.workspace.get_targets()
        
        target_list = []
        for target in targets:
            info = {
                'id': target.name,
                'provider': target.provider_id,
                'status': target.current_availability,
                'cost': 'Check Azure Portal'
            }
            
            if provider is None or target.provider_id.lower() == provider.lower():
                target_list.append(info)
        
        return target_list
    
    def create_test_circuits(self) -> Dict[str, QuantumCircuit]:
        """
        Create a suite of test circuits.
        
        Returns:
            Dictionary of circuit name -> QuantumCircuit
        """
        circuits = {}
        
        # 1. Bell State (basic entanglement test)
        bell = QuantumCircuit(2, 2, name="bell_state")
        bell.h(0)
        bell.cx(0, 1)
        bell.measure([0, 1], [0, 1])
        circuits['bell'] = bell
        
        # 2. GHZ State (3-qubit entanglement)
        ghz = QuantumCircuit(3, 3, name="ghz_state")
        ghz.h(0)
        ghz.cx(0, 1)
        ghz.cx(0, 2)
        ghz.measure([0, 1, 2], [0, 1, 2])
        circuits['ghz'] = ghz
        
        # 3. Simple VQC (variational circuit)
        vqc = QuantumCircuit(2, 2, name="simple_vqc")
        vqc.ry(0.5, 0)
        vqc.ry(1.0, 1)
        vqc.cx(0, 1)
        vqc.rz(0.3, 0)
        vqc.measure([0, 1], [0, 1])
        circuits['vqc'] = vqc
        
        # 4. Deutsch-Jozsa (quantum algorithm test)
        dj = QuantumCircuit(3, 2, name="deutsch_jozsa")
        dj.x(2)  # Ancilla in |1⟩
        dj.h([0, 1, 2])
        # Oracle (balanced function)
        dj.cx(0, 2)
        dj.cx(1, 2)
        dj.h([0, 1])
        dj.measure([0, 1], [0, 1])
        circuits['deutsch_jozsa'] = dj
        
        return circuits
    
    def submit_circuit(
        self,
        circuit: QuantumCircuit,
        target_name: str = "ionq.simulator",
        shots: int = 100,
        job_name: Optional[str] = None,
        wait: bool = True,
        timeout: int = 300
    ) -> Dict:
        """
        Submit a circuit to Azure Quantum.
        
        Args:
            circuit: Qiskit QuantumCircuit
            target_name: Azure Quantum target (e.g., 'ionq.simulator', 'quantinuum.sim.h1-1sc')
            shots: Number of measurements
            job_name: Job name (auto-generated if None)
            wait: Wait for job completion
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with job info and results
        """
        try:
            # Get target
            target = self.workspace.get_targets(target_name)
            
            logger.info(f"Submitting circuit '{circuit.name}' to {target_name}")
            
            # Convert to QIR
            bitcode = to_qir_bitcode(circuit, name=circuit.name or "circuit")
            
            # Submit job
            if job_name is None:
                job_name = f"{circuit.name}_{int(time.time())}"
            
            job = target.submit(
                input_data=bitcode,
                name=job_name,
                input_data_format="qir.v1",
                output_data_format="microsoft.quantum-results.v1",
                shots=shots
            )
            
            logger.info(f"Job submitted: {job.id}")
            
            if not wait:
                return {
                    'job_id': job.id,
                    'status': job.details.status,
                    'submitted': True
                }
            
            # Wait for completion
            start_time = time.time()
            while job.details.status not in ["Succeeded", "Failed", "Cancelled"]:
                elapsed = int(time.time() - start_time)
                
                if elapsed > timeout:
                    logger.warning(f"Job timeout after {timeout}s")
                    return {
                        'job_id': job.id,
                        'status': 'timeout',
                        'elapsed': elapsed
                    }
                
                time.sleep(5)
                job.refresh()
                logger.info(f"Job status: {job.details.status} ({elapsed}s)")
            
            elapsed = int(time.time() - start_time)
            logger.info(f"Job completed in {elapsed}s: {job.details.status}")
            
            # Get results
            result = {
                'job_id': job.id,
                'status': job.details.status,
                'elapsed': elapsed,
                'target': target_name,
                'shots': shots
            }
            
            if job.details.status == "Succeeded":
                results = job.get_results()
                result['counts'] = dict(results)
                result['success'] = True
                
                # Calculate probabilities
                total = sum(results.values())
                result['probabilities'] = {k: v/total for k, v in results.items()}
                
                logger.info(f"Results: {result['counts']}")
            else:
                result['success'] = False
                result['error'] = job.details.error_data
            
            return result
            
        except Exception as e:
            logger.error(f"Error submitting circuit: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def run_test_suite(
        self,
        target_name: str = "ionq.simulator",
        shots: int = 100
    ) -> Dict[str, Dict]:
        """
        Run the full test suite on a target.
        
        Args:
            target_name: Azure Quantum target
            shots: Number of shots per circuit
            
        Returns:
            Dictionary of circuit_name -> results
        """
        print("=" * 70)
        print(f"  AZURE QUANTUM TEST SUITE - {target_name.upper()}")
        print("=" * 70)
        
        circuits = self.create_test_circuits()
        results = {}
        
        for name, circuit in circuits.items():
            print(f"\n[{len(results)+1}/{len(circuits)}] Testing {name}...")
            print("-" * 70)
            
            result = self.submit_circuit(
                circuit=circuit,
                target_name=target_name,
                shots=shots,
                wait=True
            )
            
            results[name] = result
            
            if result.get('success'):
                print(f"✓ SUCCESS ({result['elapsed']}s)")
                print(f"  Top results: {sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True)[:3]}")
            else:
                print(f"✗ FAILED: {result.get('error', 'Unknown error')}")
        
        # Summary
        print("\n" + "=" * 70)
        print("  TEST SUMMARY")
        print("=" * 70)
        
        successes = sum(1 for r in results.values() if r.get('success'))
        total_time = sum(r.get('elapsed', 0) for r in results.values())
        
        print(f"\nSuccess rate: {successes}/{len(results)} ({successes/len(results)*100:.1f}%)")
        print(f"Total time: {total_time}s")
        print(f"Average time per circuit: {total_time/len(results):.1f}s")
        
        return results
    
    def check_job_status(self, job_id: str) -> Dict:
        """
        Check status of a submitted job.
        
        Args:
            job_id: Azure Quantum job ID
            
        Returns:
            Job status information
        """
        try:
            job = self.workspace.get_job(job_id)
            
            result = {
                'job_id': job_id,
                'status': job.details.status,
                'name': job.details.name,
                'target': job.details.target
            }
            
            if job.details.status == "Succeeded":
                results = job.get_results()
                result['counts'] = dict(results)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            return {'error': str(e)}


def demo():
    """Demonstrate Azure Quantum testing"""
    print("=" * 70)
    print("  AZURE QUANTUM TESTING FRAMEWORK")
    print("=" * 70)
    
    tester = AzureQuantumTester()
    
    # List available targets
    print("\n[1] Available Quantum Targets:")
    print("-" * 70)
    
    targets = tester.list_targets()
    for target in targets[:5]:  # Show first 5
        print(f"  • {target['id']} ({target['provider']}) - {target['status']}")
    
    # Show test circuits
    print("\n[2] Test Circuits:")
    print("-" * 70)
    
    circuits = tester.create_test_circuits()
    for name, circuit in circuits.items():
        print(f"  • {name}: {circuit.num_qubits} qubits, {circuit.depth()} depth")
    
    print("\n[3] Ready to run test suite!")
    print("-" * 70)
    print("\nTo run full test suite:")
    print("  results = tester.run_test_suite(target_name='ionq.simulator', shots=100)")
    print("\nTo submit single circuit:")
    print("  result = tester.submit_circuit(circuits['bell'], 'ionq.simulator')")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
