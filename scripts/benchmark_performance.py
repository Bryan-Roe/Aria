#!/usr/bin/env python
"""
Performance Benchmark Script

Demonstrates the performance improvements from the optimization work.
Compares old patterns vs new optimized patterns.
"""

import json
# Add shared to path
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "shared"))

from performance_utils import find_json_in_output, stream_jsonl, tail_file


def benchmark_tail_file():
    """Benchmark: Old readlines() vs new deque approach"""
    print("\n" + "=" * 80)
    print("BENCHMARK 1: File Tailing")
    print("=" * 80)

    # Create large test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log") as f:
        temp_path = Path(f.name)
        for i in range(100000):  # 100K lines
            f.write(f"Log line {i} with some content to make it realistic\n")

    size_mb = temp_path.stat().st_size / (1024 * 1024)
    print(f"Test file: {size_mb:.1f} MB, 100,000 lines")
    print("Task: Get last 20 lines\n")

    # Old method: readlines()
    t0 = time.time()
    with open(temp_path, "r") as f:
        lines = f.readlines()
        result1 = lines[-20:]
    t_old = time.time() - t0

    # New method: deque
    t0 = time.time()
    result2 = tail_file(temp_path, max_lines=20)
    t_new = time.time() - t0

    # Verify results match
    assert [line.strip() for line in result1] == [line.strip() for line in result2]

    print(f"Old method (readlines):  {t_old*1000:.2f}ms")
    print(f"New method (deque):      {t_new*1000:.2f}ms")
    print(f"Speedup:                 {t_old/t_new:.1f}x faster")
    print(f"Memory savings:          ~{size_mb:.1f} MB (entire file vs 20 lines)")

    temp_path.unlink()
    return t_old / t_new


def benchmark_json_parsing():
    """Benchmark: Old splitlines() vs new rsplit() with reverse search"""
    print("\n" + "=" * 80)
    print("BENCHMARK 2: JSON Parsing from Command Output")
    print("=" * 80)

    # Create realistic command output with JSON at the end
    output_lines = []
    output_lines.append("Starting process...")
    for i in range(1000):
        output_lines.append(f"Processing item {i}...")
    output_lines.append('{"metrics": {"accuracy": 0.95, "loss": 0.05}}')
    output_lines.append("Complete.")

    output = "\n".join(output_lines)
    print(f"Output size: {len(output):,} chars, {len(output_lines):,} lines")
    print("Task: Extract JSON metrics from end\n")

    # Old method: splitlines() and forward search
    t0 = time.time()
    result1 = None
    for line in output.splitlines():
        if line.strip().startswith("{"):
            try:
                data = json.loads(line)
                if "metrics" in data:
                    result1 = data
                    break
            except Exception:
                pass
    t_old = time.time() - t0

    # New method: rsplit() and reverse search
    t0 = time.time()
    result2 = find_json_in_output(
        output, key="metrics", search_from_end=True, max_lines=50
    )
    t_new = time.time() - t0

    # Verify results match
    assert result1 == result2

    print(f"Old method (forward):    {t_old*1000:.3f}ms")
    print(f"New method (reverse):    {t_new*1000:.3f}ms")
    print(f"Speedup:                 {t_old/t_new:.1f}x faster")

    return t_old / t_new


def benchmark_jsonl_streaming():
    """Benchmark: Load all vs streaming JSONL"""
    print("\n" + "=" * 80)
    print("BENCHMARK 3: JSONL Processing")
    print("=" * 80)

    # Create test JSONL file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
        temp_path = Path(f.name)
        for i in range(10000):
            f.write(json.dumps({"id": i, "data": "x" * 100}) + "\n")

    size_mb = temp_path.stat().st_size / (1024 * 1024)
    print(f"Test file: {size_mb:.1f} MB, 10,000 records")
    print("Task: Process records with filtering\n")

    # Old method: Load all into list
    t0 = time.time()
    with open(temp_path, "r") as f:
        all_records = [json.loads(line) for line in f if line.strip()]
    count1 = sum(1 for r in all_records if r["id"] % 2 == 0)
    t_old = time.time() - t0

    # New method: Stream with generator
    t0 = time.time()
    count2 = sum(
        1 for r in stream_jsonl(temp_path, filter_fn=lambda x: x["id"] % 2 == 0)
    )
    t_new = time.time() - t0

    # Verify results match
    assert count1 == count2 == 5000

    print(f"Old method (load all):   {t_old*1000:.2f}ms")
    print(f"New method (streaming):  {t_new*1000:.2f}ms")
    print(f"Speedup:                 {t_old/t_new:.1f}x faster")
    print(f"Memory savings:          ~{size_mb:.1f} MB (streaming vs full load)")

    temp_path.unlink()
    return t_old / t_new


def main():
    print("\n" + "=" * 80)
    print("🚀 ARIA PERFORMANCE OPTIMIZATION BENCHMARKS")
    print("=" * 80)
    print("\nThese benchmarks demonstrate the performance improvements from")
    print("the optimization work completed in this PR.\n")

    speedups = []

    speedups.append(benchmark_tail_file())
    speedups.append(benchmark_json_parsing())
    speedups.append(benchmark_jsonl_streaming())

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Average speedup: {sum(speedups)/len(speedups):.1f}x")
    print(f"Total time saved: {sum(speedups)/len(speedups) - 1:.1%} faster")
    print("\nThese optimizations are now available in shared/performance_utils.py")
    print("and have been integrated into monitoring and evaluation scripts.")
    print("\nFor more details, see docs/PERFORMANCE_OPTIMIZATION_GUIDE.md")
    print()


if __name__ == "__main__":
    main()
