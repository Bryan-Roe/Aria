#!/usr/bin/env python
"""Azure ML .env Configuration Helper

Updates the required Azure ML environment variables in the repository .env file.

Usage (non-interactive):
  python scripts/configure_azure_ml_env.py --subscription <SUB_ID> --resource-group <RG> --workspace <WS>

Show current values:
  python scripts/configure_azure_ml_env.py --show

If arguments are omitted and placeholders remain, guidance is printed.
This script never removes existing unrelated variables.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict

ENV_KEYS = ["AZURE_ML_SUBSCRIPTION_ID", "AZURE_ML_RESOURCE_GROUP", "AZURE_ML_WORKSPACE"]
PLACEHOLDER = "__REPLACE__"

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def parse_env() -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not ENV_PATH.exists():
        return data
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.strip().startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def write_env(env: Dict[str, str]) -> None:
    lines = [f"{k}={v}" for k, v in env.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def show(env: Dict[str, str]) -> None:
    print("Current Azure ML environment variables:")
    for k in ENV_KEYS:
        v = env.get(k, "<missing>")
        status = "OK" if (v and v != PLACEHOLDER) else "MISSING"
        print(f"  {k} = {v}  [{status}]")


def main() -> int:
    ap = argparse.ArgumentParser(description="Configure Azure ML .env values")
    ap.add_argument("--subscription", type=str, help="Azure subscription ID")
    ap.add_argument("--resource-group", type=str, help="Azure resource group name")
    ap.add_argument("--workspace", type=str, help="Azure ML workspace name")
    ap.add_argument("--show", action="store_true", help="Show current values and exit")
    args = ap.parse_args()

    env = parse_env()

    # Ensure keys present with placeholder if absent
    changed = False
    for k in ENV_KEYS:
        if k not in env:
            env[k] = PLACEHOLDER
            changed = True

    if args.show and not any([args.subscription, args.resource_group, args.workspace]):
        # Write placeholders if newly added then show
        if changed:
            write_env(env)
        show(env)
        if any(v == PLACEHOLDER for v in env.values()):
            print("\nPopulate missing values using:\n  python scripts/configure_azure_ml_env.py --subscription <SUB_ID> --resource-group <RG> --workspace <WS>")
        return 0

    # Apply provided updates
    if args.subscription:
        env["AZURE_ML_SUBSCRIPTION_ID"] = args.subscription.strip()
        changed = True
    if args.resource_group:
        env["AZURE_ML_RESOURCE_GROUP"] = args.resource_group.strip()
        changed = True
    if args.workspace:
        env["AZURE_ML_WORKSPACE"] = args.workspace.strip()
        changed = True

    if changed:
        write_env(env)
        print("Updated .env with provided values.")

    # Final status report
    show(env)
    missing = [k for k in ENV_KEYS if env.get(k) in (None, PLACEHOLDER, "")]
    if missing:
        print("\nStill missing: " + ", ".join(missing))
        print("Fill them with command line flags or edit the .env file directly.")
        return 1
    print("\nAll Azure ML variables configured. You can now validate/submit jobs:")
    print("  python scripts/azureml_ci_validate.py --submit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
