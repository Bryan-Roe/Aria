# Performance Optimization Implementation Guide

This guide provides step-by-step instructions for implementing the performance improvements identified in `PERFORMANCE_ANALYSIS.md`.

---

## 🎯 Implementation Roadmap

### Week 1: Critical Fixes
- **Fix #1**: Aria keyword lookups (aria_web/server.py)
- **Fix #3**: Batch evaluator indexing (scripts/batch_evaluator.py)
- **Fix #6**: Remove redundant iteration (scripts/batch_evaluator.py)

### Week 2-3: High-Priority Fixes
- **Fix #2**: Batch embedding API (shared/chat_memory.py)
- **Fix #7**: Refactor complex functions (function_app.py)
- **Fix #11**: Add caching (function_app.py ai_status)

### Month 2: Remaining Fixes
- **Fix #4, #5, #12**: Training analytics improvements
- **Fix #8**: Vectorize similarity search
- **Fixes #9-10, #13-15**: Minor optimizations

---

## 🔧 Detailed Implementation Instructions

### Critical Fix #1: Aria Keyword Lookups

**File:** `aria_web/server.py`
**Lines:** 496-521
**Estimated time:** 30 minutes
**Risk:** Low (pure optimization, same logic)

#### Step 1: Add module-level constants

Add this near the top of the file, after imports:

```python
# Performance optimization: Pre-compile action keywords
# Used by _extract_action_position() - converts ~20 list creations per call to 0
_ACTION_KEYWORDS = {
    'jump': (('jump', 'leap', 'hop'), '[aria:position:50:60]'),
    'dance': (('dance', 'spin', 'twirl'), '[aria:position:50:50]'),
    'wave': (('wave', 'greet', 'hello', 'hi'), '[aria:position:30:70]'),
    'look': (('look', 'see', 'watch', 'observe'), None),  # Special handling
    'sit': (('sit', 'rest', 'relax'), None),  # Special handling
    'run': (('run', 'race', 'sprint'), '[aria:position:85:70]'),
    'hide': (('hide', 'crouch', 'duck'), '[aria:position:10:75]'),
    'present': (('present', 'show', 'display'), '[aria:position:50:50]'),
    'think': (('think', 'wonder', 'ponder'), '[aria:position:25:50]'),
    'walk_left': (('walk left', 'go left', 'left'), '[aria:position:20:70]'),
    'walk_right': (('walk right', 'go right', 'right'), '[aria:position:80:70]'),
}
```

#### Step 2: Refactor _extract_action_position function

Replace lines 496-521 with:

```python
def _extract_action_position(cmd: str, world_state: Dict) -> Optional[str]:
    """Extract position from command (optimized).

    Uses pre-compiled keyword tuples to avoid creating lists on every call.
    """
    # Get table position for context-dependent positioning
    table_pos = {'x': 60, 'y': 50}  # Default
    for obj_name, obj_data in world_state.get('objects', {}).items():
        if 'table' in obj_name.lower():
            if isinstance(obj_data, dict) and 'position' in obj_data:
                table_pos = obj_data['position']
                break

    # Check for objects in command (pickup/drop context)
    for obj_name, obj_data in world_state.get('objects', {}).items():
        if obj_name.lower() in cmd:
            if any(word in cmd for word in ('pick', 'get', 'grab', 'take')):
                obj_pos = obj_data.get('position', {})
                if isinstance(obj_pos, dict) and 'x' in obj_pos and 'y' in obj_pos:
                    return f'[aria:position:{max(10, obj_pos["x"] - 10)}:{obj_pos["y"] + 10}]'

    # Action-based positioning (optimized with pre-compiled keywords)
    for action, (keywords, position) in _ACTION_KEYWORDS.items():
        if any(k in cmd for k in keywords):
            # Handle special cases
            if action == 'look' and 'table' in cmd:
                return '[aria:position:40:60]'
            elif action == 'look':
                return '[aria:position:20:40]'
            elif action == 'sit':
                return f'[aria:position:{table_pos["x"] - 5}:{table_pos["y"] + 35}]'

            # Return standard position
            if position:
                return position

    # Handle add/create commands
    if any(word in cmd for word in ('add', 'create', 'spawn')):
        return f'[aria:position:{table_pos["x"] - 15}:{table_pos["y"] + 20}]'

    # Default: context-aware positioning
    import hashlib
    pos_hash = int(hashlib.md5(cmd.encode()).hexdigest()[:4], 16)
    x = 30 + (pos_hash % 40)
    y = 50 + ((pos_hash // 40) % 30)
    return f'[aria:position:{x}:{y}]'
```

#### Step 3: Test the changes

```python
# Add test function (temporary, for verification)
def test_keyword_performance():
    """Test keyword lookup performance."""
    import time

    test_commands = [
        "jump high", "dance around", "wave hello", "look at table",
        "sit down", "run fast", "hide quickly", "think deeply"
    ] * 100  # 800 total commands

    world_state = {'objects': {'table': {'position': {'x': 60, 'y': 50}}}}

    start = time.perf_counter()
    for cmd in test_commands:
        _extract_action_position(cmd, world_state)
    elapsed = time.perf_counter() - start

    print(f"Processed {len(test_commands)} commands in {elapsed:.3f}s")
    print(f"Average: {elapsed/len(test_commands)*1000:.2f}ms per command")

# Run test
test_keyword_performance()
```

Expected output: ~1-2ms per command (vs 3-4ms before)

---

### Critical Fix #3: Batch Evaluator Indexing

**File:** `scripts/batch_evaluator.py`
**Lines:** 305-312
**Estimated time:** 20 minutes
**Risk:** Low (backward compatible)

#### Step 1: Add index to __init__

Modify the `__init__` method:

```python
class BatchEvaluator:
    def __init__(self):
        self.results: List[EvaluationResult] = []
        # Performance optimization: O(1) model lookup
        self._results_index: Dict[str, EvaluationResult] = {}
        self._results_cache: Dict[str, Dict] = {}  # Existing cache
```

#### Step 2: Update add_result to maintain index

Modify `add_result` method:

```python
def add_result(self, result: EvaluationResult):
    """Add evaluation result and update index."""
    self.results.append(result)
    # Update index for O(1) lookup
    self._results_index[result.model_id] = result
    # Update cache
    self._results_cache[result.model_id] = result.to_dict()
```

#### Step 3: Optimize compare_models

Replace lines 305-312:

```python
def compare_models(self, model_ids: List[str]) -> Dict:
    """Compare specific models side-by-side (optimized O(1) lookup)."""
    # O(1) lookup per model instead of O(n) linear search
    comparison = [
        self._results_index[model_id]
        for model_id in model_ids
        if model_id in self._results_index
    ]

    return {
        "models": [r.model_id for r in comparison],
        "comparison": [
            {
                "model_id": r.model_id,
                "model_type": r.model_type,
                "status": r.status,
                "metrics": r.metrics,
                "duration": r.duration,
                "error": r.error,
            }
            for r in comparison
        ]
    }
```

#### Step 4: Test the changes

```python
# Add performance test
def test_compare_performance():
    """Test model comparison performance."""
    import time
    from dataclasses import dataclass

    evaluator = BatchEvaluator()

    # Add 1000 mock results
    for i in range(1000):
        result = EvaluationResult(
            model_id=f"model_{i}",
            model_type="lora",
            status="succeeded",
            metrics={"accuracy": 0.85},
            duration=10.0,
            error=None
        )
        evaluator.add_result(result)

    # Compare 100 models
    model_ids = [f"model_{i}" for i in range(0, 1000, 10)]

    start = time.perf_counter()
    for _ in range(100):  # 100 iterations
        evaluator.compare_models(model_ids)
    elapsed = time.perf_counter() - start

    print(f"100 comparisons in {elapsed:.3f}s")
    print(f"Average: {elapsed/100*1000:.2f}ms per comparison")
```

Expected: <1ms per comparison (vs 10-50ms before for large result sets)

---

### Critical Fix #6: Remove Redundant Iteration

**File:** `scripts/batch_evaluator.py`
**Lines:** 287
**Estimated time:** 5 minutes
**Risk:** None (just removes duplication)

#### Step 1: Locate the redundant line

Find line 287 in `aggregate_results()`:

```python
# Line 287 - REMOVE THIS LINE
failed = [r for r in self.results if r.status != "succeeded"]
```

#### Step 2: Verify the list is already built

Check lines 230-236 - this is where `failed` is correctly built:

```python
# Lines 230-236 - This is correct, keep this
for r in self.results:
    total_duration += r.duration
    if r.status == "succeeded":
        succeeded.append(r)
    else:
        failed.append(r)
```

#### Step 3: Remove the redundant line

Simply delete line 287. The `failed` list is already correct.

#### Step 4: Update uses of failed list

If line 287 is after other code that uses `failed`, ensure the first definition (lines 230-236) includes all necessary fields.

---

### High-Priority Fix #2: Batch Embedding API

**File:** `shared/chat_memory.py`
**Lines:** 151-175
**Estimated time:** 1 hour
**Risk:** Medium (requires testing)

#### Step 1: Add batch storage function

Add this new function before `store_embedding`:

```python
def store_embeddings_batch(embeddings: List[Tuple[str, Sequence[float], str]]) -> int:
    """Store multiple embeddings in a single transaction (bulk insert).

    Args:
        embeddings: List of (message_id, embedding, model) tuples

    Returns:
        Number of embeddings successfully stored

    Performance: 5-10x faster than individual inserts due to:
    - Single connection/transaction
    - Bulk executemany() operation
    - Reduced network round-trips
    """
    if not embeddings:
        return 0

    conn = _get_conn()
    if not conn:
        return 0

    try:
        cursor = conn.cursor()

        # Prepare batch values
        values = []
        for message_id, embedding, model in embeddings:
            if not message_id or not embedding:
                continue
            blob = _serialize_f32(embedding)
            values.append((
                message_id,
                model or "unknown-model",
                len(embedding),
                blob
            ))

        if not values:
            return 0

        # Bulk insert - single transaction
        cursor.executemany(
            """INSERT INTO dbo.ChatMessageEmbeddings
               (MessageId, EmbeddingModel, EmbeddingDim, EmbeddingVector)
               VALUES (?,?,?,?)""",
            values
        )
        conn.commit()
        return len(values)

    except Exception as e:
        print(f"Batch embedding storage failed: {e}")
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass
```

#### Step 2: Update single-insert function

Modify `store_embedding` to use batch API:

```python
def store_embedding(message_id: Optional[str], embedding: Sequence[float], model: str) -> bool:
    """Store single embedding (backward compatible wrapper).

    For multiple embeddings, use store_embeddings_batch() for better performance.
    """
    if not message_id or not embedding:
        return False

    return store_embeddings_batch([(message_id, embedding, model)]) == 1
```

#### Step 3: Update call sites (if any)

Search for places that store multiple embeddings:

```bash
grep -r "store_embedding" --include="*.py" | grep "for\|loop"
```

If found, update to use batch API:

```python
# Before (slow)
for message_id, embedding in embeddings_to_store:
    store_embedding(message_id, embedding, model)

# After (fast)
batch = [(msg_id, emb, model) for msg_id, emb in embeddings_to_store]
store_embeddings_batch(batch)
```

---

### High-Priority Fix #11: Cache Venv Info

**File:** `function_app.py`
**Lines:** 1091-1100
**Estimated time:** 30 minutes
**Risk:** Low (caching with TTL)

#### Step 1: Add caching helper

Add this near the top of function_app.py, after imports:

```python
import time
from functools import lru_cache

# Cache TTL: 5 minutes (300 seconds)
_VENV_INFO_CACHE_TTL = 300
```

#### Step 2: Create cached venv info function

Add this before the `ai_status` function:

```python
@lru_cache(maxsize=1)
def _get_venv_info_cached(venv_path: str, cache_slot: int) -> Dict:
    """Get venv info with TTL-based caching.

    Args:
        venv_path: Path to venv python executable
        cache_slot: Time-based cache key (changes every TTL seconds)

    Returns:
        Venv info dict

    Performance: Avoids expensive subprocess calls when cached.
    Cache invalidates every 5 minutes via cache_slot parameter.
    """
    venv_python = Path(venv_path)
    venv_info = {
        "path": str(venv_python),
        "exists": venv_python.exists(),
        "packages": {},
        "error": None
    }

    if not venv_info["exists"]:
        return venv_info

    try:
        code = (
            "import json, importlib.util, importlib.metadata as md;"
            "mods=['torch','transformers','peft'];"
            "avail={m:(importlib.util.find_spec(m) is not None) for m in mods};"
            "vers={};"
            "\nfor m in mods:\n\t"
            "\n\ttry:\n\t\tvers[m]=md.version(m)\n\texcept Exception:\n\t\tvers[m]=None;"
            "print(json.dumps({'available':avail,'versions':vers}))"
        )
        proc = subprocess.run(
            [str(venv_python), "-c", code],
            capture_output=True,
            text=True,
            timeout=12
        )

        if proc.returncode == 0:
            data = json.loads(proc.stdout.strip() or "{}")
            venv_info["packages"] = data
        else:
            venv_info["error"] = proc.stderr.strip() or f"exit {proc.returncode}"

    except Exception as e:
        venv_info["error"] = str(e)

    return venv_info
```

#### Step 3: Update ai_status to use cache

Replace lines 1075-1100 in `ai_status`:

```python
# Venv info (cached for 5 minutes)
repo_root = Path(__file__).resolve().parent
venv_python = repo_root / "venv" / "Scripts" / "python.exe"

# Calculate cache slot (changes every 5 minutes)
current_cache_slot = int(time.time() / _VENV_INFO_CACHE_TTL)
venv_info = _get_venv_info_cached(str(venv_python), current_cache_slot)
```

#### Step 4: Test caching behavior

```python
# Test cache performance
import time

def test_venv_cache():
    """Test venv info caching."""
    # First call (cache miss)
    start = time.perf_counter()
    info1 = _get_venv_info_cached("/path/to/venv/python.exe", 1)
    elapsed1 = time.perf_counter() - start

    # Second call (cache hit)
    start = time.perf_counter()
    info2 = _get_venv_info_cached("/path/to/venv/python.exe", 1)
    elapsed2 = time.perf_counter() - start

    print(f"First call (miss): {elapsed1:.3f}s")
    print(f"Second call (hit): {elapsed2:.3f}s")
    print(f"Speedup: {elapsed1/elapsed2:.0f}x")

test_venv_cache()
```

Expected: First call ~0.5-2s, second call <0.001s (1000x faster)

---

## 🧪 Testing Strategy

### Unit Tests

Create `tests/test_performance_optimizations.py`:

```python
import pytest
import time
from scripts.batch_evaluator import BatchEvaluator, EvaluationResult
from aria_web.server import _extract_action_position
from shared.chat_memory import store_embeddings_batch

class TestPerformanceOptimizations:
    """Test performance improvements."""

    def test_batch_evaluator_indexing(self):
        """Test O(1) model lookup."""
        evaluator = BatchEvaluator()

        # Add 100 results
        for i in range(100):
            result = EvaluationResult(
                model_id=f"model_{i}",
                model_type="test",
                status="succeeded",
                metrics={"acc": 0.9},
                duration=1.0
            )
            evaluator.add_result(result)

        # Test lookup speed
        start = time.perf_counter()
        result = evaluator.compare_models([f"model_{i}" for i in range(50)])
        elapsed = time.perf_counter() - start

        assert len(result["models"]) == 50
        assert elapsed < 0.01  # Should be < 10ms

    def test_keyword_lookup_optimization(self):
        """Test Aria keyword lookup performance."""
        world_state = {"objects": {}}

        commands = ["jump", "dance", "wave"] * 100

        start = time.perf_counter()
        for cmd in commands:
            pos = _extract_action_position(cmd, world_state)
            assert pos is not None
        elapsed = time.perf_counter() - start

        # Should process 300 commands in < 100ms
        assert elapsed < 0.1

    def test_batch_embedding_storage(self):
        """Test batch embedding API."""
        embeddings = [
            (f"msg_{i}", [0.1] * 128, "test-model")
            for i in range(10)
        ]

        start = time.perf_counter()
        count = store_embeddings_batch(embeddings)
        elapsed = time.perf_counter() - start

        assert count == 10
        # Batch should be faster than 10 * single-insert time
        assert elapsed < 1.0  # Reasonable upper bound
```

### Integration Tests

Run existing tests to ensure no regressions:

```bash
# Run full test suite
python scripts/test_runner.py --all

# Run specific performance tests
pytest tests/test_performance_optimizations.py -v

# Run with profiling
python -m cProfile -s cumulative scripts/batch_evaluator.py > profile.txt
```

---

## 📊 Benchmarking

Create `scripts/benchmark_optimizations.py`:

```python
#!/usr/bin/env python3
"""Benchmark performance optimizations."""

import time
import statistics
from typing import Callable, List

def benchmark(
    name: str,
    func: Callable,
    *args,
    iterations: int = 100,
    warmup: int = 10
) -> float:
    """Benchmark a function."""
    # Warm-up
    for _ in range(warmup):
        func(*args)

    # Measure
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    mean_time = statistics.mean(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0

    print(f"{name}:")
    print(f"  Mean: {mean_time*1000:.3f}ms")
    print(f"  StdDev: {std_dev*1000:.3f}ms")
    print(f"  Min: {min(times)*1000:.3f}ms")
    print(f"  Max: {max(times)*1000:.3f}ms")

    return mean_time

if __name__ == "__main__":
    print("Performance Optimization Benchmarks")
    print("=" * 60)

    # Add benchmarks for each optimization
    # ... (use examples from above)
```

---

## 🔍 Validation Checklist

Before merging each optimization:

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Benchmark shows improvement (>10% faster)
- [ ] No regressions in existing functionality
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Memory usage acceptable
- [ ] Error handling preserved

---

## 📝 Rollback Plan

If an optimization causes issues:

1. **Immediate rollback**: `git revert <commit>`
2. **Investigate root cause**: Check logs, profiling data
3. **Fix and re-test**: Address issue in separate branch
4. **Re-deploy**: With additional tests

---

## 🎓 Learning Resources

- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Python Profiling](https://docs.python.org/3/library/profile.html)
- [High Performance Python Book](https://www.oreilly.com/library/view/high-performance-python/9781492055013/)

---

**Next Steps:**
1. Choose which fixes to implement first
2. Create feature branch: `git checkout -b perf/critical-fixes`
3. Implement fixes one at a time
4. Test thoroughly
5. Submit PR with benchmarks
