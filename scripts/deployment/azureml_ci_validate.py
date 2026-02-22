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
    import shutil
    # Basic presence check
    if shutil.which('az') is None:
        return False
    try:
        proc = subprocess.run(['az','version'], capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            return True
        # Some environments may return non-zero yet still output version info
        if 'azure-cli' in (proc.stdout + proc.stderr).lower():
            return True
        return False
    except Exception:
        return False

def extension_installed() -> bool:
    """Check if Azure ML CLI extension is installed (az extension show --name ml).
    Gracefully return False if command errors."""
    try:
        proc = subprocess.run(['az','extension','show','--name','ml'], capture_output=True, text=True, timeout=15)
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
    if not extension_installed():
        print('[azureml_validate] Azure ML CLI extension "ml" not installed; run: az extension add --name ml')
        print('[azureml_validate] Skipping validation until extension present.')
        return True  # graceful skip so CI does not fail
    print(f'[azureml_validate] Validating spec: {path}')
    proc = subprocess.run(['az','ml','job','validate','--file', str(path)], capture_output=True, text=True)
    if proc.returncode == 0:
        print('[azureml_validate] ✅ Validation passed')
        return True
    print('[azureml_validate] ❌ Validation failed')
    print(proc.stderr or proc.stdout)
    return False

REQUIRED_ENV_KEYS = ["AZURE_ML_SUBSCRIPTION_ID", "AZURE_ML_RESOURCE_GROUP", "AZURE_ML_WORKSPACE"]

def _env_placeholders_present(env_path: Path) -> list:
    missing_or_placeholder = []
    if not env_path.exists():
        return REQUIRED_ENV_KEYS  # treat all as missing
    lines = env_path.read_text(encoding='utf-8').splitlines()
    kv = {}
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=',1)
            kv[k.strip()] = v.strip()
    for key in REQUIRED_ENV_KEYS:
        val = kv.get(key)
        if val is None or '__REPLACE__' in val:
            missing_or_placeholder.append(key)
    return missing_or_placeholder

def submit(path: Path, force: bool = False) -> bool:
    if not az_available():
        print('[azureml_validate] Azure CLI not available; cannot submit.')
        return False
    env_path = ROOT / '.env'
    pending = _env_placeholders_present(env_path)
    if pending and not force:
        print('[azureml_validate] ✋ Submission gated. Unresolved .env placeholders: ' + ', '.join(pending))
        print('[azureml_validate]     Fill in values or use --force-submit to override.')
        return True  # treat as graceful skip
    print(f'[azureml_validate] Submitting job: {path}')
    proc = subprocess.run(['az','ml','job','create','--file', str(path)], capture_output=True, text=True)
    if proc.returncode == 0:
        # Attempt to extract job name from YAML spec for monitoring guidance
        job_name = None
        try:
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.strip().startswith('name:'):
                    job_name = line.split(':',1)[1].strip()
                    break
        except Exception:
            job_name = None
        print('[azureml_validate] 🚀 Submission succeeded')
        if job_name:
            print(f'[azureml_validate] Job name: {job_name}')
            print('[azureml_validate] Monitor: az ml job show --name {0} --resource-group $env:AZURE_ML_RESOURCE_GROUP --workspace-name $env:AZURE_ML_WORKSPACE'.format(job_name))
            print('[azureml_validate] Stream logs: az ml job stream --name {0} --resource-group $env:AZURE_ML_RESOURCE_GROUP --workspace-name $env:AZURE_ML_WORKSPACE'.format(job_name))
        return True
    print('[azureml_validate] ❌ Submission failed')
    print(proc.stderr or proc.stdout)
    return False

def main() -> int:
    ap = argparse.ArgumentParser(description='Azure ML job spec validation helper')
    ap.add_argument('--file', type=str, help='Specific job YAML to validate')
    ap.add_argument('--submit', action='store_true', help='Submit the job after successful validation')
    ap.add_argument('--force-submit', action='store_true', help='Override .env placeholder gating and submit anyway')
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
        return 0 if submit(job_path, force=args.force_submit) else 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
