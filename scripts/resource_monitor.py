#!/usr/bin/env python3
"""
Resource Monitor — CPU / Memory / Disk / GPU snapshot with threshold alerts.

Usage:
    python scripts/resource_monitor.py --snapshot          # One-shot print
    python scripts/resource_monitor.py --watch             # Continuous monitoring
    python scripts/resource_monitor.py --watch --interval 5
    python scripts/resource_monitor.py --export out.json   # JSON export
    python scripts/resource_monitor.py --thresholds        # Show threshold config
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ─── thresholds ──────────────────────────────────────────────────────────────
THRESHOLDS = {
    "cpu_percent": {"warn": 75.0, "crit": 90.0},
    "mem_percent": {"warn": 80.0, "crit": 95.0},
    "disk_percent": {"warn": 80.0, "crit": 90.0},
    "gpu_mem_percent": {"warn": 80.0, "crit": 95.0},
    "gpu_util": {"warn": 80.0, "crit": 95.0},
}


def _level(name: str, value: float) -> str:
    t = THRESHOLDS.get(name, {})
    if value >= t.get("crit", 100):
        return "crit"
    if value >= t.get("warn", 100):
        return "warn"
    return "ok"


def _badge(level: str) -> str:
    return {"ok": "✅", "warn": "⚠️ ", "crit": "🔴"}.get(level, "❓")


# ─── collectors ──────────────────────────────────────────────────────────────


def _collect_cpu_mem() -> Dict[str, Any]:
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.5)
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        la = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
        return {
            "cpu_percent": round(cpu, 1),
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_count_phys": psutil.cpu_count(logical=False),
            "load_avg_1m": round(la[0], 2),
            "load_avg_5m": round(la[1], 2),
            "load_avg_15m": round(la[2], 2),
            "mem_total_gb": round(vm.total / 1e9, 2),
            "mem_used_gb": round(vm.used / 1e9, 2),
            "mem_avail_gb": round(vm.available / 1e9, 2),
            "mem_percent": round(vm.percent, 1),
            "swap_total_gb": round(sw.total / 1e9, 2),
            "swap_used_gb": round(sw.used / 1e9, 2),
            "swap_percent": round(sw.percent, 1),
        }
    except ImportError:
        # Fallback via /proc on Linux
        result: Dict[str, Any] = {}
        try:
            with open("/proc/loadavg") as f:
                parts = f.read().split()
            result["load_avg_1m"] = float(parts[0])
            result["load_avg_5m"] = float(parts[1])
            result["load_avg_15m"] = float(parts[2])
        except Exception:
            pass
        try:
            mem: Dict[str, int] = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":")[:2]
                    mem[k.strip()] = int(v.strip().split()[0])  # kB
            total = mem.get("MemTotal", 0)
            avail = mem.get("MemAvailable", 0)
            used = total - avail
            result["mem_total_gb"] = round(total / 1e6, 2)
            result["mem_used_gb"] = round(used / 1e6, 2)
            result["mem_avail_gb"] = round(avail / 1e6, 2)
            result["mem_percent"] = round(used / total * 100, 1) if total else 0.0
        except Exception:
            pass
        return result


def _collect_disk() -> List[Dict[str, Any]]:
    try:
        import psutil

        partitions = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                partitions.append(
                    {
                        "mountpoint": p.mountpoint,
                        "device": p.device,
                        "fstype": p.fstype,
                        "total_gb": round(usage.total / 1e9, 2),
                        "used_gb": round(usage.used / 1e9, 2),
                        "free_gb": round(usage.free / 1e9, 2),
                        "disk_percent": round(usage.percent, 1),
                    }
                )
            except PermissionError:
                continue
        return partitions
    except ImportError:
        # Fallback via df
        import subprocess

        try:
            out = subprocess.check_output(
                ["df", "-BG", "--output=target,source,fstype,size,used,avail,pcent"],
                text=True,
                timeout=5,
            )
            rows = []
            for line in out.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) < 7:
                    continue
                rows.append(
                    {
                        "mountpoint": parts[0],
                        "device": parts[1],
                        "fstype": parts[2],
                        "total_gb": float(parts[3].rstrip("G")),
                        "used_gb": float(parts[4].rstrip("G")),
                        "free_gb": float(parts[5].rstrip("G")),
                        "disk_percent": float(parts[6].rstrip("%")),
                    }
                )
            return rows
        except Exception:
            return []


def _collect_gpu() -> List[Dict[str, Any]]:
    """Try nvidia-smi, then torch CUDA."""
    import subprocess

    # nvidia-smi
    try:
        qfields = "index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw"
        out = subprocess.check_output(
            ["nvidia-smi", f"--query-gpu={qfields}", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        )
        gpus = []
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 7:
                continue
            mem_used = float(parts[3]) if parts[3] not in ("[N/A]", "N/A") else 0
            mem_total = float(parts[4]) if parts[4] not in ("[N/A]", "N/A") else 1
            mem_pct = round(mem_used / mem_total * 100, 1) if mem_total else 0
            gpus.append(
                {
                    "index": int(parts[0]),
                    "name": parts[1],
                    "gpu_util": (
                        float(parts[2]) if parts[2] not in ("[N/A]", "N/A") else 0
                    ),
                    "mem_used_mb": mem_used,
                    "mem_total_mb": mem_total,
                    "gpu_mem_percent": mem_pct,
                    "temp_c": (
                        float(parts[5]) if parts[5] not in ("[N/A]", "N/A") else None
                    ),
                    "power_w": (
                        float(parts[6]) if parts[6] not in ("[N/A]", "N/A") else None
                    ),
                }
            )
        return gpus
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        pass
    # torch CUDA fallback
    try:
        torch = __import__("torch")
        gpus = []
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            mem_used_bytes = torch.cuda.memory_allocated(i)
            mem_total_bytes = props.total_memory
            pct = (
                round(mem_used_bytes / mem_total_bytes * 100, 1)
                if mem_total_bytes
                else 0
            )
            gpus.append(
                {
                    "index": i,
                    "name": props.name,
                    "gpu_util": None,
                    "mem_used_mb": round(mem_used_bytes / 1e6, 1),
                    "mem_total_mb": round(mem_total_bytes / 1e6, 1),
                    "gpu_mem_percent": pct,
                    "temp_c": None,
                    "power_w": None,
                }
            )
        return gpus
    except Exception:
        return []


# ─── snapshot ────────────────────────────────────────────────────────────────


def collect_snapshot() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_mem": _collect_cpu_mem(),
        "disks": _collect_disk(),
        "gpus": _collect_gpu(),
    }


# ─── printing ────────────────────────────────────────────────────────────────


def _bar(pct: float, width: int = 20) -> str:
    filled = int(pct / 100 * width)
    return "[" + "█" * filled + "░" * (width - filled) + f"] {pct:5.1f}%"


def print_snapshot(snap: Dict[str, Any]):
    ts = snap.get("timestamp", "")[:19].replace("T", " ")
    cm = snap.get("cpu_mem", {})
    disks = snap.get("disks", [])
    gpus = snap.get("gpus", [])

    alerts: List[str] = []

    print(f"\n{'─'*60}")
    print(f"  💻 RESOURCE MONITOR   {ts}")
    print(f"{'─'*60}")

    # CPU
    cpu_pct = cm.get("cpu_percent", 0.0)
    lvl = _level("cpu_percent", cpu_pct)
    badge = _badge(lvl)
    la1 = cm.get("load_avg_1m", "—")
    la5 = cm.get("load_avg_5m", "—")
    cores = cm.get("cpu_count", "?")
    print(f"\n  CPU  {badge}  {_bar(cpu_pct)}   load: {la1}/{la5}  cores: {cores}")
    if lvl != "ok":
        alerts.append(
            f"CPU {lvl.upper()}: {cpu_pct}% (threshold: {THRESHOLDS['cpu_percent'][lvl]}%)"
        )

    # Memory
    mem_pct = cm.get("mem_percent", 0.0)
    mem_used = cm.get("mem_used_gb", 0)
    mem_total = cm.get("mem_total_gb", 0)
    swap_pct = cm.get("swap_percent", 0.0)
    swap_used = cm.get("swap_used_gb", 0)
    lvl = _level("mem_percent", mem_pct)
    print(f"  MEM  {_badge(lvl)}  {_bar(mem_pct)}   {mem_used:.1f}/{mem_total:.1f} GB")
    if cm.get("swap_total_gb", 0):
        print(f"  SWAP     {_bar(swap_pct)}   {swap_used:.1f} GB used")
    if lvl != "ok":
        alerts.append(
            f"Memory {lvl.upper()}: {mem_pct}% (threshold: {THRESHOLDS['mem_percent'][lvl]}%)"
        )

    # Disks
    if disks:
        print("\n  DISK:")
        repo_root = str(Path(__file__).resolve().parent.parent)
        for d in disks:
            mp = d.get("mountpoint", "?")
            pct = d.get("disk_percent", 0.0)
            used = d.get("used_gb", 0)
            tot = d.get("total_gb", 0)
            lvl = _level("disk_percent", pct)
            mark = " ◀ repo" if repo_root.startswith(mp) else ""
            print(
                f"  {mp:<16} {_badge(lvl)}  {_bar(pct)}   {used:.0f}/{tot:.0f} GB{mark}"
            )
            if lvl != "ok":
                alerts.append(
                    f"Disk {mp} {lvl.upper()}: {pct}% (threshold: {THRESHOLDS['disk_percent'][lvl]}%)"
                )

    # GPUs
    if gpus:
        print("\n  GPU:")
        for g in gpus:
            name = g.get("name", "?")[:30]
            util_pct = g.get("gpu_util") or 0.0
            mem_pct_g = g.get("gpu_mem_percent", 0.0)
            temp = g.get("temp_c")
            lvl_util = _level("gpu_util", util_pct)
            lvl_mem = _level("gpu_mem_percent", mem_pct_g)
            temp_str = f"  {temp}°C" if temp is not None else ""
            print(f"  [{g['index']}] {name:<30}")
            if util_pct is not None:
                print(f"      util {_badge(lvl_util)}  {_bar(util_pct)}{temp_str}")
            print(
                f"      mem  {_badge(lvl_mem)}  {_bar(mem_pct_g)}   {g.get('mem_used_mb', 0):.0f}/{g.get('mem_total_mb', 0):.0f} MB"
            )
            for lvl, key in [(lvl_util, "gpu_util"), (lvl_mem, "gpu_mem_percent")]:
                if lvl != "ok":
                    alerts.append(
                        f"GPU[{g['index']}] {key} {lvl.upper()}: (threshold: {THRESHOLDS[key][lvl]}%)"
                    )
    else:
        print("\n  GPU: none detected")

    # Alerts
    if alerts:
        print(f"\n  {'─'*56}")
        print(f"  🚨 ALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"     • {a}")
    else:
        print("\n  ✅ All resources within normal thresholds")

    print(f"{'─'*60}\n")


# ─── main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Aria Resource Monitor")
    parser.add_argument(
        "--snapshot", action="store_true", help="One-shot snapshot (default)"
    )
    parser.add_argument("--watch", action="store_true", help="Continuous monitoring")
    parser.add_argument(
        "--interval", type=int, default=5, help="Refresh interval in seconds"
    )
    parser.add_argument(
        "--export",
        nargs="?",
        const="data_out/resource_snapshot.json",
        metavar="FILE",
        help="Export snapshot to JSON",
    )
    parser.add_argument(
        "--thresholds", action="store_true", help="Show alert thresholds"
    )
    args = parser.parse_args()

    if args.thresholds:
        print("\nAlert thresholds:")
        for k, v in THRESHOLDS.items():
            print(f"  {k:<22} warn={v['warn']}%  crit={v['crit']}%")
        print()
        return

    if args.export:
        snap = collect_snapshot()
        out = Path(args.export)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(snap, indent=2), encoding="utf-8")
        print_snapshot(snap)
        print(f"✅ Exported to {args.export}")
        return

    if args.watch:
        try:
            while True:
                os.system("clear" if os.name != "nt" else "cls")
                print_snapshot(collect_snapshot())
                print(f"  ⏱  Refreshing every {args.interval}s  (Ctrl+C to stop)\n")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
    else:
        # default: snapshot
        print_snapshot(collect_snapshot())


if __name__ == "__main__":
    main()
