#!/usr/bin/env python3
"""
Aria Platform Autonomous Systems Dashboard
Real-time monitoring of training orchestrators, quantum jobs, and AI services.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path before importing local shared modules.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.json_utils import load_status_json

DATA_OUT = REPO_ROOT / "data_out"


def load_json(path: Path) -> dict[str, Any]:
    """Safely load JSON file."""
    loaded = load_status_json(path)
    if loaded.get("_status_file_error"):
        return {}
    # Keep backwards compatibility: this helper only returns user payload.
    return {k: v for k, v in loaded.items() if not k.startswith("_status_file_")}


def format_time(iso_str: str | None) -> str:
    """Format ISO timestamp to readable format."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str


def print_status_badge(status: str) -> str:
    """Get emoji badge for status."""
    badges = {
        "completed": "✅",
        "running": "🟢",
        "paused": "⏸️",
        "error": "❌",
        "initializing": "⚙️",
        "training": "🔄",
    }
    return badges.get(status, "❓")


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_training_status():
    """Display autonomous training status."""
    status_file = DATA_OUT / "autonomous_training_status.json"
    data = load_json(status_file)

    if not data:
        print("ℹ️  No training data yet. Run autonomous training to generate reports.\n")
        print("   Quick start:")
        print("   $ python scripts/autonomous_training_demo.py --cycles 3 --interval 5")
        return

    status = data.get("status", "unknown")
    badge = print_status_badge(status)

    print(f"{badge} Status: {status.upper()}")
    print(f"   Last Updated: {format_time(data.get('last_updated'))}")
    print()

    # Metrics
    cycles = data.get("cycles_completed", 0)
    best_acc = data.get("best_accuracy", 0.0)
    datasets = data.get("dataset_inventory", {})

    print("📊 Metrics:")
    print(f"   Cycles Completed: {cycles}")
    print(f"   Best Accuracy: {best_acc:.2%}")
    print(f"   Datasets Found: {len(datasets)}")

    # Performance history
    history = data.get("performance_history", [])
    if history:
        print("\n📈 Performance Trend:")
        for h in history[-3:]:  # Show last 3
            cycle = h.get("cycle", 0)
            acc = h.get("accuracy", 0.0)
            samples = h.get("samples_processed", 0)
            print(f"   Cycle {cycle}: {acc:.2%} accuracy ({samples:,} samples)")

    # Dataset inventory
    if datasets:
        print("\n📁 Datasets Auto-Discovered:")
        for name, info in datasets.items():
            count = info.get("count", 0)
            paths = info.get("paths", [])
            print(f"   {name}: {count} dataset(s)")
            for p in paths[:2]:  # Show first 2
                print(f"      └─ {p}")
            if len(paths) > 2:
                print(f"      └─ ... and {len(paths) - 2} more")


def print_ai_services():
    """Display AI service status."""
    print("🤖 AI Services Available:")
    print()

    services = [
        ("Chat API", "/api/chat", "Multi-provider LLM streaming"),
        ("AI Status", "/api/ai/status", "Health check & provider detection"),
        ("TTS Engine", "/api/tts", "Text-to-speech (Azure or local)"),
        ("Quantum Jobs", "/api/quantum/*", "Quantum circuit submission"),
        ("Aria Character", "http://localhost:8080", "Interactive 3D character"),
    ]

    for name, endpoint, desc in services:
        print(f"   {name:20} {endpoint:20} {desc}")

    print()
    print("   Note: Azure Functions must be running via 'func host start'")
    print("   Note: Aria server must be running via 'cd apps/aria && python server.py'")


def print_quick_commands():
    """Display useful quick commands."""
    print("⚡ Quick Commands:")
    print()

    commands = [
        ("Start Aria server", "cd apps/aria && python server.py", "8080"),
        ("Start Functions API", "func host start", "7071"),
        (
            "Start async training",
            "nohup python scripts/autonomous_training_demo.py --cycles 3 &",
            "bg",
        ),
        (
            "Start continuous mode",
            "nohup python scripts/autonomous_training_demo.py --cycles 0 --interval 1800 &",
            "bg",
        ),
        ("Monitor live logs", "tail -f data_out/autonomous_training.log", "live"),
        ("Check all status", "python scripts/monitor_autonomous_training.py", "api"),
        ("Quick health snapshot", "python scripts/fast_validate.py", "sys"),
    ]

    for name, cmd, mode in commands:
        print(f"   {name:25} │ {mode:6}")
        print(f"   {' ' * 25} $ {cmd}")
        print()


def print_architecture():
    """Display system architecture."""
    print("🏗️  Aria Platform Architecture")
    print()
    print(
        """
   Frontend Layer:
   ├─ Aria Web UI (http://localhost:8080)
   │  └─ Interactive 3D character with voice/text I/O
   │
   ├─ Chat Web UI (http://localhost:7071/api/chat-web)
   │  └─ Multi-turn conversation interface
   │
   └─ Dashboard (http://localhost:7071/api/dashboard)
      └─ Monitoring & analytics hub

   API Gateway:
   └─ Azure Functions (http://localhost:7071)
      ├─ /api/chat          → Multi-provider LLM
      ├─ /api/ai/status     → Health & diagnostics
      ├─ /api/tts           → Speech synthesis
      ├─ /api/quantum/*     → Quantum workflows
      └─ /api/aria/*        → Character control

   Training Pipeline:
   ├─ Autonomous Orchestrator
   │  ├─ Dataset discovery
   │  ├─ Continuous cycles (30 min intervals)
   │  └─ Performance tracking
   │
   ├─ LoRA Fine-tuning (Phi-3.5, Qwen2.5)
   │  └─ Adaptive epochs based on accuracy
   │
   ├─ Quantum-LLM Hybrid (Pennylane + PyTorch)
   │  └─ Quantum circuit enhancement
   │
   └─ Batch Evaluation
      └─ Model comparison & ranking

   Infrastructure:
   ├─ Storage: datasets/, deployed_models/
   ├─ Logs: data_out/*/
   ├─ Config: config/
   └─ Monitoring: status.json files
    """
    )


def main():
    """Display interactive dashboard."""
    print("\n" + "━" * 70)
    print("  🚀 ARIA AUTONOMOUS PLATFORM DASHBOARD")
    print("━" * 70)

    print_header("Training Status")
    print_training_status()

    print_header("Available Services")
    print_ai_services()

    print_header("Getting Started")
    print_quick_commands()

    print_header("System Architecture")
    print_architecture()

    print_header("Next Steps")
    print(
        """
1️⃣  START BACKEND SERVICES
   $ func host start                    # Start Azure Functions on port 7071
   $ cd apps/aria && python server.py   # Start Aria server on port 8080

2️⃣  MONITOR AUTONOMOUS TRAINING
   $ tail -f data_out/autonomous_training.log
    $ python scripts/monitor_autonomous_training.py

3️⃣  INTERACT WITH SERVICES
   • Chat: curl http://localhost:7071/api/chat -d '{"text":"hello"}'
   • Status: curl http://localhost:7071/api/ai/status | jq
   • Aria: Open http://localhost:8080 in browser

4️⃣  SCALE PRODUCTION
   • Deploy to Azure Functions
   • Configure GPU resource pools
   • Enable continuous learning (config/autonomous_training.yaml)
   • Set up monitoring alerts

📚 Full Documentation:
   • AUTONOMOUS_TRAINING_REPORT.md — Detailed training analysis
   • ARIA_QUICKREF.txt — Quick reference guide
   • .github/copilot-instructions.md — Complete architecture docs
   """
    )

    print("=" * 70 + "\n")


if __name__ == "__main__":
    import os

    if "--watch" in sys.argv:
        import time

        while True:
            os.system("clear" if os.name != "nt" else "cls")
            main()
            print("\n⏱️  Refreshing every 5 seconds (Ctrl+C to stop)...\n")
            time.sleep(5)
    else:
        main()
