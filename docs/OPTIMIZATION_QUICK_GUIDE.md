# Optimization Quick Reference Guide

**Quick guide for implementing code efficiency improvements identified in CODE_INEFFICIENCY_ANALYSIS_2026-02-17.md**

## Quick Wins (< 30 minutes each)

### 1. Generator-Based Counting
**File:** `dashboard/serve.py` lines 700, 761, 766

```python
# BEFORE
count = len(list(directory.glob('*.json')))
count = len([d for d in dir.iterdir() if d.is_dir()])

# AFTER
count = sum(1 for _ in directory.glob('*.json'))
count = sum(1 for d in dir.iterdir() if d.is_dir())
```

### 2. Gradient Norm Optimization
**File:** `ai-projects/quantum-ml/web_app.py` line 440

```python
# BEFORE
avg_gradient = np.mean([np.linalg.norm(g) for g in epoch_gradients])

# AFTER
avg_gradient = np.mean(np.linalg.norm(g) for g in epoch_gradients)
```

### 3. Single-Pass Statistics
**File:** `ai-projects/quantum-ml/web_app.py` lines 952-958

```python
# BEFORE (4 iterations)
active = sum(1 for s in sessions.values() if s.status == "training")
completed = sum(1 for s in sessions.values() if s.status == "completed")
total_epochs = sum(s.current_epoch for s in sessions.values())
avg_acc = np.mean([s.best_val_acc for s in sessions.values() if s.best_val_acc > 0])

# AFTER (1 iteration)
active = completed = total_epochs = 0
accuracies = []
for s in sessions.values():
    if s.status == "training": active += 1
    elif s.status == "completed": completed += 1
    total_epochs += s.current_epoch
    if s.best_val_acc > 0: accuracies.append(s.best_val_acc)
avg_acc = np.mean(accuracies) if accuracies else 0.0
```

## Medium Complexity (1-2 hours)

### 4. File Caching with TTL
**File:** `dashboard/serve.py` (add at module level)

```python
import time
from pathlib import Path
from typing import Dict, Tuple, Any

_file_cache: Dict[str, Tuple[Any, float]] = {}
_FILE_CACHE_TTL = 5  # seconds

def _load_json_cached(filepath: Path) -> dict:
    """Load JSON file with TTL-based caching"""
    import json
    now = time.time()
    cache_key = str(filepath)

    # Check cache
    if cache_key in _file_cache:
        cached_data, cached_time = _file_cache[cache_key]
        if now - cached_time < _FILE_CACHE_TTL:
            return cached_data

    # Read file
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        _file_cache[cache_key] = (data, now)
        return data
    except Exception:
        # Use stale cache if available
        if cache_key in _file_cache:
            return _file_cache[cache_key][0]
        raise

# Replace all instances of:
#   with open(status_file, 'r') as f:
#       data = json.load(f)
# With:
#   data = _load_json_cached(status_file)
```

### 5. Keyword Matching with Frozensets
**File:** `ai-projects/chat-cli/src/agi_provider.py` lines 343-372

```python
# Add at module level (top of file)
_COMPLEXITY_MODERATE = frozenset(["explain", "compare", "analyze", "how", "why"])
_COMPLEXITY_COMPLEX = frozenset(["step by step", "detailed", "comprehensive"])
_INTENT_MOVEMENT = frozenset(["move", "walk", "go", "jump", "dance", "wave"])
_INTENT_CODING = frozenset(["code", "program", "function", "debug"])
_INTENT_EXPLANATION = frozenset(["explain", "what is", "how does"])
_INTENT_CREATION = frozenset(["create", "generate", "make", "build"])

_DOMAIN_KEYWORDS = {
    "quantum": frozenset(["quantum", "qubit", "entanglement", "superposition"]),
    "ai": frozenset(["ai", "machine learning", "neural", "model", "training"]),
    "aria": frozenset(["aria", "move", "animation", "character"]),
    "technical": frozenset(["code", "program", "api", "function", "database"]),
}

# In _analyze_query function, replace multiple any() calls with:
def _analyze_query_optimized(query: str) -> dict:
    query_lower = query.lower()
    words = query_lower.split()
    word_set = set(words)

    # Complexity - O(1) set intersection instead of O(n) any()
    complexity = "simple"
    if word_set & _COMPLEXITY_MODERATE:
        complexity = "moderate"
    elif word_set & _COMPLEXITY_COMPLEX:
        complexity = "complex"
    elif len(words) > 20:
        complexity = "complex"

    # Intent - O(1) set intersection
    intent = "general"
    if word_set & _INTENT_MOVEMENT:
        intent = "movement"
    elif word_set & _INTENT_CODING:
        intent = "coding"
    elif word_set & _INTENT_EXPLANATION:
        intent = "explanation"
    elif word_set & _INTENT_CREATION:
        intent = "creation"
    elif "?" in query:
        intent = "question"

    # Domain - O(domains) with O(1) intersection per domain
    domain = "general"
    for dom, keywords in _DOMAIN_KEYWORDS.items():
        if word_set & keywords:
            domain = dom
            break

    return {
        "query": query,
        "complexity": complexity,
        "intent": intent,
        "domain": domain,
        "word_count": len(words),
    }
```

### 6. Consistent Frozenset Usage
**File:** `aria_web/server.py` lines 554-557

```python
# Add to existing frozenset section (around lines 42-74)
MOVE_LEFT_KEYWORDS = frozenset(['walk left', 'go left', 'left', 'move left'])
MOVE_RIGHT_KEYWORDS = frozenset(['walk right', 'go right', 'right', 'move right'])

# Replace inline any() calls:
# BEFORE
elif any(k in cmd for k in ['walk left', 'go left', 'left']):
    return '[aria:position:20:70]'

# AFTER
elif _contains_any_keyword(cmd, MOVE_LEFT_KEYWORDS):
    return '[aria:position:20:70]'
```

### 7. Deque-Based Rate Limiting
**File:** `dashboard/serve.py` lines 39-40

```python
# Add at module level
from collections import deque, defaultdict

_request_timestamps = defaultdict(deque)
_MAX_REQUESTS = 100
_WINDOW_SECONDS = 60

def check_rate_limit(client_ip: str) -> bool:
    """Check if client is within rate limit using deque"""
    now = time.time()
    timestamps = _request_timestamps[client_ip]

    # Remove expired timestamps from left (oldest)
    while timestamps and now - timestamps[0] > _WINDOW_SECONDS:
        timestamps.popleft()

    if len(timestamps) >= _MAX_REQUESTS:
        return False  # Rate limited

    timestamps.append(now)
    return True

# Replace list filtering with deque-based check
```

## Complex Optimization (2-4 hours)

### 8. Quantum Gradient Optimization
**File:** `ai-projects/quantum-ml/web_app.py` lines 217-246

```python
def compute_gradient_optimized(circuit, X, y, weights):
    """Optimized gradient using PennyLane's automatic differentiation"""
    try:
        # Use PennyLane's qml.grad() for 10-100x speedup
        import pennylane as qml

        # Create loss function for autograd
        def loss_fn(w):
            return compute_loss(circuit, X, y, w)

        # Compute gradient using automatic differentiation
        grad_fn = qml.grad(loss_fn)
        grad = grad_fn(weights)

        return grad

    except Exception as e:
        # Fallback to manual parameter-shift if autograd fails
        import warnings
        warnings.warn(f"Autograd failed ({e}), using manual gradient")
        return compute_gradient(circuit, X, y, weights, use_parameter_shift=True)

# In training loop, replace:
#   grad = compute_gradient(circuit, X_batch, y_batch, weights)
# With:
#   grad = compute_gradient_optimized(circuit, X_batch, y_batch, weights)
```

## Testing Checklist

For each optimization:

- [ ] **Functionality:** Verify output matches original behavior
- [ ] **Performance:** Benchmark with realistic data (use `time.perf_counter()`)
- [ ] **Edge cases:** Test with empty inputs, large inputs, None values
- [ ] **Integration:** Run existing test suite to catch regressions
- [ ] **Memory:** Check memory usage doesn't increase significantly

## Performance Testing Template

```python
import time
import numpy as np

def benchmark_optimization(old_func, new_func, *args, iterations=100):
    """Compare performance of old vs new implementation"""

    # Warmup
    old_func(*args)
    new_func(*args)

    # Benchmark old
    start = time.perf_counter()
    for _ in range(iterations):
        result_old = old_func(*args)
    time_old = time.perf_counter() - start

    # Benchmark new
    start = time.perf_counter()
    for _ in range(iterations):
        result_new = new_func(*args)
    time_new = time.perf_counter() - start

    # Verify results match
    if isinstance(result_old, np.ndarray):
        np.testing.assert_allclose(result_old, result_new, rtol=1e-5)
    else:
        assert result_old == result_new, "Results don't match!"

    speedup = time_old / time_new
    print(f"Old: {time_old*1000:.2f}ms")
    print(f"New: {time_new*1000:.2f}ms")
    print(f"Speedup: {speedup:.1f}x")

    return speedup
```

## Expected Performance Gains

| Optimization | File | Speedup | Risk |
| -------------- | ------ | --------- | ------ |
| Quantum gradient | web_app.py | 10-100x | Low (has fallback) |
| File caching | serve.py | 5-10x | Low (5s TTL) |
| Keyword frozensets | agi_provider.py | 3-30x | Very low |
| Position keywords | server.py | 2-5x | Very low |
| Single-pass stats | web_app.py | 4x | Very low |
| Generator counting | serve.py | 5-20% | Very low |
| Deque rate limiting | serve.py | 2-5x | Low |
| Gradient norm | web_app.py | <5% | Very low |

## Implementation Order

1. Start with "Quick Wins" - low risk, immediate benefit
2. Add file caching (dashboard gets 5-10x faster)
3. Implement keyword optimizations (query processing 3-30x faster)
4. Optimize quantum gradients last (highest complexity, highest reward)

## Related Files

- Full analysis: `docs/CODE_INEFFICIENCY_ANALYSIS_2026-02-17.md`
- Previous optimizations: `docs/PERFORMANCE_IMPROVEMENTS.md`
- Test patterns: `tests/test_performance_optimizations.py`
