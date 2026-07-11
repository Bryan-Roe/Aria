"""
Visualize Azure Quantum hardware test results as charts.

Outputs:
- Per-result bar charts of measurement counts (top-N)
- For 2-qubit results, a 2x2 heatmap
- Summary chart of entanglement ratio for all 2-qubit results
- Azure job list charts: status distribution and provider x status stacked bar

Charts saved to: ai-projects/quantum-ml/results/visualizations/
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "quantum_config.yaml"
RESULTS_DIR = (REPO_ROOT / "results").resolve()
# Some utilities may save to repo-root/../results because results_dir in config is relative to CWD
ALT_RESULTS_DIR = (REPO_ROOT.parent / "results").resolve()
VIZ_DIR = RESULTS_DIR / "visualizations"
VIZ_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.autolayout": True, "figure.dpi": 120})


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def find_local_results(results_dir: Path) -> list[Path]:
    # Look for files saved by test_azure_quantum.py (bell_state_results_*.json, optimized_circuit_results_*.json)
    patterns = [
        "bell_state_results_*.json",
        "optimized_circuit_results_*.json",
        "*results*.json",
    ]
    found: list[Path] = []
    for pat in patterns:
        found.extend(results_dir.glob(pat))
    # De-duplicate while preserving order
    seen = set()
    uniq: list[Path] = []
    for p in found:
        if p.name not in seen:
            uniq.append(p)
            seen.add(p.name)
    return uniq


def load_counts_from_json(p: Path) -> dict[str, int] | None:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # Expecting {'job_id': str, 'counts': {bitstring: int}, 'success': bool}
        counts = data.get("counts")
        if isinstance(counts, dict) and counts:
            # Ensure values are ints
            return {str(k): int(v) for k, v in counts.items()}
    except Exception:
        pass
    return None


def try_load_metadata(p: Path) -> dict | None:
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        meta = data.get("metadata", {})
        # Flatten key fields
        flat = {
            "file": str(p),
            "job_id": data.get("job_id"),
            "n_qubits": meta.get("n_qubits"),
            "layers": meta.get("layers"),
            "entanglement": meta.get("entanglement"),
            "method": meta.get("method"),
            "circuit": meta.get("circuit"),
            "shots": meta.get("shots"),
            "entropy": meta.get("entropy"),
            "max_entropy": meta.get("max_entropy"),
        }
        noise = meta.get("noise", {}) or {}
        flat.update(
            {
                "noise_pauli_px": noise.get("pauli_px", 0.0),
                "noise_pauli_pz": noise.get("pauli_pz", 0.0),
                "noise_depolarizing_p": noise.get("depolarizing_p", 0.0),
                "noise_amp_damp_gamma": noise.get("amp_damp_gamma", 0.0),
            }
        )
        stab = meta.get("stabilizer", {}) or {}
        flat.update(
            {
                "stabilizer_type": stab.get("type"),
                "clifford_layers": stab.get("clifford_layers"),
                "twoq_density": stab.get("twoq_density"),
            }
        )
        return flat
    except Exception:
        return None


def compute_entanglement_ratio(counts: dict[str, int]) -> float | None:
    # Only meaningful for 2-qubit bell state
    if not counts:
        return None
    # Performance optimization: Direct iteration instead of .keys()
    bit_lengths = {len(k) for k in counts}
    if bit_lengths != {2}:
        return None
    total = sum(counts.values())
    entangled = counts.get("00", 0) + counts.get("11", 0)
    return 100.0 * entangled / total if total > 0 else None


def _abbr_label(label: str, max_len: int = 24) -> str:
    if len(label) <= max_len:
        return label
    # keep first 8 and last 8 bits by default if very long
    return f"{label[:8]}…{label[-8:]}"


def plot_counts_bar(counts: dict[str, int], title: str, out_path: Path, top_n: int = 10) -> None:
    total = sum(counts.values())
    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    labels = [k for k, _ in items]
    disp_labels = [_abbr_label(k) for k in labels]
    values = [v for _, v in items]
    perc = [100.0 * v / total for v in values]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(disp_labels, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_xlabel("Measurement state")
    ax.set_ylabel("Counts")
    for i, (_x, v, p) in enumerate(zip(disp_labels, values, perc, strict=False)):
        ax.text(i, v, f"{p:.1f}%", ha="center", va="bottom", fontsize=8)
    plt.xticks(rotation=45)
    fig.savefig(out_path)
    plt.close(fig)


def plot_2qubit_heatmap(counts: dict[str, int], title: str, out_path: Path) -> None:
    # Build 2x2 matrix in order [00, 01, 10, 11]
    mat = [
        [counts.get("00", 0), counts.get("01", 0)],
        [counts.get("10", 0), counts.get("11", 0)],
    ]
    fig, ax = plt.subplots(figsize=(4.5, 4))
    im = ax.imshow(mat, cmap="Blues")
    ax.set_xticks([0, 1], labels=["0", "1"])  # measured qubit 1
    ax.set_yticks([0, 1], labels=["0", "1"])  # measured qubit 0
    ax.set_xlabel("Qubit 1")
    ax.set_ylabel("Qubit 0")
    ax.set_title(title)
    # Annotate
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(mat[i][j]), ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.savefig(out_path)
    plt.close(fig)


def plot_hamming_weight_hist(counts: dict[str, int], out_path: Path) -> None:
    if not counts:
        return
    bit_lengths = {len(k) for k in counts}
    if len(bit_lengths) != 1:
        return
    n = bit_lengths.pop()
    # compute weight distribution
    weight_counts: dict[int, int] = {}
    for bitstr, c in counts.items():
        w = bitstr.count("1")
        weight_counts[w] = weight_counts.get(w, 0) + int(c)
    weights = sorted(weight_counts.keys())
    values = [weight_counts[w] for w in weights]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([str(w) for w in weights], values, color="#F58518")
    ax.set_title(f"Hamming weight distribution (n={n})")
    ax.set_xlabel("Number of ones in measured bitstring")
    ax.set_ylabel("Counts")
    if len(weights) > 40:
        plt.xticks([], [])
    fig.savefig(out_path)
    plt.close(fig)


def try_fetch_azure_job_list(resource_group: str, workspace: str, location: str) -> pd.DataFrame | None:
    cmd = [
        "az",
        "quantum",
        "job",
        "list",
        "--resource-group",
        resource_group,
        "--workspace-name",
        workspace,
        "--location",
        location,
        "--output",
        "json",
    ]
    try:
        out = subprocess.check_output(cmd, text=True)
        data = json.loads(out)
        if not isinstance(data, list):
            return None
        # Normalize to a DataFrame
        df = pd.json_normalize(data)
        # Coerce timestamps
        for col in (
            "creationTime",
            "beginExecutionTime",
            "endExecutionTime",
            "lastModifiedTime",
        ):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception:
        return None


def plot_job_status_distribution(df: pd.DataFrame, out_path: Path) -> None:
    if df is None or df.empty or "status" not in df.columns:
        return
    counts = df["status"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4))
    counts.plot(kind="bar", ax=ax, color="#72B7B2")
    ax.set_title("Azure Quantum Jobs by Status")
    ax.set_xlabel("Status")
    ax.set_ylabel("Count")
    fig.savefig(out_path)
    plt.close(fig)


def plot_provider_status_stacked(df: pd.DataFrame, out_path: Path) -> None:
    if df is None or df.empty or not {"providerId", "status"}.issubset(df.columns):
        return
    pivot = pd.pivot_table(
        df,
        index="providerId",
        columns="status",
        values="id",
        aggfunc="count",
        fill_value=0,
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    pivot.plot(kind="bar", stacked=True, ax=ax)
    ax.set_title("Jobs by Provider and Status")
    ax.set_xlabel("Provider")
    ax.set_ylabel("Count")
    fig.savefig(out_path)
    plt.close(fig)


def build_summary_df(files: list[Path]) -> pd.DataFrame:
    rows: list[dict] = []
    for p in files:
        meta = try_load_metadata(p)
        if not meta:
            continue
        rows.append(meta)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Compute entropy_pct
    if not df.empty and {"entropy", "max_entropy"}.issubset(df.columns):
        df["entropy_pct"] = (df["entropy"] / df["max_entropy"]) * 100.0

    # Noise label
    def _noise_label(r):
        px = r.get("noise_pauli_px", 0) or 0
        pz = r.get("noise_pauli_pz", 0) or 0
        dep = r.get("noise_depolarizing_p", 0) or 0
        amp = r.get("noise_amp_damp_gamma", 0) or 0
        labels = []
        if px or pz:
            labels.append(f"pauli(px={px},pz={pz})")
        if dep:
            labels.append(f"depol(p={dep})")
        if amp:
            labels.append(f"amp_damp(gamma={amp})")
        return "clean" if not labels else "+".join(labels)

    if not df.empty:
        df["noise_label"] = df.apply(_noise_label, axis=1)
    return df


def main() -> int:
    print("\n=== Visualizing Azure Quantum Hardware Test Results ===\n")
    cfg = load_config()

    # 1) Local result files
    local_files = find_local_results(RESULTS_DIR)
    if not local_files and ALT_RESULTS_DIR.exists():
        # Also scan alternate location (repo root results)
        alt = find_local_results(ALT_RESULTS_DIR)
        # If found there, also make sure we save charts under the quantum-ai results/visualizations
        local_files = alt
        if alt:
            print(f"Found {len(alt)} local result file(s) in {ALT_RESULTS_DIR}")
    entanglement_summary: list[tuple[str, float]] = []

    if local_files:
        # If they came from RESULTS_DIR this message is accurate; otherwise a message was already printed.
        if all(
            (p.is_relative_to(RESULTS_DIR) if hasattr(p, "is_relative_to") else str(p).startswith(str(RESULTS_DIR)))
            for p in local_files
        ):
            print(f"Found {len(local_files)} local result file(s) in {RESULTS_DIR}")
    else:
        print("No local result JSON files found in results/. We'll still generate Azure job charts if available.")

    for p in local_files:
        counts = load_counts_from_json(p)
        if not counts:
            continue
        stem = p.stem
        # Bar chart (top-10) with abbreviated labels for long bitstrings
        plot_counts_bar(
            counts,
            title=f"Counts: {stem}",
            out_path=VIZ_DIR / f"{stem}_bar.png",
            top_n=10,
        )
        # 2-qubit heatmap
        bit_lengths = {len(k) for k in counts}
        if bit_lengths == {2}:
            plot_2qubit_heatmap(
                counts,
                title=f"2-Qubit Heatmap: {stem}",
                out_path=VIZ_DIR / f"{stem}_heatmap.png",
            )
            ratio = compute_entanglement_ratio(counts)
            if ratio is not None:
                entanglement_summary.append((stem, ratio))
        # For large bitstrings, add Hamming weight histogram
        if max(bit_lengths) > 32:
            plot_hamming_weight_hist(counts, out_path=VIZ_DIR / f"{stem}_hamming_weight.png")

    # 1b) Summary charts for variational MPS runs by entanglement
    df_all = build_summary_df(local_files)
    if not df_all.empty:
        df_mps = df_all[(df_all["method"] == "matrix_product_state") & (df_all["circuit"].str.contains("variational"))]
        if not df_mps.empty:
            # For each (n_qubits, layers), plot entanglement vs entropy_pct for clean and noise separately
            for (nq, L), sub in df_mps.groupby(["n_qubits", "layers"]):
                for nlbl, part in sub.groupby("noise_label"):
                    if part.empty:
                        continue
                    pivot = (
                        part.dropna(subset=["entanglement", "entropy_pct"])
                        .groupby("entanglement")["entropy_pct"]
                        .mean()
                    )
                    if pivot.empty:
                        continue
                    fig, ax = plt.subplots(figsize=(6, 4))
                    pivot.reindex(["linear", "circular", "full"]).plot(kind="bar", ax=ax, color="#4C78A8")
                    ax.set_title(f"Entropy% by entanglement (n={nq}, L={L}, {nlbl})")
                    ax.set_xlabel("Entanglement")
                    ax.set_ylabel("Entropy %")
                    ax.set_ylim(0, 100)
                    out = (
                        VIZ_DIR
                        / f"summary_entropy_mps_n{nq}_L{L}_{nlbl.replace('=', '').replace(',', '_').replace('(', '').replace(')', '').replace(' ', '')}.png"
                    )
                    fig.savefig(out)
                    plt.close(fig)

    # 1c) Summary for stabilizer random: weight coverage vs layers
    if not df_all.empty:
        df_stab = df_all[(df_all["circuit"].str.contains("stabilizer")) & (df_all["stabilizer_type"] == "random")]
        if not df_stab.empty:
            # Compute weight coverage from counts
            coverage_rows = []
            for _, row in df_stab.iterrows():
                counts = load_counts_from_json(Path(row["file"]))
                if not counts:
                    continue
                n = int(row.get("n_qubits") or 0)
                nonzero_weights = set()
                for bitstr, c in counts.items():
                    if c > 0:
                        nonzero_weights.add(bitstr.count("1"))
                coverage = len(nonzero_weights) / (n + 1) if n > 0 else 0.0
                coverage_rows.append(
                    {
                        "n_qubits": n,
                        "clifford_layers": int(row.get("clifford_layers") or 0),
                        "coverage": coverage * 100.0,
                    }
                )
            if coverage_rows:
                df_cov = pd.DataFrame(coverage_rows)
                for nq, part in df_cov.groupby("n_qubits"):
                    fig, ax = plt.subplots(figsize=(6, 4))
                    part = part.sort_values("clifford_layers")
                    ax.plot(part["clifford_layers"], part["coverage"], marker="o")
                    ax.set_title(f"Stabilizer random: weight coverage vs layers (n={nq})")
                    ax.set_xlabel("Clifford layers")
                    ax.set_ylabel("Coverage % of weights (0..n)")
                    ax.set_ylim(0, 100)
                    fig.savefig(VIZ_DIR / f"stabilizer_random_weight_coverage_n{nq}.png")
                    plt.close(fig)

    # Summary entanglement chart for 2-qubit results
    if entanglement_summary:
        labels, ratios = zip(*entanglement_summary, strict=False)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(labels, ratios, color="#E45756")
        ax.set_title("Entanglement Quality (2-qubit Bell state)")
        ax.set_xlabel("Result")
        ax.set_ylabel("% in |00> + |11>")
        plt.xticks(rotation=45)
        fig.savefig(VIZ_DIR / "entanglement_summary.png")
        plt.close(fig)

    # 2) Azure job list charts (status & provider)
    rsrc = cfg.get("azure", {}).get("resource_group", "")
    ws = cfg.get("azure", {}).get("workspace_name", "")
    loc = cfg.get("azure", {}).get("location", "")

    if rsrc and ws and loc:
        df = try_fetch_azure_job_list(rsrc, ws, loc)
        if df is not None and not df.empty:
            plot_job_status_distribution(df, VIZ_DIR / "azure_jobs_status.png")
            plot_provider_status_stacked(df, VIZ_DIR / "azure_jobs_provider_status.png")
            print("Azure job charts saved under visualizations/.")
        else:
            print("Azure job list not available or empty (no charts generated for jobs).")
    else:
        print("Azure config incomplete; skipping Azure job charts.")

    print(f"\nCharts saved to: {VIZ_DIR}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
