#!/usr/bin/env python3
"""
Aria Web Launcher — Start all web surfaces in the repo.

Ports:
  7071  Azure Functions API    (func host start)
  8080  Aria Character Server  (src/web/aria/aria_web/server.py)
  8000  Dashboard (static)     (src/web/dashboard/dashboard/serve.py)
  8765  Monitoring Dashboard   (scripts/monitoring/vs_code_server.py)
  5000  Dashboard Flask App    (src/web/dashboard/dashboard/app.py)
  8888  Docs (GitHub Pages)    (built‑in http.server serving docs/)

After launch, open http://localhost:8000/web-hub.html for the central hub.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Service Definitions ──────────────────────────────────────────────


@dataclass
class Service:
    name: str
    port: int
    command: List[str]
    cwd: Optional[Path] = None
    env: Dict[str, str] = field(default_factory=dict)
    process: Optional[subprocess.Popen[bytes]] = field(default=None, repr=False)
    optional: bool = False  # don't fail if the service can't start


SERVICES = [
    Service(
        name="Azure Functions API",
        port=7071,
        command=["func", "host", "start", "--port", "7071"],
        cwd=REPO_ROOT,
        optional=True,
    ),
    Service(
        name="Aria Character Server",
        port=8080,
        command=[sys.executable, "server.py"],
        cwd=REPO_ROOT / "src" / "web" / "aria" / "aria_web",
    ),
    Service(
        name="Dashboard (static)",
        port=8000,
        command=[sys.executable, "serve.py"],
        cwd=REPO_ROOT / "src" / "web" / "dashboard" / "dashboard",
    ),
    Service(
        name="Monitoring Dashboard",
        port=8765,
        command=[sys.executable, str(REPO_ROOT / "scripts" / "monitoring" / "vs_code_server.py")],
        cwd=REPO_ROOT,
        optional=True,
    ),
    Service(
        name="Dashboard Flask App",
        port=5000,
        command=[sys.executable, "app.py"],
        cwd=REPO_ROOT / "src" / "web" / "dashboard" / "dashboard",
        env={"PYTHONPATH": str(REPO_ROOT)},
        optional=True,
    ),
    Service(
        name="Docs (GitHub Pages preview)",
        port=8888,
        command=[sys.executable, "-m", "http.server", "8888"],
        cwd=REPO_ROOT / "docs",
        optional=True,
    ),
]

# ── Helpers ──────────────────────────────────────────────────────────


def _is_port_busy(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def _color(text: str, code: int) -> str:
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"


def _green(t: str) -> str:
    return _color(t, 32)


def _yellow(t: str) -> str:
    return _color(t, 33)


def _red(t: str) -> str:
    return _color(t, 31)


def _cyan(t: str) -> str:
    return _color(t, 36)

# ── Main ─────────────────────────────────────────────────────────────


def main() -> None:
    print()
    print(_cyan("=" * 62))
    print(_cyan("  Aria — Web Launcher"))
    print(_cyan("  Starting all web surfaces..."))
    print(_cyan("=" * 62))
    print()

    launched: List[Service] = []
    skipped: List[str] = []

    for svc in SERVICES:
        tag = f"[{svc.name}]"

        # Check port
        if _is_port_busy(svc.port):
            print(f"  {_yellow('SKIP')}  {tag:36s}  port {svc.port} already in use")
            skipped.append(f"{svc.name} (port {svc.port} busy)")
            continue

        # Check cwd exists
        if svc.cwd and not svc.cwd.exists():
            print(f"  {_red('MISS')}  {tag:36s}  directory not found: {svc.cwd}")
            skipped.append(f"{svc.name} (dir missing)")
            continue

        # Build env — force UTF-8 so emoji prints don't crash on Windows cp1252
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", **svc.env}

        # Create log directory
        log_dir = REPO_ROOT / "data_out" / "web_launcher"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{svc.name.lower().replace(' ', '_')}.log"

        try:
            log_fh = open(log_file, "w", encoding="utf-8")
            proc = subprocess.Popen(
                svc.command,
                cwd=str(svc.cwd) if svc.cwd else None,
                env=env,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            svc.process = proc
            launched.append(svc)
            print(f"  {_green(' OK ')}  {tag:36s}  http://localhost:{svc.port}")
        except FileNotFoundError:
            if svc.optional:
                print(f"  {_yellow('SKIP')}  {tag:36s}  command not found (optional)")
                skipped.append(f"{svc.name} (command not found)")
            else:
                print(f"  {_red('FAIL')}  {tag:36s}  command not found: {svc.command[0]}")
        except Exception as exc:
            print(f"  {_red('FAIL')}  {tag:36s}  {exc}")

    # ── Summary ──────────────────────────────────────────────────────
    # Wait a moment for services to either bind or crash
    time.sleep(3)

    # Check which are still alive
    still_alive = []
    early_dead = []
    for svc in launched:
        if svc.process and svc.process.poll() is None:
            still_alive.append(svc)
        else:
            code = svc.process.returncode if svc.process else -1
            log_path = REPO_ROOT / "data_out" / "web_launcher" / f"{svc.name.lower().replace(' ', '_')}.log"
            early_dead.append((svc, code, log_path))

    print()
    print(_cyan("-" * 62))
    print(f"  {_green(str(len(still_alive)))} services running, {_yellow(str(len(skipped)))} skipped, {_red(str(len(early_dead)))} failed")
    print()

    if early_dead:
        print("  Failed services (check logs):")
        for svc, code, log_path in early_dead:
            print(f"    {_red(svc.name):36s}  exit {code}  log: {log_path}")
        print()

    if still_alive:
        print("  Service URLs:")
        for svc in still_alive:
            print(f"    {svc.name:36s}  http://localhost:{svc.port}")
        print()
        print(f"  {_cyan('Hub:')}  http://localhost:8080")
        print(f"        (or open web-hub.html from any running server)")
        print()
        print(f"  Logs:  {REPO_ROOT / 'data_out' / 'web_launcher'}/")
        print()

    # Open hub in browser — prefer a running server
    hub_url = "http://localhost:8080"
    for svc in still_alive:
        if svc.port == 8080:
            hub_url = "http://localhost:8080"
            break
    else:
        # Fall back to any running service
        if still_alive:
            hub_url = f"http://localhost:{still_alive[0].port}"
    try:
        webbrowser.open(hub_url)
        print(f"  Opened {hub_url} in your browser.")
    except Exception:
        print(f"  Could not open browser — navigate to {hub_url} manually.")

    # ── Wait for Ctrl+C ─────────────────────────────────────────────
    print()
    print("  Press Ctrl+C to stop all services...")
    print()

    def _shutdown(*_):
        print()
        print(_yellow("  Shutting down..."))
        for svc in still_alive:
            if svc.process and svc.process.poll() is None:
                try:
                    if sys.platform == "win32":
                        svc.process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        svc.process.terminate()
                except Exception:
                    pass
        # Give processes a beat, then kill stragglers
        time.sleep(1)
        for svc in still_alive:
            if svc.process and svc.process.poll() is None:
                try:
                    svc.process.kill()
                except Exception:
                    pass
        print(_green("  All services stopped."))
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, _shutdown)

    # Keep main thread alive
    try:
        while True:
            # Check for crashed services every 5s
            for svc in list(still_alive):
                if svc.process and svc.process.poll() is not None:
                    print(f"  {_red('DIED')}  {svc.name} (exit {svc.process.returncode})")
                    still_alive.remove(svc)
            if not still_alive:
                print(_yellow("  All services have exited."))
                break
            time.sleep(5)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    main()
