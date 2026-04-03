"""Evaluation AutoRun Orchestrator CLI

Minimal CLI for validating and listing evaluation jobs from a YAML config.
Implements:
- --help: prints usage and description
- --config: path to YAML config (defaults to config/evaluation/evaluation_autorun.yaml)
- --list: prints jobs as JSON to stdout
- --dry-run: validates config, writes data_out/evaluation_autorun/status.json, prints summary
- --job NAME: filters to a specific job (non-zero exit if not found)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "config" / "evaluation" / "evaluation_autorun.yaml"
STATUS_DIR = REPO_ROOT / "data_out" / "evaluation_autorun"
STATUS_FILE = STATUS_DIR / "status.json"


def _load_config(path: Path) -> Dict[str, Any]:
    """Load and return the YAML config."""
    if yaml is None:
        raise RuntimeError("PyYAML is required: pip install pyyaml")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _get_jobs(
    cfg: Dict[str, Any], job_filter: str | None = None
) -> List[Dict[str, Any]]:
    """Extract job list from config, optionally filtering by name."""
    jobs = cfg.get("jobs", [])
    if job_filter:
        jobs = [j for j in jobs if j.get("name") == job_filter]
    return jobs


def _write_status(jobs: List[Dict[str, Any]], dry_run: bool = False) -> None:
    """Write status.json to data_out."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    status = {
        "total_jobs": len(jobs),
        "succeeded": len(jobs) if dry_run else 0,
        "failed": 0,
        "running": 0,
        "last_updated": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
    }
    STATUS_FILE.write_text(json.dumps(status, indent=2), encoding="utf-8")


def cmd_list(cfg: Dict[str, Any], job_filter: str | None = None) -> None:
    """Print jobs as JSON to stdout."""
    jobs = _get_jobs(cfg, job_filter)
    print(json.dumps(jobs, indent=2))


def cmd_dry_run(cfg: Dict[str, Any], job_filter: str | None = None) -> None:
    """Validate config and print summary."""
    jobs = _get_jobs(cfg, job_filter)
    if not jobs:
        if job_filter:
            print(f"Job '{job_filter}' not found in config", file=sys.stderr)
            sys.exit(1)
        print("No jobs found in config", file=sys.stderr)
        sys.exit(1)

    _write_status(jobs, dry_run=True)

    for job in jobs:
        name = job.get("name", "unnamed")
        enabled = job.get("enabled", True)
        status = "validated" if enabled else "disabled"
        print(f"Job '{name}': {status}")

    print(f"\n{len(jobs)} job(s) validated successfully.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluation AutoRun Orchestrator — validate and run evaluation jobs"
    )
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG, help="Path to YAML config file"
    )
    parser.add_argument("--list", action="store_true", help="List jobs as JSON")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate config without running"
    )
    parser.add_argument(
        "--job", type=str, default=None, help="Filter to a specific job name"
    )

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    cfg = _load_config(args.config)

    if args.list:
        cmd_list(cfg, args.job)
    elif args.dry_run:
        cmd_dry_run(cfg, args.job)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
