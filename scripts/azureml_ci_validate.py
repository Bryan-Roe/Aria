#!/usr/bin/env python
"""Azure ML Job Spec Validation Helper

Finds the latest job_*.yaml in .azureml/ and validates it with 'az ml job validate'.
Optionally submits the job if --submit is provided.

Usage:
  python scripts/azureml_ci_validate.py            # validate latest spec
  python scripts/azureml_ci_validate.py --file .azureml/job_multi_20251125T012515Z.yaml
  python scripts/azureml_ci_validate.py --submit   # validate then submit

Exit codes:
  0 = success (validation passed or skipped gracefully)
  1 = failure (validation error or submission error)
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AML_DIR = ROOT / '.azureml'

def az_available() -> bool:
    try:
        proc = subprocess.run(['az','version'], capture_output=True, text=True, timeout=30)
        return proc.returncode == 0
    except Exception:
        return False

def pick_latest_spec() -> Path | None:
    if not AML_DIR.exists():
        return None
    specs = sorted(AML_DIR.glob('job_*.yaml'), key=lambda p: p.stat().st_mtime, reverse=True)
    return specs[0] if specs else None

def validate(path: Path) -> bool:
    if not az_available():
        print('[azureml_validate] Azure CLI not available; skipping validation.')
        return True  # skip gracefully
    print(f'[azureml_validate] Validating spec: {path}')
    proc = subprocess.run(['az','ml','job','validate','--file', str(path)], capture_output=True, text=True)
    if proc.returncode == 0:
        print('[azureml_validate] ✅ Validation passed')
        return True
    print('[azureml_validate] ❌ Validation failed')
    print(proc.stderr or proc.stdout)
    return False

def submit(path: Path) -> bool:
    if not az_available():
        print('[azureml_validate] Azure CLI not available; cannot submit.')
        return False
    print(f'[azureml_validate] Submitting job: {path}')
    proc = subprocess.run(['az','ml','job','create','--file', str(path)], capture_output=True, text=True)
    if proc.returncode == 0:
        print('[azureml_validate] 🚀 Submission succeeded')
        return True
    print('[azureml_validate] ❌ Submission failed')
    print(proc.stderr or proc.stdout)
    return False

def main() -> int:
    ap = argparse.ArgumentParser(description='Azure ML job spec validation helper')
    ap.add_argument('--file', type=str, help='Specific job YAML to validate')
    ap.add_argument('--submit', action='store_true', help='Submit the job after successful validation')
    args = ap.parse_args()

    if args.file:
        job_path = Path(args.file)
        if not job_path.exists():
            print(f'[azureml_validate] Spec file not found: {job_path}')
            return 1
    else:
        job_path = pick_latest_spec()
        if not job_path:
            print('[azureml_validate] No job_*.yaml specs found; nothing to validate.')
            return 0

    ok = validate(job_path)
    if not ok:
        return 1
    if args.submit:
        return 0 if submit(job_path) else 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
