#!/usr/bin/env python3
"""
Unified Orchestrator Status Dashboard
Shows real-time status of all Aria autonomous systems.

Usage:
    python scripts/status_dashboard.py              # One-shot snapshot
    python scripts/status_dashboard.py --watch      # Auto-refresh every 10s
    python scripts/status_dashboard.py --export     # Export to JSON
    python scripts/status_dashboard.py --export dashboard_out.json
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path before importing local shared modules.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.json_utils import load_status_json

DATA_OUT = REPO_ROOT / "data_out"

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_OUT = REPO_ROOT / "data_out"

ORCHESTRATORS = [
    ("Autonomous Training", "autonomous_training_status.json", None),
    ("Autotrain Jobs", "autotrain/status.json", None),
    ("Quantum Autorun", "quantum_autorun/status.json", None),
    ("Evaluation Autorun", "evaluation_autorun/status.json", None),
    ("Master Orchestrator", "master_orchestrator/status.json", None),
    ("CI Orchestrator", "ci_orchestrator/ci_results.json", None),
    ("Integration Smoke", "integration_smoke/status.json", None),
    ("Autonomous Agent", "autonomous_agent/status.json", None),
    ("Repo Automation", "repo_automation/status.json", None),
    ("Multi Agent", "multi_agent/status.json", None),
]

# ─── helpers ────────────────────────────────────────────────────────────────


def _load(rel: str) -> Dict[str, Any]:
    p = DATA_OUT / rel
    loaded = load_status_json(p)
    if loaded.get("_status_file_error"):
        return {}
    # Strip helper metadata for dashboard consumers.
    return {k: v for k, v in loaded.items() if not k.startswith("_status_file_")}


def _load_with_meta(rel: str, max_age_seconds: Optional[int] = None) -> Dict[str, Any]:
    p = DATA_OUT / rel
    return load_status_json(p, max_age_seconds=max_age_seconds)


def _status_hint(data: Dict[str, Any]) -> str:
    if data.get("_status_file_error"):
        return ""
    if data.get("_status_file_stale"):
        return "  ⚠️ stale"
    return ""


def _trim_status_meta(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if not k.startswith("_status_file_")}


def _fmt_time(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        now = datetime.now(timezone.utc)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = now - dt
        secs = int(delta.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs//60}m ago"
        if secs < 86400:
            return f"{secs//3600}h ago"
        return f"{secs//86400}d ago"
    except Exception:
        return iso[:19] if len(iso) >= 19 else iso


def _badge(status: str) -> str:
    return {
        "ok": "✅",
        "completed": "✅",
        "success": "✅",
        "running": "🟢",
        "training": "🔄",
        "initializing": "⚙️",
        "paused": "⏸️",
        "skipped": "⏭️",
        "failed": "❌",
        "error": "❌",
        "warning": "⚠️",
    }.get(str(status).lower(), "❓")


def _row(label: str, value: str, width: int = 30) -> str:
    return f"   {label:<{width}} {value}"


# ─── section printers ────────────────────────────────────────────────────────


def _print_orchestrator(name: str, rel_path: str) -> Dict[str, Any]:
    data_with_meta = _load_with_meta(rel_path, max_age_seconds=24 * 3600)
    data = _trim_status_meta(data_with_meta)
    if data_with_meta.get("_status_file_error"):
        print(f"   {name:<30} ⬜ no data")
        return {"name": name, "status": "no_data"}

    # Generic fields
    total = data.get("total_jobs", data.get("cycles_completed", "?"))
    ok = data.get("succeeded", data.get("ok_count", "?"))
    failed = data.get("failed", data.get("critical_failure_count", 0))
    running = data.get("running", 0)
    updated = data.get("last_updated", data.get("generated_at"))

    status_str = data.get("status", "ok" if failed == 0 else "error")
    badge = _badge(status_str)

    line = f"   {badge} {name:<28} "
    if total != "?":
        line += f"jobs: {ok}/{total}"
        if running:
            line += f"  running: {running}"
        if failed:
            line += f"  failed: {failed}"
    else:
        line += f"status: {status_str}"
    line += f"  [{_fmt_time(updated)}]"
    line += _status_hint(data_with_meta)
    print(line)
    return {
        "name": name,
        "status": status_str,
        "total": total,
        "ok": ok,
        "failed": failed,
    }


def _print_training_detail():
    data = _load("autonomous_training_status.json")
    if not data:
        return
    cycles = data.get("cycles_completed", 0)
    best_acc = data.get("best_accuracy", 0.0)
    history = data.get("performance_history", [])
    print()
    print(f"   Autonomous cycles: {cycles}   best accuracy: {best_acc:.2%}")
    if history:
        recent = history[-3:]
        print("   Recent performance:")
        for h in recent:
            acc = h.get("mean_accuracy", h.get("accuracy", 0.0))
            cyc = h.get("cycle", "?")
            print(f"      cycle {cyc}: {acc:.2%}")


def _print_services():
    print()
    services = [
        ("Azure Functions", "7071", "func host start"),
        ("Aria Character", "8080", "cd apps/aria && python server.py"),
        ("Quantum MCP", "stdio", "python ai-projects/quantum-ml/quantum_mcp_server.py"),
        (
            "LLM Maker MCP",
            "stdio",
            "python ai-projects/llm-maker/llm_maker_mcp_server.py",
        ),
    ]
    for svc, port, cmd in services:
        # Quick port probe
        alive = "—"
        if port.isdigit():
            import socket

            try:
                with socket.create_connection(("127.0.0.1", int(port)), timeout=0.3):
                    alive = "🟢 UP"
            except OSError:
                alive = "⬜ DOWN"
        else:
            alive = "stdio"
        print(f"   {svc:<20} port:{port:<6} {alive}")
        _ = cmd  # suppress unused hint


def print_dashboard() -> List[Dict[str, Any]]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    width = 70
    print("\n" + "═" * width)
    print(f"  📊 ARIA STATUS DASHBOARD   {now}")
    print("═" * width)

    print("\n── Orchestrators " + "─" * 52)
    results = []
    for name, rel, _ in ORCHESTRATORS:
        results.append(_print_orchestrator(name, rel))

    print("\n── Autonomous Training Detail " + "─" * 39)
    _print_training_detail()

    print("\n── Services " + "─" * 57)
    _print_services()

    print("\n" + "═" * width + "\n")
    return results


# ─── export ──────────────────────────────────────────────────────────────────


def export_dashboard(out_path: str):
    results = []
    for name, rel, _ in ORCHESTRATORS:
        data = _load(rel)
        results.append({"orchestrator": name, "path": rel, "data": data})

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "orchestrators": results,
    }
    Path(out_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"✅ Exported to {out_path}")


# ─── main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aria Status Dashboard")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh every 10s")
    parser.add_argument(
        "--export",
        nargs="?",
        const="data_out/dashboard_export.json",
        metavar="FILE",
        help="Export status to JSON",
    )
    parser.add_argument(
        "--interval", type=int, default=10, help="Refresh interval in seconds (--watch)"
    )
    args = parser.parse_args()

    if args.export:
        export_dashboard(args.export)
        return

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                print_dashboard()
                print(f"  ⏱  Refreshing every {args.interval}s  (Ctrl+C to stop)")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")
    else:
        print_dashboard()


if __name__ == "__main__":
    main()
