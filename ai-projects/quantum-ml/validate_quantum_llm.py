#!/usr/bin/env python3
"""
Quantum LLM Validation Suite
=============================

Comprehensive validation of all quantum LLM components.

This script tests all components and generates a validation report.

Usage:
    python validate_quantum_llm.py --quick
    python validate_quantum_llm.py --full
    python validate_quantum_llm.py --report-only

Author: Quantum AI Workspace
Date: March 9, 2026
"""

import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import json

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

logger = logging.getLogger(__name__)


class ComponentValidator:
    """Validates individual quantum LLM components."""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def validate_component(self, name: str, import_path: str, test_func=None) -> Dict[str, Any]:
        """Validate a single component."""
        result = {
            "component": name,
            "import_path": import_path,
            "status": "unknown",
            "error": None,
            "test_passed": False,
            "import_time": 0.0,
        }
        
        try:
            # Test import
            start = time.time()
            module = __import__(import_path)
            result["import_time"] = time.time() - start
            result["status"] = "imported"
            
            # Run test if provided
            if test_func:
                test_func(module)
                result["test_passed"] = True
            else:
                result["test_passed"] = True  # No test means import success is enough
            
            result["status"] = "✅ PASS"
            logger.info(f"✅ {name}: PASS")
            
        except ImportError as e:
            result["status"] = "❌ IMPORT FAILED"
            result["error"] = str(e)
            logger.error(f"❌ {name}: Import failed - {e}")
            
        except Exception as e:
            result["status"] = "❌ TEST FAILED"
            result["error"] = str(e)
            logger.error(f"❌ {name}: Test failed - {e}")
        
        self.results.append(result)
        return result
    
    def validate_all(self) -> Dict[str, Any]:
        """Validate all quantum LLM components."""
        logger.info("=" * 80)
        logger.info("QUANTUM LLM VALIDATION SUITE")
        logger.info("=" * 80)
        
        components = [
            {
                "name": "Advanced Quantum Components",
                "import_path": "src.quantum_llm_advanced",
                "description": "Circuit caching, adaptive layers, multi-scale attention"
            },
            {
                "name": "Circuit Optimizer",
                "import_path": "src.quantum_circuit_optimizer",
                "description": "Circuit compilation, batch execution, scheduling"
            },
            {
                "name": "Hybrid Trainer",
                "import_path": "src.quantum_llm_hybrid_trainer",
                "description": "Curriculum learning, adaptive routing, orchestration"
            },
            {
                "name": "Training Monitor",
                "import_path": "src.quantum_llm_monitor",
                "description": "Real-time monitoring, metrics, dashboard"
            },
            {
                "name": "Integrated System",
                "import_path": "src.quantum_llm_integrated",
                "description": "Complete integrated quantum LLM system"
            },
            {
                "name": "Dataset Utilities",
                "import_path": "src.quantum_llm_datasets",
                "description": "Tokenization, data loading, augmentation"
            },
        ]
        
        logger.info("\n📦 Validating Components:\n")
        
        for component in components:
            logger.info(f"Testing: {component['name']}")
            logger.info(f"  Description: {component['description']}")
            self.validate_component(
                component["name"],
                component["import_path"]
            )
            logger.info("")
        
        # Generate summary
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "✅ PASS")
        failed = total - passed
        
        summary = {
            "total_components": total,
            "passed": passed,
            "failed": failed,
            "success_rate": passed / total if total > 0 else 0.0,
            "total_time": time.time() - self.start_time,
            "results": self.results,
        }
        
        logger.info("=" * 80)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Components: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {summary['success_rate']:.1%}")
        logger.info(f"Total Time: {summary['total_time']:.2f}s")
        logger.info("=" * 80)
        
        if failed == 0:
            logger.info("🎉 ALL COMPONENTS VALIDATED SUCCESSFULLY!")
        else:
            logger.warning(f"⚠️  {failed} component(s) failed validation")
        
        return summary


def run_quick_validation():
    """Quick validation - import tests only."""
    logger.info("Running QUICK validation (import tests)...")
    validator = ComponentValidator()
    summary = validator.validate_all()
    return summary


def run_full_validation():
    """Full validation - imports + functional tests."""
    logger.info("Running FULL validation (imports + tests)...")
    
    validator = ComponentValidator()
    
    # Import tests
    import_summary = validator.validate_all()
    
    # Functional tests
    logger.info("\n" + "=" * 80)
    logger.info("FUNCTIONAL TESTS")
    logger.info("=" * 80)
    
    functional_results = []
    
    # Test 1: Tokenizer
    logger.info("\n🧪 Test 1: Character Tokenizer")
    try:
        from src.quantum_llm_datasets import CharacterTokenizer
        tokenizer = CharacterTokenizer(vocab_size=256)
        text = "Hello Quantum"
        encoded = tokenizer.encode(text)
        decoded = tokenizer.decode(encoded)
        assert decoded.strip() == text, f"Decode mismatch: {decoded} != {text}"
        logger.info("✅ Tokenizer test PASSED")
        functional_results.append({"test": "Tokenizer", "status": "✅ PASS"})
    except Exception as e:
        logger.error(f"❌ Tokenizer test FAILED: {e}")
        functional_results.append({"test": "Tokenizer", "status": "❌ FAIL", "error": str(e)})
    
    # Test 2: Dataset
    logger.info("\n🧪 Test 2: Text Dataset")
    try:
        from src.quantum_llm_datasets import TextDataset, CharacterTokenizer
        tokenizer = CharacterTokenizer(vocab_size=256)
        dataset = TextDataset(
            texts=["Test text 1", "Test text 2"],
            tokenizer=tokenizer,
            max_seq_length=64,
        )
        assert len(dataset) > 0, "Dataset is empty"
        input_ids, target_ids = dataset[0]
        assert input_ids.shape == target_ids.shape, "Shape mismatch"
        logger.info("✅ Dataset test PASSED")
        functional_results.append({"test": "Dataset", "status": "✅ PASS"})
    except Exception as e:
        logger.error(f"❌ Dataset test FAILED: {e}")
        functional_results.append({"test": "Dataset", "status": "❌ FAIL", "error": str(e)})
    
    # Test 3: Circuit Cache
    logger.info("\n🧪 Test 3: Circuit Cache")
    try:
        from src.quantum_llm_advanced import QuantumCircuitCache
        cache = QuantumCircuitCache(cache_size=10)
        
        # Test caching
        import torch
        key = "test_key"
        value = torch.randn(4, 64)
        
        cache.put(key, value)
        retrieved = cache.get(key)
        assert retrieved is not None, "Cache retrieval failed"
        assert torch.allclose(retrieved, value), "Cache value mismatch"
        
        stats = cache.get_stats()
        assert stats["hits"] == 1, f"Expected 1 hit, got {stats['hits']}"
        
        logger.info("✅ Circuit cache test PASSED")
        functional_results.append({"test": "CircuitCache", "status": "✅ PASS"})
    except Exception as e:
        logger.error(f"❌ Circuit cache test FAILED: {e}")
        functional_results.append({"test": "CircuitCache", "status": "❌ FAIL", "error": str(e)})
    
    # Test 4: Configuration
    logger.info("\n🧪 Test 4: Configuration System")
    try:
        from src.quantum_llm_integrated import QuantumLLMConfig
        config = QuantumLLMConfig()
        
        # Test default config
        assert config["vocab_size"] > 0, "Invalid vocab_size"
        assert config["d_model"] > 0, "Invalid d_model"
        assert config["n_qubits"] > 0, "Invalid n_qubits"
        
        # Test config update
        config.config["batch_size"] = 32
        assert config["batch_size"] == 32, "Config update failed"
        
        logger.info("✅ Configuration test PASSED")
        functional_results.append({"test": "Configuration", "status": "✅ PASS"})
    except Exception as e:
        logger.error(f"❌ Configuration test FAILED: {e}")
        functional_results.append({"test": "Configuration", "status": "❌ FAIL", "error": str(e)})
    
    # Test 5: Dashboard
    logger.info("\n🧪 Test 5: Training Dashboard")
    try:
        from src.quantum_llm_monitor import TrainingDashboard, TrainingSnapshot, QuantumMetrics
        dashboard = TrainingDashboard(
            output_dir=Path("data_out/test_dashboard"),
            update_interval=100,
        )
        
        # Test snapshot
        import torch
        snapshot = TrainingSnapshot(
            timestamp=time.time(),
            global_step=1,
            epoch=0,
            loss=2.5,
            perplexity=12.0,
            learning_rate=1e-4,
            batch_size=16,
            quantum_metrics=QuantumMetrics(
                circuit_execution_time=0.1,
                circuit_depth=10,
                gate_count=50,
                qubit_count=4,
            ),
        )
        
        dashboard.update(snapshot)
        
        logger.info("✅ Dashboard test PASSED")
        functional_results.append({"test": "Dashboard", "status": "✅ PASS"})
    except Exception as e:
        logger.error(f"❌ Dashboard test FAILED: {e}")
        functional_results.append({"test": "Dashboard", "status": "❌ FAIL", "error": str(e)})
    
    # Summarize functional tests
    logger.info("\n" + "=" * 80)
    logger.info("FUNCTIONAL TEST SUMMARY")
    logger.info("=" * 80)
    
    total_functional = len(functional_results)
    passed_functional = sum(1 for r in functional_results if r["status"] == "✅ PASS")
    
    for result in functional_results:
        status_str = result["status"]
        logger.info(f"{status_str} {result['test']}")
    
    logger.info(f"\nFunctional Tests: {passed_functional}/{total_functional} passed")
    logger.info("=" * 80)
    
    # Combined summary
    combined_summary = {
        "import_validation": import_summary,
        "functional_tests": {
            "total": total_functional,
            "passed": passed_functional,
            "failed": total_functional - passed_functional,
            "results": functional_results,
        },
        "overall_status": "✅ PASS" if (import_summary["failed"] == 0 and passed_functional == total_functional) else "❌ SOME FAILURES",
    }
    
    return combined_summary


def generate_validation_report(summary: Dict[str, Any], output_path: Path):
    """Generate comprehensive validation report."""
    
    report_lines = [
        "# Quantum LLM Validation Report",
        f"\n**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"\n**Status:** {summary.get('overall_status', summary.get('status', 'Unknown'))}",
        "\n---\n",
    ]
    
    # Import validation
    if "import_validation" in summary:
        import_val = summary["import_validation"]
        report_lines.append("\n## Import Validation\n")
        report_lines.append(f"- Total Components: {import_val['total_components']}")
        report_lines.append(f"- Passed: {import_val['passed']}")
        report_lines.append(f"- Failed: {import_val['failed']}")
        report_lines.append(f"- Success Rate: {import_val['success_rate']:.1%}")
        report_lines.append(f"- Total Time: {import_val['total_time']:.2f}s\n")
        
        report_lines.append("\n### Component Details\n")
        for result in import_val['results']:
            status_emoji = "✅" if result["status"] == "✅ PASS" else "❌"
            report_lines.append(f"- {status_emoji} **{result['component']}**")
            if result.get("error"):
                report_lines.append(f"  - Error: `{result['error']}`")
    
    # Functional tests
    if "functional_tests" in summary:
        func_tests = summary["functional_tests"]
        report_lines.append("\n## Functional Tests\n")
        report_lines.append(f"- Total Tests: {func_tests['total']}")
        report_lines.append(f"- Passed: {func_tests['passed']}")
        report_lines.append(f"- Failed: {func_tests['failed']}\n")
        
        report_lines.append("\n### Test Details\n")
        for result in func_tests['results']:
            status_emoji = "✅" if "✅" in result["status"] else "❌"
            report_lines.append(f"- {status_emoji} **{result['test']}**")
            if result.get("error"):
                report_lines.append(f"  - Error: `{result['error']}`")
    
    # Recommendations
    report_lines.append("\n---\n")
    report_lines.append("\n## Recommendations\n")
    
    if summary.get("overall_status") == "✅ PASS":
        report_lines.append("✅ **All validations passed!** The quantum LLM system is ready to use.\n")
        report_lines.append("**Next Steps:**")
        report_lines.append("- Run quick start: `python quantum_llm_quickstart.py --mode quick`")
        report_lines.append("- Review documentation: `QUANTUM_LLM_README.md`")
        report_lines.append("- Configure for your use case: `config/quantum_llm_config_example.yaml`")
    else:
        report_lines.append("⚠️ **Some validations failed.** Review errors above.\n")
        report_lines.append("**Troubleshooting:**")
        report_lines.append("- Check Python version (3.8+ required)")
        report_lines.append("- Install dependencies: `pip install torch pennylane pyyaml numpy`")
        report_lines.append("- Verify file paths and imports")
    
    report_lines.append("\n---\n")
    report_lines.append("\n*Generated by Quantum LLM Validation Suite*")
    
    # Write report
    report_text = "\n".join(report_lines)
    with open(output_path, 'w') as f:
        f.write(report_text)
    
    logger.info(f"\n📄 Validation report saved: {output_path}")
    return output_path


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quantum LLM Validation Suite")
    parser.add_argument("--quick", action="store_true", help="Quick validation (imports only)")
    parser.add_argument("--full", action="store_true", help="Full validation (imports + tests)")
    parser.add_argument("--report-only", action="store_true", help="Generate report from last run")
    parser.add_argument("--output", type=str, default="data_out/quantum_llm_validation_report.md", help="Report output path")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Run validation
    if args.report_only:
        # Try to load existing results
        logger.info("Report-only mode not yet implemented")
        return
    elif args.full:
        summary = run_full_validation()
    else:
        # Default or --quick
        summary = run_quick_validation()
    
    # Generate report
    report_path = generate_validation_report(summary, output_path)
    
    # Also save JSON
    json_path = output_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"📄 JSON report saved: {json_path}")
    
    # Final status
    logger.info("\n" + "=" * 80)
    if summary.get("overall_status") == "✅ PASS":
        logger.info("🎉 VALIDATION SUCCESSFUL - QUANTUM LLM SYSTEM READY!")
    else:
        logger.info("⚠️  VALIDATION COMPLETED WITH SOME FAILURES - REVIEW REPORT")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
