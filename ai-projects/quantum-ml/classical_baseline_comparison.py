"""
Classical ML Baseline Comparison
Compare quantum models vs classical ML algorithms on all datasets

This script trains classical ML baselines (SVM, Random Forest, Neural Network)
on the same datasets used for quantum training to validate quantum advantage.
"""

import json
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")

# Set random seed for reproducibility
np.random.seed(42)

# Dataset configurations matching quantum training
DATASETS = {
    "banknote": {
        "path": Path(__file__).parent.parent / "datasets" / "quantum" / "banknote.csv",
        "target_col": -1,  # Last column
        "n_features": 4,
        "has_header": False,
    },
    "ionosphere": {
        "path": Path(__file__).parent.parent
        / "datasets"
        / "quantum"
        / "ionosphere.csv",
        "target_col": -1,  # Last column
        "n_features": 4,
        "has_header": False,
    },
    "sonar": {
        "path": Path(__file__).parent.parent / "datasets" / "quantum" / "sonar.csv",
        "target_col": -1,  # Last column
        "n_features": 4,
        "has_header": False,
    },
    "heart_disease": {
        "path": Path(__file__).parent.parent
        / "datasets"
        / "quantum"
        / "heart_disease.csv",
        "target_col": -1,  # Last column
        "n_features": 4,
        "missing_values": ["?"],
        "has_header": False,
    },
}

# Classical models to benchmark
CLASSICAL_MODELS = {
    "SVM (RBF)": SVC(kernel="rbf", C=1.0, gamma="scale", random_state=42),
    "SVM (Linear)": SVC(kernel="linear", C=1.0, random_state=42),
    "Random Forest": RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=42
    ),
    "Neural Network": MLPClassifier(
        hidden_layer_sizes=(16,),
        activation="relu",
        solver="adam",
        learning_rate_init=0.001,
        max_iter=1000,
        random_state=42,
    ),
}

# Quantum model results for comparison (from previous training)
QUANTUM_RESULTS = {
    "banknote": 1.0000,  # 100.00%
    "ionosphere": 0.8571,  # 85.71%
    "sonar": 0.7619,  # 76.19%
    "heart_disease": 0.9464,  # 94.64%
}


def load_and_preprocess_dataset(dataset_name, config):
    """Load and preprocess a dataset matching quantum training procedure"""
    print(f"\n{'='*70}")
    print(f"📁 Loading {dataset_name.upper()} Dataset")
    print(f"{'='*70}")

    dataset_path = config["path"]
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    # Load dataset
    has_header = config.get("has_header", True)
    header = "infer" if has_header else None

    if "missing_values" in config:
        df = pd.read_csv(
            dataset_path, header=header, na_values=config["missing_values"]
        )
    else:
        df = pd.read_csv(dataset_path, header=header)

    print(f"   Samples: {len(df)}")
    print(f"   Features: {len(df.columns) - 1}")

    # Handle missing values
    if df.isnull().sum().sum() > 0:
        print(f"   Missing values found: {df.isnull().sum().sum()}")
        imputer = SimpleImputer(strategy="median")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
        print("   ✅ Missing values imputed")

    # Separate features and target
    target_col = config["target_col"]
    if target_col == -1:
        # Last column is target
        X = df.iloc[:, :-1].values
        y = df.iloc[:, -1].values
    else:
        X = df.drop(columns=[target_col]).values
        y = df[target_col].values

    # For heart disease, binarize target (0 = no disease, >0 = disease)
    if dataset_name == "heart_disease":
        y = (y > 0).astype(int)

    # Convert string labels to numeric if needed
    if y.dtype == object:
        from sklearn.preprocessing import LabelEncoder

        le = LabelEncoder()
        y = le.fit_transform(y)

    print(f"   Classes: {len(np.unique(y))} ({np.bincount(y)})")

    # Train/test split (80/20 like quantum training)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Reduce to n_features using PCA (matching quantum qubit count)
    n_features = config["n_features"]
    pca = PCA(n_components=n_features, random_state=42)
    X_train_final = pca.fit_transform(X_train_scaled)
    X_test_final = pca.transform(X_test_scaled)

    explained_variance = pca.explained_variance_ratio_.sum() * 100
    print(
        f"   ✅ Reduced to {n_features} features (PCA variance: {explained_variance:.2f}%)"
    )
    print(f"   Train: {X_train_final.shape}, Test: {X_test_final.shape}")

    return X_train_final, X_test_final, y_train, y_test


def train_classical_model(model_name, model, X_train, X_test, y_train, y_test):
    """Train and evaluate a classical ML model"""
    print(f"\n🔧 Training {model_name}...")

    # Train model
    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Metrics
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)

    print(f"   Train Accuracy: {train_acc:.4f} ({train_acc*100:.2f}%)")
    print(f"   Test Accuracy:  {test_acc:.4f} ({test_acc*100:.2f}%)")

    # Classification report
    report = classification_report(
        y_test, y_pred_test, output_dict=True, zero_division=0
    )

    return {
        "model_name": model_name,
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "classification_report": report,
    }


def benchmark_dataset(dataset_name, config):
    """Benchmark all classical models on a dataset"""
    print(f"\n{'#'*70}")
    print(f"# BENCHMARKING: {dataset_name.upper()}")
    print(f"{'#'*70}")

    # Load data
    X_train, X_test, y_train, y_test = load_and_preprocess_dataset(dataset_name, config)

    # Train all classical models
    results = []
    for model_name, model in CLASSICAL_MODELS.items():
        result = train_classical_model(
            model_name, model, X_train, X_test, y_train, y_test
        )
        result["dataset"] = dataset_name
        results.append(result)

    # Add quantum result for comparison
    quantum_acc = QUANTUM_RESULTS.get(dataset_name, 0.0)
    results.append(
        {
            "dataset": dataset_name,
            "model_name": "Quantum Hybrid QNN",
            "train_accuracy": None,  # Not tracked separately in quantum training
            "test_accuracy": float(quantum_acc),
            "classification_report": None,
        }
    )

    # Summary table
    print(f"\n{'='*70}")
    print(f"📊 {dataset_name.upper()} - RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"{'Model':<25} {'Test Accuracy':<15} {'vs Quantum':<15}")
    print(f"{'-'*70}")

    for result in results:
        test_acc = result["test_accuracy"]
        model_name = result["model_name"]

        if model_name == "Quantum Hybrid QNN":
            vs_quantum = "BASELINE"
        else:
            diff = test_acc - quantum_acc
            if diff > 0:
                vs_quantum = f"+{diff*100:.2f}%"
            else:
                vs_quantum = f"{diff*100:.2f}%"

        print(f"{model_name:<25} {test_acc*100:>6.2f}%         {vs_quantum:<15}")

    print(f"{'='*70}\n")

    return results


def generate_comparison_plots(all_results):
    """Generate comparison visualizations"""
    print("\n📊 Generating comparison plots...")

    # Prepare data for plotting
    datasets = list(DATASETS.keys())
    model_names = list(CLASSICAL_MODELS.keys()) + ["Quantum Hybrid QNN"]

    # Create accuracy matrix
    accuracy_matrix = np.zeros((len(datasets), len(model_names)))

    for i, dataset in enumerate(datasets):
        dataset_results = [r for r in all_results if r["dataset"] == dataset]
        for j, model_name in enumerate(model_names):
            model_result = next(
                (r for r in dataset_results if r["model_name"] == model_name), None
            )
            if model_result:
                accuracy_matrix[i, j] = model_result["test_accuracy"] * 100

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Classical vs Quantum ML - Comprehensive Comparison",
        fontsize=16,
        fontweight="bold",
        y=0.995,
    )

    # Plot 1: Heatmap
    ax1 = axes[0, 0]
    sns.heatmap(
        accuracy_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        xticklabels=[m.replace(" ", "\n") for m in model_names],
        yticklabels=[d.replace("_", " ").title() for d in datasets],
        vmin=70,
        vmax=100,
        ax=ax1,
        cbar_kws={"label": "Accuracy (%)"},
    )
    ax1.set_title("Accuracy Heatmap (All Models × All Datasets)", fontweight="bold")
    ax1.set_ylabel("Dataset", fontweight="bold")
    ax1.set_xlabel("Model", fontweight="bold")

    # Plot 2: Grouped bar chart
    ax2 = axes[0, 1]
    x = np.arange(len(datasets))
    width = 0.15

    for i, model_name in enumerate(model_names):
        accuracies = [accuracy_matrix[j, i] for j in range(len(datasets))]
        offset = (i - len(model_names) / 2 + 0.5) * width
        bars = ax2.bar(x + offset, accuracies, width, label=model_name)

        # Highlight quantum model
        if model_name == "Quantum Hybrid QNN":
            for bar in bars:
                bar.set_edgecolor("red")
                bar.set_linewidth(2)

    ax2.set_ylabel("Test Accuracy (%)", fontweight="bold")
    ax2.set_xlabel("Dataset", fontweight="bold")
    ax2.set_title(
        "Model Performance Comparison (Grouped by Dataset)", fontweight="bold"
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels([d.replace("_", " ").title() for d in datasets])
    ax2.legend(loc="lower right", fontsize=8)
    ax2.grid(axis="y", alpha=0.3)
    ax2.set_ylim([70, 105])

    # Plot 3: Average performance
    ax3 = axes[1, 0]
    avg_accuracies = accuracy_matrix.mean(axis=0)
    colors = ["#1f77b4"] * (len(model_names) - 1) + ["#ff7f0e"]  # Quantum in orange
    bars = ax3.barh(model_names, avg_accuracies, color=colors, edgecolor="black")

    # Add value labels
    for i, (bar, acc) in enumerate(zip(bars, avg_accuracies)):
        ax3.text(acc + 0.5, i, f"{acc:.2f}%", va="center", fontweight="bold")

    ax3.set_xlabel("Average Test Accuracy (%)", fontweight="bold")
    ax3.set_title("Average Performance Across All Datasets", fontweight="bold")
    ax3.set_xlim([70, 100])
    ax3.grid(axis="x", alpha=0.3)

    # Plot 4: Quantum advantage/disadvantage
    ax4 = axes[1, 1]
    quantum_idx = model_names.index("Quantum Hybrid QNN")
    quantum_scores = accuracy_matrix[:, quantum_idx]

    best_classical_scores = np.max(
        np.delete(accuracy_matrix, quantum_idx, axis=1), axis=1
    )
    advantages = quantum_scores - best_classical_scores

    colors_adv = ["green" if a > 0 else "red" for a in advantages]
    bars = ax4.barh(
        [d.replace("_", " ").title() for d in datasets],
        advantages,
        color=colors_adv,
        edgecolor="black",
    )

    # Add value labels
    for i, (bar, adv) in enumerate(zip(bars, advantages)):
        x_pos = adv + (0.5 if adv > 0 else -0.5)
        ax4.text(x_pos, i, f"{adv:+.2f}%", va="center", fontweight="bold")

    ax4.axvline(0, color="black", linewidth=2, linestyle="--")
    ax4.set_xlabel("Quantum Advantage (% points vs Best Classical)", fontweight="bold")
    ax4.set_title("Quantum vs Best Classical Model (by Dataset)", fontweight="bold")
    ax4.grid(axis="x", alpha=0.3)

    plt.tight_layout()

    # Save plot
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    plot_path = results_dir / "classical_vs_quantum_comparison.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    print(f"   ✅ Saved plot to: {plot_path}")

    return accuracy_matrix, avg_accuracies


def generate_markdown_report(all_results, accuracy_matrix, avg_accuracies):
    """Generate detailed markdown report"""
    print("\n📄 Generating markdown report...")

    report = []
    report.append("# Classical vs Quantum ML - Benchmark Report")
    report.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    report.append("## Executive Summary\n")
    report.append(
        "This report compares quantum hybrid neural networks against classical ML baselines "
    )
    report.append(
        "across four quantum-classical datasets: banknote authentication, ionosphere radar, "
    )
    report.append("sonar detection, and heart disease diagnosis.\n")

    # Overall winner
    model_names = list(CLASSICAL_MODELS.keys()) + ["Quantum Hybrid QNN"]
    best_model_idx = np.argmax(avg_accuracies)
    best_model = model_names[best_model_idx]
    best_avg = avg_accuracies[best_model_idx]

    report.append(
        f"**🏆 Best Overall Model:** {best_model} ({best_avg:.2f}% average accuracy)\n"
    )

    # Quantum performance
    quantum_idx = model_names.index("Quantum Hybrid QNN")
    quantum_avg = avg_accuracies[quantum_idx]
    quantum_rank = sorted(avg_accuracies, reverse=True).index(quantum_avg) + 1

    report.append(
        f"**⚛️ Quantum Model:** Ranked #{quantum_rank} with {quantum_avg:.2f}% average accuracy\n"
    )

    # Dataset-by-dataset results
    report.append("\n## Detailed Results by Dataset\n")

    datasets = list(DATASETS.keys())
    for i, dataset in enumerate(datasets):
        report.append(f"\n### {dataset.replace('_', ' ').title()}\n")

        dataset_results = [r for r in all_results if r["dataset"] == dataset]
        sorted_results = sorted(
            dataset_results, key=lambda x: x["test_accuracy"], reverse=True
        )

        report.append("| Rank | Model | Test Accuracy | vs Quantum |")
        report.append("|------|-------|---------------|------------|")

        quantum_acc = QUANTUM_RESULTS[dataset]
        for rank, result in enumerate(sorted_results, 1):
            model_name = result["model_name"]
            test_acc = result["test_accuracy"]

            if model_name == "Quantum Hybrid QNN":
                vs_quantum = "BASELINE"
                emoji = "⚛️"
            else:
                diff = test_acc - quantum_acc
                vs_quantum = f"{diff*100:+.2f}%"
                emoji = "🥇" if rank == 1 else ""

            report.append(
                f"| {rank} | {emoji} {model_name} | {test_acc*100:.2f}% | {vs_quantum} |"
            )

        report.append("")

    # Average performance table
    report.append("\n## Average Performance Across All Datasets\n")
    report.append("| Rank | Model | Average Accuracy |")
    report.append("|------|-------|------------------|")

    sorted_indices = np.argsort(avg_accuracies)[::-1]
    for rank, idx in enumerate(sorted_indices, 1):
        model_name = model_names[idx]
        avg_acc = avg_accuracies[idx]
        emoji = (
            "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else ""))
        )
        if model_name == "Quantum Hybrid QNN":
            emoji += " ⚛️"
        report.append(f"| {rank} | {emoji} {model_name} | {avg_acc:.2f}% |")

    # Key insights
    report.append("\n## Key Insights\n")

    quantum_wins = sum(
        1
        for i in range(len(datasets))
        if accuracy_matrix[i, quantum_idx] == accuracy_matrix[i].max()
    )

    report.append(f"- **Quantum Model Won:** {quantum_wins}/{len(datasets)} datasets\n")

    best_quantum_dataset = datasets[np.argmax(accuracy_matrix[:, quantum_idx])]
    best_quantum_acc = accuracy_matrix[:, quantum_idx].max()
    report.append(
        f"- **Best Quantum Performance:** {best_quantum_dataset.replace('_', ' ').title()} ({best_quantum_acc:.2f}%)\n"
    )

    # Classical winner
    classical_avg = np.delete(avg_accuracies, quantum_idx)
    classical_names = [m for m in model_names if m != "Quantum Hybrid QNN"]
    best_classical_idx = np.argmax(classical_avg)
    best_classical = classical_names[best_classical_idx]
    best_classical_avg = classical_avg[best_classical_idx]

    report.append(
        f"- **Best Classical Model:** {best_classical} ({best_classical_avg:.2f}% average)\n"
    )

    # Quantum advantage
    quantum_advantage = quantum_avg - best_classical_avg
    if quantum_advantage > 0:
        report.append(
            f"- **⚛️ Quantum Advantage:** +{quantum_advantage:.2f}% over best classical\n"
        )
    else:
        report.append(
            f"- **Classical Advantage:** {abs(quantum_advantage):.2f}% over quantum\n"
        )

    # Recommendations
    report.append("\n## Recommendations\n")

    if quantum_wins >= len(datasets) / 2:
        report.append("- ✅ **Quantum models show promise** on these datasets\n")
        report.append(
            "- 🚀 **Next step:** Deploy to Azure Quantum hardware for validation\n"
        )
    else:
        report.append("- ⚠️ **Classical models outperform quantum** on average\n")
        report.append(
            "- 🔧 **Next step:** Optimize quantum hyperparameters and entanglement patterns\n"
        )

    report.append(
        "- 📊 **Hyperparameter tuning** could improve both classical and quantum models\n"
    )
    report.append("- 🔄 **Cross-validation** would provide more robust estimates\n")

    # Save report
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)
    report_path = results_dir / "classical_vs_quantum_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"   ✅ Saved report to: {report_path}")

    return report_path


def save_results_json(all_results):
    """Save complete results as JSON"""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    results_path = results_dir / "classical_vs_quantum_results.json"

    results_data = {
        "timestamp": datetime.now().isoformat(),
        "datasets": list(DATASETS.keys()),
        "models": list(CLASSICAL_MODELS.keys()) + ["Quantum Hybrid QNN"],
        "results": all_results,
        "quantum_baseline": QUANTUM_RESULTS,
    }

    with open(results_path, "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"   ✅ Saved JSON results to: {results_path}")


def main():
    """Run complete classical vs quantum benchmark"""
    print("=" * 70)
    print("  CLASSICAL vs QUANTUM ML - COMPREHENSIVE BENCHMARK")
    print("=" * 70)
    print("\n🎯 Objective: Compare quantum hybrid models against classical baselines")
    print(f"   Datasets: {len(DATASETS)}")
    print(f"   Classical Models: {len(CLASSICAL_MODELS)}")
    print("   Quantum Model: Hybrid QNN (4 qubits, 2 layers)")

    # Benchmark all datasets
    all_results = []
    for dataset_name, config in DATASETS.items():
        try:
            results = benchmark_dataset(dataset_name, config)
            all_results.extend(results)
        except Exception as e:
            print(f"\n❌ Error benchmarking {dataset_name}: {e}")
            continue

    if not all_results:
        print("\n❌ No results to analyze!")
        return

    # Generate visualizations
    accuracy_matrix, avg_accuracies = generate_comparison_plots(all_results)

    # Generate report
    generate_markdown_report(all_results, accuracy_matrix, avg_accuracies)

    # Save JSON
    save_results_json(all_results)

    # Final summary
    print("\n" + "=" * 70)
    print("  ✅ BENCHMARK COMPLETE!")
    print("=" * 70)
    print("\n📁 Output Files:")
    print("   - results/classical_vs_quantum_comparison.png")
    print("   - results/classical_vs_quantum_report.md")
    print("   - results/classical_vs_quantum_results.json")
    print("\n💡 Next Steps:")
    print("   1. Review comparison plots and report")
    print("   2. Analyze quantum advantages/disadvantages")
    print("   3. Consider hyperparameter optimization")
    print("   4. Test on Azure Quantum hardware")
    print("=" * 70)


if __name__ == "__main__":
    main()
