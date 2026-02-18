#!/usr/bin/env python3
"""
Quick CI validation script to verify pytest setup before running full suite.
This runs basic checks to ensure the test environment is properly configured.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False


def main():
    """Run all validation checks."""
    print("\n" + "="*60)
    print("🚀 PYTEST CI VALIDATION")
    print("="*60)
    
    checks = [
        (
            [sys.executable, "-m", "pytest", "--version"],
            "Check pytest installation"
        ),
        (
            [sys.executable, "-m", "pytest", "--collect-only", "tests/", "-q"],
            "Collect all tests"
        ),
        (
            [sys.executable, "-m", "pytest", "--markers"],
            "Verify test markers"
        ),
        (
            [sys.executable, "-c", "import pytest; import croniter; print('✓ Dependencies OK')"],
            "Check required dependencies"
        ),
    ]
    
    results = []
    for cmd, desc in checks:
        results.append(run_command(cmd, desc))
    
    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 All validation checks passed!")
        print("✅ Ready to run pytest CI pipeline")
        return 0
    else:
        print("\n⚠️ Some validation checks failed")
        print("❌ Please fix issues before running full test suite")
        return 1


if __name__ == "__main__":
    sys.exit(main())
