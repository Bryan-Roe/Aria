"""
Quantum LLM Complete Integration
=================================

Unified interface integrating all quantum LLM components:
- Advanced quantum layers
- Circuit optimization
- Hybrid training orchestration
- Real-time monitoring

Complete end-to-end quantum-enhanced language model training system.

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import argparse
import yaml
import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# Import all quantum LLM components
try:
    from quantum_llm_advanced import (
        QuantumCircuitCache,
        AdaptiveQuantumLayer,
        MultiScaleQuantumAttention,
        QuantumPromptTuning,
        QuantumErrorMitigation,
    )
    ADVANCED_AVAILABLE = True
except ImportError:
    ADVANCED_AVAILABLE = False
    logging.warning("Advanced quantum components not available")

try:
    from quantum_circuit_optimizer import (
        CircuitCompiler,
        BatchCircuitExecutor,
        AdaptiveCircuitScheduler,
        QuantumClassicalPartitioner,
        OptimizationStrategy,
    )
    OPTIMIZER_AVAILABLE = True
except ImportError:
    OPTIMIZER_AVAILABLE = False
    logging.warning("Circuit optimizer not available")

try:
    from quantum_llm_hybrid_trainer import (
        HybridTrainingOrchestrator,
        TrainingStage,
        CurriculumScheduler,
        AdaptiveQuantumRouter,
    )
    TRAINER_AVAILABLE = True
except ImportError:
    TRAINER_AVAILABLE = False
    logging.warning("Hybrid trainer not available")

try:
    from quantum_llm_monitor import (
        TrainingDashboard,
        QuantumMetrics,
        TrainingSnapshot,
        VisualizationExporter,
    )
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    logging.warning("Monitoring tools not available")

logger = logging.getLogger(__name__)


class QuantumLLMConfig:
    """Configuration for quantum-enhanced LLM."""
    
    def __init__(self, config_path: Optional[Path] = None):
        # Default configuration
        self.config = {
            # Model architecture
            "vocab_size": 256,
            "d_model": 128,
            "n_heads": 4,
            "n_layers": 4,
            "d_ff": 512,
            "max_seq_length": 512,
            
            # Quantum configuration
            "n_qubits": 4,
            "quantum_backend": "default.qubit",
            "quantum_shots": 1000,
            "enable_quantum_attention": True,
            "enable_quantum_ffn": True,
            "enable_multi_scale_attention": True,
            "enable_adaptive_entanglement": True,
            "enable_circuit_caching": True,
            "enable_error_mitigation": False,
            
            # Training configuration
            "batch_size": 16,
            "learning_rate": 1e-4,
            "num_epochs": 10,
            "enable_curriculum": True,
            "enable_adaptive_routing": True,
            
            # Optimization
            "optimization_level": 2,
            "enable_circuit_fusion": True,
            "max_batch_circuits": 10,
            
            # Monitoring
            "enable_dashboard": True,
            "dashboard_update_interval": 10,
            "enable_alerts": True,
            
            # Output
            "output_dir": "data_out/quantum_llm_integrated",
            "save_checkpoints": True,
            "checkpoint_interval": 100,
        }
        
        # Load from file if provided
        if config_path and Path(config_path).exists():
            self.load(config_path)
    
    def load(self, config_path: Path):
        """Load configuration from YAML file."""
        with open(config_path) as f:
            loaded_config = yaml.safe_load(f)
            self.config.update(loaded_config)
        logger.info(f"Configuration loaded from {config_path}")
    
    def save(self, config_path: Path):
        """Save configuration to YAML file."""
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
        logger.info(f"Configuration saved to {config_path}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def __getitem__(self, key: str):
        """Dict-like access."""
        return self.config[key]


class IntegratedQuantumLLM(nn.Module):
    """
    Fully integrated quantum-enhanced language model.
    
    Combines all advanced quantum components into a unified model.
    """
    
    def __init__(self, config: QuantumLLMConfig):
        super().__init__()
        self.config = config
        
        # Embedding layer
        self.embedding = nn.Embedding(
            config["vocab_size"],
            config["d_model"],
        )
        
        # Positional encoding
        self.pos_encoding = nn.Parameter(
            torch.randn(1, config["max_seq_length"], config["d_model"]) * 0.02
        )
        
        # Build transformer layers
        self.layers = nn.ModuleList([
            self._build_layer(i) for i in range(config["n_layers"])
        ])
        
        # Output head
        self.output_head = nn.Linear(config["d_model"], config["vocab_size"])
        
        # Quantum components
        self._init_quantum_components()
        
        logger.info(f"IntegratedQuantumLLM initialized: {config['n_layers']} layers, "
                   f"{config['d_model']} dim, {config['n_qubits']} qubits")
    
    def _build_layer(self, layer_idx: int) -> nn.Module:
        """Build a single transformer layer."""
        config = self.config
        
        # Choose attention mechanism
        if config["enable_multi_scale_attention"] and ADVANCED_AVAILABLE:
            attention = MultiScaleQuantumAttention(
                d_model=config["d_model"],
                n_heads=config["n_heads"],
                n_qubits_per_head=[2, 3, 4, 6],  # Multi-scale
            )
        else:
            # Fallback to standard attention
            attention = nn.MultiheadAttention(
                embed_dim=config["d_model"],
                num_heads=config["n_heads"],
                batch_first=True,
            )
        
        # Feedforward network
        if config["enable_quantum_ffn"] and ADVANCED_AVAILABLE:
            ffn = AdaptiveQuantumLayer(
                d_model=config["d_model"],
                n_qubits=config["n_qubits"],
            )
        else:
            ffn = nn.Sequential(
                nn.Linear(config["d_model"], config["d_ff"]),
                nn.ReLU(),
                nn.Linear(config["d_ff"], config["d_model"]),
            )
        
        # Layer normalization
        norm1 = nn.LayerNorm(config["d_model"])
        norm2 = nn.LayerNorm(config["d_model"])
        
        return nn.ModuleDict({
            "attention": attention,
            "norm1": norm1,
            "ffn": ffn,
            "norm2": norm2,
        })
    
    def _init_quantum_components(self):
        """Initialize quantum-specific components."""
        config = self.config
        
        # Circuit cache
        if config["enable_circuit_caching"] and ADVANCED_AVAILABLE:
            self.circuit_cache = QuantumCircuitCache(cache_size=1000)
        else:
            self.circuit_cache = None
        
        # Error mitigation
        if config["enable_error_mitigation"] and ADVANCED_AVAILABLE:
            self.error_mitigation = QuantumErrorMitigation(
                n_qubits=config["n_qubits"]
            )
        else:
            self.error_mitigation = None
        
        # Prompt tuning
        if ADVANCED_AVAILABLE:
            self.prompt_tuning = QuantumPromptTuning(
                d_model=config["d_model"],
                n_qubits=config["n_qubits"],
                n_prompts=10,
            )
        else:
            self.prompt_tuning = None
    
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the quantum-enhanced LLM.
        
        Args:
            input_ids: Input token IDs [batch_size, seq_length]
        
        Returns:
            Logits [batch_size, seq_length, vocab_size]
        """
        batch_size, seq_length = input_ids.shape
        
        # Embedding + positional encoding
        x = self.embedding(input_ids)
        x = x + self.pos_encoding[:, :seq_length, :]
        
        # Process through transformer layers
        for layer in self.layers:
            # Self-attention with residual
            attn_out, _ = layer["attention"](x, x, x)
            x = layer["norm1"](x + attn_out)
            
            # Feedforward with residual
            ffn_out = layer["ffn"](x) if callable(layer["ffn"]) else layer["ffn"].forward(x)
            x = layer["norm2"](x + ffn_out)
        
        # Output projection
        logits = self.output_head(x)
        
        return logits
    
    def get_quantum_stats(self) -> Dict[str, Any]:
        """Get quantum component statistics."""
        stats = {}
        
        if self.circuit_cache:
            stats["cache"] = self.circuit_cache.get_stats()
        
        if self.error_mitigation:
            stats["error_mitigation"] = {
                "enabled": True,
                "n_qubits": self.config["n_qubits"],
            }
        
        return stats


class QuantumLLMSystem:
    """
    Complete quantum LLM training system.
    
    Integrates model, trainer, optimizer, and monitoring.
    """
    
    def __init__(
        self,
        config: QuantumLLMConfig,
        device: str = "cpu",
    ):
        self.config = config
        self.device = device
        self.output_dir = Path(config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self.model = IntegratedQuantumLLM(config).to(device)
        
        # Initialize components
        self._init_components()
        
        logger.info(f"QuantumLLMSystem initialized on {device}")
        logger.info(f"Output directory: {self.output_dir}")
    
    def _init_components(self):
        """Initialize all system components."""
        config = self.config
        
        # Circuit optimizer
        if OPTIMIZER_AVAILABLE and config["optimization_level"] > 0:
            self.circuit_compiler = CircuitCompiler(
                OptimizationStrategy(
                    compilation_level=config["optimization_level"],
                    enable_gate_fusion=config["enable_circuit_fusion"],
                )
            )
            self.batch_executor = BatchCircuitExecutor(
                max_batch_size=config["max_batch_circuits"],
            )
        else:
            self.circuit_compiler = None
            self.batch_executor = None
        
        # Training orchestrator
        if TRAINER_AVAILABLE and config["enable_curriculum"]:
            stages = self._create_training_stages()
            self.orchestrator = HybridTrainingOrchestrator(
                model=self.model,
                stages=stages,
                output_dir=self.output_dir / "training",
                device=self.device,
            )
        else:
            self.orchestrator = None
        
        # Monitoring dashboard
        if MONITOR_AVAILABLE and config["enable_dashboard"]:
            self.dashboard = TrainingDashboard(
                output_dir=self.output_dir / "dashboard",
                update_interval=config["dashboard_update_interval"],
                enable_alerts=config["enable_alerts"],
            )
        else:
            self.dashboard = None
    
    def _create_training_stages(self) -> List[TrainingStage]:
        """Create curriculum training stages."""
        config = self.config
        
        stages = [
            TrainingStage(
                name="classical_warmup",
                quantum_ratio=0.0,
                num_epochs=2,
                learning_rate=config["learning_rate"],
                batch_size=config["batch_size"],
            ),
            TrainingStage(
                name="quantum_transition",
                quantum_ratio=0.3,
                num_epochs=3,
                learning_rate=config["learning_rate"] * 0.5,
                batch_size=config["batch_size"],
                enable_quantum_layers=["attention"],
            ),
            TrainingStage(
                name="full_quantum",
                quantum_ratio=0.7,
                num_epochs=config["num_epochs"] - 5,
                learning_rate=config["learning_rate"] * 0.1,
                batch_size=max(4, config["batch_size"] // 2),
                enable_quantum_layers=["attention", "feedforward"],
            ),
        ]
        
        return stages
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Optional[Dataset] = None,
    ) -> Dict[str, Any]:
        """
        Train the quantum LLM system.
        
        Args:
            train_dataset: Training dataset
            val_dataset: Optional validation dataset
        
        Returns:
            Training report
        """
        logger.info("Starting quantum LLM training")
        
        # Create data loaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config["batch_size"],
            shuffle=True,
        )
        
        val_loader = None
        if val_dataset:
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config["batch_size"],
                shuffle=False,
            )
        
        # Run training
        if self.orchestrator and TRAINER_AVAILABLE:
            report = self.orchestrator.run_full_curriculum(train_loader, val_loader)
        else:
            # Fallback to simple training
            report = self._simple_training(train_loader, val_loader)
        
        # Save final model
        self.save_model("final_model.pt")
        
        # Generate visualizations
        if self.dashboard and MONITOR_AVAILABLE:
            exporter = VisualizationExporter(self.output_dir / "visualizations")
            exporter.export_all(self.dashboard.metrics_aggregator.snapshots)
        
        logger.info("✅ Training complete")
        return report
    
    def _simple_training(self, train_loader, val_loader) -> Dict[str, Any]:
        """Fallback simple training loop."""
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=self.config["learning_rate"])
        criterion = nn.CrossEntropyLoss()
        
        total_loss = 0.0
        for epoch in range(self.config["num_epochs"]):
            for batch_idx, (inputs, targets) in enumerate(train_loader):
                inputs = inputs.to(self.device)
                targets = targets.to(self.device)
                
                outputs = self.model(inputs)
                loss = criterion(outputs.view(-1, outputs.size(-1)), targets.view(-1))
                
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                
                if batch_idx % 10 == 0:
                    logger.info(f"Epoch {epoch} | Batch {batch_idx} | Loss: {loss.item():.4f}")
        
        return {"total_loss": total_loss, "epochs": self.config["num_epochs"]}
    
    def save_model(self, filename: str = "model.pt"):
        """Save model checkpoint."""
        path = self.output_dir / filename
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "config": self.config.config,
            "quantum_stats": self.model.get_quantum_stats(),
        }, path)
        logger.info(f"Model saved: {path}")
    
    def load_model(self, path: Path):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        logger.info(f"Model loaded from {path}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive system report."""
        report = {
            "configuration": self.config.config,
            "model_parameters": sum(p.numel() for p in self.model.parameters()),
            "quantum_stats": self.model.get_quantum_stats(),
        }
        
        if self.dashboard:
            report["training_dashboard"] = self.dashboard.get_full_report()
        
        if self.circuit_compiler and OPTIMIZER_AVAILABLE:
            report["circuit_optimization"] = self.circuit_compiler.get_optimization_report()
        
        if self.batch_executor and OPTIMIZER_AVAILABLE:
            report["batch_execution"] = self.batch_executor.get_cache_stats()
        
        # Save report
        report_path = self.output_dir / "system_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"System report saved: {report_path}")
        return report


def main():
    """Main entry point for integrated quantum LLM training."""
    parser = argparse.ArgumentParser(description="Integrated Quantum LLM Training System")
    parser.add_argument("--config", type=str, help="Path to configuration YAML")
    parser.add_argument("--output-dir", type=str, default="data_out/quantum_llm_integrated")
    parser.add_argument("--device", type=str, default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--dry-run", action="store_true", help="Test configuration without training")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    if args.config:
        config = QuantumLLMConfig(Path(args.config))
    else:
        config = QuantumLLMConfig()
        config.config["output_dir"] = args.output_dir
    
    # Initialize system
    system = QuantumLLMSystem(config, device=args.device)
    
    logger.info("=" * 80)
    logger.info("QUANTUM LLM INTEGRATED SYSTEM")
    logger.info("=" * 80)
    logger.info(f"Model parameters: {sum(p.numel() for p in system.model.parameters()):,}")
    logger.info(f"Quantum components available:")
    logger.info(f"  - Advanced layers: {ADVANCED_AVAILABLE}")
    logger.info(f"  - Circuit optimizer: {OPTIMIZER_AVAILABLE}")
    logger.info(f"  - Hybrid trainer: {TRAINER_AVAILABLE}")
    logger.info(f"  - Monitoring: {MONITOR_AVAILABLE}")
    logger.info("=" * 80)
    
    if args.dry_run:
        logger.info("✅ Dry run successful - configuration valid")
        return
    
    # For actual training, would need to load/create dataset
    logger.info("⚠️  Ready to train - provide dataset to system.train()")
    
    # Generate initial report
    system.generate_report()


if __name__ == "__main__":
    main()
