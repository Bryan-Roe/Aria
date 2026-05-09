# Future Performance Optimization Opportunities

## Date: 2026-02-17

This document lists potential performance optimizations identified but not yet implemented, ordered by estimated impact.

---

## 🔮 Deferred Optimizations (Lower Priority)

### 1. function_app.py - Image URL Caching
**Location**: `function_app.py:1420` - Vision inference endpoint

**Issue**: Image fetched via HTTP on every request, even for repeated URLs.

**Current Code**:
```python
response = requests.get(image_url, timeout=10)
response.raise_for_status()
img = Image.open(io.BytesIO(response.content))
result = vi.predict(img)
```

**Suggested Improvement**:
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=50)
def _fetch_image_cached(url: str, cache_buster: str = None):
    """Fetch image with LRU cache. cache_buster allows invalidation."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.content

# Usage
image_bytes = _fetch_image_cached(image_url)
img = Image.open(io.BytesIO(image_bytes))
```

**Estimated Impact**:
- Low frequency endpoint (vision inference)
- Significant speedup (eliminates network I/O) for repeated URLs
- **Priority**: Low (implement if vision endpoint becomes high-traffic)

---

### 2. shared/chat_memory.py - NumPy Vectorized Cosine Similarity
**Location**: `shared/chat_memory.py:240-251` - `fetch_similar_messages()`

**Issue**: Python loop computing cosine similarity for ~500 embeddings per query.

**Current Code**:
```python
def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

# Loop over all embeddings
for r in rows:
    emb = _deserialize_f32(r.EmbeddingVector, dim)
    sim = _cosine(query_embedding, emb)
```

**Suggested Improvement**:
```python
try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

def _cosine_batch(query: Sequence[float], embeddings: List[Sequence[float]]) -> List[float]:
    """Vectorized cosine similarity using NumPy if available."""
    if _HAS_NUMPY and len(embeddings) > 10:
        query_arr = np.array(query, dtype=np.float32)
        emb_matrix = np.array(embeddings, dtype=np.float32)

        # Normalize
        query_norm = query_arr / np.linalg.norm(query_arr)
        emb_norms = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)

        # Batch dot product
        similarities = np.dot(emb_norms, query_norm)
        return similarities.tolist()

    # Fallback to Python loop
    return [_cosine(query, emb) for emb in embeddings]
```

**Estimated Impact**:
- **Speedup**: 8-10x for 500 embeddings with 256 dimensions
- **Memory**: ~2MB additional for NumPy arrays (acceptable)
- **Priority**: Medium (implement when embedding search becomes bottleneck)
- **Note**: Already documented in `docs/PERFORMANCE_IMPROVEMENTS.md`

---

### 3. function_app.py - Status Endpoint File Existence Caching
**Location**: `function_app.py` - `/api/ai/status` endpoint

**Issue**: Checks many file paths on every status request.

**Current Pattern** (hypothetical):
```python
status = {
    "adapter_present": os.path.exists(adapter_path),
    "config_present": os.path.exists(config_path),
    # ... many more checks
}
```

**Suggested Improvement**:
```python
from functools import lru_cache
import time

_file_cache = {}
_CACHE_TTL = 10  # seconds

def _exists_cached(path: str) -> bool:
    """Check file existence with 10s TTL cache."""
    now = time.time()
    if path in _file_cache:
        cached_val, cached_time = _file_cache[path]
        if now - cached_time < _CACHE_TTL:
            return cached_val

    exists = os.path.exists(path)
    _file_cache[path] = (exists, now)
    return exists
```

**Estimated Impact**:
- **Latency reduction**: ~5-10ms per status request
- **Frequency**: Status endpoint called periodically by monitoring
- **Priority**: Low (acceptable latency for monitoring endpoint)

---

### 4. Batch Processing Optimization Opportunities

#### 4.1 ai-projects/quantum-ml/src/quantum_classifier.py - Batch Processing
**Location**: `quantum_classifier.py` - `forward()` method

**Issue**: Sequential processing of batch items in quantum circuit execution.

**Note**: This is inherently limited by quantum simulation/hardware characteristics. Async I/O could help for cloud backends, but local simulation is CPU-bound.

**Priority**: Low (quantum operations are inherently sequential)

---

## 🔍 Profiling Recommendations

To identify the next set of optimizations, consider:

### 1. Add Performance Monitoring to Key Endpoints
```python
import time
import functools

def timed(func):
    """Decorator to measure and log function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        if duration > 0.1:  # Log slow operations
            print(f"⚠️ {func.__name__} took {duration:.3f}s")
        return result
    return wrapper
```

Apply to:
- All Azure Functions endpoints
- `generate_tags_fallback()` in aria_web/server.py
- `fetch_similar_messages()` in shared/chat_memory.py
- Training pipeline orchestrators

### 2. Enable SQL Query Logging
```python
# In shared/sql_engine.py or wherever SQL is executed
import time
import logging

def execute_with_timing(cursor, query, *args):
    start = time.perf_counter()
    cursor.execute(query, *args)
    duration = time.perf_counter() - start
    if duration > 0.05:
        logging.warning(f"Slow query ({duration:.3f}s): {query[:100]}")
    return cursor
```

### 3. Profile Hot Paths with cProfile
```bash
# For server endpoints
python -m cProfile -s cumulative aria_web/server.py > profile.txt

# For scripts
python -m cProfile -s cumulative scripts/autotrain.py --dry-run > profile.txt
```

Look for functions with:
- High `cumtime` (cumulative time)
- High `ncalls` (call count)
- High `percall` (time per call)

---

## 📊 Performance Monitoring Dashboard

Consider adding `/api/performance/metrics` endpoint:

```python
@app.route('/api/performance/metrics')
def performance_metrics():
    return {
        "connection_pool": {
            "size": len(_connection_pool),
            "max_size": _MAX_POOL_SIZE,
            "utilization": len(_connection_pool) / _MAX_POOL_SIZE
        },
        "keyword_cache_hits": _keyword_cache_hits,  # If implemented
        "regex_pattern_count": len([k for k in globals() if k.startswith('_RE_')]),
        "recent_slow_operations": get_slow_operations_log()
    }
```

---

## 🎯 Optimization Prioritization Matrix

| Optimization | Impact | Effort | Priority |
|--------------|--------|--------|----------|
| Image URL caching | High (if high-traffic) | Low | Conditional |
| NumPy cosine similarity | Medium | Medium | Medium |
| File existence caching | Low | Low | Low |
| Quantum batch processing | Low | High | Low |
| Performance monitoring | High (visibility) | Medium | High |

---

## ✅ Already Optimized (Reference)

These were fixed in the 2026-02-17 optimization pass:

1. ✅ aria_web/server.py keyword sets (1.09x speedup)
2. ✅ shared/chat_memory.py connection pooling (50-100x for batch)
3. ✅ aria_web/server.py regex compilation (2-5x speedup)
4. ✅ scripts/analyze_learning_progress.py generators (memory-efficient)
5. ✅ cooking-ai/src/providers/local.py tag filtering (O(n²) → O(n))

See `docs/PERFORMANCE_OPTIMIZATION_SUMMARY_2026-02-17.md` for details.

---

## 📝 Next Steps

1. **Implement performance monitoring** (highest priority for visibility)
2. **Profile high-traffic endpoints** to identify real bottlenecks
3. **Implement NumPy cosine similarity** if embedding search becomes slow
4. **Add image caching** if vision endpoint sees high traffic
5. **Monitor connection pool saturation** via `/api/ai/status`

The optimizations already implemented address the most impactful issues identified. Further optimization should be data-driven based on production metrics and profiling.
