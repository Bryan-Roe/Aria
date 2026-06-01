import sys
import time
from pathlib import Path

# Ensure package source is importable when tests run from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tool_validator import ToolValidator


def sample_code():
    return """
import math
import requests

with open('test.txt', 'w') as f:
    f.write('hello')

for i in range(100):
    s = 'requests.get("http://example.com")'
    s2 = 'socket.connect()'
    s3 = 'eval("2+2")'
"""


def test_validate_perf_runs_under_threshold():
    v = ToolValidator()
    code = sample_code()

    iterations = 500
    start = time.perf_counter()
    for _ in range(iterations):
        valid, errors = v.validate(code)
        assert isinstance(valid, bool)
    elapsed = time.perf_counter() - start

    # allow a generous threshold to avoid flaky CI; this captures large regressions
    assert elapsed < 1.0, f"Validation too slow: {elapsed:.3f}s for {iterations} iterations"
