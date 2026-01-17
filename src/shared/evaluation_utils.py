"""
Evaluation Utilities & Helpers

Common utilities for all evaluation scripts:
- Metric computation functions
- Dataset loading/validation
- Result serialization
- Performance tracking
- Threshold checking
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class EvaluationMetrics:
    """Standard evaluation metrics container."""
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    bleu: Optional[float] = None
    rouge: Optional[float] = None
    perplexity: Optional[float] = None
    response_time_ms: Optional[float] = None
    token_efficiency: Optional[float] = None
    determinism: Optional[float] = None
    roc_auc: Optional[float] = None
    cost_per_token: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {
            k: v for k, v in asdict(self).items() if v is not None
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict())


@dataclass
class EvaluationResult:
    """Complete evaluation result with metadata."""
    model_id: str
    model_type: str
    dataset: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "pending"  # pending, running, succeeded, failed
    samples_evaluated: int = 0
    duration_seconds: float = 0.0
    metrics: EvaluationMetrics = field(default_factory=EvaluationMetrics)
    error: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "model_type": self.model_type,
            "dataset": self.dataset,
            "timestamp": self.timestamp,
            "status": self.status,
            "samples_evaluated": self.samples_evaluated,
            "duration_seconds": self.duration_seconds,
            "metrics": self.metrics.to_dict(),
            "error": self.error,
            "config": self.config,
        }

    def save(self, output_dir: Path):
        """Save result to JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        result_file = output_dir / "result.json"
        with result_file.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("Result saved: %s", result_file)

    @staticmethod
    def load(result_file: Path) -> EvaluationResult:
        """Load result from JSON file."""
        with result_file.open("r") as f:
            data = json.load(f)
        metrics = EvaluationMetrics(
            **{k: v for k, v in data.pop("metrics", {}).items()})
        return EvaluationResult(metrics=metrics, **data)


# ============================================================================
# Metric Computation Functions
# ============================================================================

def compute_accuracy(predictions: List[str], references: List[str]) -> float:
    """
    Compute exact match accuracy.

    Args:
        predictions: List of predicted strings
        references: List of reference strings

    Returns:
        Accuracy score (0..1)
    """
    if not predictions:
        return 0.0

    matches = sum(1 for p, r in zip(predictions, references)
                  if p.strip() == r.strip())
    return matches / len(predictions)


def compute_bleu(
    predictions: List[str],
    references: List[str],
    n: int = 4
) -> float:
    """
    Compute BLEU score (approximate unigram overlap).

    Args:
        predictions: List of predicted strings
        references: List of reference strings
        n: N-gram level (default: 4 for BLEU-4)

    Returns:
        BLEU score approximation (0..1)
    """
    if not predictions:
        return 0.0

    def get_ngrams(text: str, n: int) -> set:
        words = text.lower().split()
        return {tuple(words[i:i+n]) for i in range(len(words) - n + 1)}

    scores = []
    for pred, ref in zip(predictions, references):
        pred_ngrams = get_ngrams(pred, n)
        ref_ngrams = get_ngrams(ref, n)

        if not ref_ngrams:
            scores.append(1.0 if not pred_ngrams else 0.0)
        else:
            overlap = len(pred_ngrams & ref_ngrams)
            scores.append(overlap / len(ref_ngrams))

    return np.mean(scores) if scores else 0.0


def compute_rouge_l(predictions: List[str], references: List[str]) -> float:
    """
    Compute ROUGE-L (LCS-based) score.

    Args:
        predictions: List of predicted strings
        references: List of reference strings

    Returns:
        ROUGE-L score (0..1)
    """
    if not predictions:
        return 0.0

    def lcs_length(a: str, b: str) -> int:
        """Compute longest common subsequence length."""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])

        return dp[m][n]

    def rouge_l_score(pred: str, ref: str) -> float:
        """Compute ROUGE-L F1 for a single prediction."""
        lcs = lcs_length(pred, ref)

        if not pred or not ref:
            return 1.0 if pred == ref else 0.0

        precision = lcs / len(pred) if pred else 0.0
        recall = lcs / len(ref) if ref else 0.0

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)
        return f1

    scores = [rouge_l_score(p, r) for p, r in zip(predictions, references)]
    return np.mean(scores) if scores else 0.0


def compute_precision(tp: int, fp: int) -> float:
    """
    Compute precision: TP / (TP + FP).

    Args:
        tp: True positives
        fp: False positives

    Returns:
        Precision (0..1)
    """
    if tp + fp == 0:
        return 0.0
    return tp / (tp + fp)


def compute_recall(tp: int, fn: int) -> float:
    """
    Compute recall: TP / (TP + FN).

    Args:
        tp: True positives
        fn: False negatives

    Returns:
        Recall (0..1)
    """
    if tp + fn == 0:
        return 0.0
    return tp / (tp + fn)


def compute_f1_score(precision: float, recall: float) -> float:
    """
    Compute F1 score: 2 * (P * R) / (P + R).

    Args:
        precision: Precision value
        recall: Recall value

    Returns:
        F1 score (0..1)
    """
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def compute_perplexity(losses: List[float]) -> float:
    """
    Compute perplexity: exp(mean_loss).

    Args:
        losses: List of loss values

    Returns:
        Perplexity (≥1)
    """
    if not losses:
        return float('inf')

    mean_loss = np.mean(losses)
    return float(np.exp(mean_loss))


def compute_determinism(
    predictions_run1: List[str],
    predictions_run2: List[str]
) -> float:
    """
    Compute determinism: fraction of identical predictions across runs.

    Args:
        predictions_run1: Predictions from first run
        predictions_run2: Predictions from second run

    Returns:
        Determinism score (0..1)
    """
    if not predictions_run1:
        return 0.0

    matches = sum(
        1 for p1, p2 in zip(predictions_run1, predictions_run2)
        if p1.strip() == p2.strip()
    )
    return matches / len(predictions_run1)


def compute_token_efficiency(
    tokens_used: List[int],
    token_budget: int
) -> float:
    """
    Compute token efficiency: average tokens used vs budget.

    Args:
        tokens_used: List of token counts for each prediction
        token_budget: Maximum tokens allowed per prediction

    Returns:
        Efficiency percentage (0..100)
    """
    if not tokens_used or token_budget == 0:
        return 0.0

    mean_used = np.mean(tokens_used)
    return float(min(100.0, (mean_used / token_budget) * 100))


# ============================================================================
# Dataset Utilities
# ============================================================================

def load_jsonl_dataset(
    path: Path,
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load JSONL dataset (one JSON object per line).

    Args:
        path: Path to JSONL file
        max_samples: Max samples to load (None = all)

    Returns:
        List of dataset items
    """
    items = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_samples and i >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse line %d: %s", i+1, e)

    return items


def load_json_dataset(
    path: Path,
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load JSON array dataset.

    Args:
        path: Path to JSON file
        max_samples: Max samples to load (None = all)

    Returns:
        List of dataset items
    """
    with path.open("r", encoding="utf-8") as f:
        items = json.load(f)

    if not isinstance(items, list):
        items = [items]

    if max_samples:
        items = items[:max_samples]

    return items


def load_csv_dataset(
    path: Path,
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Load CSV dataset (simple: first column = input, second = label).

    Args:
        path: Path to CSV file
        max_samples: Max samples to load (None = all)

    Returns:
        List of dataset items with 'input' and 'label' keys
    """
    import csv

    items = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if max_samples and i >= max_samples:
                break
            if not row:
                continue

            items.append({
                "input": row[0] if row else "",
                "label": row[1] if len(row) > 1 else None,
            })

    return items


def load_dataset(
    path: Path,
    max_samples: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Auto-detect and load dataset (JSONL, JSON, or CSV).

    Args:
        path: Path to dataset file
        max_samples: Max samples to load

    Returns:
        List of dataset items
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if path.suffix == ".jsonl":
        return load_jsonl_dataset(path, max_samples)
    elif path.suffix == ".json":
        return load_json_dataset(path, max_samples)
    elif path.suffix == ".csv":
        return load_csv_dataset(path, max_samples)
    else:
        # Try to detect by content
        try:
            return load_jsonl_dataset(path, max_samples)
        except (ValueError, OSError):
            return load_csv_dataset(path, max_samples)


# ============================================================================
# Result Aggregation
# ============================================================================

@dataclass
class AggregatedResults:
    """Aggregated results from multiple evaluations."""
    total_evaluations: int = 0
    succeeded: int = 0
    failed: int = 0
    total_samples: int = 0
    avg_duration: float = 0.0
    metrics_summary: Dict[str, Dict[str, float]] = field(
        default_factory=dict)  # metric -> {mean, min, max}
    results: List[EvaluationResult] = field(default_factory=list)

    def add_result(self, result: EvaluationResult):
        """Add individual evaluation result."""
        self.total_evaluations += 1
        self.total_samples += result.samples_evaluated

        if result.status == "succeeded":
            self.succeeded += 1
        else:
            self.failed += 1

        self.results.append(result)

    def compute_summary(self):
        """Compute aggregate metrics summary."""
        if not self.results:
            return

        self.avg_duration = np.mean([r.duration_seconds for r in self.results])

        # Aggregate metrics
        all_metrics = {}
        for result in self.results:
            for metric_name, value in result.metrics.to_dict().items():
                if metric_name not in all_metrics:
                    all_metrics[metric_name] = []
                all_metrics[metric_name].append(value)

        self.metrics_summary = {
            metric: {
                "mean": float(np.mean(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
                "std": float(np.std(values)),
            }
            for metric, values in all_metrics.items()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_evaluations": self.total_evaluations,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "total_samples": self.total_samples,
            "avg_duration_seconds": self.avg_duration,
            "metrics_summary": self.metrics_summary,
        }

    def save(self, output_dir: Path):
        """Save aggregated results to JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)

        summary_file = output_dir / "summary.json"
        with summary_file.open("w") as f:
            json.dump(self.to_dict(), f, indent=2)

        results_file = output_dir / "results.json"
        with results_file.open("w") as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)

        logger.info("Aggregated results saved to %s", output_dir)


# ============================================================================
# Threshold & Quality Gates
# ============================================================================

@dataclass
class QualityThresholds:
    """Quality gates for model evaluation."""
    min_accuracy: float = 0.7
    min_precision: float = 0.6
    min_recall: float = 0.6
    min_f1: float = 0.65
    max_response_time_ms: float = 1000.0
    min_determinism: float = 0.9

    def check_result(self, result: EvaluationResult) -> Tuple[bool, List[str]]:
        """
        Check if result passes all thresholds.

        Returns:
            (passes, list_of_failures)
        """
        failures = []
        metrics = result.metrics

        if (
            metrics.accuracy is not None
            and metrics.accuracy < self.min_accuracy
        ):
            failures.append(
                f"Accuracy {metrics.accuracy:.3f} < {self.min_accuracy}")

        if (
            metrics.precision is not None
            and metrics.precision < self.min_precision
        ):
            failures.append(
                f"Precision {metrics.precision:.3f} < {self.min_precision}")

        if metrics.recall is not None and metrics.recall < self.min_recall:
            failures.append(f"Recall {metrics.recall:.3f} < {self.min_recall}")

        if metrics.f1_score is not None and metrics.f1_score < self.min_f1:
            failures.append(f"F1 {metrics.f1_score:.3f} < {self.min_f1}")

        if metrics.response_time_ms is not None and (
            metrics.response_time_ms > self.max_response_time_ms
        ):
            failures.append(
                f"Response time {metrics.response_time_ms:.1f}ms > "
                f"{self.max_response_time_ms}ms"
            )

        if metrics.determinism is not None and (
            metrics.determinism < self.min_determinism
        ):
            failures.append(
                f"Determinism {metrics.determinism:.3f} < "
                f"{self.min_determinism}"
            )

        return len(failures) == 0, failures


# ============================================================================
# Logging & Diagnostics
# ============================================================================

def setup_evaluation_logging(
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Setup logging for evaluation scripts.

    Args:
        log_file: Optional log file path

    Returns:
        Logger instance
    """
    eval_logger = logging.getLogger("evaluation")
    eval_logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(name)s] %(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    eval_logger.addHandler(console_handler)

    # File handler (if provided)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        eval_logger.addHandler(file_handler)

    return eval_logger
