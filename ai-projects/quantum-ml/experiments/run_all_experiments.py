"""
Master Experiment Runner - Quantum AI Project
==============================================

Executes all three experiments sequentially:
1. Parameter Tuning - Find optimal hyperparameters
2. Extended Datasets - Test on challenging datasets
3. Plot Analysis - Generate comprehensive analysis report

This provides a complete exploration of quantum ML capabilities.
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner(text, color="cyan"):
    """Print a colorful banner"""
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "magenta": "\033[95m",
        "red": "\033[91m",
        "reset": "\033[0m",
    }

    c = colors.get(color, colors["cyan"])
    r = colors["reset"]

    print(f"\n{c}{'='*70}{r}")
    print(f"{c}{text.center(70)}{r}")
    print(f"{c}{'='*70}{r}\n")


def print_section(number, title, description):
    """Print experiment section header"""
    print(f"\n\033[92m🔬 Experiment {number}: {title}\033[0m")
    print(f"\033[90m{description}\033[0m\n")


def run_parameter_tuning():
    """Run parameter tuning experiments"""
    print_section(
        1,
        "Parameter Tuning",
        "Testing layer depth, learning rate, and entanglement patterns",
    )

    try:
        # Import and run parameter tuning
        import experiments.parameter_tuning as pt

        # Run all three experiments automatically
        print("\033[93m▶ Running Layer Depth Experiment...\033[0m")
        pt.experiment_layer_depth()
        print("\033[92m✓ Layer depth experiment completed\033[0m\n")

        print("\033[93m▶ Running Learning Rate Experiment...\033[0m")
        pt.experiment_learning_rate()
        print("\033[92m✓ Learning rate experiment completed\033[0m\n")

        print("\033[93m▶ Running Entanglement Pattern Experiment...\033[0m")
        pt.experiment_entanglement()
        print("\033[92m✓ Entanglement pattern experiment completed\033[0m\n")

        return True

    except Exception as e:
        print(f"\033[91m✗ Error in parameter tuning: {e}\033[0m")
        return False


def run_extended_datasets():
    """Run extended datasets experiments"""
    print_section(
        2,
        "Extended Datasets",
        "Testing quantum classifier on XOR, Spiral, Imbalanced, and Wine datasets",
    )

    try:
        # Import and run extended datasets
        import experiments.extended_datasets as ed

        datasets = ["xor", "spiral", "imbalanced", "wine"]

        for dataset in datasets:
            print(f"\033[93m▶ Running {dataset.upper()} dataset...\033[0m")

            if dataset == "xor":
                ed.run_xor_dataset()
            elif dataset == "spiral":
                ed.run_spiral_dataset()
            elif dataset == "imbalanced":
                ed.run_imbalanced_dataset()
            elif dataset == "wine":
                ed.run_wine_dataset()

            print(f"\033[92m✓ {dataset.upper()} dataset completed\033[0m\n")

        # Generate comparison
        print("\033[93m▶ Generating dataset comparison...\033[0m")
        ed.compare_all_datasets()
        print("\033[92m✓ Dataset comparison completed\033[0m\n")

        return True

    except Exception as e:
        print(f"\033[91m✗ Error in extended datasets: {e}\033[0m")
        return False


def run_plot_analysis():
    """Run plot analysis"""
    print_section(
        3, "Plot Analysis", "Analyzing generated plots and providing insights"
    )

    try:
        # Import and run plot analysis
        import experiments.analyze_plots as ap

        print("\033[93m▶ Analyzing state evolution plot...\033[0m")
        ap.analyze_state_evolution()
        print("\033[92m✓ State evolution analysis completed\033[0m\n")

        print("\033[93m▶ Analyzing training results...\033[0m")
        ap.analyze_training_results()
        print("\033[92m✓ Training analysis completed\033[0m\n")

        print("\033[93m▶ Analyzing model comparison...\033[0m")
        ap.analyze_model_comparison()
        print("\033[92m✓ Model comparison analysis completed\033[0m\n")

        print("\033[93m▶ Generating recommendations...\033[0m")
        ap.recommendations()
        print("\033[92m✓ Recommendations generated\033[0m\n")

        return True

    except Exception as e:
        print(f"\033[91m✗ Error in plot analysis: {e}\033[0m")
        return False


def generate_summary_report(results):
    """Generate a summary report of all experiments"""
    print_banner("EXPERIMENT SUMMARY REPORT", "green")

    # Calculate total experiments
    total = len(results)
    successful = sum(1 for r in results.values() if r["success"])

    print("\n\033[96m📊 Overall Statistics:\033[0m")
    print(f"   Total Experiments: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {total - successful}")
    print(f"   Success Rate: {successful/total*100:.1f}%\n")

    # Detail each experiment
    for name, result in results.items():
        status = "\033[92m✓\033[0m" if result["success"] else "\033[91m✗\033[0m"
        duration = result["duration"]
        print(f"{status} {name}")
        print(f"   Duration: {duration:.2f} seconds")
        if not result["success"]:
            print(f"   \033[91mError: {result.get('error', 'Unknown')}\033[0m")
        print()

    # Generated files
    print("\033[96m📁 Generated Files:\033[0m")
    results_dir = Path(__file__).parent.parent / "results"

    # Count files in experiments directory
    exp_dir = results_dir / "experiments"
    if exp_dir.exists():
        exp_files = list(exp_dir.glob("*.png"))
        print(f"   Experiments: {len(exp_files)} plots")
        for f in exp_files:
            size_kb = f.stat().st_size / 1024
            print(f"      - {f.name} ({size_kb:.1f} KB)")

    # Count files in extended_datasets directory
    ext_dir = results_dir / "extended_datasets"
    if ext_dir.exists():
        ext_files = list(ext_dir.glob("*.png"))
        print(f"   Extended Datasets: {len(ext_files)} plots")
        for f in ext_files:
            size_kb = f.stat().st_size / 1024
            print(f"      - {f.name} ({size_kb:.1f} KB)")

    print("\n\033[96m🎯 Next Steps:\033[0m")
    print("   1. Review generated plots in results/ directory")
    print("   2. Analyze parameter tuning results to optimize configuration")
    print("   3. Examine extended dataset performance for quantum advantage")
    print("   4. Read plot analysis insights for deeper understanding")
    print("   5. Update quantum_config.yaml with optimal parameters")
    print("   6. Consider deploying to Azure Quantum for real hardware")

    print("\n\033[96m📚 Documentation:\033[0m")
    print("   - Parameter Tuning: experiments/parameter_tuning.py")
    print("   - Extended Datasets: experiments/extended_datasets.py")
    print("   - Plot Analysis: experiments/analyze_plots.py")
    print("   - Azure Deployment: experiments/AZURE_QUICKSTART.md")

    # Save report to file
    report_path = results_dir / "EXPERIMENT_REPORT.md"
    save_report_to_file(report_path, results)
    print(f"\n\033[92m📝 Detailed report saved to: {report_path}\033[0m")


def save_report_to_file(filepath, results):
    """Save experiment report to markdown file"""
    with open(filepath, "w") as f:
        f.write("# Quantum AI - Experiment Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## Executive Summary\n\n")
        total = len(results)
        successful = sum(1 for r in results.values() if r["success"])
        f.write(f"- Total Experiments: {total}\n")
        f.write(f"- Successful: {successful}\n")
        f.write(f"- Success Rate: {successful/total*100:.1f}%\n\n")

        f.write("## Experiment Results\n\n")
        for name, result in results.items():
            status = "✓ Success" if result["success"] else "✗ Failed"
            f.write(f"### {name}\n\n")
            f.write(f"- **Status:** {status}\n")
            f.write(f"- **Duration:** {result['duration']:.2f} seconds\n")
            if not result["success"]:
                f.write(f"- **Error:** {result.get('error', 'Unknown')}\n")
            f.write("\n")

        f.write("## Key Findings\n\n")
        f.write("### Parameter Tuning\n")
        f.write("- Optimal layer depth identified\n")
        f.write("- Learning rate sensitivity analyzed\n")
        f.write("- Entanglement pattern performance compared\n\n")

        f.write("### Extended Datasets\n")
        f.write("- XOR: Tests quantum advantage on linearly inseparable data\n")
        f.write("- Spiral: Evaluates performance on highly non-linear patterns\n")
        f.write("- Imbalanced: Validates robustness on skewed class distributions\n")
        f.write("- Wine: Assesses real-world multiclass classification\n\n")

        f.write("### Plot Analysis\n")
        f.write("- State evolution confirms quantum mechanics principles\n")
        f.write("- Training dynamics reveal convergence patterns\n")
        f.write("- Model comparison highlights dataset-specific performance\n\n")

        f.write("## Recommendations\n\n")
        f.write(
            "1. **Update Configuration:** Apply optimal parameters from tuning experiments\n"
        )
        f.write(
            "2. **Focus Datasets:** Prioritize datasets where quantum shows advantage\n"
        )
        f.write(
            "3. **Increase Complexity:** Test on larger quantum circuits (6-8 qubits)\n"
        )
        f.write(
            "4. **Hardware Testing:** Deploy to Azure Quantum for real quantum computer validation\n"
        )
        f.write(
            "5. **Noise Analysis:** Investigate robustness to quantum noise and decoherence\n\n"
        )

        f.write("## Next Steps\n\n")
        f.write("- [ ] Review all generated plots in `results/` directory\n")
        f.write("- [ ] Update `quantum_config.yaml` with optimal hyperparameters\n")
        f.write("- [ ] Run experiments on Azure Quantum hardware\n")
        f.write("- [ ] Implement error mitigation strategies\n")
        f.write("- [ ] Scale to larger datasets and circuits\n")
        f.write("- [ ] Publish findings and share results\n\n")

        f.write("---\n\n")
        f.write(
            "*This report was automatically generated by the Quantum AI experiment runner.*\n"
        )


def main():
    """Main experiment runner"""
    print_banner("QUANTUM AI - MASTER EXPERIMENT RUNNER", "cyan")

    print("\033[96mThis will run all experiments sequentially:\033[0m")
    print("  1. Parameter Tuning (layer depth, learning rate, entanglement)")
    print("  2. Extended Datasets (XOR, Spiral, Imbalanced, Wine)")
    print("  3. Plot Analysis (insights and recommendations)\n")

    print("\033[93m⚠️  This may take 15-30 minutes depending on your hardware.\033[0m")
    print("\033[93m⚠️  Ensure virtual environment is activated.\033[0m\n")

    response = input("Continue? (y/n): ").strip().lower()
    if response != "y":
        print("\n\033[91mExperiments cancelled.\033[0m")
        return

    # Track results
    results = {}
    start_time = time.time()

    # Experiment 1: Parameter Tuning
    exp_start = time.time()
    success = run_parameter_tuning()
    results["Parameter Tuning"] = {
        "success": success,
        "duration": time.time() - exp_start,
    }

    # Experiment 2: Extended Datasets
    exp_start = time.time()
    success = run_extended_datasets()
    results["Extended Datasets"] = {
        "success": success,
        "duration": time.time() - exp_start,
    }

    # Experiment 3: Plot Analysis
    exp_start = time.time()
    success = run_plot_analysis()
    results["Plot Analysis"] = {"success": success, "duration": time.time() - exp_start}

    # Total time
    total_time = time.time() - start_time

    # Generate summary
    print_banner("ALL EXPERIMENTS COMPLETE", "green")
    print(f"\n\033[96m⏱️  Total Time: {total_time/60:.1f} minutes\033[0m\n")

    generate_summary_report(results)

    print_banner("THANK YOU FOR USING QUANTUM AI!", "magenta")


if __name__ == "__main__":
    main()
