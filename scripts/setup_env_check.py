#!/usr/bin/env python3
"""
Environment Setup Validation Script

Provides a comprehensive check that all components are properly configured
for local development and identifies any missing dependencies or services.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")
    print(f"{BOLD}{BLUE}{title}{RESET}")
    print(f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")


def print_ok(msg: str) -> None:
    """Print a success message."""
    print(f"{GREEN}✓{RESET} {msg}")


def print_error(msg: str) -> None:
    """Print an error message."""
    print(f"{RED}✗{RESET} {msg}")


def print_warning(msg: str) -> None:
    """Print a warning message."""
    print(f"{YELLOW}⚠{RESET} {msg}")


def print_info(msg: str) -> None:
    """Print an info message."""
    print(f"{BLUE}ℹ{RESET} {msg}")


def check_python_environment() -> bool:
    """Check Python version and environment."""
    print_section("Python Environment")

    # Check Python version
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    if version_info.major >= 3 and version_info.minor >= 9:
        print_ok(f"Python {version_str}")
    else:
        print_error(f"Python {version_str} (requires >= 3.9)")
        return False

    # Check if in virtual environment
    if hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix):
        print_ok("Virtual environment detected")
    else:
        print_warning("Not running in a virtual environment (recommended for isolation)")

    return True


def check_environment_files() -> bool:
    """Check .env and local.settings.json files."""
    print_section("Environment Files")

    repo_root = Path(__file__).parent.parent.resolve()
    all_ok = True

    # Check .env
    env_file = repo_root / ".env"
    if env_file.exists():
        print_ok(f".env file exists ({env_file.stat().st_size} bytes)")
        with open(env_file) as f:
            content = f.read()
            if "OLLAMA_BASE_URL" in content:
                print_ok("Ollama configured in .env")
            else:
                print_warning("Ollama not configured in .env")
    else:
        print_error(".env file not found")
        all_ok = False

    # Check local.settings.json
    local_settings = repo_root / "local.settings.json"
    if local_settings.exists():
        try:
            with open(local_settings) as f:
                settings = json.load(f)
                values = settings.get("Values", {})
                print_ok(f"local.settings.json exists ({len(values)} settings configured)")
                if "OLLAMA_BASE_URL" in values:
                    print_ok("Ollama configured in local.settings.json")
        except json.JSONDecodeError as e:
            print_error(f"local.settings.json is invalid JSON: {e}")
            all_ok = False
    else:
        print_error("local.settings.json not found")
        all_ok = False

    return all_ok


def check_core_dependencies() -> bool:
    """Check that core Python packages are installed."""
    print_section("Core Dependencies")

    required_packages = {
        "openai": "OpenAI SDK",
        "flask": "Flask web framework",
        "pytest": "Testing framework",
        "yaml": "YAML parser",
        "sqlalchemy": "Database ORM",
        "sqlite3": "SQLite (built-in)",
        "json": "JSON (built-in)",
    }

    all_ok = True
    for package, name in required_packages.items():
        try:
            __import__(package)
            print_ok(f"{name}")
        except ImportError:
            print_error(f"{name} (missing)")
            all_ok = False

    # Optional dependency for local Azure Functions work.
    try:
        __import__("azure_functions")
        print_ok("Azure Functions")
    except ImportError:
        print_warning("Azure Functions (optional; install if using Functions host)")

    return all_ok


def check_local_services() -> bool:
    """Check if local services are running."""
    print_section("Local Services Status")

    services = {
        "Ollama": ("http://127.0.0.1:11434/api/tags", 11434),
        "LM Studio": ("http://127.0.0.1:1234/api/v1/models", 1234),
    }

    for name, (url, port) in services.items():
        try:
            import urllib.request

            request = urllib.request.Request(url, headers={"User-Agent": "setup-check"})  # noqa: S310
            with urllib.request.urlopen(request, timeout=1):  # noqa: S310
                print_ok(f"{name} is running on port {port}")
        except Exception:
            print_warning(f"{name} not accessible on port {port} (not running)")

    return True


def check_project_structure() -> bool:
    """Check that expected project directories exist."""
    print_section("Project Structure")

    repo_root = Path(__file__).parent.parent.resolve()
    expected_required_dirs = {
        "ai-projects/chat-cli": "Chat CLI module",
        "ai-projects/quantum-ml": "Quantum ML module",
        "apps/aria": "Aria character interface",
        "apps/dashboard": "Dashboard interface",
        "shared": "Shared infrastructure",
        "scripts": "Automation scripts",
        "tests": "Test suite",
        "data_out": "Output data directory",
    }

    expected_optional_dirs = {
        "apps/chat": "Chat web interface",
        "config": "Configuration files",
    }

    all_ok = True
    for rel_path, description in expected_required_dirs.items():
        full_path = repo_root / rel_path
        if full_path.exists():
            print_ok(f"{description} ({rel_path})")
        else:
            print_error(f"{description} ({rel_path}) - not found")
            all_ok = False

    for rel_path, description in expected_optional_dirs.items():
        full_path = repo_root / rel_path
        if full_path.exists():
            print_ok(f"{description} ({rel_path})")
        else:
            print_warning(f"{description} ({rel_path}) - optional and not found")

    return all_ok


def check_databases() -> bool:
    """Check database connectivity."""
    print_section("Database Configuration")

    repo_root = Path(__file__).parent.parent.resolve()

    # Check SQLite
    db_conn = os.getenv("QAI_DB_CONN", "sqlite:///data_out/qai.db")
    if "sqlite" in db_conn:
        db_path = db_conn.replace("sqlite:///", "")
        db_full_path = repo_root / db_path
        parent = db_full_path.parent
        if parent.exists():
            print_ok(f"SQLite configured: {db_path}")
        else:
            print_warning(f"SQLite directory will be created: {db_path}")
    else:
        print_info(f"Custom database: {db_conn.split('://')[0] if '://' in db_conn else 'unknown'}")

    return True


def check_ollama_models() -> bool:
    """Check available Ollama models."""
    print_section("Ollama Models")

    try:
        import json as json_module
        import urllib.request

        url = "http://127.0.0.1:11434/api/tags"
        request = urllib.request.Request(url, headers={"User-Agent": "setup-check"})  # noqa: S310

        with urllib.request.urlopen(request, timeout=2) as response:  # noqa: S310
            data = json_module.loads(response.read().decode())
            models = data.get("models", [])

            if models:
                print_ok(f"Found {len(models)} Ollama models:")
                for model in models:
                    size = model.get("details", {}).get("parameter_size", "unknown")
                    print(f"  • {model.get('name', 'unknown')} ({size})")
            else:
                print_warning("No Ollama models found. Run: ollama pull mistral")

        return True
    except Exception as e:
        print_warning(f"Cannot check Ollama models: {str(e)}")
        return True  # Not a blocking issue


def check_ai_token_health() -> bool:
    """Check AI token health status emitted by scripts/generate_ai_tokens.py.

    Advisory-only (non-blocking): this section helps developers quickly see
    whether provider tokens were validated recently and if any provider is
    currently healthy.
    """
    print_section("AI Token Health")

    status_path = Path(__file__).parent.parent / "data_out" / "ai_token_status.json"
    if not status_path.exists():
        print_warning("No token health status found. Run: python3 scripts/generate_ai_tokens.py")
        return True

    try:
        payload = json.loads(status_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print_warning(f"Token status file is invalid JSON: {exc}")
        return True

    healthy = int(payload.get("healthy", 0))
    total = int(payload.get("total", 0))
    last_updated = payload.get("last_updated", "unknown")

    if healthy > 0:
        print_ok(f"Token health: {healthy}/{total} providers healthy")
    else:
        print_warning("Token health: no healthy providers reported")

    print_info(f"Last token check: {last_updated}")

    providers = payload.get("providers", {})
    if isinstance(providers, dict) and providers:
        for name, details in providers.items():
            if not isinstance(details, dict):
                continue
            status = details.get("status", "unknown")
            model = details.get("model", "")
            error = details.get("error", "")
            line = f"  • {name}: {status}"
            if model:
                line += f" (model: {model})"
            if error and status != "ok":
                line += f" — {error}"
            print(line)

    return True


def check_azure_functions() -> bool:
    """Check Azure Functions configuration."""
    print_section("Azure Functions")

    try:
        result = subprocess.run(["func", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_ok(f"Azure Functions CLI installed (version {version})")
        else:
            print_warning("Azure Functions CLI not properly configured")
    except FileNotFoundError:
        print_warning("Azure Functions CLI (func) not installed")
    except subprocess.TimeoutExpired:
        print_warning("Azure Functions CLI check timed out")

    return True


def check_test_suite() -> bool:
    """Check if pytest is configured."""
    print_section("Test Suite")

    repo_root = Path(__file__).parent.parent.resolve()
    pytest_ini = repo_root / "pytest.ini"

    if pytest_ini.exists():
        print_ok("pytest.ini configured")
    else:
        print_warning("pytest.ini not found")

    tests_dir = repo_root / "tests"
    if tests_dir.exists():
        test_files = list(tests_dir.glob("test_*.py"))
        print_ok(f"Test suite directory exists ({len(test_files)} test files)")
    else:
        print_warning("Tests directory not found")

    return True


def print_next_steps() -> None:
    """Print recommended next steps."""
    print_section("Next Steps")

    print(
        f"""
{BOLD}1. Start Services:{RESET}
   • Ollama:    ollama serve
   • LM Studio: lm-studio (GUI application)

{BOLD}2. Run Development Environment:{RESET}
   • Chat CLI:  cd ai-projects/chat-cli && python3 src/chat_cli.py --once "Hello"
   • Aria Web:  cd apps/aria && python3 server.py
   • Functions: func host start

{BOLD}3. Run Tests:{RESET}
   • All tests:       python3 -m pytest tests/ -v
    • Quick smoke:     python3 -m pytest -q tests --maxfail=1
    • Setup check:     python3 scripts/setup_env_check.py

{BOLD}4. Optional Configuration:{RESET}
   • Edit .env for cloud services (OpenAI, Azure OpenAI, etc.)
   • Configure local.settings.json for Azure Functions
   • Set up Cosmos DB or PostgreSQL for production

{BOLD}5. More Information:{RESET}
    • Quick start:     cat QUICK_START_AUTOMATION.md
    • Automation:      cat AUTOMATION_RUNNER.md
    • Watch status:    python3 scripts/watch_continuous_automation.py
"""
    )


def main() -> int:
    """Run all environment checks."""
    print(f"\n{BOLD}{BLUE}Aria Platform - Environment Setup Validation{RESET}")
    print(f"{BLUE}Generated at: {Path(__file__).name}{RESET}\n")

    checks = [
        ("Python Environment", check_python_environment),
        ("Environment Files", check_environment_files),
        ("Core Dependencies", check_core_dependencies),
        ("Project Structure", check_project_structure),
        ("Database Configuration", check_databases),
        ("Local Services", check_local_services),
        ("AI Token Health", check_ai_token_health),
        ("Ollama Models", check_ollama_models),
        ("Azure Functions", check_azure_functions),
        ("Test Suite", check_test_suite),
    ]

    results: list[tuple[str, bool]] = []
    for check_name, check_fn in checks:
        try:
            result = check_fn()
            results.append((check_name, result))
        except Exception as e:
            print_error(f"Error in {check_name}: {e}")
            results.append((check_name, False))

    # Print summary
    print_section("Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status}  {check_name}")

    print(f"\n{BOLD}Result: {passed}/{total} checks passed{RESET}")

    if passed == total:
        print(f"{GREEN}✓ Environment is ready!{RESET}")
    else:
        print(f"{YELLOW}⚠ Some checks failed. Review the output above.{RESET}")

    print_next_steps()

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
