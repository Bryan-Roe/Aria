"""Upgrade script for moving the quantum-ai environment from pre-1.0 Qiskit
stack (e.g. qiskit==0.46.x) to the consolidated Qiskit 1.x meta package.

Features:
  * --dry-run: Show planned requirement changes without modifying files.
  * --install: After updating requirements, rebuild the venv and install.
  * --revert: Restore from the most recent requirements.backup.* snapshot.
  * Backs up original requirements.txt with timestamped filename.

Usage examples (run from repo root or quantum-ai directory):

    python ai-projects/quantum-ml/scripts/upgrade_qiskit_to_1x.py --dry-run
    python ai-projects/quantum-ml/scripts/upgrade_qiskit_to_1x.py --install
    python ai-projects/quantum-ml/scripts/upgrade_qiskit_to_1x.py --target-version 1.0.2 --ml-version 0.7.0 --install
    python ai-projects/quantum-ml/scripts/upgrade_qiskit_to_1x.py --revert

Post-upgrade validation:
    1. Delete any stale interpreter caches.
    2. Run: ai-projects/quantum-ml/venv/Scripts/python ai-projects/quantum-ml/scripts/validate_qiskit_env.py
    3. Run a smoke test: ai-projects/quantum-ml/venv/Scripts/python ai-projects/quantum-ml/src/quantum_classifier.py

Caveats:
  * Qiskit 1.x reorganizes subpackages; some algorithms previously accessed via
    qiskit_machine_learning may require updates or the qiskit_algorithms package.
  * Pennylane-qiskit compatibility with 1.x may lag behind; verify any advanced
    hybrid workflows after upgrade.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shutil
import subprocess
import sys
from datetime import timezone
from pathlib import Path

REQ_PATTERN_QISKIT = re.compile(r"^qiskit==.*$", re.IGNORECASE)
REQ_PATTERN_QISKIT_AER = re.compile(r"^qiskit-aer==.*$", re.IGNORECASE)
REQ_PATTERN_QML = re.compile(r"^qiskit-machine-learning==.*$", re.IGNORECASE)

DEFAULT_TARGET = "1.0.2"  # Adjust as newer stable releases arrive
DEFAULT_QML_VERSION = "0.7.0"  # Minimum version compatible with Qiskit 1.x


def _load_requirements(path: Path) -> list[str]:
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]


def _write_requirements(path: Path, lines: list[str]):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _backup(path: Path) -> Path:
    ts = _dt.datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.parent / f"requirements.backup.{ts}.txt"
    shutil.copy2(path, backup)
    return backup


def _find_latest_backup(req_dir: Path) -> Path | None:
    candidates = sorted(req_dir.glob("requirements.backup.*.txt"))
    return candidates[-1] if candidates else None


def plan_upgrade(lines: list[str], target_version: str, ml_version: str) -> list[str]:
    new_lines: list[str] = []
    replaced_qiskit = False
    replaced_qml = False
    for line in lines:
        if REQ_PATTERN_QISKIT.match(line):
            new_lines.append(f"qiskit>={target_version},<2.0.0")
            replaced_qiskit = True
        elif REQ_PATTERN_QISKIT_AER.match(line):
            # Drop explicit aer pin; the meta package installs aer automatically
            continue
        elif REQ_PATTERN_QML.match(line):
            new_lines.append(f"qiskit-machine-learning>={ml_version},<0.8.0")
            replaced_qml = True
        else:
            new_lines.append(line)

    # If qiskit line wasn't found, append it
    if not replaced_qiskit:
        new_lines.append(f"qiskit>={target_version},<2.0.0")
    if not replaced_qml:
        new_lines.append(f"qiskit-machine-learning>={ml_version},<0.8.0")
    return new_lines


def perform_install(venv_dir: Path, req_path: Path):
    """Recreate venv and install requirements."""
    if venv_dir.exists():
        shutil.rmtree(venv_dir)
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    pip_exe = venv_dir / "Scripts" / "python.exe"
    subprocess.check_call([str(pip_exe), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(pip_exe), "-m", "pip", "install", "-r", str(req_path)])
    # Quick version report
    code = "import qiskit, json; print(json.dumps({'qiskit': qiskit.__version__}))"
    out = subprocess.check_output([str(pip_exe), "-c", code], text=True).strip()
    print(f"[install] Version check: {out}")


def revert(req_path: Path, req_dir: Path):
    backup = _find_latest_backup(req_dir)
    if not backup:
        print("No backup found to revert.")
        return 1
    _write_requirements(req_path, _load_requirements(backup))
    print(f"Reverted requirements.txt from backup: {backup.name}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Upgrade Qiskit environment to 1.x")
    parser.add_argument(
        "--target-version",
        default=DEFAULT_TARGET,
        help="Target Qiskit 1.x version (default 1.0.2)",
    )
    parser.add_argument(
        "--ml-version",
        default=DEFAULT_QML_VERSION,
        help="Target qiskit-machine-learning version (default 0.7.0)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show planned changes without writing"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="After updating requirements, recreate venv and install",
    )
    parser.add_argument(
        "--revert",
        action="store_true",
        help="Revert requirements.txt from latest backup",
    )
    args = parser.parse_args()

    quantum_root = Path(__file__).resolve().parents[1]
    req_path = quantum_root / "requirements.txt"
    venv_dir = quantum_root / "venv"

    if args.revert:
        sys.exit(revert(req_path, quantum_root))

    if not req_path.exists():
        print(f"requirements.txt not found at {req_path}")
        sys.exit(1)

    lines = _load_requirements(req_path)

    # Detect current qiskit version (best-effort)
    current_version = None
    try:
        import qiskit  # type: ignore

        current_version = getattr(qiskit, "__version__", None)
    except Exception:
        pass
    print(f"Current qiskit version (if importable): {current_version}")

    planned = plan_upgrade(lines, args.target_version, args.ml_version)

    if args.dry_run:
        print("--- Planned requirements.txt changes (dry-run) ---")
        for l in planned:
            print(l)
        print("(no changes written)")
        sys.exit(0)

    backup = _backup(req_path)
    _write_requirements(req_path, planned)
    print(f"requirements.txt updated. Backup saved to: {backup}")

    if args.install:
        print("Recreating virtual environment and installing updated dependencies...")
        perform_install(venv_dir, req_path)
        print("Upgrade complete. Run validate_qiskit_env.py to verify coherence.")
    else:
        print("Upgrade staged. Run with --install to apply environment changes.")


if __name__ == "__main__":
    main()
