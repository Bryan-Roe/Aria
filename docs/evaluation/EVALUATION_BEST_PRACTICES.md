# Evaluation Framework — Best Practices & Advanced Patterns

**Last updated:** December 8, 2025

Advanced guidance for implementing custom evaluations, extending the framework, and integrating evaluations into CI/CD pipelines.

## Table of Contents

1. [Custom Evaluation Metrics](#custom-evaluation-metrics)
2. [Extending Evaluators](#extending-evaluators)
3. [Integration Patterns](#integration-patterns)
4. [Performance Optimization](#performance-optimization)
5. [Distributed Evaluation](#distributed-evaluation)
6. [Monitoring & Observability](#monitoring--observability)
7. [Data Management](#data-management)

---

## Custom Evaluation Metrics

### Adding a Custom Metric

To add a custom metric to the framework:

#### 1. Implement Metric Function

```python
# In shared/evaluation_utils.py or custom module

def compute_custom_similarity(predictions: List[str], references: List[str]) -> float:
    """
    Compute custom semantic similarity between predictions and references.
    
    This example uses Levenshtein distance (edit distance).
    """
    import difflib
    
    scores = []
    for pred, ref in zip(predictions, references):
        # Compute similarity ratio (0..1, where 1 = identical)
        ratio = difflib.SequenceMatcher(None, pred, ref).ratio()
        scores.append(ratio)
    
    import numpy as np
    return float(np.mean(scores)) if scores else 0.0


# Register in metric registry
CUSTOM_METRICS = {
    "custom_similarity": compute_custom_similarity,
}
```

#### 2. Use in Evaluator

```python
# In evaluate_lora_model.py or custom evaluator

def evaluate_with_custom_metric(
    model_path: str,
    dataset: List[Dict],
    custom_metric_fn: callable,
) -> EvaluationResult:
    """Evaluate model with custom metric."""
    
    # Make predictions
    predictions = [predict(item) for item in dataset]
    references = [item.get("expected", "") for item in dataset]
    
    # Compute custom metric
    custom_score = custom_metric_fn(predictions, references)
    
    # Return result with custom metric
    metrics = EvaluationMetrics(
        accuracy=compute_accuracy(predictions, references),
        **{"custom_metric": custom_score}  # Add custom metric
    )
    
    return EvaluationResult(
        model_id=model_path,
        model_type="lora",
        dataset="custom_dataset",
        metrics=metrics,
        status="succeeded",
    )
```

#### 3. Add to Configuration

```yaml
# config/evaluation/evaluation_autorun.yaml

jobs:
  - name: eval_with_custom_metric
    enabled: true
    model_type: lora
    model_path: data_out/lora_training/phi35
    dataset: datasets/chat/mixed_chat
    metrics:
      - accuracy
      - custom_similarity  # Custom metric
      - bleu
```

### Examples: Common Custom Metrics

#### Semantic Similarity (using embeddings)

```python
from sentence_transformers import SentenceTransformer

def compute_semantic_similarity(
    predictions: List[str],
    references: List[str],
    model_name: str = "all-MiniLM-L6-v2"
) -> float:
    """Compute semantic similarity using sentence embeddings."""
    
    model = SentenceTransformer(model_name)
    
    # Embed all texts
    all_texts = list(set(predictions + references))
    embeddings = model.encode(all_texts)
    
    # Create embedding map
    text_to_emb = {text: emb for text, emb in zip(all_texts, embeddings)}
    
    # Compute cosine similarities
    from sklearn.metrics.pairwise import cosine_similarity
    
    scores = []
    for pred, ref in zip(predictions, references):
        pred_emb = text_to_emb[pred].reshape(1, -1)
        ref_emb = text_to_emb[ref].reshape(1, -1)
        sim = cosine_similarity(pred_emb, ref_emb)[0][0]
        scores.append(sim)
    
    import numpy as np
    return float(np.mean(scores))
```

#### Custom Task-Specific Metric

```python
def compute_code_correctness(
    predictions: List[str],  # Generated code snippets
    references: List[str],   # Reference/expected code
) -> float:
    """
    Evaluate code correctness by attempting to compile/execute.
    
    This is task-specific for code generation evaluation.
    """
    import tempfile
    import subprocess
    
    correct_count = 0
    
    for pred_code, ref_code in zip(predictions, references):
        try:
            # Try to compile/execute generated code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
                f.write(pred_code)
                f.flush()
                
                # Attempt compilation
                compile(pred_code, f.name, 'exec')
                correct_count += 1
        except SyntaxError:
            pass  # Code failed to compile
    
    return correct_count / len(predictions) if predictions else 0.0
```

---

## Extending Evaluators

### Custom Evaluator Class

Create a custom evaluator for a new model type:

```python
# scripts/evaluate_custom_model.py

"""Custom evaluator for proprietary model."""

from pathlib import Path
from typing import List, Dict, Any
import argparse
import json
from dataclasses import dataclass

from shared.evaluation_utils import (
    EvaluationMetrics,
    EvaluationResult,
    load_dataset,
)


class CustomModelEvaluator:
    """Evaluator for custom model type."""
    
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self._load_model()
    
    def _load_model(self):
        """Load custom model from path."""
        # Implementation depends on model format
        if self.model_path.is_dir():
            # Load from directory (e.g., HuggingFace format)
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
        else:
            # Load from file (e.g., ONNX, JAX, TF SavedModel)
            raise NotImplementedError(f"Loading from {self.model_path.suffix}")
    
    def predict(self, input_text: str) -> str:
        """Generate prediction for single input."""
        # Tokenize
        inputs = self.tokenizer(input_text, return_tensors="pt")
        
        # Generate
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
        )
        
        # Decode
        prediction = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        return prediction
    
    def evaluate(
        self,
        dataset: List[Dict[str, Any]],
        metrics: List[str],
    ) -> EvaluationResult:
        """Evaluate on dataset."""
        
        predictions = []
        references = []
        
        # Generate predictions
        for item in dataset:
            input_text = item.get("input", "")
            pred = self.predict(input_text)
            predictions.append(pred)
            
            # Get reference (expected output)
            ref = item.get("expected", item.get("label", ""))
            references.append(ref)
        
        # Compute metrics
        from shared.evaluation_utils import (
            compute_accuracy,
            compute_bleu,
            compute_rouge_l,
        )
        
        computed_metrics = EvaluationMetrics()
        
        for metric in metrics:
            if metric == "accuracy":
                computed_metrics.accuracy = compute_accuracy(predictions, references)
            elif metric == "bleu":
                computed_metrics.bleu = compute_bleu(predictions, references)
            elif metric == "rouge":
                computed_metrics.rouge = compute_rouge_l(predictions, references)
        
        # Return result
        return EvaluationResult(
            model_id=self.model_path.name,
            model_type="custom",
            dataset="custom_dataset",
            status="succeeded",
            samples_evaluated=len(dataset),
            metrics=computed_metrics,
        )


def main():
    parser = argparse.ArgumentParser(description="Evaluate custom model")
    parser.add_argument("--model-path", required=True, help="Path to custom model")
    parser.add_argument("--dataset", required=True, help="Path to dataset")
    parser.add_argument("--metric", action="append", required=True, help="Metric to compute")
    parser.add_argument("--max-samples", type=int, help="Max samples to evaluate")
    parser.add_argument("--save-dir", type=Path, default=Path("results"))
    
    args = parser.parse_args()
    
    # Load dataset
    dataset = load_dataset(Path(args.dataset), max_samples=args.max_samples)
    
    # Evaluate
    evaluator = CustomModelEvaluator(args.model_path)
    result = evaluator.evaluate(dataset, args.metric)
    
    # Save results
    result.save(args.save_dir)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
```

---

## Integration Patterns

### Integration with Training Pipeline

Automatically evaluate after training:

```python
# In scripts/training/train_and_promote.py

class TrainAndPromote:
    """Train model and optionally evaluate."""
    
    def run(self, auto_evaluate: bool = False):
        """Train, evaluate, and promote model."""
        
        # 1. Train model
        trained_model = self.train()
        
        # 2. Optional: Evaluate
        if auto_evaluate:
            eval_result = self.evaluate_model(trained_model)
            
            # Check if meets quality gate
            if eval_result.metrics.accuracy >= 0.85:
                print("✓ Model passes quality gate")
                self.promote_model(trained_model)
            else:
                print("✗ Model failed quality gate")
                return False
        
        return True
    
    def evaluate_model(self, model_path: str) -> EvaluationResult:
        """Evaluate trained model."""
        from scripts.evaluate_lora_model import evaluate_lora
        
        return evaluate_lora(
            model_path=model_path,
            dataset="datasets/chat/dolly",
            max_samples=100,
            metrics=["accuracy", "bleu"],
        )
```

### Integration with CI/CD Pipeline

Fast evaluation in CI without external services:

```bash
# .github/workflows/ci.yml (GitHub Actions example)

name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run local evaluation (smoke test)
        run: |
          python ./scripts/evaluate_local_model.py \
            --dataset datasets/chat/mixed_chat \
            --max-samples 20 \
            --metric accuracy \
            --metric determinism \
            --save-dir results/ci_eval
      
      - name: Check evaluation results
        run: |
          python -c "
          import json
          with open('results/ci_eval/result.json') as f:
              data = json.load(f)
              accuracy = data['metrics'].get('accuracy', 0)
              if accuracy < 0.7:
                  print(f'ERROR: Accuracy {accuracy} below threshold 0.7')
                  exit(1)
              print(f'✓ Accuracy {accuracy} passed threshold')
          "
```

### Integration with Monitoring

Send evaluation metrics to monitoring systems:

```python
# Custom extension to evaluation result

from shared.evaluation_utils import EvaluationResult

class MonitoredEvaluationResult(EvaluationResult):
    """Evaluation result with monitoring/alerting."""
    
    def send_to_monitoring(self, service: str = "azure_monitor"):
        """Send metrics to monitoring service."""
        
        if service == "azure_monitor":
            from azure.monitor.opentelemetry import AzureMonitorTracer
            
            tracer = AzureMonitorTracer()
            
            # Log each metric
            for metric_name, value in self.metrics.to_dict().items():
                tracer.add_event(
                    name=f"model_evaluation_{metric_name}",
                    attributes={
                        "model_id": self.model_id,
                        "metric": metric_name,
                        "value": value,
                        "dataset": self.dataset,
                    }
                )
        
        elif service == "prometheus":
            from prometheus_client import Counter, Histogram
            
            # Register metrics
            evaluation_counter = Counter(
                'model_evaluations_total',
                'Total model evaluations',
                ['model_id', 'status'],
            )
            
            metric_histogram = Histogram(
                'model_metrics',
                'Model evaluation metrics',
                ['metric_name', 'model_id'],
            )
            
            # Record metrics
            evaluation_counter.labels(
                model_id=self.model_id,
                status=self.status,
            ).inc()
            
            for metric_name, value in self.metrics.to_dict().items():
                metric_histogram.labels(
                    metric_name=metric_name,
                    model_id=self.model_id,
                ).observe(value)
```

---

## Performance Optimization

### Batch Evaluation

Evaluate multiple models in parallel:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_evaluate(
    models: List[str],
    dataset: Path,
    max_workers: int = 4,
) -> Dict[str, EvaluationResult]:
    """Evaluate multiple models in parallel."""
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all evaluation jobs
        future_to_model = {
            executor.submit(evaluate_single_model, model, dataset): model
            for model in models
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_model):
            model = future_to_model[future]
            try:
                result = future.result()
                results[model] = result
                print(f"✓ {model}: {result.metrics.accuracy:.3f}")
            except Exception as e:
                print(f"✗ {model}: {e}")
                results[model] = None
    
    return results
```

### Caching Predictions

Cache predictions to avoid re-evaluation:

```python
import hashlib
import pickle
from functools import lru_cache

class CachedEvaluator:
    """Evaluator with prediction caching."""
    
    def __init__(self, model_path: str, cache_dir: Path = Path(".eval_cache")):
        self.model_path = model_path
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, input_text: str) -> str:
        """Generate cache key from input."""
        return hashlib.md5(input_text.encode()).hexdigest()
    
    def predict_cached(self, input_text: str) -> str:
        """Predict with caching."""
        
        cache_key = self._get_cache_key(input_text)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Check cache
        if cache_file.exists():
            with cache_file.open("rb") as f:
                return pickle.load(f)
        
        # Compute prediction
        prediction = self.predict(input_text)
        
        # Save to cache
        with cache_file.open("wb") as f:
            pickle.dump(prediction, f)
        
        return prediction
    
    def predict(self, input_text: str) -> str:
        """Generate prediction (override in subclass)."""
        raise NotImplementedError
```

### Dataset Sampling

Evaluate on representative samples:

```python
import random

def stratified_sample(
    dataset: List[Dict],
    sample_size: int,
    stratify_by: str = "category",
) -> List[Dict]:
    """
    Sample dataset while maintaining distribution of stratification key.
    
    Args:
        dataset: Full dataset
        sample_size: Number of samples to keep
        stratify_by: Key to use for stratification
    
    Returns:
        Stratified sample
    """
    
    # Group by stratification key
    groups = {}
    for item in dataset:
        key = item.get(stratify_by, "unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    
    # Sample from each group proportionally
    sampled = []
    for key, items in groups.items():
        group_fraction = len(items) / len(dataset)
        group_sample_size = max(1, int(sample_size * group_fraction))
        sampled.extend(random.sample(items, min(group_sample_size, len(items))))
    
    return sampled[:sample_size]
```

---

## Distributed Evaluation

### Multi-GPU Evaluation

Distribute evaluation across GPUs:

```python
import torch
from torch.nn.parallel import DataParallel

class DistributedLORAEvaluator:
    """LoRA evaluator using multiple GPUs."""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._load_model()
    
    def _load_model(self):
        """Load model and wrap with DataParallel."""
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        base_model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=torch.float16,
        )
        
        # Load LoRA adapter
        from peft import get_peft_model
        self.model = get_peft_model(base_model, "lora")
        
        # Wrap for multi-GPU
        if torch.cuda.device_count() > 1:
            self.model = DataParallel(self.model)
        
        self.model = self.model.to("cuda")
    
    def evaluate_batch(self, batch: List[str]) -> List[str]:
        """Evaluate batch across GPUs."""
        
        # Tokenize batch
        inputs = self.tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
        ).to("cuda")
        
        # Generate on GPU(s)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=100,
            )
        
        # Decode
        predictions = self.tokenizer.batch_decode(
            outputs,
            skip_special_tokens=True,
        )
        
        return predictions
```

---

## Monitoring & Observability

### Evaluation Metrics Dashboard

Create dashboard of evaluation metrics over time:

```python
# scripts/evaluation_dashboard.py

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

class EvaluationDashboard:
    """Evaluation metrics dashboard."""
    
    def __init__(self, results_dir: Path = Path("data_out/evaluation_autorun")):
        self.results_dir = results_dir
    
    def get_recent_evaluations(self, days: int = 7) -> List[Dict]:
        """Get evaluations from last N days."""
        
        cutoff = datetime.now() - timedelta(days=days)
        results = []
        
        for job_dir in self.results_dir.iterdir():
            if not job_dir.is_dir():
                continue
            
            for timestamp_dir in job_dir.iterdir():
                if not timestamp_dir.is_dir():
                    continue
                
                result_file = timestamp_dir / "result.json"
                if result_file.exists():
                    with result_file.open() as f:
                        result = json.load(f)
                        result["job"] = job_dir.name
                        result["timestamp_dir"] = timestamp_dir.name
                        results.append(result)
        
        return results
    
    def plot_metric_trends(self, metric: str = "accuracy"):
        """Plot metric trend over time."""
        
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("matplotlib required for plotting")
            return
        
        evaluations = self.get_recent_evaluations(days=30)
        
        # Group by job
        jobs = {}
        for eval in evaluations:
            job = eval.get("job", "unknown")
            if job not in jobs:
                jobs[job] = {"timestamps": [], "values": []}
            
            value = eval.get("metrics", {}).get(metric)
            if value is not None:
                jobs[job]["timestamps"].append(eval.get("timestamp", ""))
                jobs[job]["values"].append(value)
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for job, data in jobs.items():
            if data["values"]:
                ax.plot(data["timestamps"], data["values"], marker='o', label=job)
        
        ax.set_xlabel("Timestamp")
        ax.set_ylabel(metric.capitalize())
        ax.set_title(f"{metric.capitalize()} Trends (Last 30 Days)")
        ax.legend()
        ax.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"exports/trend_{metric}.png")
        print(f"Saved plot to exports/trend_{metric}.png")
```

---

## Data Management

### Dataset Versioning

Track dataset versions and lineage:

```python
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass
class DatasetMetadata:
    """Metadata for dataset version."""
    name: str
    version: str
    num_samples: int
    hash: str  # SHA256 of dataset contents
    created_at: str
    parent_version: str = None
    source: str = None
    preprocessing: List[str] = None

class DatasetVersionManager:
    """Manage dataset versions and lineage."""
    
    def __init__(self, datasets_dir: Path):
        self.datasets_dir = datasets_dir
        self.metadata_dir = datasets_dir / ".metadata"
        self.metadata_dir.mkdir(exist_ok=True)
    
    def register_dataset(
        self,
        dataset_path: Path,
        version: str,
        parent_version: str = None,
    ) -> DatasetMetadata:
        """Register dataset version."""
        
        import hashlib
        
        # Compute hash
        hash_digest = hashlib.sha256()
        with dataset_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_digest.update(chunk)
        
        # Create metadata
        from datetime import datetime
        metadata = DatasetMetadata(
            name=dataset_path.stem,
            version=version,
            num_samples=self._count_samples(dataset_path),
            hash=hash_digest.hexdigest(),
            created_at=datetime.now().isoformat(),
            parent_version=parent_version,
        )
        
        # Save metadata
        meta_file = self.metadata_dir / f"{metadata.name}-{version}.json"
        with meta_file.open("w") as f:
            json.dump(asdict(metadata), f, indent=2)
        
        return metadata
    
    def _count_samples(self, path: Path) -> int:
        """Count samples in dataset file."""
        if path.suffix == ".jsonl":
            with path.open() as f:
                return sum(1 for _ in f)
        elif path.suffix == ".json":
            with path.open() as f:
                data = json.load(f)
                return len(data) if isinstance(data, list) else 1
        else:
            return 0
```

---

## Summary

The advanced patterns in this guide enable:

✅ **Custom metrics** tailored to your evaluation needs  
✅ **Custom evaluators** for any model type  
✅ **CI/CD integration** for automated quality gates  
✅ **Parallel evaluation** across multiple models/GPUs  
✅ **Monitoring integration** with production systems  
✅ **Dataset versioning** for reproducibility  

For more information, see the main [EVALUATION_FRAMEWORK.md](EVALUATION_FRAMEWORK.md).
