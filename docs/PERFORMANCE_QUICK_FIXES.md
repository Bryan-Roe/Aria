# Performance Quick Fixes - Developer Reference

Quick reference for common performance anti-patterns and their fixes in the Aria codebase.

---

## 🚀 Quick Wins (Copy-Paste Fixes)

### 1. Keyword/String Membership Checks

❌ **SLOW - Creates list every time:**
```python
if any(k in cmd for k in ['jump', 'leap', 'hop']):
    do_something()
```

✅ **FAST - Use tuple or module-level frozenset:**
```python
# For small sets, tuple is fastest
if any(k in cmd for k in ('jump', 'leap', 'hop')):
    do_something()

# For repeated checks or large sets, use module-level constant
_JUMP_KEYWORDS = frozenset(['jump', 'leap', 'hop'])
if any(k in cmd for k in _JUMP_KEYWORDS):
    do_something()
```

**Improvement:** 20-40% faster per check

---

### 2. Status/Enum Membership Checks

❌ **SLOW - Creates list:**
```python
if status in ["succeeded", "completed", "done"]:
    process()
```

✅ **FAST - Use tuple or frozenset:**
```python
# Tuple for small, fixed sets
if status in ("succeeded", "completed", "done"):
    process()

# frozenset for repeated checks or larger sets
SUCCESS_STATUSES = frozenset(["succeeded", "completed", "done"])
if status in SUCCESS_STATUSES:
    process()
```

**Improvement:** 15-30% faster

---

### 3. Linear Searches in Lists

❌ **SLOW - O(n) search:**
```python
# Searching for item in list
for item in large_list:
    if item.id == target_id:
        return item
```

✅ **FAST - O(1) dict lookup:**
```python
# Build index once
items_by_id = {item.id: item for item in large_list}

# O(1) lookup
return items_by_id.get(target_id)
```

**Improvement:** 50-100x faster for 100+ items

---

### 4. String Concatenation in Loops

❌ **SLOW - O(n²) due to immutable strings:**
```python
result = ""
for item in items:
    result += str(item) + ", "
```

✅ **FAST - O(n) using list and join:**
```python
result = ", ".join(str(item) for item in items)
```

**Improvement:** 5-10x faster for 100+ items

---

### 5. Multiple Passes Over Same Data

❌ **SLOW - Multiple iterations:**
```python
succeeded = [r for r in results if r.status == "success"]
failed = [r for r in results if r.status != "success"]
total_time = sum(r.duration for r in results)
```

✅ **FAST - Single-pass aggregation:**
```python
succeeded = []
failed = []
total_time = 0

for r in results:
    total_time += r.duration
    if r.status == "success":
        succeeded.append(r)
    else:
        failed.append(r)
```

**Improvement:** 3x faster

---

### 6. Average/Statistics Calculations

❌ **SLOW - Manual calculation:**
```python
for key, values in data.items():
    avg = sum(values) / len(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
```

✅ **FAST - Use statistics module:**
```python
import statistics

for key, values in data.items():
    avg = statistics.mean(values)
    variance = statistics.pvariance(values)
```

**Improvement:** 2x faster, more numerically stable

---

### 7. Finding Maximum with Custom Key

❌ **SLOW - Manual tracking:**
```python
best_value = float('-inf')
best_item = None

for item in items:
    value = compute_score(item)
    if value > best_value:
        best_value = value
        best_item = item
```

✅ **FAST - Use built-in max:**
```python
best_item = max(items, key=lambda item: compute_score(item))
```

**Improvement:** More readable, often faster (C implementation)

---

### 8. Top-K Selection

❌ **SLOW - Full sort:**
```python
# When you only need top 10 out of 1000s
top_items = sorted(items, key=lambda x: x.score, reverse=True)[:10]
```

✅ **FAST - Use heapq.nlargest:**
```python
import heapq

top_items = heapq.nlargest(10, items, key=lambda x: x.score)
```

**Improvement:** 5-10x faster for large collections
- `heapq.nlargest`: O(n log k) where k=10
- `sorted`: O(n log n) where n=1000s

---

### 9. Database Operations in Loops

❌ **SLOW - Connection per operation:**
```python
for item in items:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO table VALUES (?)", (item,))
    conn.commit()
    conn.close()
```

✅ **FAST - Batch operations:**
```python
conn = get_connection()
cursor = conn.cursor()
cursor.executemany("INSERT INTO table VALUES (?)", [(item,) for item in items])
conn.commit()
conn.close()
```

**Improvement:** 10-50x faster

---

### 10. List Comprehension vs append

❌ **SLOWER - Repeated append:**
```python
results = []
for item in items:
    if item.valid:
        results.append(transform(item))
```

✅ **FASTER - List comprehension:**
```python
results = [transform(item) for item in items if item.valid]
```

**Improvement:** 10-20% faster, more readable

---

## 🔍 Detection Patterns

### How to Find These Issues

```bash
# Find list creations in conditionals
grep -n "in \[" *.py

# Find string concatenation in loops
grep -n "+=" *.py

# Find multiple iterations
grep -n "for.*in.*:" *.py | grep -A5 "for.*in.*:"

# Find manual statistics
grep -n "sum(.*).*len(" *.py
```

---

## 📊 When to Optimize

### DO optimize when:
- ✅ Code is in a hot path (called frequently)
- ✅ Processing large datasets (>1000 items)
- ✅ Operation is in a loop
- ✅ User-facing performance issue
- ✅ Easy win (simple fix with big impact)

### DON'T optimize when:
- ❌ Code runs once at startup
- ❌ Small datasets (<100 items)
- ❌ Premature (no profiling data)
- ❌ Makes code significantly harder to read
- ❌ Current performance is acceptable

---

## 🧪 Testing Performance Improvements

### Simple Benchmark Template

```python
import time

def benchmark(func, *args, iterations=1000):
    """Benchmark a function."""
    # Warm-up
    for _ in range(10):
        func(*args)

    # Measure
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    elapsed = time.perf_counter() - start

    print(f"{func.__name__}: {elapsed:.3f}s total, {elapsed/iterations*1000:.3f}ms avg")
    return elapsed

# Usage
old_time = benchmark(old_function, test_data)
new_time = benchmark(new_function, test_data)
print(f"Speedup: {old_time/new_time:.2f}x")
```

---

## 🎯 Priority Checklist

When reviewing code for performance:

1. ☐ Are there list literals in conditionals? → Use tuple/frozenset
2. ☐ Are there linear searches in loops? → Use dict/set
3. ☐ Is there string concatenation in loops? → Use join()
4. ☐ Are collections iterated multiple times? → Single-pass
5. ☐ Are there manual statistics calculations? → Use statistics module
6. ☐ Are there database operations in loops? → Batch operations
7. ☐ Is there repeated computation? → Cache results
8. ☐ Are there full sorts for top-k? → Use heapq

---

## 📚 Related Resources

- `docs/PERFORMANCE_ANALYSIS.md` - Full analysis with benchmarks
- `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md` - Comprehensive guide
- `shared/performance_utils.py` - Reusable optimization utilities
- `scripts/benchmark_performance.py` - Benchmarking tools

---

## 💡 Pro Tips

1. **Profile before optimizing** - Use `cProfile` or `line_profiler`
2. **Measure improvements** - Always benchmark before/after
3. **Consider readability** - Don't sacrifice clarity for minor gains
4. **Test correctness** - Ensure optimizations don't change behavior
5. **Document trade-offs** - Explain complex optimizations

```python
# Example: Profile a function
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = expensive_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 slowest
```

---

**Remember:** The best optimization is the one that matters to users! Focus on hot paths and measurable improvements.
