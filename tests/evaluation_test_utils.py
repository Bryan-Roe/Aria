"""
Evaluation Test Utilities

Shared test fixtures and helpers for evaluation tests:
- Dataset generation (synthetic test data)
- Mock evaluation objects
- Result fixtures
- Common assertions
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from shared.evaluation_utils import (
    EvaluationMetrics,
    EvaluationResult,
    AggregatedResults,
)


# ============================================================================
# Synthetic Dataset Fixtures
# ============================================================================

def generate_chat_dataset(
    num_samples: int = 10,
    dataset_format: str = "jsonl"
) -> List[Dict[str, Any]]:
    """
    Generate synthetic chat dataset for testing.

    Args:
        num_samples: Number of samples to generate
        dataset_format: "jsonl" or "messages"

    Returns:
        List of sample dicts
    """
    samples = []

    for i in range(num_samples):
        if dataset_format == "jsonl":
            samples.append({
                "input": f"Test input {i}",
                "expected": f"Test output {i}",
            })
        else:  # messages format
            samples.append({
                "messages": [
                    {"role": "user", "content": f"Test question {i}"},
                    {"role": "assistant", "content": f"Test answer {i}"},
                ]
            })

    return samples


def generate_classification_dataset(
    num_samples: int = 10,
    num_classes: int = 2,
) -> List[Dict[str, Any]]:
    """
    Generate synthetic classification dataset.

    Args:
        num_samples: Number of samples
        num_classes: Number of classes

    Returns:
        List of sample dicts with 'features' and 'label'
    """
    samples = []

    for i in range(num_samples):
        samples.append({
            "features": [float(j % 10) for j in range(5)],
            "label": str(i % num_classes),
        })

    return samples


@pytest.fixture
def temp_dataset_dir(tmp_path: Path) -> Path:
    """Temporary directory for dataset files."""
    return tmp_path / "datasets"


@pytest.fixture
def sample_jsonl_dataset(temp_dataset_dir: Path) -> Path:
    """Create sample JSONL dataset."""
    dataset_file = temp_dataset_dir / "sample.jsonl"
    dataset_file.parent.mkdir(parents=True, exist_ok=True)

    samples = generate_chat_dataset(num_samples=5, dataset_format="jsonl")
    with dataset_file.open("w") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")

    return dataset_file


@pytest.fixture
def sample_json_dataset(temp_dataset_dir: Path) -> Path:
    """Create sample JSON array dataset."""
    dataset_file = temp_dataset_dir / "sample.json"
    dataset_file.parent.mkdir(parents=True, exist_ok=True)

    samples = generate_chat_dataset(num_samples=5, dataset_format="messages")
    with dataset_file.open("w") as f:
        json.dump(samples, f)

    return dataset_file


@pytest.fixture
def sample_csv_dataset(temp_dataset_dir: Path) -> Path:
    """Create sample CSV dataset."""
    import csv

    dataset_file = temp_dataset_dir / "sample.csv"
    dataset_file.parent.mkdir(parents=True, exist_ok=True)

    with dataset_file.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["input", "label"])
        for i in range(5):
            writer.writerow([f"input_{i}", f"label_{i}"])

    return dataset_file


# ============================================================================
# Evaluation Result Fixtures
# ============================================================================

@pytest.fixture
def sample_evaluation_result() -> EvaluationResult:
    """Sample evaluation result with dummy data."""
    metrics = EvaluationMetrics(
        accuracy=0.95,
        precision=0.93,
        recall=0.97,
        f1_score=0.95,
        response_time_ms=150.0,
    )

    return EvaluationResult(
        model_id="test_model",
        model_type="lora",
        dataset="datasets/chat/test",
        status="succeeded",
        samples_evaluated=100,
        duration_seconds=45.0,
        metrics=metrics,
    )


@pytest.fixture
def sample_aggregated_results() -> AggregatedResults:
    """Sample aggregated results from multiple evaluations."""
    agg = AggregatedResults()

    # Add multiple results
    for i in range(3):
        metrics = EvaluationMetrics(
            accuracy=0.90 + (i * 0.02),
            f1_score=0.88 + (i * 0.02),
            response_time_ms=100 + (i * 10),
        )

        result = EvaluationResult(
            model_id=f"model_{i}",
            model_type="lora",
            dataset="datasets/chat/test",
            status="succeeded",
            samples_evaluated=50 + (i * 10),
            duration_seconds=20 + (i * 5),
            metrics=metrics,
        )
        agg.add_result(result)

    agg.compute_summary()
    return agg


# ============================================================================
# Mock Evaluators
# ============================================================================

class MockLORAEvaluator:
    """Mock LoRA evaluator for testing."""

    def __init__(self, accuracy: float = 0.9, f1_score: float = 0.88):
        self.accuracy = accuracy
        self.f1_score = f1_score

    def evaluate(self, dataset: List[Dict]) -> EvaluationResult:
        """Return mock evaluation result."""
        metrics = EvaluationMetrics(
            accuracy=self.accuracy,
            f1_score=self.f1_score,
            response_time_ms=100.0,
        )

        return EvaluationResult(
            model_id="mock_lora",
            model_type="lora",
            dataset="mock_dataset",
            status="succeeded",
            samples_evaluated=len(dataset),
            duration_seconds=10.0,
            metrics=metrics,
        )


class MockQuantumEvaluator:
    """Mock quantum evaluator for testing."""

    def __init__(self, accuracy: float = 0.85):
        self.accuracy = accuracy

    def evaluate(self, dataset: List[Dict]) -> EvaluationResult:
        """Return mock evaluation result."""
        metrics = EvaluationMetrics(
            accuracy=self.accuracy,
            precision=self.accuracy - 0.05,
            recall=self.accuracy - 0.03,
            f1_score=self.accuracy - 0.04,
        )

        return EvaluationResult(
            model_id="mock_quantum",
            model_type="quantum",
            dataset="mock_quantum_dataset",
            status="succeeded",
            samples_evaluated=len(dataset),
            duration_seconds=15.0,
            metrics=metrics,
        )


# ============================================================================
# Common Assertions
# ============================================================================

def assert_evaluation_result_valid(result: EvaluationResult):
    """Assert evaluation result has valid structure."""
    assert result.model_id
    assert result.model_type
    assert result.dataset
    assert result.status in ["pending", "running", "succeeded", "failed"]
    assert result.samples_evaluated >= 0
    assert result.duration_seconds >= 0.0


def assert_metrics_in_range(metrics: EvaluationMetrics):
    """Assert all metrics are in valid ranges."""
    if metrics.accuracy is not None:
        assert 0.0 <= metrics.accuracy <= 1.0, "accuracy out of range"

    if metrics.precision is not None:
        assert 0.0 <= metrics.precision <= 1.0, "precision out of range"

    if metrics.recall is not None:
        assert 0.0 <= metrics.recall <= 1.0, "recall out of range"

    if metrics.f1_score is not None:
        assert 0.0 <= metrics.f1_score <= 1.0, "f1_score out of range"

    if metrics.bleu is not None:
        assert 0.0 <= metrics.bleu <= 1.0, "bleu out of range"

    if metrics.rouge is not None:
        assert 0.0 <= metrics.rouge <= 1.0, "rouge out of range"

    if metrics.response_time_ms is not None:
        assert metrics.response_time_ms >= 0.0, "response_time_ms negative"

    if metrics.determinism is not None:
        assert 0.0 <= metrics.determinism <= 1.0, "determinism out of range"


def assert_result_passes_threshold(
    result: EvaluationResult,
    min_accuracy: float = 0.7,
    min_f1: float = 0.65,
):
    """Assert result passes minimum quality thresholds."""
    if result.metrics.accuracy is not None:
        assert result.metrics.accuracy >= min_accuracy, \
            f"Accuracy {result.metrics.accuracy} < {min_accuracy}"

    if result.metrics.f1_score is not None:
        assert result.metrics.f1_score >= min_f1, \
            f"F1 {result.metrics.f1_score} < {min_f1}"


# ============================================================================
# Context Managers & Helpers
# ============================================================================

@pytest.fixture
def evaluation_temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for evaluation outputs."""
    eval_dir = tmp_path / "evaluations"
    eval_dir.mkdir(parents=True, exist_ok=True)
    return eval_dir


class EvaluationTestContext:
    """Helper context for evaluation tests."""

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.datasets_dir = tmp_path / "datasets"
        self.results_dir = tmp_path / "results"
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def create_dataset(self, name: str, samples: List[Dict]) -> Path:
        """Create a test dataset."""
        dataset_file = self.datasets_dir / f"{name}.jsonl"
        with dataset_file.open("w") as f:
            for sample in samples:
                f.write(json.dumps(sample) + "\n")
        return dataset_file

    def save_result(self, result: EvaluationResult) -> Path:
        """Save evaluation result."""
        result.save(self.results_dir)
        return self.results_dir / "result.json"


@pytest.fixture
def eval_test_context(tmp_path: Path) -> EvaluationTestContext:
    """Provide evaluation test context."""
    return EvaluationTestContext(tmp_path)


# ============================================================================
# Comparison Helpers
# ============================================================================

def compare_results(
    result1: EvaluationResult,
    result2: EvaluationResult
) -> Dict[str, Any]:
    """
    Compare two evaluation results.

    Returns dict with differences.
    """
    comparison = {
        "model_1": result1.model_id,
        "model_2": result2.model_id,
        "metrics_diff": {},
    }

    metrics1 = result1.metrics.to_dict()
    metrics2 = result2.metrics.to_dict()

    all_metrics = set(metrics1.keys()) | set(metrics2.keys())

    for metric in all_metrics:
        v1 = metrics1.get(metric)
        v2 = metrics2.get(metric)

        if v1 is not None and v2 is not None:
            diff = v2 - v1
            pct_change = (diff / v1 * 100) if v1 != 0 else 0.0
            comparison["metrics_diff"][metric] = {
                "model_1": v1,
                "model_2": v2,
                "diff": diff,
                "pct_change": pct_change,
            }

    return comparison


def rank_results(results: List[EvaluationResult]) -> List[tuple]:
    """
    Rank results by composite score.

    Returns list of (rank, model_id, score)
    """
    scores = []

    for result in results:
        metrics = result.metrics.to_dict()

        # Compute composite score (weighted average of available metrics)
        weights = {
            "accuracy": 0.4,
            "f1_score": 0.3,
            "precision": 0.15,
            "recall": 0.15,
        }

        composite = 0.0
        weight_sum = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                composite += metrics[metric] * weight
                weight_sum += weight

        if weight_sum > 0:
            composite /= weight_sum

        scores.append((result.model_id, composite))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)

    return [(i+1, model_id, score) for i, (model_id, score) in enumerate(scores)]
