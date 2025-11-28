#!/usr/bin/env python
"""Metrics Ranker

Aggregates pre/post perplexity improvements for LoRA training variants and produces
ranking outputs in JSON + Markdown.

Inputs:
  - autotrain.yaml (to discover jobs + save_dir paths)
  - Each job's metrics.jsonl (written by MetricsLogger in training script)

Outputs:
  data_out/metrics_ranker/ranking.json
  data_out/metrics_ranker/ranking.md

Scoring:
  score (delta) = pre_perplexity - post_perplexity (higher is better improvement)

Alerts:
  - Missing metrics file
  - Missing pre/post metrics
  - Shared metrics file path across multiple jobs (configuration issue)
"""
from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except Exception:
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTOTRAIN_CFG = REPO_ROOT / "config" / "training" / "autotrain.yaml"
OUT_DIR = REPO_ROOT / "data_out" / "metrics_ranker"


@dataclass
class ModelMetrics:
    job: str
    metrics_file: Path
    pre_perplexity: Optional[float] = None
    post_perplexity: Optional[float] = None
    delta: Optional[float] = None
    lines: int = 0
    alerts: List[str] = None  # type: ignore

    def finalize(self) -> None:
        if self.alerts is None:
            self.alerts = []
        if self.pre_perplexity is not None and self.post_perplexity is not None:
            self.delta = self.pre_perplexity - self.post_perplexity
        else:
            self.delta = None
            if self.pre_perplexity is None:
                self.alerts.append("missing pre")
            if self.post_perplexity is None:
                self.alerts.append("missing post")


def read_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise SystemExit("pyyaml not installed; cannot parse autotrain.yaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_jobs() -> List[Dict[str, Any]]:
    if not AUTOTRAIN_CFG.exists():
        raise SystemExit(f"autotrain config missing: {AUTOTRAIN_CFG}")
    cfg = read_yaml(AUTOTRAIN_CFG)
    return list(cfg.get("jobs", []))


def extract_metrics(metrics_path: Path, job_name: str) -> ModelMetrics:
    m = ModelMetrics(job=job_name, metrics_file=metrics_path)
    if not metrics_path.exists():
        m.alerts = ["metrics file missing"]
        return m
    try:
        with metrics_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m.lines += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                # Prefer explicit phase records
                if rec.get("phase") == "pre" and "eval_perplexity" in rec:
                    m.pre_perplexity = float(rec["eval_perplexity"])
                elif rec.get("phase") == "post" and "eval_perplexity" in rec:
                    m.post_perplexity = float(rec["eval_perplexity"])
                # Fallback: capture first & last eval_perplexity if phase absent
                elif "eval_perplexity" in rec and m.pre_perplexity is None:
                    m.pre_perplexity = float(rec["eval_perplexity"])
                elif "eval_perplexity" in rec:
                    # Keep updating post until end of file
                    m.post_perplexity = float(rec["eval_perplexity"])
    except Exception as e:
        m.alerts = [f"read error: {e}"]
    m.finalize()
    return m


def build_ranking(models: List[ModelMetrics]) -> Dict[str, Any]:
    # Identify duplicate metrics paths
    path_counts: Dict[str, int] = {}
    for m in models:
        p = str(m.metrics_file)
        path_counts[p] = path_counts.get(p, 0) + 1
    duplicates = [p for p, c in path_counts.items() if c > 1]

    ranked = sorted(models, key=lambda x: (x.delta is not None, x.delta if x.delta is not None else -math.inf), reverse=True)
    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "models": [
            {
                "job": m.job,
                "metrics_file": str(m.metrics_file),
                "pre_perplexity": m.pre_perplexity,
                "post_perplexity": m.post_perplexity,
                "delta": (round(m.delta, 4) if m.delta is not None else None),
                "lines": m.lines,
                "alerts": m.alerts or [],
            }
            for m in ranked
        ],
        "duplicates": duplicates,
        "alerts": [],
    }
    if duplicates:
        data["alerts"].append(f"Duplicate metrics paths across jobs: {len(duplicates)}")
    missing = [m.job for m in models if any(a.startswith("metrics file missing") for a in (m.alerts or []))]
    if missing:
        data["alerts"].append(f"Missing metrics for: {', '.join(missing[:5])}")
    return data


def write_outputs(ranking: Dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "ranking.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2)

    # Markdown table
    lines = [
        "# Metrics Ranking",
        "",
        f"_Generated {ranking['generated_at']}_",
        "",
        "| Job | Pre PPL | Post PPL | Δ Improvement | Metrics Lines | Alerts |",
        "|------|---------|----------|---------------|---------------|--------|",
    ]
    for m in ranking["models"]:
        alerts = "; ".join(m.get("alerts", []))
        lines.append(
            f"| {m['job']} | {m['pre_perplexity'] if m['pre_perplexity'] is not None else '-'} | "
            f"{m['post_perplexity'] if m['post_perplexity'] is not None else '-'} | "
            f"{m['delta'] if m['delta'] is not None else '-'} | {m['lines']} | {alerts or '-'} |"
        )
    if ranking.get("alerts"):
        lines.append("\n## Global Alerts\n")
        for a in ranking["alerts"]:
            lines.append(f"- {a}")
    md_path = OUT_DIR / "ranking.md"
    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Ranking written: {json_path}")
    print(f"Markdown: {md_path}")


def main() -> None:
    jobs = load_jobs()
    models: List[ModelMetrics] = []
    for j in jobs:
        job_name = str(j.get("name"))
        save_dir = j.get("save_dir")
        if not save_dir:
            # Skip jobs without dedicated save_dir; cannot attribute metrics uniquely
            continue
        metrics_file = REPO_ROOT / save_dir / "metrics.jsonl"
        models.append(extract_metrics(metrics_file, job_name))
    ranking = build_ranking(models)
    write_outputs(ranking)


if __name__ == "__main__":
    main()
