#!/usr/bin/env python3
"""
Test Suite for Repository Automation System

Validates:
- File structure
- Component configuration
- Script functionality
- Dependencies
- Integration points
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def check_file_exists(path: Path, description: str) -> bool:
    """Check if file exists"""
    if path.exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} missing: {path}")
        return False


def test_file_structure():
    """Test required files exist"""
    print("\n📁 Testing file structure...")

    files = [
        (REPO_ROOT / "scripts/repo_automation.py", "Main automation script"),
        (REPO_ROOT / "scripts/start_repo_automation.sh", "Startup wrapper"),
        (REPO_ROOT / "scripts/backup_manager.py", "Backup manager"),
        (REPO_ROOT / "scripts/aria_automation.py", "Aria automation"),
        (REPO_ROOT / "scripts/autotrain.py", "Training orchestrator"),
        (REPO_ROOT / "scripts/quantum_autorun.py", "Quantum orchestrator"),
        (REPO_ROOT / "scripts/evaluation_autorun.py", "Evaluation orchestrator"),
        (REPO_ROOT / "REPO_AUTOMATION_GUIDE.md", "Documentation"),
    ]

    results = [check_file_exists(path, desc) for path, desc in files]
    return all(results)


def test_scripts_executable():
    """Test scripts are executable"""
    print("\n🔐 Testing script permissions...")

    scripts = [
        REPO_ROOT / "scripts/start_repo_automation.sh",
        REPO_ROOT / "scripts/start_aria.sh",
    ]

    all_executable = True
    for script in scripts:
        if script.exists() and script.stat().st_mode & 0o111:
            print(f"✅ Executable: {script.name}")
        else:
            print(f"❌ Not executable: {script.name}")
            all_executable = False

    return all_executable


def test_imports():
    """Test Python imports"""
    print("\n📦 Testing Python imports...")

    try:
        import psutil

        print("✅ psutil installed")
    except ImportError:
        print("❌ psutil not installed")
        return False

    return True


def test_script_help():
    """Test scripts respond to --help"""
    print("\n❓ Testing script help messages...")

    scripts = [
        "scripts/repo_automation.py",
        "scripts/aria_automation.py",
        "scripts/backup_manager.py",
    ]

    all_ok = True
    for script in scripts:
        try:
            result = subprocess.run(
                ["python3", str(REPO_ROOT / script), "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print(f"✅ {script} --help works")
            else:
                print(f"❌ {script} --help failed")
                all_ok = False
        except Exception as e:
            print(f"❌ {script} error: {e}")
            all_ok = False

    return all_ok


def test_component_config():
    """Test component configuration"""
    print("\n⚙️  Testing component configuration...")

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from repo_automation import RepoAutomation

        automation = RepoAutomation()

        expected_components = [
            "aria",
            "training",
            "quantum",
            "evaluation",
            "datasets",
            "monitoring",
            "backup",
        ]

        for component in expected_components:
            if component in automation.components:
                print(f"✅ Component configured: {component}")
            else:
                print(f"❌ Component missing: {component}")
                return False

        return True

    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


def test_directories():
    """Test required directories exist or can be created"""
    print("\n📂 Testing directories...")

    dirs = [
        REPO_ROOT / "data_out",
        REPO_ROOT / "data_out/repo_automation",
        REPO_ROOT / "backups",
    ]

    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        if directory.exists():
            print(f"✅ Directory: {directory}")
        else:
            print(f"❌ Cannot create: {directory}")
            return False

    return True


def test_integration():
    """Test integration with existing systems"""
    print("\n🔗 Testing integration points...")

    # Check master orchestrator integration
    master_config = REPO_ROOT / "config/master_orchestrator.yaml"
    if master_config.exists():
        print(f"✅ Master orchestrator config exists")
    else:
        print(f"⚠️  Master orchestrator config not found (optional)")

    # Check component scripts exist
    component_scripts = [
        "scripts/aria_automation.py",
        "scripts/autotrain.py",
        "scripts/quantum_autorun.py",
        "scripts/evaluation_autorun.py",
    ]

    all_exist = True
    for script in component_scripts:
        path = REPO_ROOT / script
        if path.exists():
            print(f"✅ Component script: {script}")
        else:
            print(f"❌ Missing component: {script}")
            all_exist = False

    return all_exist


def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 Repository Automation Test Suite")
    print("=" * 80)

    tests = [
        ("File Structure", test_file_structure),
        ("Script Permissions", test_scripts_executable),
        ("Python Imports", test_imports),
        ("Script Help", test_script_help),
        ("Component Config", test_component_config),
        ("Directories", test_directories),
        ("Integration", test_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Results Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print("\n" + "=" * 80)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 80 + "\n")

    if passed == total:
        print("🎉 All tests passed! Repository automation ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix issues before using automation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
