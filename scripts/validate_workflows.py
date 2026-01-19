#!/usr/bin/env python3
"""
Quick validation script for GitHub Actions workflows.
Checks if all required scripts and files exist.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

REPO_ROOT = Path(__file__).parent.parent

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists relative to repo root."""
    full_path = REPO_ROOT / file_path
    return full_path.exists()

def validate_workflow_dependencies() -> List[Tuple[str, str, bool, str]]:
    """Validate all workflow dependencies.
    
    Returns:
        List of tuples: (workflow_name, file_path, exists, status)
    """
    checks = []
    
    # Auto Validation workflow
    checks.append(('Auto Validation', 'scripts/orchestrators/auto_bootstrap.py', 
                   check_file_exists('scripts/orchestrators/auto_bootstrap.py'), 'Required'))
    
    # CI Pipeline workflow
    checks.append(('CI Pipeline', 'scripts/orchestrators/ci_orchestrator.py',
                   check_file_exists('scripts/orchestrators/ci_orchestrator.py'), 'Required'))
    checks.append(('CI Pipeline', 'scripts/test_runner.py',
                   check_file_exists('scripts/test_runner.py'), 'Required'))
    checks.append(('CI Pipeline', 'scripts/training/autotrain.py',
                   check_file_exists('scripts/training/autotrain.py'), 'Required'))
    
    # Aria Tests workflow
    checks.append(('Aria Tests', 'aria_web/server.py',
                   check_file_exists('aria_web/server.py'), 'Required'))
    checks.append(('Aria Tests', 'tests/test_aria_server.py',
                   check_file_exists('tests/test_aria_server.py'), 'Required'))
    checks.append(('Aria Tests', 'tests/test_object_api_integration.py',
                   check_file_exists('tests/test_object_api_integration.py'), 'Required'))
    checks.append(('Aria Tests', 'tests/test_ui_playwright.py',
                   check_file_exists('tests/test_ui_playwright.py'), 'Optional'))
    checks.append(('Aria Tests', 'tests/test_ui_pyppeteer.py',
                   check_file_exists('tests/test_ui_pyppeteer.py'), 'Optional'))
    checks.append(('Aria Tests', 'tests/test_ui_selenium.py',
                   check_file_exists('tests/test_ui_selenium.py'), 'Optional'))
    
    # E2E Tests workflow (same as Aria Tests)
    checks.append(('E2E Tests', 'aria_web/server.py',
                   check_file_exists('aria_web/server.py'), 'Required'))
    checks.append(('E2E Tests', 'tests/test_aria_server.py',
                   check_file_exists('tests/test_aria_server.py'), 'Required'))
    
    # Aria Pages workflow
    checks.append(('Aria Pages', 'aria_web/index.html',
                   check_file_exists('aria_web/index.html'), 'Required'))
    
    # Quantum Orchestration workflow
    checks.append(('Quantum Orchestration', 'quantum-ai/azure/quantum_master_orchestration.ps1',
                   check_file_exists('quantum-ai/azure/quantum_master_orchestration.ps1'), 'Optional'))
    
    # AzureML Train workflow
    checks.append(('AzureML Train', 'AI/microsoft_phi-silica-3.6_v1/azureml/job-lora-train.yml',
                   check_file_exists('AI/microsoft_phi-silica-3.6_v1/azureml/job-lora-train.yml'), 'Optional'))
    
    # Common requirements
    checks.append(('All Workflows', 'requirements.txt',
                   check_file_exists('requirements.txt'), 'Required'))
    checks.append(('All Workflows', 'pytest.ini',
                   check_file_exists('pytest.ini'), 'Optional'))
    
    return checks

def print_validation_results(checks: List[Tuple[str, str, bool, str]]) -> bool:
    """Print validation results and return overall status."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}GitHub Actions Workflow Validation{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    current_workflow = None
    all_required_exist = True
    
    for workflow, file_path, exists, status in checks:
        if workflow != current_workflow:
            if current_workflow is not None:
                print()  # Add spacing between workflows
            current_workflow = workflow
            print(f"{BLUE}[{workflow}]{RESET}")
        
        status_icon = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
        status_text = f"({YELLOW}{status}{RESET})" if status == "Optional" else f"({status})"
        
        print(f"  {status_icon} {file_path} {status_text}")
        
        if not exists and status == "Required":
            all_required_exist = False
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    
    if all_required_exist:
        print(f"{GREEN}✓ All required files exist!{RESET}")
        print(f"{GREEN}GitHub Actions workflows should run successfully.{RESET}\n")
        return True
    else:
        print(f"{RED}✗ Some required files are missing!{RESET}")
        print(f"{YELLOW}Fix missing files before running workflows.{RESET}\n")
        return False

def check_port_configuration():
    """Check if aria_web/server.py uses the correct port."""
    server_file = REPO_ROOT / 'aria_web' / 'server.py'
    
    if not server_file.exists():
        print(f"{YELLOW}⚠ Cannot check port configuration: server.py not found{RESET}")
        return
    
    with open(server_file, 'r') as f:
        content = f.read()
    
    # Check for port configuration
    if "ARIA_PORT" in content and "8080" in content:
        print(f"{GREEN}✓ Server port configuration looks correct (8080){RESET}")
    else:
        print(f"{YELLOW}⚠ Check server.py port configuration{RESET}")

def main():
    """Main validation function."""
    print(f"\n{BLUE}Validating GitHub Actions workflow dependencies...{RESET}\n")
    
    checks = validate_workflow_dependencies()
    all_ok = print_validation_results(checks)
    
    # Additional checks
    print(f"{BLUE}Additional Checks:{RESET}")
    check_port_configuration()
    
    # Check Python version
    print(f"{GREEN}✓ Python version: {sys.version.split()[0]}{RESET}")
    
    # Check if in repo root
    if (REPO_ROOT / '.github' / 'workflows').exists():
        print(f"{GREEN}✓ .github/workflows directory exists{RESET}")
    else:
        print(f"{RED}✗ .github/workflows directory not found{RESET}")
        all_ok = False
    
    print()
    
    sys.exit(0 if all_ok else 1)

if __name__ == '__main__':
    main()
