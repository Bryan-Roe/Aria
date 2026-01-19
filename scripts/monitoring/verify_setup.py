#!/usr/bin/env python3
"""
Verification checklist for VS Code Auto Operations setup

Run this to verify everything is working correctly.
"""

import subprocess
import sys
import json
from pathlib import Path
import time

class VerificationChecklist:
    """Verify VS Code Auto Operations setup"""

    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent  # Goes up 3 levels: monitoring → scripts → workspace
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def banner(self):
        print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║   ✓ VS Code Auto Operations Verification Checklist        ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")

    def check(self, name, func):
        """Run a check and report result"""
        print(f"\n📋 {name}")
        try:
            result = func()
            if result is True:
                print(f"   ✅ PASSED")
                self.passed += 1
            elif result is None:
                print(f"   ⚠️  WARNING")
                self.warnings += 1
            else:
                print(f"   ❌ FAILED: {result}")
                self.failed += 1
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            self.failed += 1

    # Individual checks

    def check_python_version(self):
        """Python 3.7+ required"""
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            print(f"   Python {version.major}.{version.minor}.{version.micro}")
            return True
        return f"Python {version.major}.{version.minor} < 3.7"

    def check_flask_installed(self):
        """Flask package required"""
        try:
            import flask
            print(f"   Flask {flask.__version__}")
            return True
        except ImportError:
            return "Flask not installed"

    def check_flask_cors_installed(self):
        """Flask-CORS package required"""
        try:
            import flask_cors
            print(f"   Flask-CORS installed")
            return True
        except ImportError:
            return "Flask-CORS not installed"

    def check_auto_ops_dashboard_exists(self):
        """Dashboard script exists"""
        path = self.workspace_root / "scripts" / "monitoring" / "auto_ops_dashboard.py"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return f"Not found: {path}"

    def check_vs_code_server_exists(self):
        """VS Code server script exists"""
        path = self.workspace_root / "scripts" / "monitoring" / "vs_code_server.py"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return f"Not found: {path}"

    def check_alert_monitor_exists(self):
        """Alert monitor script exists"""
        path = self.workspace_root / "scripts" / "monitoring" / "vs_code_alert_monitor.py"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return f"Not found: {path}"

    def check_quickstart_exists(self):
        """Quickstart script exists"""
        path = self.workspace_root / "scripts" / "monitoring" / "vscode_quickstart.py"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return f"Not found: {path}"

    def check_tasks_json_exists(self):
        """VS Code tasks.json exists"""
        path = self.workspace_root / ".vscode" / "tasks.json"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return f"Not found: {path}"

    def check_tasks_json_valid(self):
        """tasks.json is valid JSON"""
        path = self.workspace_root / ".vscode" / "tasks.json"
        try:
            with open(path) as f:
                json.load(f)
            print(f"   Valid JSON ✓")
            return True
        except json.JSONDecodeError as e:
            return f"Invalid JSON: {e}"

    def check_monitor_tasks_in_json(self):
        """Monitor tasks are in tasks.json"""
        path = self.workspace_root / ".vscode" / "tasks.json"
        try:
            with open(path) as f:
                data = json.load(f)
            labels = [t.get("label", "") for t in data.get("tasks", [])]
            monitor_tasks = [l for l in labels if l.startswith("Monitor:")]
            if monitor_tasks:
                print(f"   Found {len(monitor_tasks)} monitor tasks")
                for task in monitor_tasks[:3]:
                    print(f"     • {task}")
                return True
            return "No monitor tasks found"
        except Exception as e:
            return f"Error: {e}"

    def check_keybindings_exists(self):
        """Keybindings file exists"""
        path = self.workspace_root / ".vscode" / "keybindings-auto-ops.json"
        if path.exists():
            print(f"   Found: {path.relative_to(self.workspace_root)}")
            return True
        return None  # Optional file

    def check_documentation_exists(self):
        """Documentation files exist"""
        files = [
            "docs/VSCODE_INTEGRATION.md",
            "docs/AUTO_OPS_MONITORING_SUITE.md",
            "docs/GETTING_STARTED_VSCODE.md",
            "AUTO_OPS_VISIBILITY_INDEX.md"
        ]
        found = []
        for file in files:
            path = self.workspace_root / file
            if path.exists():
                found.append(file.split("/")[-1])
        if found:
            print(f"   Found {len(found)}/{len(files)} docs")
            for f in found[:2]:
                print(f"     • {f}")
            return True
        return f"Missing docs"

    def check_status_files_exist(self):
        """Status JSON files exist (sample)"""
        status_files = [
            "data_out/autonomous_training_status.json",
            "data_out/autotrain/status.json",
        ]
        found = []
        for file in status_files:
            path = self.workspace_root / file
            if path.exists():
                found.append(file.split("/")[-1])
        if found:
            print(f"   Found {len(found)} status files")
            return True
        return None  # They may not exist yet

    def check_dashboard_port_free(self):
        """Port 8765 is available"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8765))
            sock.close()
            if result == 0:
                return None  # Port in use, but that's ok (maybe already running)
            else:
                print(f"   Port 8765 is free ✓")
                return True
        except Exception as e:
            return f"Error: {e}"

    def run_all_checks(self):
        """Run all verification checks"""
        self.banner()

        print("🔧 DEPENDENCIES")
        self.check("Python version (3.7+)", self.check_python_version)
        self.check("Flask installed", self.check_flask_installed)
        self.check("Flask-CORS installed", self.check_flask_cors_installed)

        print("\n📁 SCRIPTS")
        self.check("Auto Ops Dashboard script", self.check_auto_ops_dashboard_exists)
        self.check("VS Code server script", self.check_vs_code_server_exists)
        self.check("Alert monitor script", self.check_alert_monitor_exists)
        self.check("Quickstart helper script", self.check_quickstart_exists)

        print("\n⚙️  CONFIGURATION")
        self.check("tasks.json exists", self.check_tasks_json_exists)
        self.check("tasks.json is valid", self.check_tasks_json_valid)
        self.check("Monitor tasks in tasks.json", self.check_monitor_tasks_in_json)
        self.check("Keybindings file (optional)", self.check_keybindings_exists)

        print("\n📚 DOCUMENTATION")
        self.check("Documentation files", self.check_documentation_exists)

        print("\n📊 DATA")
        self.check("Status JSON files (sample)", self.check_status_files_exist)

        print("\n🌐 NETWORK")
        self.check("Dashboard port 8765 available", self.check_dashboard_port_free)

        self.summary()

    def summary(self):
        """Print summary"""
        total = self.passed + self.failed + self.warnings

        print(f"\n{'='*60}")
        print(f"📊 SUMMARY")
        print(f"{'='*60}")
        print(f"  ✅ Passed:  {self.passed}/{total}")
        print(f"  ⚠️  Warnings: {self.warnings}/{total}")
        print(f"  ❌ Failed:  {self.failed}/{total}")

        if self.failed == 0:
            print(f"\n{'='*60}")
            print("🎉 ALL CHECKS PASSED!")
            print(f"{'='*60}")
            print("""
Ready to start monitoring! Choose one:

  1. Interactive menu:
     python scripts/monitoring/vscode_quickstart.py

  2. Start full suite:
     Ctrl+Alt+A

  3. CLI dashboard:
     python scripts/monitoring/auto_ops_dashboard.py

Next: Read the getting started guide
  docs/GETTING_STARTED_VSCODE.md
""")
            return 0
        else:
            print(f"\n{'='*60}")
            print("❌ SOME CHECKS FAILED")
            print(f"{'='*60}")
            print("""
Run this to fix missing packages:
  pip install flask flask-cors

For other issues, check documentation:
  docs/GETTING_STARTED_VSCODE.md
""")
            return 1


def main():
    """Main entry point"""
    checker = VerificationChecklist()
    checker.run_all_checks()


if __name__ == "__main__":
    main()
