#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Paths relative to repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
LOCAL_TRAIN_DIR = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "local_train"
TRAIN_SCRIPT = LOCAL_TRAIN_DIR / "train_local.py"
VENV_DIR = LOCAL_TRAIN_DIR / "venv"
REQUIREMENTS = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "requirements.txt"
SENTINEL = VENV_DIR / ".deps_installed"


def run(cmd, cwd=None, env=None):
    print(f"$ {' '.join(str(c) for c in cmd)}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=False,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        return proc.returncode
    except subprocess.TimeoutExpired:
        print("Error: Command timed out after 30 minutes")
        return -1
    except Exception as e:
        print(f"Error executing command: {e}")
        return -1


def ensure_venv(python_exe: Path):
    if not VENV_DIR.exists():
        print(f"Creating venv at: {VENV_DIR}")
        rc = run([str(python_exe), "-m", "venv", str(VENV_DIR)])
        if rc != 0:
            sys.exit(rc)


def install_requirements(venv_python: Path, force: bool = False):
    if force or not SENTINEL.exists():
        print("Installing requirements into venv...")
        rc = run([str(venv_python), "-m", "pip",
                 "install", "-r", str(REQUIREMENTS)])
        if rc != 0:
            sys.exit(rc)
        SENTINEL.touch()
    else:
        print("Requirements already installed (skipping). Use --reinstall to force.")


def main():
    parser = argparse.ArgumentParser(
        description="Run local LoRA training (auto-setup).")
    parser.add_argument("--config", default="local_config.yaml",
                        help="Config YAML under local_train (default: local_config.yaml)")
    parser.add_argument("--max-samples", type=int, default=10,
                        help="Limit training samples for quick runs")
    parser.add_argument("--epochs", type=int, default=1,
                        help="Number of epochs for training")
    parser.add_argument("--reinstall", action="store_true",
                        help="Force reinstall of requirements")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print steps without executing the train step")
    args = parser.parse_args()

    # Resolve Python to create venv
    system_python = Path(sys.executable)
    ensure_venv(system_python)

    # Venv executables (cross-platform)
    venv_python = VENV_DIR / "bin" / "python"
    # Windows path fallback
    if not venv_python.exists():
        venv_python = VENV_DIR / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"Error: venv python not found at {venv_python}")
        sys.exit(1)

    install_requirements(venv_python, force=args.reinstall)

    # Environment tweaks
    env = os.environ.copy()
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    env.setdefault("PYTHONUTF8", "1")

    # Train command
    config_path = LOCAL_TRAIN_DIR / args.config
    if not config_path.exists():
        print(f"Error: config not found: {config_path}")
        sys.exit(1)

    cmd = [
        str(venv_python),
        str(TRAIN_SCRIPT),
        "--config", str(config_path.name),
        "--max-samples", str(args.max_samples),
        "--epochs", str(args.epochs),
    ]

    print("\n============================================================")
    print("AUTO TRAIN RUNNER")
    print("============================================================")
    print(f"Repo root: {REPO_ROOT}")
    print(f"Local train dir: {LOCAL_TRAIN_DIR}")
    print(f"Using config: {config_path.name}")
    print(f"Venv: {VENV_DIR}")
    print("============================================================\n")

    if args.dry_run:
        print("Dry run complete (skipping training).")
        return

    # Run from local_train so relative config paths resolve
    rc = run(cmd, cwd=str(LOCAL_TRAIN_DIR), env=env)
    if rc != 0:
        print(f"Training failed with exit code {rc}")
        sys.exit(rc)

    final_dir = LOCAL_TRAIN_DIR / "outputs" / "final"
    if final_dir.exists():
        print(f"\nTraining complete. Artifacts at: {final_dir}")
        # List key files
        for name in ["adapter_model.safetensors", "adapter_config.json", "tokenizer.json", "README.md"]:
            p = final_dir / name
            print(f" - {name}: {'OK' if p.exists() else 'MISSING'}")
    else:
        print("Training finished, but final output directory not found.")


if __name__ == "__main__":
    main()
