from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterable, Sequence
from functools import lru_cache
from pathlib import Path
from textwrap import dedent

DEFAULT_PROBE_MODULES: tuple[str, ...] = ("torch", "transformers", "peft")


def _candidate_venv_python_paths(repo_root: Path, venv_names: Sequence[str]) -> list[Path]:
    """Return likely Python executable locations for a repo-local venv."""
    if sys.platform == "win32":
        layout = (
            ("Scripts", "python.exe"),
            ("Scripts", "python"),
            ("bin", "python.exe"),
            ("bin", "python"),
        )
    else:
        layout = (
            ("bin", "python"),
            ("bin", "python.exe"),
            ("Scripts", "python"),
            ("Scripts", "python.exe"),
        )

    candidates: list[Path] = []
    for venv_name in venv_names:
        for folder, executable in layout:
            candidates.append(repo_root / venv_name / folder / executable)
    return candidates


def locate_project_python(repo_root: Path, venv_names: Sequence[str] = (".venv", "venv")) -> Path:
    """Locate the repo-local Python executable if one exists.

    The returned path is the first existing candidate, ordered to prefer
    ``.venv`` before ``venv`` and to respect platform-specific layouts.
    If no candidate exists, the most likely default path is returned so the
    caller can still surface a useful diagnostic path in health payloads.
    """
    candidates = _candidate_venv_python_paths(repo_root, venv_names)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@lru_cache(maxsize=16)
def probe_python_packages(
    python_path: str,
    modules: tuple[str, ...] = DEFAULT_PROBE_MODULES,
    timeout_seconds: int = 12,
) -> dict[str, object]:
    """Inspect whether a Python executable can import the requested modules.

    Results are cached by executable path and module tuple because the status
    endpoints call this frequently and the package inventory does not normally
    change during a running process.
    """
    python = Path(python_path)
    if not python.exists():
        return {
            "available": {module: False for module in modules},
            "versions": {module: None for module in modules},
            "cached": True,
            "error": f"Python executable not found: {python}",
        }

    code = dedent(f"""
        import importlib.metadata as md
        import importlib.util
        import json

        mods = {list(modules)!r}
        avail = {{m: (importlib.util.find_spec(m) is not None) for m in mods}}
        vers = {{}}
        for m in mods:
            try:
                vers[m] = md.version(m)
            except md.PackageNotFoundError:
                vers[m] = None

        print(json.dumps({{'available': avail, 'versions': vers}}))
        """).strip()

    try:
        proc = subprocess.run(
            [str(python), "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "available": {module: False for module in modules},
            "versions": {module: None for module in modules},
            "cached": True,
            "error": f"Probe timed out after {timeout_seconds}s: {exc}",
        }

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    if proc.returncode != 0:
        return {
            "available": {module: False for module in modules},
            "versions": {module: None for module in modules},
            "cached": True,
            "error": stderr or f"exit {proc.returncode}",
        }

    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError as exc:
        return {
            "available": {module: False for module in modules},
            "versions": {module: None for module in modules},
            "cached": True,
            "error": f"JSON decode failed: {exc}",
        }

    return {
        "available": data.get("available", {}),
        "versions": data.get("versions", {}),
        "cached": True,
    }


def build_venv_info(
    repo_root: Path,
    modules: Iterable[str] = DEFAULT_PROBE_MODULES,
    timeout_seconds: int = 12,
) -> dict[str, object]:
    """Build a status payload describing the repo-local virtual environment."""
    python_path = locate_project_python(repo_root)
    venv_info: dict[str, object] = {
        "path": str(python_path),
        "exists": python_path.exists(),
        "packages": {},
        "error": None,
    }

    if venv_info["exists"]:
        probe = probe_python_packages(str(python_path), tuple(modules), timeout_seconds=timeout_seconds)
        venv_info["packages"] = {
            "available": probe.get("available", {}),
            "versions": probe.get("versions", {}),
        }
        if probe.get("error"):
            venv_info["error"] = probe["error"]

    return venv_info
