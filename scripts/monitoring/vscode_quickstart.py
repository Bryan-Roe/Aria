#!/usr/bin/env python3
"""
VS Code Auto Operations - Quick Setup & Launcher

This script helps set up and launch the VS Code monitoring suite.

Usage:
    python scripts/monitoring/vscode_quickstart.py          # Interactive menu
    python scripts/monitoring/vscode_quickstart.py --server # Start dashboard
    python scripts/monitoring/vscode_quickstart.py --alerts # Start alerts
    python scripts/monitoring/vscode_quickstart.py --cli    # Show CLI dashboard
"""

import subprocess
import sys
import os
import json
import time
import platform
import argparse
from pathlib import Path
from datetime import datetime


class VSCodeQuickStart:
    """Helper to launch VS Code monitoring components"""

    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.scripts_dir = self.workspace_root / "scripts" / "monitoring"
        self.dashboard_url = "http://localhost:8765"
        self.is_windows = platform.system() == "Windows"

    def banner(self):
        """Print banner"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 VS Code Auto Operations Integration                   ║
║                                                              ║
║     Full real-time monitoring in VS Code                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)

    def check_dependencies(self):
        """Check if required packages are installed"""
        try:
            import flask
            import flask_cors
            return True
        except ImportError:
            print("❌ Missing dependencies. Installing...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "flask", "flask-cors"],
                check=True
            )
            return True

    def start_server(self, bg=False):
        """Start dashboard server"""
        print("🚀 Starting dashboard server (localhost:8765)...")
        server_script = self.scripts_dir / "vs_code_server.py"

        if self.is_windows:
            if bg:
                subprocess.Popen(
                    [sys.executable, str(server_script)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run([sys.executable, str(server_script)])
        else:
            cmd = f"python {server_script}"
            if bg:
                subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(cmd, shell=True)

        if bg:
            print("   ✅ Server started in background")
            time.sleep(2)
            print(f"   📍 Access at: {self.dashboard_url}")
            print("   💡 Tip: Use Simple Browser: Ctrl+Shift+P → 'Simple Browser: Open'")

    def start_alerts(self):
        """Start alert monitor"""
        print("🔔 Starting alert monitor...")
        alerts_script = self.scripts_dir / "vs_code_alert_monitor.py"
        subprocess.run([sys.executable, str(alerts_script)])

    def show_cli_dashboard(self, mode="full"):
        """Show CLI dashboard"""
        print(f"📊 Showing {mode} dashboard...")
        dashboard_script = self.scripts_dir / "auto_ops_dashboard.py"
        subprocess.run([sys.executable, str(dashboard_script), f"--{mode}"])

    def start_full_suite(self):
        """Start all components"""
        print("⚡ Starting full monitoring suite...\n")

        # Start server in background
        print("[1/3] Starting dashboard server...")
        self.start_server(bg=True)

        # Start alerts in background
        print("[2/3] Starting alert monitor...")
        alerts_script = self.scripts_dir / "vs_code_alert_monitor.py"
        if self.is_windows:
            subprocess.Popen(
                [sys.executable, str(alerts_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        else:
            subprocess.Popen(f"python {alerts_script}", shell=True)
        print("   ✅ Alert monitor started in background")

        # Show dashboard
        print("[3/3] Displaying dashboard...")
        time.sleep(1)
        self.show_dashboard_info()

    def show_dashboard_info(self):
        """Show how to access dashboard"""
        print("\n" + "=" * 70)
        print("✅ Monitoring suite is running!")
        print("=" * 70)
        print(f"""
📊 Dashboard Server
   URL: {self.dashboard_url}
   How to open:
     1. Use VS Code Simple Browser:
        • Press: Ctrl+Shift+P
        • Search: 'Simple Browser: Open'
        • Enter: {self.dashboard_url}
     2. Or open in your browser: {self.dashboard_url}

🔔 Alert Monitor
   Watches for: CPU, Memory, Disk, Failed jobs, Accuracy decline
   Output: Terminal output panel in VS Code

📋 Running Tasks
   View in: Ctrl+Shift+P → Tasks: Run Task
   Or: Ctrl+Shift+U → Show running tasks

⌨️ Quick Commands
   • Ctrl+Alt+A — Start full suite
   • Ctrl+Alt+D — Start dashboard only
   • Ctrl+Alt+S — Show CLI dashboard
   • Ctrl+Alt+W — Watch mode (auto-refresh)
   • Ctrl+Alt+P — Problems only

💡 Tips
   1. Keep dashboard open while developing
   2. Watch for alerts in output panel
   3. Use Pause/Resume in dashboard to control refresh
   4. Click operations to see full details
""")

    def interactive_menu(self):
        """Show interactive menu"""
        self.banner()

        while True:
            print("""
╔════════════════════════════════════════════════════════╗
║                   What do you want?                     ║
╠════════════════════════════════════════════════════════╣
║  1  Start Full Suite (dashboard + alerts + CLI)         ║
║  2  Start Dashboard Only (web interface)               ║
║  3  Start Alert Monitor Only (background)              ║
║  4  Show CLI Dashboard (full view)                     ║
║  5  Show CLI Dashboard (watch mode)                    ║
║  6  Show CLI Dashboard (problems only)                 ║
║  7  Show Help & Setup                                  ║
║  Q  Quit                                               ║
╚════════════════════════════════════════════════════════╝
""")

            choice = input("Choose (1-7 or Q): ").strip().upper()

            if choice == "1":
                self.check_dependencies()
                self.start_full_suite()
                break
            elif choice == "2":
                self.check_dependencies()
                self.start_server(bg=False)
                break
            elif choice == "3":
                self.start_alerts()
                break
            elif choice == "4":
                self.show_cli_dashboard("full")
            elif choice == "5":
                self.show_cli_dashboard("watch")
            elif choice == "6":
                self.show_cli_dashboard("problems")
            elif choice == "7":
                self.show_help()
            elif choice == "Q":
                print("Goodbye! 👋")
                break
            else:
                print("Invalid choice. Try again.")

    def show_help(self):
        """Show help information"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                       Setup & Help                           ║
╚══════════════════════════════════════════════════════════════╝

📦 REQUIREMENTS
   • Python 3.7+
   • Flask & Flask-CORS (auto-installed if missing)
   • VS Code (for best experience)

🚀 QUICK START
   1. Press: Ctrl+Shift+P
   2. Search: "Monitor: Start Full VS Code Suite"
   3. Wait 2 seconds
   4. Open: http://localhost:8765 in Simple Browser

📊 COMPONENTS

   Dashboard Server (localhost:8765)
   • Real-time operation monitoring
   • Auto-refresh every 5 seconds
   • Pause/resume controls
   • Alert display

   Alert Monitor
   • Checks every 30 seconds
   • Watches: CPU, Memory, Disk, Jobs, Accuracy
   • 5-minute cooldown (prevents spam)
   • Output to terminal/output panel

   CLI Dashboard
   • Full: Complete status of all operations
   • Watch: Auto-refresh every 5 seconds
   • Compact: Minimal view
   • Problems: Only showing issues
   • JSON: Machine-readable format

🔧 COMMANDS

   Command Line:
   $ python scripts/monitoring/auto_ops_dashboard.py --full
   $ python scripts/monitoring/auto_ops_dashboard.py --watch
   $ python scripts/monitoring/auto_ops_dashboard.py --problems
   $ python scripts/monitoring/vs_code_server.py
   $ python scripts/monitoring/vs_code_alert_monitor.py

   VS Code Tasks:
   • Ctrl+Shift+P → "Tasks: Run Task"
   • Select any "Monitor: ..." task

   Keyboard Shortcuts:
   • Ctrl+Alt+A — Full suite
   • Ctrl+Alt+D — Dashboard
   • Ctrl+Alt+S — CLI dashboard
   • Ctrl+Alt+W — CLI watch
   • Ctrl+Alt+P — CLI problems

⚡ PERFORMANCE
   • Dashboard: ~50MB RAM, negligible CPU
   • Alert monitor: ~30MB RAM, checks every 30s
   • Network: Minimal (status JSON only)
   • No database required

🐛 TROUBLESHOOTING

   Q: Dashboard won't load
   A: Check if server is running and port 8765 is free
      Try: http://localhost:8765
      Or change port in vs_code_server.py

   Q: Alerts not showing
   A: Check if alert monitor is running
      View output panel: View → Output

   Q: Port 8765 already in use
   A: Edit vs_code_server.py and change port number

   Q: Tasks not showing in VS Code
   A: Reload window: Ctrl+Shift+P → "Developer: Reload"

📚 DOCUMENTATION
   • docs/VSCODE_INTEGRATION.md — Complete guide
   • docs/AUTO_OPS_VISIBILITY_INDEX.md — All features
   • README.md — Project overview

👨‍💻 SUPPORT
   • Check status: python scripts/monitoring/auto_ops_dashboard.py
   • View alerts: python scripts/monitoring/auto_ops_dashboard.py --problems
   • Health check: curl http://localhost:7071/api/ai/status | jq
"""
        print(help_text)

    def run_cli(self):
        """Run with CLI arguments"""
        parser = argparse.ArgumentParser(
            description="VS Code Auto Operations Quick Start"
        )
        parser.add_argument(
            "--server",
            action="store_true",
            help="Start dashboard server only"
        )
        parser.add_argument(
            "--alerts",
            action="store_true",
            help="Start alert monitor only"
        )
        parser.add_argument(
            "--cli",
            action="store_true",
            help="Show CLI dashboard"
        )
        parser.add_argument(
            "--full",
            action="store_true",
            help="Start full suite"
        )
        parser.add_argument(
            "--watch",
            action="store_true",
            help="Show CLI in watch mode"
        )
        parser.add_argument(
            "--problems",
            action="store_true",
            help="Show problems only"
        )
        parser.add_argument(
            "--help-long",
            action="store_true",
            help="Show detailed help"
        )

        args = parser.parse_args()

        if args.help_long:
            self.show_help()
        elif args.server:
            self.check_dependencies()
            self.start_server()
        elif args.alerts:
            self.start_alerts()
        elif args.cli:
            self.show_cli_dashboard("full")
        elif args.watch:
            self.show_cli_dashboard("watch")
        elif args.problems:
            self.show_cli_dashboard("problems")
        elif args.full:
            self.check_dependencies()
            self.start_full_suite()
        else:
            self.interactive_menu()


def main():
    """Main entry point"""
    try:
        qs = VSCodeQuickStart()
        qs.run_cli()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
