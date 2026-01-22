#!/usr/bin/env python3
"""
GGUF Model Registry and Metadata Management

Maintains a centralized registry of all quantum-enhanced GGUF models,
their metadata, performance metrics, and deployment status.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
import hashlib

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_FILE = REPO_ROOT / "data_out" / "quantum_gguf_training" / "gguf_registry.json"
DEPLOYED_MODELS = REPO_ROOT / "deployed_models"


@dataclass
class GGUFMetadata:
    """Metadata for a GGUF model"""
    model_id: str
    name: str
    base_model: str
    quantization_type: str
    file_path: Path
    file_size_mb: float
    created_at: str
    model_hash: str
    
    quantum_enhanced: bool = False
    quantum_features: List[str] = field(default_factory=list)
    quantum_fidelity: float = 0.0
    
    inference_speed_tokens_per_sec: float = 0.0
    perplexity: float = 0.0
    context_window: int = 2048
    
    deployment_status: str = "validated"  # validated, deployed, archived
    deployment_platform: str = ""
    last_inference_at: Optional[str] = None
    
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling Path objects"""
        d = asdict(self)
        d['file_path'] = str(d['file_path'])
        return d


class GGUFRegistry:
    """Central registry for quantum-enhanced GGUF models"""
    
    def __init__(self, registry_path: Optional[Path] = None):
        """Initialize registry
        
        Args:
            registry_path: Custom registry file path (defaults to standard location)
        """
        self.registry_path = registry_path or REGISTRY_FILE
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, GGUFMetadata] = {}
        self._load()
        
    def _load(self):
        """Load registry from disk"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    self.models = {
                        model_id: GGUFMetadata(
                            **{k: v if k != 'file_path' else Path(v)
                               for k, v in model_data.items()}
                        )
                        for model_id, model_data in data.items()
                    }
                logger.info(f"✅ Loaded {len(self.models)} models from registry")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load registry: {e}")
                self.models = {}
        else:
            logger.info("📝 Creating new registry")
            self.models = {}
    
    def _save(self):
        """Save registry to disk"""
        try:
            data = {
                model_id: model.to_dict()
                for model_id, model in self.models.items()
            }
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"💾 Saved registry with {len(self.models)} models")
        except Exception as e:
            logger.error(f"❌ Failed to save registry: {e}")
            raise
    
    def register_model(self, metadata: GGUFMetadata) -> str:
        """Register a new GGUF model
        
        Args:
            metadata: Model metadata
            
        Returns:
            Model ID
        """
        model_id = metadata.model_id
        self.models[model_id] = metadata
        self._save()
        logger.info(f"✅ Registered model: {model_id} ({metadata.quantization_type})")
        return model_id
    
    def get_model(self, model_id: str) -> Optional[GGUFMetadata]:
        """Get model metadata by ID
        
        Args:
            model_id: Model ID
            
        Returns:
            Model metadata or None if not found
        """
        return self.models.get(model_id)
    
    def list_models(
        self,
        quantization_type: Optional[str] = None,
        quantum_enhanced: Optional[bool] = None,
        deployment_status: Optional[str] = None,
        base_model: Optional[str] = None
    ) -> List[GGUFMetadata]:
        """List models with optional filtering
        
        Args:
            quantization_type: Filter by quantization (q4_0, q5_0, etc.)
            quantum_enhanced: Filter by quantum enhancement
            deployment_status: Filter by deployment status
            base_model: Filter by base model
            
        Returns:
            List of matching models
        """
        results = list(self.models.values())
        
        if quantization_type:
            results = [m for m in results if m.quantization_type == quantization_type]
        
        if quantum_enhanced is not None:
            results = [m for m in results if m.quantum_enhanced == quantum_enhanced]
        
        if deployment_status:
            results = [m for m in results if m.deployment_status == deployment_status]
        
        if base_model:
            results = [m for m in results if m.base_model == base_model]
        
        return results
    
    def get_best_model(
        self,
        metric: str = "inference_speed_tokens_per_sec",
        quantization_type: Optional[str] = None,
        quantum_enhanced: Optional[bool] = None
    ) -> Optional[GGUFMetadata]:
        """Get best model by metric
        
        Args:
            metric: Metric to rank by (inference_speed_tokens_per_sec, perplexity, etc.)
            quantization_type: Optional filter
            quantum_enhanced: Optional filter
            
        Returns:
            Best model or None
        """
        models = self.list_models(
            quantization_type=quantization_type,
            quantum_enhanced=quantum_enhanced
        )
        
        if not models:
            return None
        
        # Determine if higher or lower is better
        if metric in ['perplexity', 'quantum_error_rate', 'latency']:
            return min(models, key=lambda m: getattr(m, metric, float('inf')))
        else:
            return max(models, key=lambda m: getattr(m, metric, 0))
    
    def update_deployment_status(
        self,
        model_id: str,
        status: str,
        platform: Optional[str] = None
    ):
        """Update model deployment status
        
        Args:
            model_id: Model ID
            status: New status (validated, deployed, archived)
            platform: Deployment platform (llama-cpp, vllm, etc.)
        """
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found in registry")
        
        model = self.models[model_id]
        model.deployment_status = status
        if platform:
            model.deployment_platform = platform
        model.last_inference_at = datetime.now(timezone.utc).isoformat()
        
        self._save()
        logger.info(f"✅ Updated {model_id}: {status} on {platform or 'N/A'}")
    
    def record_inference(self, model_id: str):
        """Record inference timestamp for a model"""
        if model_id in self.models:
            self.models[model_id].last_inference_at = datetime.now(timezone.utc).isoformat()
            self._save()
    
    def export_summary(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Export registry summary
        
        Args:
            output_path: Optional path to save JSON summary
            
        Returns:
            Summary dictionary
        """
        summary = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_models": len(self.models),
            "quantum_enhanced_count": sum(1 for m in self.models.values() if m.quantum_enhanced),
            "deployed_count": sum(1 for m in self.models.values() if m.deployment_status == "deployed"),
            "by_quantization": {},
            "by_base_model": {},
            "models": {}
        }
        
        # Aggregate by quantization type
        for model in self.models.values():
            qt = model.quantization_type
            if qt not in summary["by_quantization"]:
                summary["by_quantization"][qt] = 0
            summary["by_quantization"][qt] += 1
            
            # Aggregate by base model
            bm = model.base_model
            if bm not in summary["by_base_model"]:
                summary["by_base_model"][bm] = 0
            summary["by_base_model"][bm] += 1
            
            # Store model info
            summary["models"][model.model_id] = {
                "name": model.name,
                "quantization": model.quantization_type,
                "quantum_enhanced": model.quantum_enhanced,
                "inference_speed": model.inference_speed_tokens_per_sec,
                "perplexity": model.perplexity,
                "deployment_status": model.deployment_status
            }
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            logger.info(f"💾 Exported summary to {output_path}")
        
        return summary
    
    def print_summary(self):
        """Print registry summary to console"""
        summary = self.export_summary()
        print("\n" + "="*70)
        print("📊 GGUF MODEL REGISTRY SUMMARY")
        print("="*70)
        print(f"Total Models: {summary['total_models']}")
        print(f"Quantum Enhanced: {summary['quantum_enhanced_count']}")
        print(f"Deployed: {summary['deployed_count']}")
        
        print("\n📦 By Quantization Type:")
        for qt, count in summary['by_quantization'].items():
            print(f"  {qt}: {count}")
        
        print("\n🧠 By Base Model:")
        for bm, count in summary['by_base_model'].items():
            print(f"  {bm}: {count}")
        
        print("\n📋 Recent Models:")
        for model_id in sorted(self.models.keys())[-5:]:
            model = self.models[model_id]
            quantum_mark = "🔮" if model.quantum_enhanced else "⚙️"
            print(f"  {quantum_mark} {model_id}")
            print(f"     Size: {model.file_size_mb:.1f}MB | Quantization: {model.quantization_type}")
            print(f"     Speed: {model.inference_speed_tokens_per_sec:.1f} tok/s | Status: {model.deployment_status}")
        
        print("="*70 + "\n")


if __name__ == "__main__":
    # Test registry
    registry = GGUFRegistry()
    registry.print_summary()
