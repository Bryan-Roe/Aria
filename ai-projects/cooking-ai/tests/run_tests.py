from __future__ import annotations

import importlib
import sys
from pathlib import Path

TEST_MODULES = [
    "test_agent",
    "test_schemas",
]

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

failures = 0
for mod_name in TEST_MODULES:
    try:
        mod = importlib.import_module(mod_name)
        if hasattr(mod, "__all__"):
            pass
    except Exception as e:  # pragma: no cover
        print(f"[FAIL] import {mod_name}: {e}")
        failures += 1

if failures:
    print(f"{failures} test modules failed to import")
    raise SystemExit(1)
print("All test modules imported OK. (Run each to execute assertions)")
