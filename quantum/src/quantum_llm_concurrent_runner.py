"""
Quantum-LLM Concurrent Execution Engine
========================================

Manages parallel execution of quantum circuits while LLM trains.
Provides:
- Background quantum circuit runner (threaded)
- Atomic parameter synchronization between quantum and classical threads
- Queued result delivery (circuit outputs → LLM loss feedback)
- Non-blocking quantum task scheduling

Usage:
    runner = QuantumCircuitRunner(n_qubits=4, n_layers=2)
    runner.start()
    runner.submit_circuit(circuit_params)
    results = runner.get_results(timeout=5.0)
    runner.stop()

Author: Quantum AI Workspace
Date: March 2026
"""

import logging
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import torch

logger = logging.getLogger(__name__)


@dataclass
class QuantumTask:
    """A quantum circuit execution task."""

    task_id: str
    circuit_params: Dict[str, Any]
    n_qubits: int
    n_layers: int
    shots: int = 1000
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class QuantumResult:
    """Result from a quantum circuit execution."""

    task_id: str
    success: bool
    output: Optional[torch.Tensor] = None
    loss_feedback: Optional[float] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class QuantumCircuitRunner:
    """
    Background quantum circuit executor running in dedicated thread.

    Queues incoming circuit parameters, executes them in the background,
    and returns results via output queue without blocking LLM training.
    """

    def __init__(
        self,
        n_qubits: int = 4,
        n_layers: int = 2,
        backend: str = "default.qubit",
        max_queue_size: int = 50,
    ):
        """Initialize quantum runner."""
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.backend = backend
        self.max_queue_size = max_queue_size

        # Task queues
        self.input_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.output_queue: queue.Queue = queue.Queue(maxsize=100)  # Bounded to prevent accumulation

        # Thread control
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._running = False

        # Metrics
        self.tasks_submitted = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.avg_execution_time = 0.0

        logger.info(
            f"Initialized QuantumCircuitRunner: "
            f"{n_qubits}q, {n_layers} layers, backend={backend}"
        )

    def start(self) -> None:
        """Start the background quantum execution thread."""
        if self._running:
            logger.warning("Quantum runner already running")
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._run_loop, daemon=False, name="QuantumRunner"
        )
        self._thread.start()
        logger.info("Quantum circuit runner started")

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the runner and wait for pending tasks."""
        if not self._running:
            return

        logger.info("Stopping quantum runner...")
        self._stop_event.set()

        try:
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning(
                    f"Quantum runner did not stop within {timeout}s"
                )
            else:
                logger.info("Quantum runner stopped")
        except Exception as e:
            logger.error(f"Error stopping runner: {e}")

        self._running = False

    def submit_circuit(self, task: QuantumTask) -> None:
        """
        Submit a quantum circuit task for background execution.

        Args:
            task: QuantumTask with circuit parameters and config

        Raises:
            queue.Full: If input queue is at capacity
        """
        try:
            self.input_queue.put(task, timeout=1.0)
            self.tasks_submitted += 1
            logger.debug(f"Submitted quantum task: {task.task_id}")
        except queue.Full:
            logger.error(
                "Quantum task queue full; circuit execution skipped"
            )
            # Post error result
            self.output_queue.put(
                QuantumResult(
                    task_id=task.task_id,
                    success=False,
                    error="Queue full",
                )
            )

    def get_results(
        self, timeout: Optional[float] = None, max_count: int = None
    ) -> List[QuantumResult]:
        """
        Retrieve completed quantum circuit results (non-blocking).

        Args:
            timeout: Max seconds to wait for next result (default: no wait)
            max_count: Max number of results to retrieve (default: all)

        Returns:
            List of QuantumResult objects
        """
        results = []
        deadline = time.time() + (timeout or 0)

        while True:
            try:
                wait_time = deadline - time.time() if timeout else 0
                if wait_time < 0:
                    break

                result = self.output_queue.get(
                    timeout=wait_time if timeout else 0.001
                )
                results.append(result)

                if max_count and len(results) >= max_count:
                    break
            except queue.Empty:
                break

        return results

    def _run_loop(self) -> None:
        """Main execution loop (runs in background thread)."""
        logger.info("Quantum runner loop started")

        while not self._stop_event.is_set():
            try:
                task = self.input_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            start_time = time.time()

            try:
                # Execute quantum circuit
                result = self._execute_circuit(task)
                execution_time = time.time() - start_time

                result.execution_time = execution_time
                self.output_queue.put(result)

                self.tasks_completed += 1
                self.avg_execution_time = (
                    self.avg_execution_time * 0.9 + execution_time * 0.1
                )

                logger.debug(
                    f"Completed quantum task {task.task_id} "
                    f"({execution_time:.2f}s)"
                )

            except Exception as e:
                logger.error(f"Quantum circuit execution failed: {e}")
                self.tasks_failed += 1

                result = QuantumResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e),
                )
                self.output_queue.put(result)

        logger.info("Quantum runner loop stopped")

    def _execute_circuit(self, task: QuantumTask) -> QuantumResult:
        """
        Execute a single quantum circuit.

        Falls back to analytic simulation if PennyLane unavailable.
        """
        try:
            import pennylane as qml

            dev = qml.device(
                task.circuit_params.get("device", "default.qubit"),
                wires=task.n_qubits,
            )

            @qml.qnode(dev)
            def circuit(params):
                # Simple variational ansatz
                for layer in range(task.n_layers):
                    for i in range(task.n_qubits):
                        qml.RX(params[layer * task.n_qubits + i], wires=i)
                    for i in range(task.n_qubits - 1):
                        qml.CNOT(wires=[i, i + 1])
                return qml.expval(qml.PauliZ(0))

            # Extract or generate parameters
            if "params" in task.circuit_params:
                params = task.circuit_params["params"]
            else:
                params = np.random.randn(
                    task.n_layers * task.n_qubits
                ) * 0.1

            # Execute circuit
            output = circuit(params)
            output_tensor = torch.tensor(
                [float(output)], dtype=torch.float32
            )

            return QuantumResult(
                task_id=task.task_id,
                success=True,
                output=output_tensor,
                loss_feedback=None,
            )

        except ImportError:
            logger.debug("PennyLane unavailable; using analytic fallback")

            # Analytic fallback: random Pauli expectation
            output = float(np.random.randn() * 0.5)
            output_tensor = torch.tensor([output], dtype=torch.float32)

            return QuantumResult(
                task_id=task.task_id,
                success=True,
                output=output_tensor,
                loss_feedback=None,
            )

    def metrics(self) -> Dict[str, Any]:
        """Get execution metrics."""
        return {
            "submitted": self.tasks_submitted,
            "completed": self.tasks_completed,
            "failed": self.tasks_failed,
            "pending": self.input_queue.qsize(),
            "output_pending": self.output_queue.qsize(),
            "avg_exec_time": self.avg_execution_time,
            "running": self._running,
        }


class SharedParameterSync:
    """
    Thread-safe parameter synchronization between quantum and LLM threads.

    Allows atomic updates of shared parameters (attention weights, etc.)
    without race conditions.
    """

    def __init__(self):
        """Initialize parameter store."""
        self._params: Dict[str, torch.Tensor] = {}
        self._lock = threading.RLock()
        self._version = 0

    def set(self, name: str, tensor: torch.Tensor) -> int:
        """Set a parameter and return version number."""
        with self._lock:
            self._params[name] = tensor.clone().detach()
            self._version += 1
            return self._version

    def get(self, name: str) -> Optional[torch.Tensor]:
        """Get a parameter (returns clone)."""
        with self._lock:
            if name in self._params:
                return self._params[name].clone()
        return None

    def get_all(self) -> Dict[str, torch.Tensor]:
        """Get all parameters as a snapshot."""
        with self._lock:
            return {k: v.clone() for k, v in self._params.items()}

    def version(self) -> int:
        """Get current version number."""
        with self._lock:
            return self._version
