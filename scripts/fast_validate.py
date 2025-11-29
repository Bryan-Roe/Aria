#!/usr/bin/env python
"""
Fast validation runner - minimal checks for rapid feedback
Optimized for speed over completeness
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).resolve().parents[1]

def quick_check_datasets() -> Dict[str, Any]:
    """Lightning-fast dataset existence check (no JSONL parsing)."""
    datasets_dir = REPO_ROOT / "datasets"
    if not datasets_dir.exists():
        return {"status": "missing", "error": "datasets/ directory not found"}
    
    categories = ["chat", "quantum", "vision"]
    found = 0
    for cat in categories:
        cat_dir = datasets_dir / cat
        if cat_dir.exists() and any(cat_dir.iterdir()):
            found += 1
    
    return {
        "status": "ok" if found > 0 else "empty",
        "categories_found": found,
        "speed": "instant"
    }

def quick_check_scripts() -> Dict[str, Any]:
    """Verify critical scripts exist without importing."""
    critical = [
        "scripts/autotrain.py",
        "scripts/test_runner.py",
        "AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py"
    ]
    missing = []
    for script in critical:
        if not (REPO_ROOT / script).exists():
            missing.append(script)
    
    return {
        "status": "ok" if not missing else "missing_scripts",
        "missing": missing,
        "speed": "instant"
    }

def quick_check_venv() -> Dict[str, Any]:
    """Check Python venv exists without inspecting packages."""
    venv_markers = [
        "venv/Scripts/python.exe",
        "venv/bin/python",
        "quantum-ai/venv/Scripts/python.exe"
    ]
    found = sum(1 for m in venv_markers if (REPO_ROOT / m).exists())
    
    return {
        "status": "ok" if found > 0 else "no_venv",
        "venvs_found": found,
        "speed": "instant"
    }

def quick_check_outputs() -> Dict[str, Any]:
    """Verify output directories writable without listing all files."""
    output_dirs = ["data_out", "deployed_models"]
    issues = []
    
    for dirname in output_dirs:
        dirpath = REPO_ROOT / dirname
        if not dirpath.exists():
            try:
                dirpath.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"{dirname}: {e}")
    
    return {
        "status": "ok" if not issues else "write_issues",
        "issues": issues,
        "speed": "instant"
    }

def main() -> None:
    """Run all fast checks (completes in <100ms)."""
    print("🚀 Fast Validation (no heavy imports, no parsing)")
    print("=" * 60)
    
    checks = [
        ("Datasets", quick_check_datasets),
        ("Scripts", quick_check_scripts),
        ("Virtual Envs", quick_check_venv),
        ("Output Dirs", quick_check_outputs),
    ]
    
    results: List[Dict[str, Any]] = []
    all_ok = True
    
    for name, func in checks:
        result = func()
        results.append({"check": name, **result})
        
        status_icon = "✅" if result["status"] == "ok" else "❌"
        print(f"{status_icon} {name:15} - {result['status']}")
        
        if result["status"] != "ok":
            all_ok = False
            for key in ["error", "missing", "issues"]:
                if key in result and result[key]:
                    print(f"   ⚠️  {result[key]}")
    
    print("=" * 60)
    
    # Write results
    output_path = REPO_ROOT / "data_out" / "fast_validate_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"checks": results, "all_ok": all_ok}, f, indent=2)
    
    print(f"✅ Validation complete! Results: {output_path.relative_to(REPO_ROOT)}")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
