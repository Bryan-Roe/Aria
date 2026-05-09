"""
Tests for Quantum-Enhanced LLM Training Module
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

# Add scripts to path
scripts_path = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_path))

try:
    from quantum_llm_trainer import (QuantumAttentionOptimizer,
                                     QuantumEnhancedLLMTrainer,
                                     QuantumFeatureEncoder,
                                     get_quantum_llm_status)

    QUANTUM_LLM_AVAILABLE = True
except (ImportError, OSError) as e:
    QUANTUM_LLM_AVAILABLE = False
    pytest.skip(f"Quantum LLM trainer not available: {e}", allow_module_level=True)


@pytest.mark.unit
class TestQuantumAttentionOptimizer:
    """Test quantum attention optimization"""

    def test_initialization(self):
        """Test optimizer initialization"""
        optimizer = QuantumAttentionOptimizer(n_qubits=4, n_layers=2)
        assert optimizer.n_qubits == 4
        assert optimizer.n_layers == 2

    def test_optimize_attention_weights(self):
        """Test attention weight optimization"""
        optimizer = QuantumAttentionOptimizer(n_qubits=4, n_layers=2)

        # Create mock attention scores
        attention_scores = torch.randn(2, 8, 8)

        # Optimize
        optimized = optimizer.optimize_attention_weights(attention_scores)

        # Check output shape matches input
        assert optimized.shape == attention_scores.shape

        # Check values are valid (no NaN or Inf)
        assert not torch.isnan(optimized).any()
        assert not torch.isinf(optimized).any()

    def test_optimize_attention_weights_preserves_shape_when_quantum_output_is_shorter(
        self,
    ):
        """Quantum output is per-qubit, so optimizer must resize it back to chunk length."""

        class _ShortQuantumLayer:
            def __call__(self, inputs):
                return torch.tensor(
                    [[0.1, 0.2, 0.3, 0.4]], dtype=inputs.dtype, device=inputs.device
                )

        optimizer = QuantumAttentionOptimizer(n_qubits=4, n_layers=2)
        optimizer._quantum_layer = _ShortQuantumLayer()

        attention_scores = torch.randn(1, 8, 8)
        optimized = optimizer.optimize_attention_weights(attention_scores)

        assert optimized.shape == attention_scores.shape
        assert not torch.isnan(optimized).any()
        assert not torch.isinf(optimized).any()


@pytest.mark.unit
class TestQuantumFeatureEncoder:
    """Test quantum feature encoding"""

    def test_initialization(self):
        """Test encoder initialization"""
        encoder = QuantumFeatureEncoder(n_qubits=4, n_layers=2)
        assert encoder.n_qubits == 4
        assert encoder.n_layers == 2

    def test_encode_features(self):
        """Test feature encoding"""
        encoder = QuantumFeatureEncoder(n_qubits=4, n_layers=2)

        # Create mock features
        features = torch.randn(4, 16)

        # Encode
        encoded = encoder.encode(features)

        # Check output is valid
        assert encoded is not None
        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()


@pytest.mark.unit
class TestQuantumEnhancedLLMTrainer:
    """Test main quantum LLM trainer"""

    def test_initialization(self):
        """Test trainer initialization"""
        config = {
            "quantum_backend": "local",
            "n_qubits": 4,
            "n_quantum_layers": 2,
            "passive": False,
        }

        trainer = QuantumEnhancedLLMTrainer(config)

        assert trainer.quantum_backend == "local"
        assert trainer.n_qubits == 4
        assert trainer.n_layers == 2
        assert not trainer.passive_mode

    def test_train_with_quantum_enhancement(self):
        """Test quantum-enhanced training"""
        config = {
            "quantum_backend": "local",
            "n_qubits": 4,
            "n_quantum_layers": 2,
            "passive": False,
        }

        trainer = QuantumEnhancedLLMTrainer(config)

        # Create temporary directories
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "train.json"
            output_dir = Path(tmpdir) / "output"

            # Create mock dataset
            mock_data = [
                {
                    "messages": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi!"},
                    ]
                },
                {
                    "messages": [
                        {"role": "user", "content": "How are you?"},
                        {"role": "assistant", "content": "I'm good!"},
                    ]
                },
            ]

            with open(dataset_path, "w") as f:
                json.dump(mock_data, f)

            # Run training
            results = trainer.train_with_quantum_enhancement(
                model=None, dataset_path=dataset_path, output_dir=output_dir, epochs=1
            )

            # Check results
            assert results["status"] == "success"
            assert results["epochs_completed"] == 1
            assert "quantum_metrics" in results
            assert results["quantum_metrics"]["circuit_executions"] > 0

            # Check output files
            assert output_dir.exists()
            results_file = output_dir / "quantum_training_results.json"
            assert results_file.exists()

            status = get_quantum_llm_status(output_dir=output_dir)
            assert status["status"] == "completed"
            assert status["checkpoint_exists"] is True
            assert status["inference_ready"] is True
            assert status["checkpoint_path"].endswith("best_quantum_llm.pt")

    def test_load_dataset_json(self):
        """Test loading JSON dataset"""
        config = {"quantum_backend": "local", "n_qubits": 4, "n_quantum_layers": 2}

        trainer = QuantumEnhancedLLMTrainer(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "train.json"

            mock_data = [{"text": "Sample 1"}, {"text": "Sample 2"}]

            with open(dataset_path, "w") as f:
                json.dump(mock_data, f)

            dataset = trainer._load_dataset(dataset_path)

            assert len(dataset) == 2
            assert dataset[0]["text"] == "Sample 1"

    def test_load_dataset_jsonl(self):
        """Test loading JSONL dataset"""
        config = {"quantum_backend": "local", "n_qubits": 4, "n_quantum_layers": 2}

        trainer = QuantumEnhancedLLMTrainer(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "train.jsonl"

            with open(dataset_path, "w") as f:
                f.write('{"text": "Sample 1"}\n')
                f.write('{"text": "Sample 2"}\n')

            dataset = trainer._load_dataset(dataset_path)

            assert len(dataset) == 2
            assert dataset[0]["text"] == "Sample 1"

    def test_train_epoch_with_quantum(self):
        """Test training epoch with quantum enhancement"""
        config = {"quantum_backend": "local", "n_qubits": 4, "n_quantum_layers": 2}

        trainer = QuantumEnhancedLLMTrainer(config)

        mock_dataset = [{"text": f"Sample {i}"} for i in range(100)]

        loss = trainer._train_epoch_with_quantum(
            model=None, dataset=mock_dataset, epoch=0
        )

        # Check loss is reasonable
        assert isinstance(loss, float)
        assert loss > 0
        assert loss < 10

        # Check quantum metrics updated
        assert trainer.quantum_metrics["circuit_executions"] > 0
        assert len(trainer.training_history) == 1


@pytest.mark.integration
class TestQuantumLLMIntegration:
    """Integration tests for quantum LLM training"""

    def test_full_training_pipeline(self):
        """Test complete training pipeline"""
        config = {
            "quantum_backend": "local",
            "n_qubits": 4,
            "n_quantum_layers": 2,
            "passive": False,
        }

        trainer = QuantumEnhancedLLMTrainer(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "train.json"
            output_dir = Path(tmpdir) / "output"

            # Create larger mock dataset
            mock_data = [
                {
                    "messages": [
                        {"role": "user", "content": f"Question {i}"},
                        {"role": "assistant", "content": f"Answer {i}"},
                    ]
                }
                for i in range(50)
            ]

            with open(dataset_path, "w") as f:
                json.dump(mock_data, f)

            # Run full training
            results = trainer.train_with_quantum_enhancement(
                model=None, dataset_path=dataset_path, output_dir=output_dir, epochs=2
            )

            # Verify results
            assert results["status"] == "success"
            assert results["epochs_completed"] == 2
            assert results["quantum_metrics"]["circuit_executions"] > 0

            # Verify training history
            assert len(trainer.training_history) == 2

            # Verify loss decreased
            if len(trainer.training_history) > 1:
                first_loss = trainer.training_history[0]["loss"]
                last_loss = trainer.training_history[-1]["loss"]
                # Loss should decrease or stay similar
                assert last_loss <= first_loss * 1.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
