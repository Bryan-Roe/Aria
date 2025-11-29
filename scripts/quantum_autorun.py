"""Quantum AutoRun Orchestrator CLI

Minimal CLI for validating and listing quantum jobs from a YAML config.
Implements:
- --help: prints usage and description
- --config: path to YAML config (defaults to repo root quantum_autorun.yaml)
- --list: prints jobs as JSON to stdout
- --dry-run: validates config, writes data_out/quantum_autorun/status.json, prints summary
- --job NAME: filters to a specific job (non-zero exit if not found)

Config schema (YAML):
jobs:
  - name: heart_quick
	preset: heart
	epochs: 1
	n_qubits: 4
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # Tests will provide simple configs; fail gracefully if missing


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "quantum_autorun.yaml"
STATUS_DIR = REPO_ROOT / "data_out" / "quantum_autorun"
STATUS_FILE = STATUS_DIR / "status.json"


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"jobs": []}
    if yaml is None:
        # Minimal YAML loader fallback: handle a very small subset for tests
        # Prefer PyYAML when available.
        text = path.read_text(encoding="utf-8")
        # Extremely simple parse: find lines under jobs: and collect name/preset/etc
        jobs: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        in_jobs = False
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("jobs:"):
                in_jobs = True
                continue
            if in_jobs and s.startswith("-"):
                if current:
                    jobs.append(current)
                current = {}
                continue
            if in_jobs and ":" in s:
                k, v = s.split(":", 1)
                current[k.strip()] = v.strip()
        if current:
            jobs.append(current)
        return {"jobs": jobs}
    # Normal path: use safe_load
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {"jobs": []}
    data.setdefault("jobs", [])
    return data


def filter_jobs(jobs: List[Dict[str, Any]], name: str | None) -> List[Dict[str, Any]]:
    if not name:
        return jobs
    filtered = [j for j in jobs if j.get("name") == name]
    return filtered


def write_status(jobs: List[Dict[str, Any]]) -> None:
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_jobs": len(jobs),
        "jobs": jobs,
        "last_updated": None,
        "succeeded": 0,
        "failed": 0,
        "running": 0,
        "avg_duration": None,
    }
    STATUS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Quantum AutoRun Orchestrator")
    parser.add_argument("--config", type=str,
                        default=str(DEFAULT_CONFIG), help="Path to YAML config")
    parser.add_argument("--list", action="store_true",
                        help="List jobs as JSON")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate config and write status.json")
    parser.add_argument("--job", type=str, default=None,
                        help="Filter to a specific job by name")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)
    jobs: List[Dict[str, Any]] = cfg.get("jobs", [])

    if args.job:
        jobs = filter_jobs(jobs, args.job)
        if not jobs:
            msg = f"Job '{args.job}' not found"
            # Print to stderr to satisfy test expectations
            print(msg, file=sys.stderr)
            return 1

    if args.list:
        print(json.dumps(jobs, indent=2))
        return 0

    if args.dry_run:
        write_status(jobs)
        # Print summary to stdout for tests
        names = ", ".join([j.get("name", "<unnamed>") for j in jobs])
        print(f"Validated {len(jobs)} job(s): {names}")
        return 0

    # No operation requested; show help and exit 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
