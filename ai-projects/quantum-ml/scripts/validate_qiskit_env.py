"""Validate Qiskit environment consistency.
Detects mixed installations of Qiskit 1.x and legacy (<1.0) components that cause ImportError.
Run with the quantum-ai venv interpreter:

    python ai-projects/quantum-ml/scripts/validate_qiskit_env.py

Exit codes:
 0 - OK (single coherent Qiskit environment)
 1 - Conflict detected
"""

from __future__ import annotations

import importlib
import json
import pkgutil
import sys
from typing import Dict, List

LEGACY_PACKAGES = [
    "qiskit_terra",  # legacy terra dist name (often 'qiskit-terra')
    "qiskit-aer",  # old namespace dist style
    "qiskit_ibmq_provider",  # deprecated provider
]
MODERN_ROOT = "qiskit"


def find_distributions() -> Dict[str, str]:
    versions = {}
    for m in pkgutil.iter_modules():
        name = m.name
        if name.startswith("qiskit"):
            try:
                mod = importlib.import_module(name)
                ver = getattr(mod, "__version__", "unknown")
                versions[name] = ver
            except Exception as e:
                versions[name] = f"error: {e}"
    return versions


def classify(versions: Dict[str, str]) -> Dict[str, List[str]]:
    modern = []
    legacy = []
    errors = []
    for name, ver in versions.items():
        if ver.startswith("error:"):
            errors.append(name)
            continue
        # Qiskit 1.x core lives under 'qiskit'
        if name == MODERN_ROOT:
            modern.append(name)
        elif any(name.startswith(lp.replace("-", "_")) for lp in LEGACY_PACKAGES):
            legacy.append(name)
        else:
            # ancillary packages (machine learning, optimization, etc.)
            modern.append(name)
    return {
        "modern": sorted(modern),
        "legacy": sorted(legacy),
        "errors": sorted(errors),
    }


def detect_conflict(versions: Dict[str, str]) -> Dict[str, object]:
    """Determine conflict status and recommendation for a supplied versions map.

    Parameters
    ----------
    versions: Mapping of distribution name -> version string or 'error: ...'.

    Returns
    -------
    dict with keys:
      conflict (bool) - whether mixed/invalid environment detected
      recommendation (str) - human guidance
      root_major (int|None) - parsed major version of qiskit root if available
      groups (dict) - classify() output
    """
    groups = classify(versions)
    qiskit_root_version = versions.get(MODERN_ROOT)
    root_major = None
    if qiskit_root_version and not str(qiskit_root_version).startswith("error"):
        try:
            root_major = int(str(qiskit_root_version).split(".")[0])
        except Exception:  # pragma: no cover - defensive
            root_major = None

    conflict = False
    if groups["errors"]:
        conflict = True
    elif root_major is not None and root_major >= 1 and groups["legacy"]:
        conflict = True

    if conflict:
        if groups["errors"]:
            recommendation = "One or more qiskit-related packages failed to import. Recreate the environment and ensure compatible versions."
        else:
            recommendation = "Environment mixes Qiskit >=1.x root package with legacy (<1.0) components. Recreate a clean venv and install only modern (>=1.x) packages or pin everything to <1.0 consistently."
    else:
        if root_major is not None and root_major < 1:
            recommendation = f"Pre-1.0 Qiskit environment detected (qiskit=={qiskit_root_version}). Presence of qiskit_aer and related extras is expected; no conflict."
        else:
            recommendation = "No mixed legacy components detected."

    return {
        "conflict": conflict,
        "recommendation": recommendation,
        "root_major": root_major,
        "groups": groups,
    }


def main():
    versions = find_distributions()
    conflict_meta = detect_conflict(versions)
    qiskit_root_version = versions.get(MODERN_ROOT)
    report = {
        "python": sys.version,
        "qiskit_root_version": qiskit_root_version,
        "packages": versions,
        "groups": conflict_meta["groups"],
        "conflict_detected": conflict_meta["conflict"],
        "recommendation": conflict_meta["recommendation"],
    }
    exit_code = 1 if conflict_meta["conflict"] else 0

    print(json.dumps(report, indent=2))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
