#!/usr/bin/env python3
"""
Aria Diagnostic & Setup Verification Script

Checks all components and provides setup status + next steps.
"""

import subprocess
import sys
import json
import os
from pathlib import Path
from scripts.utils.repo_root import get_repo_root

# Colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

REPO_ROOT = get_repo_root()

def print_header(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_python():
    """Check Python version"""
    print_header("Python Environment")
    try:
        version = sys.version.split()[0]
        print(f"{GREEN}✓{RESET} Python {version}")
        print(f"  Location: {sys.executable}")
        return True
    except Exception as e:
        print(f"{RED}✗{RESET} Python check failed: {e}")
        return False

def check_projects():
    """Check project directories"""
    print_header("Project Directories")
    repo_root = REPO_ROOT
    projects = {
        "aria_web": repo_root / "aria_web" / "server.py",
        "talk-to-ai": repo_root / "talk-to-ai" / "src" / "chat_cli.py",
        "quantum-ai": repo_root / "quantum-ai" / "quantum_mcp_server.py",
        "functions": repo_root / "function_app.py",
    }
    
    all_ok = True
    for name, path in projects.items():
        if path.exists():
            print(f"{GREEN}✓{RESET} {name:20} {path}")
        else:
            print(f"{RED}✗{RESET} {name:20} NOT FOUND: {path}")
            all_ok = False
    
    return all_ok

def check_dependencies():
    """Check key Python packages"""
    print_header("Python Dependencies")
    packages = [
        "flask", "requests", "pydantic", "sqlalchemy", 
        "torch", "qiskit", "pandas", "numpy"
    ]
    
    all_ok = True
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"{GREEN}✓{RESET} {pkg:20} installed")
        except ImportError:
            print(f"{YELLOW}○{RESET} {pkg:20} optional (not installed)")
            if pkg in ["torch", "qiskit"]:  # These are optional
                continue
            else:
                all_ok = False
    
    return all_ok

def check_providers():
    """Test chat provider detection"""
    print_header("Chat Provider Detection")
    try:
        sys.path.insert(0, str(REPO_ROOT / "talk-to-ai" / "src"))
        sys.path.insert(0, str(REPO_ROOT))
        from chat_providers import detect_provider
        
        provider, choice = detect_provider()
        print(f"{GREEN}✓{RESET} Provider detected: {choice.name}")
        print(f"  Model: {choice.model}")
        
        # Check env vars
        print(f"\n  Environment variables:")
        env_vars = {
            "LMSTUDIO_BASE_URL": "LMStudio",
            "AZURE_OPENAI_API_KEY": "Azure OpenAI",
            "OPENAI_API_KEY": "OpenAI",
            "QAI_LORA_MODEL": "LoRA adapter",
        }
        
        for var, desc in env_vars.items():
            if os.getenv(var):
                print(f"    {GREEN}✓{RESET} {desc:20} {var} is set")
            else:
                print(f"    {YELLOW}○{RESET} {desc:20} {var} not set")
        
        return True
    except Exception as e:
        print(f"{RED}✗{RESET} Provider detection failed: {e}")
        return False

def check_config_files():
    """Check essential config files"""
    print_header("Configuration Files")
    repo_root = REPO_ROOT
    configs = {
        "local.settings.json": repo_root / "local.settings.json",
        "autonomous_training.yaml": repo_root / "config" / "autonomous_training.yaml",
        "quantum_autorun.yaml": repo_root / "quantum_autorun.yaml",
        "master_orchestrator.yaml": repo_root / "config" / "master_orchestrator.yaml",
    }
    
    all_ok = True
    for name, path in configs.items():
        if path.exists():
            size = path.stat().st_size
            print(f"{GREEN}✓{RESET} {name:30} {size:,} bytes")
        else:
            print(f"{YELLOW}○{RESET} {name:30} optional")
    
    return all_ok

def check_ports():
    """Check if ports are available"""
    print_header("Port Availability")
    ports = {
        "8080": "Aria Web Interface",
        "7071": "Azure Functions",
        "1234": "LMStudio (optional)",
    }
    
    import socket
    
    for port, service in ports.items():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', int(port)))
            s.close()
            
            if result == 0:
                print(f"{YELLOW}○{RESET} Port {port:5} IN USE - {service}")
            else:
                print(f"{GREEN}✓{RESET} Port {port:5} available - {service}")
        except Exception as e:
            print(f"{YELLOW}○{RESET} Port {port:5} check failed - {service}")

def check_data_directories():
    """Check data output directories"""
    print_header("Data Directories")
    repo_root = REPO_ROOT
    dirs = {
        "data_out": repo_root / "data_out",
        "datasets": repo_root / "datasets",
        "deployed_models": repo_root / "deployed_models",
    }
    
    all_ok = True
    for name, path in dirs.items():
        if path.exists():
            count = len(list(path.glob("*")))
            print(f"{GREEN}✓{RESET} {name:20} exists ({count} items)")
        else:
            print(f"{YELLOW}○{RESET} {name:20} will be created on first run")
    
    return all_ok

def main():
    """Run all checks"""
    print(f"\n{BLUE}{'*'*60}{RESET}")
    print(f"{BLUE}ARIA SYSTEM DIAGNOSTIC & SETUP VERIFICATION{RESET}".center(60))
    print(f"{BLUE}{'*'*60}{RESET}")
    
    results = {
        "Python Environment": check_python(),
        "Project Directories": check_projects(),
        "Dependencies": check_dependencies(),
        "Chat Providers": check_providers(),
        "Configuration Files": check_config_files(),
        "Data Directories": check_data_directories(),
    }
    
    check_ports()
    
    # Summary
    print_header("Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  {status:30} {check}")
    
    print(f"\n  Overall: {BLUE}{passed}/{total} checks passed{RESET}")
    
    # Next Steps
    print_header("Next Steps")
    print(f"""
{BLUE}1. Configure Multi-Provider Chat{RESET}
   Edit: local.settings.json
   Options:
   • Local Echo (already working, zero config)
   • Azure OpenAI (set 4 env vars)
   • OpenAI (set OPENAI_API_KEY)
   • LMStudio (run local + set LMSTUDIO_BASE_URL)

{BLUE}2. Start Aria Web Interface{RESET}
   {YELLOW}cd aria_web && python server.py{RESET}
   Then open: http://localhost:8080

{BLUE}3. Start Azure Functions{RESET}
   {YELLOW}func host start{RESET}
   Health check: curl http://localhost:7071/api/ai/status | jq .

{BLUE}4. Start Autonomous Training{RESET}
   {YELLOW}python scripts/training/autonomous_training_orchestrator.py{RESET}
   Monitor: tail -f data_out/autonomous_training.log

{BLUE}5. Start Quantum MCP Server{RESET}
   {YELLOW}python quantum-ai/quantum_mcp_server.py{RESET}

{BLUE}6. Start Monitoring Dashboard{RESET}
   {YELLOW}python scripts/monitoring/auto_ops_dashboard.py --watch{RESET}

{BLUE}Or start everything at once:{RESET}
   {YELLOW}bash scripts/start_aria_full.sh{RESET}

{BLUE}Test Chat Provider:{RESET}
   {YELLOW}python talk-to-ai/src/chat_cli.py --provider local --once "Hello Aria"{RESET}

See: ARIA_SETUP_GUIDE.md for detailed instructions
    """)

if __name__ == "__main__":
    main()
