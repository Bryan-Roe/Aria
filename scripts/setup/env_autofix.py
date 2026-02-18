#!/usr/bin/env python
"""Environment Auto-Fix Utility

Detects corruption in the model-specific virtual environment and attempts automated repair.

Logic:
1. Validate venv path exists.
2. Run torch import test under model venv python.
3. If import raises OSError referencing CUDA DLLs or missing sympy artifacts → mark corrupt.
4. Attempt safe rename of existing venv (append .corrupt.<timestamp>) if locked deletion fails.
5. Recreate venv and install base requirements + GPU torch stack.
6. Re-test torch import; record outcome in status JSON.
7. Never deletes the old venv if rename fails (leave for manual intervention).

Outputs:
  data_out/env_autofix/status.json

Usage:
  python .\\scripts\\env_autofix.py                # one-shot repair attempt
  python .\\scripts\\env_autofix.py --dry-run      # only diagnose
  python .\\scripts\\env_autofix.py --force        # force rebuild even if healthy
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

REPO_ROOT = Path(__file__).resolve().parents[1]
MODEL_VENV = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "venv"
REQ_FILE = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "requirements.txt"
DATA_OUT = REPO_ROOT / "data_out" / "env_autofix"

CUDA_INDEX_URL = "https://download.pytorch.org/whl/cu121"
TORCH_PKGS = [
    "torch==2.5.1+cu121",
    "torchvision==0.20.1+cu121",
    "torchaudio==2.5.1+cu121",
]

def run(cmd, timeout=900, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, env=env)

def torch_health(python_exe: Path) -> Dict[str, Any]:
    """Return torch health info using a reliable helper script first.

    We prefer executing the repository helper script `_torch_health_check.py` to avoid
    Windows quoting / inline `-c` parsing issues that previously produced a false
    `no_output` corruption signal. Falls back to the inline command only if the
    helper script is missing or its output cannot be parsed.
    """
    if not python_exe.exists():
        return {"ok": False, "error": "python_exe_missing"}

    script_path = REPO_ROOT / "scripts" / "_torch_health_check.py"
    if script_path.exists():
        proc = run([str(python_exe), str(script_path)], timeout=30)
        output = proc.stdout.strip()
        if output:
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    data.setdefault("method", "script")
                    return data
                return {"ok": False, "error": "script_non_dict", "raw": output[:200], "method": "script"}
            except Exception as e:
                # Fall through to inline method
                fallback_error = f"script_parse_failure: {e}"[:200]
        else:
            fallback_error = "script_no_output"
    else:
        fallback_error = "script_missing"

    # Inline fallback
    code = (
        "import json;"
        "resp={'ok':False};"
        "try:" 
        " import torch; resp={'ok':True,'cuda':torch.cuda.is_available(),'version':torch.__version__};" 
        "except Exception as e: resp={'ok':False,'error':str(e)};" 
        "print(json.dumps(resp))"
    )
    proc_inline = run([str(python_exe), "-c", code], timeout=30)
    output_inline = proc_inline.stdout.strip()
    if not output_inline:
        return {"ok": False, "error": "no_output", "stderr": proc_inline.stderr[:200] if proc_inline.stderr else "", "fallback_error": fallback_error, "method": "inline"}
    try:
        result = json.loads(output_inline)
        if not result:
            return {"ok": False, "error": "empty_result", "fallback_error": fallback_error, "method": "inline"}
        result.setdefault("method", "inline")
        result["fallback_error"] = fallback_error
        return result
    except Exception as e:
        return {"ok": False, "error": "parse_failure", "raw": output_inline[:200], "stderr": proc_inline.stderr[:200] if proc_inline.stderr else "", "fallback_error": fallback_error, "method": "inline"}

def mark_status(obj: Dict[str, Any]) -> None:
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    obj["timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"
    with (DATA_OUT / "status.json").open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)

def create_new_venv(python_exe: Path, target: Path) -> Dict[str, Any]:
    result = {"step": "create_new_venv", "target": str(target)}
    proc = run([sys.executable, "-m", "venv", str(target)], timeout=600)
    if proc.returncode != 0:
        result.update({"ok": False, "error": proc.stderr[-400:]})
        return result
    result["ok"] = True
    return result

def install_requirements(python_exe: Path) -> Dict[str, Any]:
    steps = []
    if REQ_FILE.exists():
        proc = run([str(python_exe), "-m", "pip", "install", "-r", str(REQ_FILE)])
        steps.append({"action": "install_req", "return_code": proc.returncode, "stderr": proc.stderr[-400:]})
    # Install torch stack
    proc2 = run([str(python_exe), "-m", "pip", "install", "--no-cache-dir", "--index-url", CUDA_INDEX_URL, *TORCH_PKGS], timeout=1800)
    steps.append({"action": "install_torch", "return_code": proc2.returncode, "stderr": proc2.stderr[-400:]})
    return {"step": "install_requirements", "details": steps}

def safe_rename(path: Path) -> Dict[str, Any]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    new_name = path.parent / f"{path.name}.corrupt.{ts}"
    try:
        path.rename(new_name)
        return {"step": "rename", "ok": True, "new_path": str(new_name)}
    except Exception as e:
        return {"step": "rename", "ok": False, "error": str(e)}

def main() -> None:
    ap = argparse.ArgumentParser(description="Auto-repair model venv")
    ap.add_argument("--dry-run", action="store_true", help="Diagnose only")
    ap.add_argument("--force", action="store_true", help="Force rebuild even if healthy")
    args = ap.parse_args()

    status: Dict[str, Any] = {"venv": str(MODEL_VENV)}

    py_exe = MODEL_VENV / "Scripts" / "python.exe"
    status["exists"] = MODEL_VENV.exists()
    if not MODEL_VENV.exists():
        status["state"] = "missing"
        if args.dry_run:
            mark_status(status)
            print(json.dumps(status, indent=2))
            return
        # Create fresh venv
        create_res = create_new_venv(Path(sys.executable), MODEL_VENV)
        status["create"] = create_res
        py_exe = MODEL_VENV / "Scripts" / "python.exe"
        install_res = install_requirements(py_exe)
        status["install"] = install_res
        health = torch_health(py_exe)
        status["health"] = health
        status["state"] = "recreated" if health.get("ok") else "error"
        mark_status(status)
        print(json.dumps(status, indent=2))
        return

    # Existing venv - test health
    health = torch_health(py_exe)
    status["initial_health"] = health
    corrupt_signatures = ["WinError 127", "c10_cuda.dll", "shm-MSI.dll", "wrap_triton", "procedure could not be found", "python_exe_missing", "ModuleNotFoundError", "no_output", "empty_result", "parse_failure"]
    is_corrupt = (not health.get("ok")) and any(sig in str(health) for sig in corrupt_signatures)
    status["is_corrupt"] = is_corrupt

    if args.dry_run and not args.force:
        status["state"] = "corrupt" if is_corrupt else "healthy"
        mark_status(status)
        print(json.dumps(status, indent=2))
        return

    if (not is_corrupt) and (not args.force):
        status["state"] = "healthy"
        mark_status(status)
        print(json.dumps(status, indent=2))
        return

    # Repair path
    status["state"] = "repairing"
    rename_res = safe_rename(MODEL_VENV)
    status["rename"] = rename_res
    if not rename_res.get("ok"):
        status["state"] = "locked"
        status["message"] = "Rename failed (likely files locked). Close processes using venv and retry."
        mark_status(status)
        print(json.dumps(status, indent=2))
        return

    # Recreate
    create_res = create_new_venv(Path(sys.executable), MODEL_VENV)
    status["create"] = create_res
    if not create_res.get("ok"):
        status["state"] = "error"
        mark_status(status)
        print(json.dumps(status, indent=2))
        return

    install_res = install_requirements(MODEL_VENV / "Scripts" / "python.exe")
    status["install"] = install_res
    health2 = torch_health(MODEL_VENV / "Scripts" / "python.exe")
    status["final_health"] = health2
    status["state"] = "repaired" if health2.get("ok") else "error"
    mark_status(status)
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
