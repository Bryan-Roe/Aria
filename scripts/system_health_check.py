#!/usr/bin/env python3
# ruff: noqa
# flake8: noqa
"""
System Health Check — Comprehensive Aria platform health report.

Checks: Python env, venvs, Azure Functions availability, datasets,
        MCP servers, key configs, and running services.

Usage:
    python scripts/system_health_check.py         # Full report
    python scripts/system_health_check.py --json  # JSON output
    python scripts/system_health_check.py --quiet # Errors/warnings only
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import List

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

REPO_ROOT = Path(__file__).resolve().parent.parent

# ─── result model ─────────────────────────────────────────────────────────────


@dataclass
class CheckResult:
    name: str
    status: str  # ok | warn | fail
    detail: str = ""
    sub: List[CheckResult] = field(default_factory=list)

    @property
    def icon(self) -> str:
        return {"ok": "✅", "warn": "⚠️ ", "fail": "❌"}.get(self.status, "❓")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["icon"] = self.icon
        return d


def _ok(name: str, detail: str = "") -> CheckResult:
    return CheckResult(name, "ok", detail)


def _warn(name: str, detail: str = "") -> CheckResult:
    return CheckResult(name, "warn", detail)


def _fail(name: str, detail: str = "") -> CheckResult:
    return CheckResult(name, "fail", detail)


# ─── checks ───────────────────────────────────────────────────────────────────


def check_python() -> CheckResult:
    v = sys.version.split()[0]
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        return _warn("Python version", f"{v} — recommend ≥ 3.10")
    return _ok("Python version", f"{v} at {sys.executable}")


def check_venvs() -> CheckResult:
    expected = [
        ("Main venv", REPO_ROOT / ".venv"),
        ("Quantum-ML venv", REPO_ROOT / "ai-projects/quantum-ml/venv"),
    ]
    parent = CheckResult("Virtual environments", "ok")
    for label, path in expected:
        cfg = path / "pyvenv.cfg"
        py = path / "bin" / "python3"
        if not cfg.exists():
            parent.sub.append(_warn(label, f"missing — {path}"))
            if parent.status == "ok":
                parent.status = "warn"
        elif not py.exists() or py.stat().st_size == 0:
            parent.sub.append(
                _warn(label, f"python3 binary missing/empty — {py}"))
            if parent.status == "ok":
                parent.status = "warn"
        else:
            try:
                ver = subprocess.check_output(
                    [str(py), "--version"], text=True, timeout=5).strip()
                parent.sub.append(_ok(label, ver))
            except Exception as e:
                parent.sub.append(_warn(label, f"python3 not executable: {e}"))
                if parent.status == "ok":
                    parent.status = "warn"
    return parent


def check_datasets() -> CheckResult:
    datasets_dir = REPO_ROOT / "datasets"
    if not datasets_dir.exists():
        return _fail("Datasets directory", f"missing: {datasets_dir}")
    chat_dir = datasets_dir / "chat"
    if not chat_dir.exists() or not any(chat_dir.iterdir()):
        return _warn("Datasets", "datasets/chat/ is empty or missing")
    count = sum(1 for _ in datasets_dir.rglob("*.json"))
    count += sum(1 for _ in datasets_dir.rglob("*.jsonl"))
    return _ok("Datasets", f"{count} json/jsonl files in datasets/")


def check_configs() -> CheckResult:
    required = [
        "config/autonomous_training.yaml",
        "config/master_orchestrator.yaml",
        "host.json",
        "requirements.txt",
    ]
    parent = CheckResult("Config files", "ok")
    for rel in required:
        p = REPO_ROOT / rel
        if not p.exists():
            parent.sub.append(_fail(rel, "missing"))
            parent.status = "fail"
        else:
            parent.sub.append(_ok(rel))
    return parent


def check_data_out() -> CheckResult:
    required_dirs = [
        "data_out/autotrain",
        "data_out/quantum_autorun",
        "data_out/evaluation_autorun",
        "data_out/master_orchestrator",
        "data_out/integration_smoke",
    ]
    parent = CheckResult("Output directories", "ok")
    for rel in required_dirs:
        p = REPO_ROOT / rel
        if not p.exists():
            parent.sub.append(
                _warn(rel, "missing — will be created on first run"))
            if parent.status == "ok":
                parent.status = "warn"
        else:
            parent.sub.append(_ok(rel))
    return parent


def check_key_scripts() -> CheckResult:
    scripts = [
        "scripts/autonomous_training_orchestrator.py",
        "scripts/autotrain.py",
        "scripts/quantum_autorun.py",
        "scripts/repo_automation.py",
        "scripts/aria_automation.py",
        "scripts/master_orchestrator.py",
        "scripts/fast_validate.py",
        "scripts/test_runner.py",
        "scripts/status_dashboard.py",
        "scripts/resource_monitor.py",
        "scripts/system_health_check.py",
        "apps/aria/server.py",
        "function_app.py",
    ]
    parent = CheckResult("Key scripts", "ok")
    for rel in scripts:
        p = REPO_ROOT / rel
        if not p.exists():
            parent.sub.append(_fail(rel, "missing"))
            parent.status = "fail"
        else:
            # Quick compile check
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(p)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode != 0:
                    parent.sub.append(
                        _warn(rel, f"syntax error: {result.stderr[:80]}"))
                    if parent.status == "ok":
                        parent.status = "warn"
                else:
                    parent.sub.append(_ok(rel))
            except Exception as e:
                parent.sub.append(_warn(rel, str(e)[:80]))
                if parent.status == "ok":
                    parent.status = "warn"
    return parent


def check_python_deps() -> CheckResult:
    """Check critical Python packages are importable (via subprocess to avoid hang)."""
    packages = [
        ("mcp", "mcp", False),
        ("qiskit", "qiskit", False),
        ("torch", "torch", True),
        ("transformers", "transformers", True),
        ("peft", "peft", True),
        ("openai", "openai", False),
        ("azure-functions", "azure.functions", False),
        ("pydantic", "pydantic", False),
        ("psutil", "psutil", False),
        ("RestrictedPython", "RestrictedPython", False),
    ]
    parent = CheckResult("Python dependencies", "ok")
    for display, import_name, optional in packages:
        script = f"import {import_name}; " f"v = getattr({import_name.split('.')[0]}, '__version__', '?'); " f"print(v)"
        try:
            out = subprocess.check_output(
                [sys.executable, "-c", script],
                text=True,
                timeout=8,
                stderr=subprocess.DEVNULL,
            ).strip()
            parent.sub.append(_ok(display, f"v{out}"))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if optional:
                parent.sub.append(
                    _warn(display, "not installed (optional ML lib)"))
                if parent.status == "ok":
                    parent.status = "warn"
            else:
                parent.sub.append(_fail(display, "not installed"))
                parent.status = "fail"
    return parent


def check_services() -> CheckResult:
    """Check if local services are reachable."""
    ports = [
        ("Azure Functions", 7071),
        ("Aria Character", 8080),
    ]
    parent = CheckResult("Running services", "ok",
                         "These are optional — start them as needed")
    for name, port in ports:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                parent.sub.append(_ok(name, f"listening on :{port}"))
        except OSError:
            parent.sub.append(_warn(name, f"not running on :{port}"))
            if parent.status == "ok":
                parent.status = "warn"
    return parent


def check_func_tools() -> CheckResult:
    """Check Azure Functions Core Tools availability."""
    func = shutil.which("func")
    if func:
        try:
            out = subprocess.check_output(
                [func, "--version"], text=True, timeout=5).strip()
            return _ok("Azure Functions Core Tools", f"v{out} at {func}")
        except Exception:
            return _warn("Azure Functions Core Tools", f"found at {func} but --version failed")
    else:
        return _warn(
            "Azure Functions Core Tools",
            "func not found — use local_dev_adapter.py as fallback",
        )


def check_mcp_servers() -> CheckResult:
    """Check MCP server files, config parsing, and stdio MCP handshake."""
    load_mcp_config = import_module("validate_mcp_setup").load_mcp_config
    servers = [
        (
            "quantum-ai MCP",
            "ai-projects/quantum-ml/quantum_mcp_server.py",
            ["qiskit", "mcp.server"],
        ),
        (
            "llm-maker MCP",
            "ai-projects/llm-maker/llm_maker_mcp_server.py",
            ["mcp.server"],
        ),
    ]
    parent = CheckResult("MCP servers", "ok")
    for name, rel, imports in servers:
        p = REPO_ROOT / rel
        if not p.exists():
            parent.sub.append(_fail(name, f"missing: {rel}"))
            parent.status = "fail"
            continue
        missing = []
        for imp in imports:
            ret = subprocess.run(
                [sys.executable, "-c", f"import {imp}"], capture_output=True, timeout=8)
            if ret.returncode != 0:
                missing.append(imp)
        if missing:
            parent.sub.append(
                _fail(name, f"missing imports: {', '.join(missing)}"))
            parent.status = "fail"
        else:
            parent.sub.append(_ok(name, "file exists & imports ok"))
    # mcp.json
    mcp_cfg = REPO_ROOT / ".vscode/mcp.json"
    if mcp_cfg.exists():
        try:
            cfg = load_mcp_config(mcp_cfg)
            count = len(cfg.get("servers", {}))
            parent.sub.append(
                _ok(".vscode/mcp.json", f"{count} servers configured"))
        except Exception as e:
            parent.sub.append(_warn(".vscode/mcp.json", f"parse error: {e}"))
            if parent.status == "ok":
                parent.status = "warn"
    else:
        parent.sub.append(_warn(".vscode/mcp.json", "not found"))
        if parent.status == "ok":
            parent.status = "warn"

    validator_python = REPO_ROOT / ".venv/bin/python"
    validator_script = REPO_ROOT / "scripts/validate_mcp_setup.py"
    if validator_python.exists() and validator_script.exists():
        result = subprocess.run(
            [str(validator_python), str(validator_script)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = (result.stdout or result.stderr).strip()
        if result.returncode == 0:
            parent.sub.append(_ok("MCP stdio validation", output.splitlines(
            )[-1] if output else "all servers responded"))
        else:
            parent.sub.append(_fail("MCP stdio validation",
                              output or "validation failed"))
            parent.status = "fail"
    else:
        parent.sub.append(_warn("MCP stdio validation",
                          "validator script or .venv python missing"))
        if parent.status == "ok":
            parent.status = "warn"
    return parent


def check_local_settings() -> CheckResult:
    """Check local.settings.json exists and doesn't have hard-coded secrets."""
    p = REPO_ROOT / "local.settings.json"
    example = REPO_ROOT / "local.settings.json.example"
    if not p.exists():
        if example.exists():
            return _warn(
                "local.settings.json",
                "missing — copy local.settings.json.example and fill in values",
            )
        return _fail("local.settings.json", "missing (no example template found either)")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        # Warn if it looks like keys are placeholder values
        vals = data.get("Values", {})
        placeholders = [k for k, v in vals.items() if str(
            v).startswith("<") and str(v).endswith(">")]
        if placeholders:
            return _warn(
                "local.settings.json",
                f"placeholder values: {', '.join(placeholders[:5])}",
            )
        return _ok("local.settings.json", f"{len(vals)} env vars configured")
    except Exception as e:
        return _fail("local.settings.json", f"parse error: {e}")


# ─── report ───────────────────────────────────────────────────────────────────


def run_all_checks() -> List[CheckResult]:
    checks = [
        check_python(),
        check_venvs(),
        check_datasets(),
        check_configs(),
        check_data_out(),
        check_key_scripts(),
        check_python_deps(),
        check_services(),
        check_func_tools(),
        check_mcp_servers(),
        check_local_settings(),
    ]
    return checks


def _print_result(r: CheckResult, indent: int = 0, quiet: bool = False):
    prefix = "  " * indent
    if quiet and r.status == "ok" and not r.sub:
        return
    # For parent items, always show if they have non-ok children
    if r.sub:
        has_issues = any(s.status != "ok" for s in r.sub)
        if quiet and not has_issues:
            return
        print(f"{prefix}{r.icon} {r.name}{': ' + r.detail if r.detail else ''}")
        for s in r.sub:
            _print_result(s, indent + 1, quiet)
    else:
        detail = f": {r.detail}" if r.detail else ""
        print(f"{prefix}{r.icon} {r.name}{detail}")


def print_report(checks: List[CheckResult], quiet: bool = False):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(checks)
    ok = sum(1 for c in checks if c.status == "ok")
    warns = sum(1 for c in checks if c.status == "warn")
    fails = sum(1 for c in checks if c.status == "fail")

    print(f"\n{'═'*65}")
    print(f"  🩺 ARIA SYSTEM HEALTH CHECK   {now}")
    print(f"{'═'*65}\n")

    for check in checks:
        _print_result(check, indent=0, quiet=quiet)
        print()

    print(f"{'─'*65}")
    summary_icon = "✅" if fails == 0 and warns == 0 else (
        "⚠️ " if fails == 0 else "❌")
    print(
        f"  {summary_icon} Summary: {ok}/{total} OK  {warns} warnings  {fails} failures")
    print(f"{'═'*65}\n")


def checks_to_json(checks: List[CheckResult]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(checks),
            "ok": sum(1 for c in checks if c.status == "ok"),
            "warn": sum(1 for c in checks if c.status == "warn"),
            "fail": sum(1 for c in checks if c.status == "fail"),
            "all_ok": all(c.status == "ok" for c in checks),
        },
        "checks": [c.to_dict() for c in checks],
    }


# ─── main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aria System Health Check")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--quiet", action="store_true",
                        help="Show warnings/failures only")
    parser.add_argument("--export", metavar="FILE",
                        help="Export JSON report to file")
    args = parser.parse_args()

    checks = run_all_checks()

    if args.json or args.export:
        report = checks_to_json(checks)
        json_str = json.dumps(report, indent=2)
        if args.export:
            Path(args.export).write_text(json_str, encoding="utf-8")
            print(f"✅ Report written to {args.export}")
        if args.json:
            print(json_str)
        if not args.json and not args.export:
            pass
        return

    print_report(checks, quiet=args.quiet)

    # Exit code reflects failures
    if any(c.status == "fail" for c in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
