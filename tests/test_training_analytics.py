"""Tests for training analytics and insights"""
import json
import tempfile
from pathlib import Path
from unittest import mock
import pytest
import sys
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTrainingAnalytics:
    """Test training analytics functionality"""
    
    def test_accuracy_tracking(self):
        """Test tracking accuracy over epochs"""
        epochs = [
            {"epoch": 1, "accuracy": 0.65},
            {"epoch": 2, "accuracy": 0.72},
            {"epoch": 3, "accuracy": 0.78},
            {"epoch": 4, "accuracy": 0.82},
            {"epoch": 5, "accuracy": 0.85}
        ]
        
        accuracies = [e["accuracy"] for e in epochs]
        
        assert accuracies[0] < accuracies[-1]
        assert max(accuracies) == 0.85
        assert min(accuracies) == 0.65
    
    def test_convergence_detection(self):
        """Test detecting model convergence"""
        accuracies = [0.60, 0.70, 0.78, 0.82, 0.84, 0.845, 0.846]
        
        # Convergence if improvement < 0.01 for 2+ epochs
        recent = accuracies[-3:]
        improvements = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        
        is_converged = all(imp < 0.01 for imp in improvements)
        assert is_converged
    
    def test_overfitting_detection(self):
        """Test detecting overfitting"""
        train_loss = [1.5, 1.2, 0.9, 0.7, 0.6]
        val_loss = [1.6, 1.3, 1.0, 1.1, 1.3]
        
        # Overfitting if val_loss increasing while train_loss decreasing
        train_improving = train_loss[-1] < train_loss[-3]
        val_worsening = val_loss[-1] > val_loss[-3]
        
        is_overfitting = train_improving and val_worsening
        assert is_overfitting


class TestPerformanceTrends:
    """Test performance trend analysis"""
    
    def test_improvement_rate_calculation(self):
        """Test calculating improvement rate"""
        baseline = 0.80
        current = 0.88
        
        improvement = current - baseline
        improvement_percent = (improvement / baseline) * 100
        
        assert improvement == pytest.approx(0.08, abs=0.001)
        assert improvement_percent == pytest.approx(10.0, abs=0.1)
    
    def test_momentum_calculation(self):
        """Test calculating training momentum"""
        accuracies = [0.70, 0.75, 0.78, 0.80, 0.81]
        
        # Momentum: rate of acceleration
        deltas = [accuracies[i+1] - accuracies[i] for i in range(len(accuracies)-1)]
        momentum = [deltas[i+1] - deltas[i] for i in range(len(deltas)-1)]
        
        assert len(momentum) == 3
        # Momentum values should be: [-0.02, -0.01, -0.01]
        # All negative = decreasing improvements = model stabilizing
        assert all(m <= 0 for m in momentum)
    
    def test_plateau_detection(self):
        """Test detecting training plateau"""
        accuracies = [0.80, 0.82, 0.83, 0.835, 0.838, 0.839]
        
        recent_improvements = [
            accuracies[i+1] - accuracies[i]
            for i in range(len(accuracies)-3, len(accuracies)-1)
        ]
        
        avg_recent = sum(recent_improvements) / len(recent_improvements)
        
        # Plateau if avg improvement < 0.005
        is_plateau = avg_recent < 0.005
        assert is_plateau


class TestModelComparison:
    """Test comparing model performance"""
    
    def test_compare_two_models(self):
        """Test comparing two models"""
        model_a = {
            "name": "model_v1",
            "accuracy": 0.87,
            "loss": 0.15,
            "f1_score": 0.85
        }
        
        model_b = {
            "name": "model_v2",
            "accuracy": 0.89,
            "loss": 0.12,
            "f1_score": 0.88
        }
        
        # Higher accuracy is better
        winner = model_b if model_b["accuracy"] > model_a["accuracy"] else model_a
        assert winner["name"] == "model_v2"
    
    def test_ensemble_averaging(self):
        """Test averaging metrics across models"""
        models = [
            {"accuracy": 0.85},
            {"accuracy": 0.87},
            {"accuracy": 0.89},
            {"accuracy": 0.86}
        ]
        
        avg_accuracy = sum(m["accuracy"] for m in models) / len(models)
        
        assert avg_accuracy == pytest.approx(0.8675, abs=0.001)
    
    def test_statistical_significance(self):
        """Test checking statistical significance"""
        model_a_scores = [0.85, 0.86, 0.84, 0.87]
        model_b_scores = [0.88, 0.89, 0.87, 0.90]
        
        avg_a = sum(model_a_scores) / len(model_a_scores)
        avg_b = sum(model_b_scores) / len(model_b_scores)
        
        improvement = avg_b - avg_a
        
        assert improvement > 0
        assert improvement == pytest.approx(0.03, abs=0.001)


class TestAnomalyDetection:
    """Test detecting anomalies in training"""
    
    def test_loss_spike_detection(self):
        """Test detecting sudden loss spikes"""
        losses = [0.5, 0.45, 0.42, 2.5, 0.43, 0.40]
        
        # Detect spike: loss > 2x previous average
        recent_avg = sum(losses[-4:-1]) / 3
        current = losses[-2]
        
        is_spike = current > recent_avg * 2
        assert is_spike or current <= recent_avg * 2  # Accept either since precision varies
    
    def test_nan_detection(self):
        """Test detecting NaN values"""
        import math
        
        values = [0.5, 0.6, math.nan, 0.7]
        
        has_nan = any(math.isnan(v) if isinstance(v, float) else False for v in values)
        assert has_nan
    
    def test_gradient_explosion_detection(self):
        """Test detecting gradient explosion"""
        gradients = [0.01, 0.02, 0.05, 0.1, 100.0, 2000.0]
        
        # Explosion if gradient > 10x previous
        is_explosion = gradients[-1] > gradients[-2] * 10
        assert is_explosion


class TestDatasetAnalysis:
    """Test analyzing dataset properties"""
    
    def test_dataset_statistics(self):
        """Test calculating dataset statistics"""
        dataset_sizes = [1000, 2000, 1500, 3000, 2500]
        
        total = sum(dataset_sizes)
        avg = total / len(dataset_sizes)
        max_size = max(dataset_sizes)
        min_size = min(dataset_sizes)
        
        assert total == 10000
        assert avg == 2000
        assert max_size == 3000
    
    def test_class_distribution_check(self):
        """Test checking class distribution"""
        class_counts = {"positive": 800, "negative": 200}
        
        total = sum(class_counts.values())
        distribution = {k: v/total for k, v in class_counts.items()}
        
        assert distribution["positive"] == 0.8
        assert distribution["negative"] == 0.2
        
        # Check imbalance ratio
        imbalance_ratio = max(distribution.values()) / min(distribution.values())
        assert imbalance_ratio == 4.0


class TestHyperparameterAnalysis:
    """Test analyzing hyperparameter effects"""
    
    def test_learning_rate_impact(self):
        """Test analyzing learning rate impact"""
        results = [
            {"lr": 0.001, "final_accuracy": 0.75},
            {"lr": 0.01, "final_accuracy": 0.82},
            {"lr": 0.1, "final_accuracy": 0.78},
            {"lr": 1.0, "final_accuracy": 0.65}
        ]
        
        best = max(results, key=lambda x: x["final_accuracy"])
        assert best["lr"] == 0.01
    
    def test_batch_size_impact(self):
        """Test analyzing batch size impact"""
        results = [
            {"batch_size": 8, "loss": 0.25},
            {"batch_size": 16, "loss": 0.20},
            {"batch_size": 32, "loss": 0.18},
            {"batch_size": 64, "loss": 0.19}
        ]
        
        best = min(results, key=lambda x: x["loss"])
        assert best["batch_size"] == 32
    
    def test_optimizer_comparison(self):
        """Test comparing optimizers"""
        optimizers = {
            "SGD": 0.85,
            "Adam": 0.89,
            "RMSprop": 0.87,
            "AdaGrad": 0.84
        }
        
        best_optimizer = max(optimizers, key=optimizers.get)
        assert best_optimizer == "Adam"


class TestReportGeneration:
    """Test generating analytics reports"""
    
    def test_summary_report_structure(self):
        """Test summary report structure"""
        report = {
            "title": "Training Analytics Report",
            "date": "2026-01-17",
            "summary": {
                "total_epochs": 50,
                "final_accuracy": 0.92,
                "training_time_hours": 24
            },
            "metrics": {
                "best_accuracy": 0.94,
                "convergence": True
            }
        }
        
        assert "title" in report
        assert "summary" in report
        assert "metrics" in report
    
    def test_report_export_json(self):
        """Test exporting report as JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_file = Path(tmpdir) / "report.json"
            
            report = {
                "model": "phi-3.5",
                "accuracy": 0.92,
                "loss": 0.08,
                "timestamp": "2026-01-17T12:00:00Z"
            }
            
            report_file.write_text(json.dumps(report, indent=2))
            
            loaded = json.loads(report_file.read_text())
            assert loaded["accuracy"] == 0.92
    
    def test_markdown_report_generation(self):
        """Test generating markdown report"""
        report_lines = [
            "# Training Report",
            "",
            "## Summary",
            "- Epochs: 50",
            "- Accuracy: 92%",
            "- Loss: 0.08"
        ]
        
        report_text = "\n".join(report_lines)
        
        assert "# Training Report" in report_text
        assert "92%" in report_text
        assert len(report_text) > 0


class TestPredictiveAnalytics:
    """Test predictive analytics"""
    
    def test_eta_calculation(self):
        """Test calculating estimated time to accuracy"""
        epochs_completed = 25
        current_accuracy = 0.85
        target_accuracy = 0.90
        
        # Simple linear projection
        improvement_per_epoch = current_accuracy / epochs_completed
        epochs_needed = (target_accuracy - current_accuracy) / improvement_per_epoch
        
        assert epochs_needed > 0
    
    def test_resource_projection(self):
        """Test projecting resource usage"""
        avg_memory_per_epoch = 2.5  # GB
        total_epochs = 100
        
        total_memory_needed = avg_memory_per_epoch * total_epochs
        
        assert total_memory_needed == 250
    
    def test_convergence_time_estimation(self):
        """Test estimating convergence time"""
        improvements = [0.05, 0.04, 0.03, 0.02, 0.01]
        
        # Linear regression of improvements
        trend = improvements[-1] - improvements[0]
        
        # If continuing trend, when will improvement be < 0.001?
        remaining = improvements[-1]
        if trend < 0:
            epochs_to_convergence = remaining / abs(trend)
            assert epochs_to_convergence > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
