#!/usr/bin/env python3
"""System health check and status report for QAI workspace.

Generates a comprehensive report of system status, component health,
and recommendations for improvements.

Usage:
    python scripts/system_health_check.py
    python scripts/system_health_check.py --format json
    python scripts/system_health_check.py --output report.txt
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent


class HealthChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {},
        }
    
    def check_python_environment(self) -> Dict[str, Any]:
        """Check Python version and virtual environments."""
        status = {
            "python_version": sys.version.split()[0],
            "venvs": {},
        }
        
        # Check root venv
        root_venv = REPO_ROOT / "venv" / "Scripts" / "python.exe"
        status["venvs"]["root"] = {
            "path": str(root_venv),
            "exists": root_venv.exists(),
            "purpose": "Azure Functions runtime",
        }
        
        # Check quantum-ai venv
        quantum_venv = REPO_ROOT / "quantum-ai" / "venv" / "Scripts" / "python.exe"
        status["venvs"]["quantum-ai"] = {
            "path": str(quantum_venv),
            "exists": quantum_venv.exists(),
            "purpose": "Quantum ML training",
        }
        
        # Check ML venv
        ml_venv = REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "venv" / "Scripts" / "python.exe"
        status["venvs"]["ml"] = {
            "path": str(ml_venv),
            "exists": ml_venv.exists(),
            "purpose": "LoRA fine-tuning",
        }
        
        # Check talk-to-ai venv
        chat_venv = REPO_ROOT / "talk-to-ai" / "venv" / "Scripts" / "python.exe"
        status["venvs"]["talk-to-ai"] = {
            "path": str(chat_venv),
            "exists": chat_venv.exists(),
            "purpose": "Chat CLI",
        }
        
        return status
    
    def check_azure_functions(self) -> Dict[str, Any]:
        """Check if Azure Functions is running."""
        status = {"running": False, "url": "http://localhost:7071"}
        
        try:
            import urllib.request
            with urllib.request.urlopen("http://localhost:7071/api/ai/status", timeout=2) as response:
                if response.status == 200:
                    status["running"] = True
                    data = json.loads(response.read())
                    status["provider"] = data.get("active_provider")
                    status["quantum_enabled"] = data.get("quantum", {}).get("enabled")
                    status["telemetry_enabled"] = data.get("telemetry", {}).get("enabled")
        except Exception:
            pass
        
        return status
    
    def check_documentation(self) -> Dict[str, Any]:
        """Check documentation completeness."""
        docs = {
            "README.md": "Main project overview",
            "ENHANCEMENTS_SUMMARY.md": "Recent improvements",
            "TELEMETRY_COSMOS_ENABLEMENT.md": "Observability setup",
            "QUICK_REFERENCE.md": "Developer cheat sheet",
            "QUANTUM_AUTORUN_README.md": "Quantum orchestrator",
            "AUTOTRAIN_README.md": "LoRA training orchestrator",
        }
        
        status = {"files": {}}
        for doc, description in docs.items():
            path = REPO_ROOT / doc
            status["files"][doc] = {
                "exists": path.exists(),
                "size_kb": path.stat().st_size / 1024 if path.exists() else 0,
                "description": description,
            }
        
        status["complete_count"] = sum(1 for v in status["files"].values() if v["exists"])
        status["total_count"] = len(docs)
        
        return status
    
    def check_test_coverage(self) -> Dict[str, Any]:
        """Check test files and recent test results."""
        test_dir = REPO_ROOT / "tests"
        status = {
            "test_files": [],
            "total_tests": 0,
        }
        
        if test_dir.exists():
            test_files = list(test_dir.glob("test_*.py"))
            status["test_files"] = [f.name for f in test_files]
            status["total_tests"] = len(test_files)
        
        # Try to get last test run results
        pytest_cache = REPO_ROOT / ".pytest_cache"
        if pytest_cache.exists():
            lastfailed = pytest_cache / "v" / "cache" / "lastfailed"
            if lastfailed.exists():
                status["last_run_had_failures"] = True
            else:
                status["last_run_had_failures"] = False
        
        return status
    
    def check_orchestrators(self) -> Dict[str, Any]:
        """Check orchestrator status files."""
        status = {}
        
        # AutoTrain status
        autotrain_status = REPO_ROOT / "data_out" / "autotrain" / "status.json"
        if autotrain_status.exists():
            with open(autotrain_status) as f:
                data = json.load(f)
            status["autotrain"] = {
                "exists": True,
                "jobs_configured": len(data.get("jobs", [])),
                "last_run": data.get("end_time"),
            }
        else:
            status["autotrain"] = {"exists": False}
        
        # Quantum AutoRun status
        quantum_status = REPO_ROOT / "data_out" / "quantum_autorun" / "status.json"
        if quantum_status.exists():
            with open(quantum_status) as f:
                data = json.load(f)
            status["quantum_autorun"] = {
                "exists": True,
                "jobs_configured": len(data.get("jobs", [])),
                "last_run": data.get("end_time"),
            }
        else:
            status["quantum_autorun"] = {"exists": False}
        
        return status
    
    def check_datasets(self) -> Dict[str, Any]:
        """Check dataset availability."""
        datasets_dir = REPO_ROOT / "datasets"
        status = {
            "quantum": 0,
            "chat": 0,
            "total_size_mb": 0,
        }
        
        if datasets_dir.exists():
            # Count quantum datasets
            quantum_dir = datasets_dir / "quantum"
            if quantum_dir.exists():
                status["quantum"] = len(list(quantum_dir.glob("*.csv")))
            
            # Count chat datasets
            chat_dir = datasets_dir / "chat"
            if chat_dir.exists():
                status["chat"] = len(list(chat_dir.glob("*")))
            
            # Calculate total size
            total_bytes = sum(f.stat().st_size for f in datasets_dir.rglob("*") if f.is_file())
            status["total_size_mb"] = total_bytes / (1024 * 1024)
        
        return status
    
    def run_all_checks(self):
        """Run all health checks."""
        print("Running health checks...")
        
        self.results["checks"]["python"] = self.check_python_environment()
        self.results["checks"]["azure_functions"] = self.check_azure_functions()
        self.results["checks"]["documentation"] = self.check_documentation()
        self.results["checks"]["tests"] = self.check_test_coverage()
        self.results["checks"]["orchestrators"] = self.check_orchestrators()
        self.results["checks"]["datasets"] = self.check_datasets()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate summary and recommendations."""
        checks = self.results["checks"]
        
        # Count virtual environments
        venvs_ok = sum(1 for v in checks["python"]["venvs"].values() if v["exists"])
        total_venvs = len(checks["python"]["venvs"])
        
        # Documentation completeness
        docs_ok = checks["documentation"]["complete_count"]
        total_docs = checks["documentation"]["total_count"]
        
        # Test coverage
        test_count = checks["tests"]["total_tests"]
        
        self.results["summary"] = {
            "overall_health": "good",  # Will be calculated
            "venvs": f"{venvs_ok}/{total_venvs}",
            "docs": f"{docs_ok}/{total_docs}",
            "tests": test_count,
            "azure_functions_running": checks["azure_functions"]["running"],
            "recommendations": [],
        }
        
        # Generate recommendations
        if venvs_ok < total_venvs:
            self.results["summary"]["recommendations"].append(
                "Some virtual environments are missing. Run setup scripts in each project directory."
            )
        
        if not checks["azure_functions"]["running"]:
            self.results["summary"]["recommendations"].append(
                "Azure Functions not running. Start with: func host start"
            )
        
        if docs_ok < total_docs:
            missing = [k for k, v in checks["documentation"]["files"].items() if not v["exists"]]
            self.results["summary"]["recommendations"].append(
                f"Missing documentation: {', '.join(missing)}"
            )
        
        # Overall health determination
        issues = len(self.results["summary"]["recommendations"])
        if issues == 0:
            self.results["summary"]["overall_health"] = "excellent"
        elif issues <= 2:
            self.results["summary"]["overall_health"] = "good"
        else:
            self.results["summary"]["overall_health"] = "needs attention"
    
    def print_report(self):
        """Print human-readable report."""
        print("\n" + "="*70)
        print("QAI SYSTEM HEALTH REPORT")
        print("="*70)
        print(f"\nGenerated: {self.results['timestamp']}")
        print(f"Overall Health: {self.results['summary']['overall_health'].upper()}")
        
        print("\n[PYTHON ENVIRONMENTS]")
        for name, info in self.results["checks"]["python"]["venvs"].items():
            status = "✓" if info["exists"] else "✗"
            print(f"  {status} {name}: {info['purpose']}")
        
        print("\n[AZURE FUNCTIONS]")
        af = self.results["checks"]["azure_functions"]
        if af["running"]:
            print(f"  ✓ Running at {af['url']}")
            print(f"    Provider: {af.get('provider', 'unknown')}")
            print(f"    Quantum: {'enabled' if af.get('quantum_enabled') else 'disabled'}")
            print(f"    Telemetry: {'enabled' if af.get('telemetry_enabled') else 'disabled'}")
        else:
            print(f"  ✗ Not running (expected at {af['url']})")
        
        print("\n[DOCUMENTATION]")
        docs = self.results["checks"]["documentation"]
        print(f"  Complete: {docs['complete_count']}/{docs['total_count']}")
        for doc, info in docs["files"].items():
            status = "✓" if info["exists"] else "✗"
            print(f"    {status} {doc}")
        
        print("\n[TESTS]")
        tests = self.results["checks"]["tests"]
        print(f"  Test files: {tests['total_tests']}")
        
        print("\n[ORCHESTRATORS]")
        orch = self.results["checks"]["orchestrators"]
        for name, info in orch.items():
            if info["exists"]:
                print(f"  ✓ {name}: {info['jobs_configured']} jobs configured")
            else:
                print(f"  ⚠ {name}: No status file (not yet run)")
        
        print("\n[DATASETS]")
        ds = self.results["checks"]["datasets"]
        print(f"  Quantum datasets: {ds['quantum']}")
        print(f"  Chat datasets: {ds['chat']}")
        print(f"  Total size: {ds['total_size_mb']:.1f} MB")
        
        if self.results["summary"]["recommendations"]:
            print("\n[RECOMMENDATIONS]")
            for i, rec in enumerate(self.results["summary"]["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="QAI System Health Check")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()
    
    checker = HealthChecker()
    checker.run_all_checks()
    
    if args.format == "json":
        output = json.dumps(checker.results, indent=2)
        if args.output:
            Path(args.output).write_text(output)
        else:
            print(output)
    else:
        if args.output:
            # Redirect stdout to file
            import sys
            original_stdout = sys.stdout
            with open(args.output, "w") as f:
                sys.stdout = f
                checker.print_report()
            sys.stdout = original_stdout
            print(f"Report saved to {args.output}")
        else:
            checker.print_report()


if __name__ == "__main__":
    main()
