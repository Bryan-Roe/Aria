"""
GPU Monitoring Utilities for QAI Dashboard
Provides real-time GPU metrics via nvidia-smi
"""

import json
import subprocess
from typing import Dict, List


def get_gpu_info() -> Dict:
    """Get detailed GPU information using nvidia-smi"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,power.limit",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return {"error": "nvidia-smi failed", "available": False}

        gpus = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 9:
                gpus.append(
                    {
                        "index": int(parts[0]),
                        "name": parts[1],
                        "temperature": (
                            float(parts[2]) if parts[2] not in ["N/A", "[N/A]"] else 0
                        ),
                        "utilization": (
                            float(parts[3]) if parts[3] not in ["N/A", "[N/A]"] else 0
                        ),
                        "memory_utilization": (
                            float(parts[4]) if parts[4] not in ["N/A", "[N/A]"] else 0
                        ),
                        "memory_used": (
                            float(parts[5]) if parts[5] not in ["N/A", "[N/A]"] else 0
                        ),
                        "memory_total": (
                            float(parts[6]) if parts[6] not in ["N/A", "[N/A]"] else 0
                        ),
                        "power_draw": (
                            float(parts[7]) if parts[7] not in ["N/A", "[N/A]"] else 0
                        ),
                        "power_limit": (
                            float(parts[8]) if parts[8] not in ["N/A", "[N/A]"] else 0
                        ),
                    }
                )

        return {"available": True, "count": len(gpus), "gpus": gpus}

    except FileNotFoundError:
        return {"error": "nvidia-smi not found", "available": False}
    except subprocess.TimeoutExpired:
        return {"error": "nvidia-smi timeout", "available": False}
    except Exception as e:
        return {"error": str(e), "available": False}


def get_gpu_processes() -> List[Dict]:
    """Get processes currently using GPU"""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,name,used_memory",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return []

        processes = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                processes.append(
                    {
                        "pid": int(parts[0]),
                        "name": parts[1],
                        "memory_mb": (
                            float(parts[2]) if parts[2] not in ["N/A", "[N/A]"] else 0
                        ),
                    }
                )

        return processes

    except Exception:
        return []


def get_system_resources() -> Dict:
    """Get CPU and memory information"""
    try:
        import psutil

        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_gb": round(psutil.disk_usage("/").total / (1024**3), 2),
                "used_gb": round(psutil.disk_usage("/").used / (1024**3), 2),
                "percent": psutil.disk_usage("/").percent,
            },
        }
    except ImportError:
        return {"error": "psutil not installed"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test GPU monitoring
    print("=== GPU Information ===")
    gpu_info = get_gpu_info()
    print(json.dumps(gpu_info, indent=2))

    print("\n=== GPU Processes ===")
    processes = get_gpu_processes()
    print(json.dumps(processes, indent=2))

    print("\n=== System Resources ===")
    resources = get_system_resources()
    print(json.dumps(resources, indent=2))
