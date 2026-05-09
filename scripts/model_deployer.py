#!/usr/bin/env python
"""
Model Deployer - Promotes trained LoRA adapters to the deployed models registry.

Scans data_out/ for trained models, selects based on strategy, and registers
them in deployed_models/model_registry.json for serving.

Usage:
    python scripts/model_deployer.py --deploy best --strategy canary
    python scripts/model_deployer.py --deploy best --strategy full
    python scripts/model_deployer.py --list
    python scripts/model_deployer.py --status
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DEPLOYED_DIR = REPO_ROOT / "deployed_models"
REGISTRY_FILE = DEPLOYED_DIR / "model_registry.json"
DATA_OUT = REPO_ROOT / "data_out"


def _load_registry() -> Dict[str, Any]:
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"models": [], "active_model": None, "last_updated": None}


def _save_registry(registry: Dict[str, Any]) -> None:
    DEPLOYED_DIR.mkdir(parents=True, exist_ok=True)
    registry["last_updated"] = datetime.now(timezone.utc).isoformat()
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))
    print(f"📄 Registry saved to {REGISTRY_FILE}")


def _scan_candidate_models() -> List[Dict[str, Any]]:
    """Scan data_out/ for adapter checkpoints eligible for deployment."""
    candidates = []

    # Standard locations: data_out/<orchestrator>/models/
    for adapter_config in DATA_OUT.rglob("adapter_config.json"):
        adapter_dir = adapter_config.parent
        # Check safetensors or bin weights exist
        has_weights = list(adapter_dir.glob("adapter_model.safetensors")) or list(
            adapter_dir.glob("adapter_model.bin")
        )
        if not has_weights:
            continue

        # Try to read training metadata if present
        metrics_file = adapter_dir.parent / "metrics.json"
        accuracy = None
        if metrics_file.exists():
            try:
                m = json.loads(metrics_file.read_text())
                accuracy = m.get("accuracy") or m.get("mean_accuracy")
            except Exception:
                pass

        candidates.append(
            {
                "path": str(adapter_dir),
                "name": adapter_dir.name,
                "accuracy": accuracy,
                "mtime": adapter_dir.stat().st_mtime,
            }
        )

    # Also check deployed_models/ for existing variants
    for adapter_config in DEPLOYED_DIR.rglob("adapter_config.json"):
        adapter_dir = adapter_config.parent
        if str(adapter_dir) not in [c["path"] for c in candidates]:
            candidates.append(
                {
                    "path": str(adapter_dir),
                    "name": adapter_dir.name,
                    "accuracy": None,
                    "mtime": adapter_dir.stat().st_mtime,
                }
            )

    return candidates


def _select_best(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Select the best model by accuracy, then recency."""
    if not candidates:
        return None
    # Prefer highest accuracy; fallback to most recent
    scored = sorted(
        candidates,
        key=lambda c: (c["accuracy"] or 0.0, c["mtime"]),
        reverse=True,
    )
    return scored[0]


def cmd_list(_args: argparse.Namespace) -> int:
    candidates = _scan_candidate_models()
    registry = _load_registry()
    active = registry.get("active_model")

    if not candidates:
        print("No candidate models found in data_out/ or deployed_models/")
        return 0

    print(f"{'Model':<40} {'Accuracy':>10}  {'Active':>6}")
    print("-" * 60)
    for c in candidates:
        acc = f"{c['accuracy']:.4f}" if c["accuracy"] is not None else "   n/a"
        is_active = "  ✓" if active and active == c["path"] else "   "
        print(f"{c['name']:<40} {acc:>10}  {is_active}")
    return 0


def cmd_status(_args: argparse.Namespace) -> int:
    registry = _load_registry()
    print(json.dumps(registry, indent=2))
    return 0


def cmd_deploy(args: argparse.Namespace) -> int:
    strategy = args.strategy or "canary"
    deploy_target = args.deploy or "best"

    print(f"🚀 Model deployer — target={deploy_target}, strategy={strategy}")

    candidates = _scan_candidate_models()
    if not candidates:
        print("⚠️  No trained models found. Nothing to deploy.")
        # Write a placeholder registry so the artifact upload doesn't fail
        registry = _load_registry()
        registry["deploy_status"] = "no_models"
        _save_registry(registry)
        return 0

    if deploy_target == "best":
        model = _select_best(candidates)
    else:
        # Try to match by name or path
        match = [
            c
            for c in candidates
            if deploy_target in c["name"] or deploy_target in c["path"]
        ]
        model = match[0] if match else _select_best(candidates)

    if not model:
        print("❌ Could not select a model for deployment")
        return 1

    print(
        f"  Selected: {model['name']} (accuracy={model['accuracy']}, strategy={strategy})"
    )

    src_path = Path(model["path"])
    dest_path = DEPLOYED_DIR / model["name"]

    if src_path != dest_path:
        dest_path.mkdir(parents=True, exist_ok=True)
        for f in src_path.iterdir():
            shutil.copy2(f, dest_path / f.name)
        print(f"  Copied model files → {dest_path}")

    registry = _load_registry()

    # For canary: mark as canary and don't replace active immediately
    entry: Dict[str, Any] = {
        "name": model["name"],
        "path": str(dest_path),
        "accuracy": model["accuracy"],
        "strategy": strategy,
        "deployed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Update or append in registry
    existing = [m for m in registry["models"] if m.get("name") == model["name"]]
    if existing:
        existing[0].update(entry)
    else:
        registry["models"].append(entry)

    if strategy == "full":
        registry["active_model"] = str(dest_path)
        print("  ✓ Full deployment — active model updated")
    elif strategy == "canary":
        registry["canary_model"] = str(dest_path)
        print(
            "  ✓ Canary deployment — canary model set (run with --strategy full to promote)"
        )
    else:
        registry["active_model"] = str(dest_path)

    registry["deploy_status"] = "deployed"
    _save_registry(registry)
    print("✅ Deployment complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Model deployer for Aria LoRA adapters"
    )
    sub = parser.add_subparsers()

    # Top-level flags that match the ci-pipeline usage pattern:
    # python scripts/model_deployer.py --deploy best --strategy canary
    parser.add_argument(
        "--deploy", metavar="TARGET", help="Model to deploy: 'best' or a model name"
    )
    parser.add_argument(
        "--strategy",
        choices=["canary", "full"],
        default="canary",
        help="Deployment strategy",
    )
    parser.add_argument("--list", action="store_true", help="List candidate models")
    parser.add_argument("--status", action="store_true", help="Print registry status")

    args = parser.parse_args()

    if args.list:
        return cmd_list(args)
    if args.status:
        return cmd_status(args)
    if args.deploy:
        return cmd_deploy(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
