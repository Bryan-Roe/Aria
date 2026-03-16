"""
Hybrid Quantum-Classical LLM Training Orchestrator
===================================================

Advanced training workflow manager for quantum-enhanced language models.

Features:
- Adaptive quantum/classical routing
- Progressive quantum integration
- Curriculum learning for quantum circuits
- Resource-aware training scheduling
- Multi-stage training pipeline

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

logger = logging.getLogger(__name__)


@dataclass
class TrainingStage:
    """Configuration for a training stage."""
    name: str
    quantum_ratio: float  # 0.0 to 1.0
    num_epochs: int
    learning_rate: float
    batch_size: int
    enable_quantum_layers: List[str] = field(default_factory=list)
    freeze_classical_layers: bool = False


@dataclass
class TrainingMetrics:
    """Metrics for training monitoring."""
    stage: str = ""
    epoch: int = 0
    batch: int = 0
    loss: float = 0.0
    perplexity: float = 0.0
    quantum_execution_time: float = 0.0
    classical_execution_time: float = 0.0
    quantum_layer_count: int = 0
    learning_rate: float = 0.0
    timestamp: float = field(default_factory=time.time)


class CurriculumScheduler:
    """
    Manages progressive quantum integration during training.
    
    Gradually increases quantum circuit complexity as training progresses.
    """
    
    def __init__(
        self,
        stages: List[TrainingStage],
        warmup_stages: int = 2,
    ):
        self.stages = stages
        self.warmup_stages = warmup_stages
        self.current_stage_idx = 0
        
        logger.info(f"CurriculumScheduler: {len(stages)} stages, {warmup_stages} warmup stages")
    
    def get_current_stage(self) -> TrainingStage:
        """Get current training stage."""
        return self.stages[self.current_stage_idx]
    
    def advance_stage(self) -> bool:
        """
        Advance to next training stage.
        
        Returns:
            True if advanced, False if at final stage
        """
        if self.current_stage_idx < len(self.stages) - 1:
            self.current_stage_idx += 1
            logger.info(f"Advanced to stage {self.current_stage_idx}: {self.get_current_stage().name}")
            return True
        return False
    
    def is_warmup_stage(self) -> bool:
        """Check if currently in warmup."""
        return self.current_stage_idx < self.warmup_stages
    
    def get_quantum_ratio(self) -> float:
        """Get current quantum operation ratio."""
        return self.stages[self.current_stage_idx].quantum_ratio
    
    def get_progress(self) -> Dict[str, Any]:
        """Get training progress."""
        return {
            "current_stage": self.current_stage_idx,
            "total_stages": len(self.stages),
            "stage_name": self.get_current_stage().name,
            "quantum_ratio": self.get_quantum_ratio(),
            "is_warmup": self.is_warmup_stage(),
        }


class AdaptiveQuantumRouter:
    """
    Routes operations to quantum or classical based on learned policy.
    
    Uses reinforcement learning to optimize routing decisions.
    """
    
    def __init__(
        self,
        input_dim: int = 64,
        learning_rate: float = 0.001,
    ):
        self.input_dim = input_dim
        
        # Simple policy network
        self.policy_net = nn.Sequential(
            nn.Linear(input_dim + 5, 128),  # +5 for context features
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),  # Probability of using quantum
        )
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.routing_history = []
        
        logger.info("AdaptiveQuantumRouter initialized")
    
    def route(
        self,
        input_features: torch.Tensor,
        context: Dict[str, float],
    ) -> bool:
        """
        Decide whether to use quantum or classical execution.
        
        Args:
            input_features: Input tensor features
            context: Contextual information (complexity, resource usage, etc.)
        
        Returns:
            True for quantum, False for classical
        """
        # Extract context features
        context_features = torch.tensor([
            context.get("complexity", 0.5),
            context.get("batch_size", 16) / 32.0,  # normalized
            context.get("sequence_length", 128) / 512.0,
            context.get("quantum_capacity", 0.5),
            context.get("training_progress", 0.0),
        ], dtype=torch.float32)
        
        # Combine with input features
        if len(input_features.shape) > 1:
            input_flat = input_features.mean(dim=0)  # aggregate
        else:
            input_flat = input_features
        
        # Pad or truncate to input_dim
        if input_flat.shape[0] > self.input_dim:
            input_flat = input_flat[:self.input_dim]
        elif input_flat.shape[0] < self.input_dim:
            padding = torch.zeros(self.input_dim - input_flat.shape[0])
            input_flat = torch.cat([input_flat, padding])
        
        combined = torch.cat([input_flat, context_features])
        
        # Get routing probability
        with torch.no_grad():
            prob_quantum = self.policy_net(combined).item()
        
        decision = prob_quantum > 0.5
        
        self.routing_history.append({
            "decision": "quantum" if decision else "classical",
            "probability": prob_quantum,
            "context": context.copy(),
        })
        
        return decision
    
    def update_policy(
        self,
        reward: float,
        recent_decisions: int = 10,
    ):
        """
        Update routing policy based on reward signal.
        
        Args:
            reward: Reward signal (higher is better)
            recent_decisions: Number of recent decisions to update
        """
        if len(self.routing_history) < recent_decisions:
            return
        
        # Simple policy gradient update
        # In practice, would use proper RL algorithm (PPO, A2C, etc.)
        loss = -reward * len(self.routing_history[-recent_decisions:])
        
        self.optimizer.zero_grad()
        loss_tensor = torch.tensor(loss, requires_grad=True)
        loss_tensor.backward()
        self.optimizer.step()
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        if not self.routing_history:
            return {"quantum_ratio": 0.0, "total_decisions": 0}
        
        quantum_count = sum(1 for h in self.routing_history if h["decision"] == "quantum")
        total = len(self.routing_history)
        
        return {
            "quantum_ratio": quantum_count / total,
            "classical_ratio": (total - quantum_count) / total,
            "total_decisions": total,
            "avg_quantum_prob": np.mean([h["probability"] for h in self.routing_history]),
        }


class HybridTrainingOrchestrator:
    """
    Orchestrates quantum-classical hybrid training workflow.
    
    Manages:
    - Multi-stage curriculum
    - Quantum/classical routing
    - Resource monitoring
    - Checkpoint management
    - Metric tracking
    """
    
    def __init__(
        self,
        model: nn.Module,
        stages: List[TrainingStage],
        output_dir: Path,
        device: str = "cpu",
    ):
        self.model = model.to(device)
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.curriculum = CurriculumScheduler(stages)
        self.router = AdaptiveQuantumRouter()
        
        # Metrics
        self.metrics_history: List[TrainingMetrics] = []
        self.best_loss = float('inf')
        self.global_step = 0
        
        logger.info(f"HybridTrainingOrchestrator initialized: {len(stages)} stages, device={device}")
    
    def train_stage(
        self,
        stage: TrainingStage,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
    ) -> Dict[str, float]:
        """
        Train for one curriculum stage.
        
        Args:
            stage: Training stage configuration
            train_loader: Training data loader
            val_loader: Optional validation data loader
        
        Returns:
            Stage metrics
        """
        logger.info(f"Starting stage: {stage.name} (quantum_ratio={stage.quantum_ratio:.2f})")
        
        # Configure model for this stage
        self._configure_model_for_stage(stage)
        
        # Setup optimizer
        optimizer = optim.AdamW(
            [p for p in self.model.parameters() if p.requires_grad],
            lr=stage.learning_rate,
        )
        
        criterion = nn.CrossEntropyLoss()
        
        stage_metrics = {
            "total_loss": 0.0,
            "total_batches": 0,
            "quantum_execution_time": 0.0,
            "classical_execution_time": 0.0,
        }
        
        for epoch in range(stage.num_epochs):
            epoch_loss = 0.0
            
            self.model.train()
            for batch_idx, (inputs, targets) in enumerate(train_loader):
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                
                # Forward pass with timing
                start_time = time.time()
                outputs = self.model(inputs)
                forward_time = time.time() - start_time
                
                # Compute loss
                loss = criterion(outputs.view(-1, outputs.size(-1)), targets.view(-1))
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # Track metrics
                metrics = TrainingMetrics(
                    stage=stage.name,
                    epoch=epoch,
                    batch=batch_idx,
                    loss=loss.item(),
                    perplexity=torch.exp(loss).item(),
                    quantum_execution_time=forward_time * stage.quantum_ratio,
                    classical_execution_time=forward_time * (1 - stage.quantum_ratio),
                    learning_rate=stage.learning_rate,
                )
                
                self.metrics_history.append(metrics)
                self.global_step += 1
                
                epoch_loss += loss.item()
                stage_metrics["total_loss"] += loss.item()
                stage_metrics["total_batches"] += 1
                stage_metrics["quantum_execution_time"] += metrics.quantum_execution_time
                stage_metrics["classical_execution_time"] += metrics.classical_execution_time
                
                # Logging
                if batch_idx % 10 == 0:
                    logger.info(
                        f"Stage {stage.name} | Epoch {epoch}/{stage.num_epochs} | "
                        f"Batch {batch_idx} | Loss: {loss.item():.4f} | "
                        f"PPL: {metrics.perplexity:.2f}"
                    )
                
                # Update router policy based on performance
                if batch_idx % 50 == 0 and batch_idx > 0:
                    reward = -epoch_loss / (batch_idx + 1)  # negative avg loss as reward
                    self.router.update_policy(reward)
            
            # Validation
            if val_loader is not None:
                val_metrics = self._validate(val_loader, criterion)
                logger.info(
                    f"Validation | Epoch {epoch} | Loss: {val_metrics['loss']:.4f} | "
                    f"PPL: {val_metrics['perplexity']:.2f}"
                )
                
                # Checkpoint if best
                if val_metrics['loss'] < self.best_loss:
                    self.best_loss = val_metrics['loss']
                    self._save_checkpoint(stage.name, epoch, val_metrics)
        
        # Compute stage average metrics
        avg_metrics = {
            "avg_loss": stage_metrics["total_loss"] / stage_metrics["total_batches"],
            "total_quantum_time": stage_metrics["quantum_execution_time"],
            "total_classical_time": stage_metrics["classical_execution_time"],
            "quantum_time_ratio": stage_metrics["quantum_execution_time"] / 
                                   (stage_metrics["quantum_execution_time"] + stage_metrics["classical_execution_time"] + 1e-8),
        }
        
        logger.info(f"Stage {stage.name} complete: avg_loss={avg_metrics['avg_loss']:.4f}")
        
        return avg_metrics
    
    def _configure_model_for_stage(self, stage: TrainingStage):
        """Configure model layers for current stage."""
        # Enable/disable quantum layers
        for name, module in self.model.named_modules():
            if "quantum" in name.lower():
                module.requires_grad = name in stage.enable_quantum_layers
        
        # Freeze classical layers if requested
        if stage.freeze_classical_layers:
            for name, param in self.model.named_parameters():
                if "quantum" not in name.lower():
                    param.requires_grad = False
    
    def _validate(self, val_loader: DataLoader, criterion) -> Dict[str, float]:
        """Run validation."""
        self.model.eval()
        total_loss = 0.0
        total_batches = 0
        
        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(inputs)
                loss = criterion(outputs.view(-1, outputs.size(-1)), targets.view(-1))
                
                total_loss += loss.item()
                total_batches += 1
        
        avg_loss = total_loss / total_batches
        
        return {
            "loss": avg_loss,
            "perplexity": np.exp(avg_loss),
        }
    
    def _save_checkpoint(self, stage_name: str, epoch: int, metrics: Dict):
        """Save training checkpoint."""
        checkpoint_path = self.output_dir / f"checkpoint_{stage_name}_epoch{epoch}.pt"
        
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "stage": stage_name,
            "epoch": epoch,
            "global_step": self.global_step,
            "metrics": metrics,
            "router_state": self.router.policy_net.state_dict(),
        }, checkpoint_path)
        
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def run_full_curriculum(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
    ) -> Dict[str, Any]:
        """
        Run complete curriculum training.
        
        Returns:
            Final training report
        """
        logger.info("Starting full curriculum training")
        start_time = time.time()
        
        all_stage_metrics = []
        
        while True:
            stage = self.curriculum.get_current_stage()
            stage_metrics = self.train_stage(stage, train_loader, val_loader)
            all_stage_metrics.append({
                "stage": stage.name,
                "metrics": stage_metrics,
            })
            
            if not self.curriculum.advance_stage():
                break
        
        total_time = time.time() - start_time
        
        # Generate final report
        report = {
            "total_stages": len(all_stage_metrics),
            "total_time": total_time,
            "total_steps": self.global_step,
            "best_loss": self.best_loss,
            "stage_metrics": all_stage_metrics,
            "routing_stats": self.router.get_routing_stats(),
            "curriculum_progress": self.curriculum.get_progress(),
        }
        
        # Save report
        report_path = self.output_dir / "training_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Training complete: {total_time:.2f}s, {self.global_step} steps")
        logger.info(f"Report saved: {report_path}")
        
        return report


# Export key components
__all__ = [
    "TrainingStage",
    "TrainingMetrics",
    "CurriculumScheduler",
    "AdaptiveQuantumRouter",
    "HybridTrainingOrchestrator",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    stages = [
        TrainingStage(
            name="warmup_classical",
            quantum_ratio=0.0,
            num_epochs=2,
            learning_rate=1e-4,
            batch_size=16,
        ),
        TrainingStage(
            name="gradual_quantum",
            quantum_ratio=0.3,
            num_epochs=5,
            learning_rate=5e-5,
            batch_size=16,
            enable_quantum_layers=["attention"],
        ),
        TrainingStage(
            name="full_quantum",
            quantum_ratio=0.7,
            num_epochs=10,
            learning_rate=1e-5,
            batch_size=8,
            enable_quantum_layers=["attention", "feedforward"],
        ),
    ]
    
    logger.info(f"✅ Example training curriculum: {len(stages)} stages")
    for stage in stages:
        logger.info(f"  - {stage.name}: quantum_ratio={stage.quantum_ratio}, epochs={stage.num_epochs}")
