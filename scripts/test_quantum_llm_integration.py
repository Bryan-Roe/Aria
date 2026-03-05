#!/usr/bin/env python3
"""
Comprehensive integration test for Quantum-Enhanced LLM Training
Verifies all components are properly integrated and functional.
"""

import sys
import json
import tempfile
import importlib
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add scripts to path
scripts_path = Path(__file__).parent
sys.path.insert(0, str(scripts_path))
sys.path.insert(0, str(scripts_path.parent / "quantum"))
sys.path.insert(0, str(scripts_path.parent / "quantum" / "src"))


def test_imports():
    """Test that all required modules can be imported"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Module Imports")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    # Test quantum-LLM trainer import
    try:
        trainer_mod = importlib.import_module("quantum_llm_trainer")
        _ = trainer_mod.QuantumAttentionOptimizer
        _ = trainer_mod.QuantumFeatureEncoder
        _ = trainer_mod.QuantumEnhancedLLMTrainer
        TRANSFORMERS_AVAILABLE = trainer_mod.TRANSFORMERS_AVAILABLE
        logger.info("✅ quantum_llm_trainer imports successful")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Failed to import quantum_llm_trainer: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    # Test quantum module imports (optional)
    try:
        importlib.import_module("quantum_classifier")
        importlib.import_module("hybrid_qnn")
        logger.info(
            "✅ Quantum modules (quantum_classifier, hybrid_qnn) available"
        )
        tests_passed += 1
    except ImportError:
        logger.warning(
            "⚠️ Quantum modules not available (expected in some environments)"
        )

    # Test transformers availability
    logger.info(f"  Transformers available: {TRANSFORMERS_AVAILABLE}")

    return tests_passed, tests_failed


def test_configuration():
    """Test configuration loading"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Configuration Loading")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    quantum_config_path = Path("config/quantum_llm_config.yaml")
    autonomous_config_path = Path("config/autonomous_training.yaml")

    # Test quantum config
    try:
        import yaml
        with open(quantum_config_path) as f:
            quantum_config = yaml.safe_load(f)

        required_keys = [
            "quantum_settings",
            "passive_training",
            "llm_training",
        ]
        missing = [k for k in required_keys if k not in quantum_config]

        if missing:
            logger.error(f"❌ quantum_config missing keys: {missing}")
            tests_failed += 1
        else:
            logger.info("✅ quantum_llm_config.yaml valid")
            tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Failed to load quantum config: {e}")
        tests_failed += 1

    # Test autonomous config
    try:
        with open(autonomous_config_path) as f:
            autonomous_config = yaml.safe_load(f)

        if "quantum_llm" not in autonomous_config:
            logger.error(
                "❌ autonomous_training.yaml missing quantum_llm config"
            )
            tests_failed += 1
        elif not autonomous_config.get("quantum_llm", {}).get("enabled"):
            logger.warning(
                "⚠️ quantum_llm.enabled is False in autonomous config"
            )
        else:
            logger.info(
                "✅ autonomous_training.yaml has quantum_llm integration"
            )
            tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Failed to load autonomous config: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_trainer_initialization():
    """Test trainer can be initialized"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Trainer Initialization")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    try:
        from quantum_llm_trainer import QuantumEnhancedLLMTrainer

        config = {
            "quantum_backend": "local",
            "n_qubits": 4,
            "n_quantum_layers": 2,
            "passive": False,
        }

        trainer = QuantumEnhancedLLMTrainer(config)

        # Verify initialization
        assert trainer.quantum_backend == "local"
        assert trainer.n_qubits == 4
        assert trainer.n_layers == 2

        logger.info("✅ QuantumEnhancedLLMTrainer initialized successfully")
        tests_passed += 1
    except Exception as e:
        logger.error(f"❌ Failed to initialize trainer: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_optimizer_and_encoder():
    """Test quantum optimizer and encoder"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Quantum Optimizer & Encoder")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    try:
        import torch
        from quantum_llm_trainer import (
            QuantumAttentionOptimizer,
            QuantumFeatureEncoder,
        )

        # Test optimizer
        optimizer = QuantumAttentionOptimizer(n_qubits=4, n_layers=2)
        attention_scores = torch.randn(2, 8, 8)
        optimized = optimizer.optimize_attention_weights(attention_scores)

        assert optimized.shape == attention_scores.shape
        assert not torch.isnan(optimized).any()
        assert not torch.isinf(optimized).any()

        logger.info("✅ QuantumAttentionOptimizer works correctly")
        tests_passed += 1

        # Test encoder
        encoder = QuantumFeatureEncoder(n_qubits=4, n_layers=2)
        features = torch.randn(4, 16)
        encoded = encoder.encode(features)

        assert not torch.isnan(encoded).any()
        assert not torch.isinf(encoded).any()

        logger.info("✅ QuantumFeatureEncoder works correctly")
        tests_passed += 1

    except Exception as e:
        logger.error(f"❌ Optimizer/Encoder test failed: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_training_pipeline():
    """Test training pipeline with mock data"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Training Pipeline")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    try:
        from quantum_llm_trainer import QuantumEnhancedLLMTrainer

        config = {
            "quantum_backend": "local",
            "n_qubits": 4,
            "n_quantum_layers": 2,
            "passive": False,
        }

        trainer = QuantumEnhancedLLMTrainer(config)

        # Create temp dataset
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir) / "train.json"
            output_dir = Path(tmpdir) / "output"

            mock_data = [
                {"messages": [
                    {"role": "user", "content": f"Q{i}"},
                    {"role": "assistant", "content": f"A{i}"}
                ]}
                for i in range(10)
            ]

            with open(dataset_path, 'w') as f:
                json.dump(mock_data, f)

            # Run training
            results = trainer.train_with_quantum_enhancement(
                model=None,
                dataset_path=dataset_path,
                output_dir=output_dir,
                epochs=1
            )

            # Verify results
            assert results["status"] == "success"
            assert results["epochs_completed"] == 1
            assert "quantum_metrics" in results
            assert results["quantum_metrics"]["circuit_executions"] > 0

            # Verify output files
            assert output_dir.exists()
            assert (output_dir / "quantum_training_results.json").exists()

            logger.info("✅ Training pipeline executed successfully")
            tests_passed += 1

    except Exception as e:
        logger.error(f"❌ Training pipeline failed: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_orchestrator_config():
    """Test that autonomous orchestrator can load quantum config"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Orchestrator Integration")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    try:
        import yaml

        # Load autonomous config
        with open("config/autonomous_training.yaml") as f:
            config = yaml.safe_load(f)

        quantum_config = config.get("quantum_llm", {})

        # Verify quantum config structure
        required_keys = [
            "enabled",
            "passive_mode",
            "backend",
            "training_interval_minutes",
        ]
        missing = [k for k in required_keys if k not in quantum_config]

        if missing:
            logger.error(f"❌ quantum_llm config missing keys: {missing}")
            tests_failed += 1
        else:
            logger.info("✅ Orchestrator has proper quantum_llm configuration")
            tests_passed += 1

        # Verify quantum training script exists
        quantum_script = Path("scripts/quantum_llm_trainer.py")
        if not quantum_script.exists():
            logger.error("❌ quantum_llm_trainer.py script not found")
            tests_failed += 1
        else:
            logger.info(
                "✅ quantum_llm_trainer.py script exists and is accessible"
            )
            tests_passed += 1

    except Exception as e:
        logger.error(f"❌ Orchestrator integration test failed: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def test_repo_automation():
    """Test that repo automation includes quantum LLM"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Repo Automation Wiring")
    logger.info("=" * 80)

    tests_passed = 0
    tests_failed = 0

    try:
        repo_auto_path = Path("scripts/repo_automation.py")

        if not repo_auto_path.exists():
            logger.warning("⚠️ repo_automation.py not found (optional)")
            return tests_passed, tests_failed

        with open(repo_auto_path) as f:
            content = f.read()

        # Check orchestrator is called
        if "autonomous_training_orchestrator.py" in content:
            logger.info(
                "✅ repo_automation.py calls autonomous_training_orchestrator"
            )
            tests_passed += 1
        else:
            logger.warning(
                "⚠️ repo_automation.py may not call orchestrator properly"
            )

    except Exception as e:
        logger.error(f"❌ Repo automation test failed: {e}")
        tests_failed += 1

    return tests_passed, tests_failed


def generate_integration_report():
    """Generate comprehensive integration report"""
    logger.info("\n" + "=" * 80)
    logger.info("INTEGRATION VERIFICATION REPORT")
    logger.info("=" * 80)

    all_passed = 0
    all_failed = 0

    # Run all tests
    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Trainer Init", test_trainer_initialization),
        ("Quantum Ops", test_optimizer_and_encoder),
        ("Training", test_training_pipeline),
        ("Orchestrator", test_orchestrator_config),
        ("Repo Auto", test_repo_automation),
    ]

    results = {}
    for name, test_func in tests:
        try:
            passed, failed = test_func()
            results[name] = {"passed": passed, "failed": failed}
            all_passed += passed
            all_failed += failed
        except Exception as e:
            logger.error(f"❌ Test suite {name} crashed: {e}")
            all_failed += 1

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    for name, result in results.items():
        status = "✅" if result["failed"] == 0 else "⚠️"
        logger.info(
            f"{status} {name}: {result['passed']} passed, "
            f"{result['failed']} failed"
        )

    logger.info(f"\nTotal: {all_passed} passed, {all_failed} failed")

    if all_failed == 0:
        logger.info("\n🎉 ALL INTEGRATION TESTS PASSED!")
        logger.info(
            "\nQuantum-Enhanced LLM Training is fully integrated "
            "and ready for use:"
        )
        logger.info(
            "  • standalone: "
            "python scripts/quantum_llm_trainer.py --dataset ..."
        )
        logger.info(
            "  • passive: "
            "python scripts/quantum_llm_trainer.py --passive --config ..."
        )
        logger.info(
            "  • autonomous: "
            "python scripts/autonomous_training_orchestrator.py"
        )
        logger.info("  • full repo: python scripts/repo_automation.py --start")
    else:
        logger.warning(f"\n⚠️ {all_failed} test(s) failed. See details above.")

    return all_failed == 0


if __name__ == "__main__":
    success = generate_integration_report()
    sys.exit(0 if success else 1)
