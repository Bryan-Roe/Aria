# Performance Optimization Guide

This document describes performance optimizations implemented in the Aria codebase and provides best practices for writing efficient Python code.

## Recent Optimizations

### 1. Memory-Efficient File Reading

**Problem**: Loading entire log files into memory using `readlines()` can cause excessive memory usage for large files.

**Solution**: Use `collections.deque` with `maxlen` parameter for tail-like operations:

```python
# ❌ BAD: Loads entire file into memory
with open(log_file, 'r') as f:
    all_lines = f.readlines()
    return all_lines[-20:]  # Only need last 20 lines

# ✅ GOOD: Memory-efficient with deque
from collections import deque
with open(log_file, 'r') as f:
    return list(deque(f, maxlen=20))  # Only keeps last 20 lines
```

**Files Optimized**:
- `scripts/monitor_autonomous_training.py` - Line 61-71
- `dashboard/serve.py` - Line 525-531

**Benefits**:
- Reduces memory usage from O(n) to O(k) where k is the tail size
- Faster for large log files (GB-sized files)
- No change to external API

### 2. Iterator-Based Data Processing

**Best Practice**: Use generators and iterators instead of loading all data into memory.

```python
# ❌ BAD: Loads all records into memory
def load_all_records(file_path):
    records = []
    with open(file_path) as f:
        for line in f:
            records.append(json.loads(line))
    return records

# ✅ GOOD: Yields records one at a time
def load_records(file_path):
    with open(file_path) as f:
        for line in f:
            yield json.loads(line)
```

**Already Implemented**:
- `AI/microsoft_phi-silica-3.6_v1/scripts/prepare_dataset.py` - Uses generators throughout
- All JSONL reading functions use `yield` pattern

### 3. Database Connection Pooling

**Implementation**: `shared/sql_engine.py`

**Features**:
- Connection pooling with configurable size (`QAI_SQL_POOL_SIZE`)
- Pre-ping to evict dead connections
- Pool recycling every 30 minutes
- Slow query tracking
- Health monitoring via `/api/ai/status`

**Configuration**:
```python
# Set pool size via environment variable
export QAI_SQL_POOL_SIZE=20  # Default: 10

# Monitor pool saturation
curl http://localhost:7071/api/ai/status | jq '.sql'
# Warns when ≥80% saturated
```

### 4. Smart File Reading for Large Files

**Implementation**: `dashboard/app.py` - `_tail_lines()` function

**Strategy**:
- Small files (< 64KB): Read entire file
- Large files: Read backwards in blocks until enough lines found

```python
def _tail_lines(path: Path, max_lines: int) -> List[str]:
    size = path.stat().st_size
    if size <= 65536:  # Small file heuristic
        with path.open("r") as f:
            lines = f.readlines()
            return lines[-max_lines:]

    # Large file: read backwards in blocks
    # ... (block-based backward reading)
```

### 5. Subprocess Management

**Best Practices**:
- Use `ThreadPoolExecutor` for parallel subprocess execution
- Set reasonable timeouts (30 min for training jobs)
- Capture output only when needed
- Use `text=True` to avoid manual decoding

**Example**: `scripts/batch_evaluator.py`
```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(evaluate_model, task): task
        for task in tasks
    }

    for future in as_completed(futures):
        result = future.result()
        # Process result
```

## Performance Anti-Patterns to Avoid

### 1. String Concatenation in Loops

```python
# ❌ BAD: O(n²) due to string immutability
result = ""
for item in large_list:
    result += str(item) + "\n"

# ✅ GOOD: O(n) using join
result = "\n".join(str(item) for item in large_list)
```

### 2. Repeated CSV/JSON Reads

```python
# ❌ BAD: Re-reads file in loop
for dataset_name in dataset_names:
    df = pd.read_csv(dataset_path)  # Same file!
    process(df, dataset_name)

# ✅ GOOD: Read once, reuse
df = pd.read_csv(dataset_path)
for dataset_name in dataset_names:
    process(df, dataset_name)
```

### 3. List Comprehension for Large Datasets

```python
# ❌ BAD: Loads all results into memory
results = [expensive_operation(x) for x in huge_list]

# ✅ GOOD: Use generator for lazy evaluation
results = (expensive_operation(x) for x in huge_list)
for result in results:
    process(result)  # Processed one at a time
```

### 4. Synchronous I/O in Loops

```python
# ❌ BAD: Sequential subprocess calls
for script in scripts:
    subprocess.run(['python', script])  # Blocks until complete

# ✅ GOOD: Parallel execution
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(subprocess.run, ['python', s])
               for s in scripts]
    results = [f.result() for f in futures]
```

## Monitoring Performance

### 1. SQL Health Check

Check database pool saturation:
```bash
curl http://localhost:7071/api/ai/status | jq '.sql'
```

Response includes:
- `pool_size`: Total connections in pool
- `checked_out`: Currently in use
- `overflow`: Connections beyond pool limit
- `saturation_alert`: `true` if ≥80% saturated

### 2. Resource Monitoring

Use the resource monitor script:
```bash
python scripts/resource_monitor.py --snapshot
python scripts/resource_monitor.py --watch  # Continuous monitoring
```

### 3. Training Analytics

Monitor training performance trends:
```bash
python scripts/training_analytics.py
```

## When to Use Async/Await

**Use async when**:
- Multiple I/O operations can run concurrently
- Network requests or file I/O dominate runtime
- Clear dependencies between operations

**Example**: Autonomous training orchestrator
```python
async def run_training_cycle():
    # Concurrent dataset downloads
    results = await asyncio.gather(
        download_dataset('dataset1'),
        download_dataset('dataset2'),
        download_dataset('dataset3')
    )

    # Sequential training (GPU bound)
    await train_model(results)
```

**Don't use async for**:
- CPU-bound operations (use multiprocessing instead)
- Simple monitoring loops with fixed intervals
- Code that doesn't do I/O

## Caching Strategies

### 1. Disk Caching (Already Implemented)

**Pattern**: Check if file exists before downloading/processing
```python
output_path = QUANTUM_DIR / f"{name}.csv"
if output_path.exists():
    return True, f"Already exists ({output_path.stat().st_size:,} bytes)"

# Download and process...
```

**Used in**:
- `scripts/expand_quantum_datasets.py` - Dataset downloads
- All training scripts - Model checkpoints

### 2. Memory Caching (Where Appropriate)

**Pattern**: Use `functools.lru_cache` for expensive pure functions
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(param):
    # Computation here
    return result
```

**Good for**:
- Configuration parsing
- Data transformations
- Feature engineering

**Not good for**:
- Large datasets (memory pressure)
- Non-deterministic functions
- Functions with side effects

### 3. Singleton Pattern (Implemented)

**Pattern**: Lazy initialization of expensive resources
```python
class CosmosClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize connection
        return cls._instance
```

**Used in**:
- `shared/cosmos_client.py` - Cosmos DB connection
- `shared/sql_engine.py` - SQL connection pools

## Benchmarking

### Quick Performance Check

Add timing to critical sections:
```python
import time

t0 = time.time()
expensive_operation()
print(f"Operation took {time.time() - t0:.2f}s")
```

### Profiling with cProfile

```bash
# Profile a script
python -m cProfile -o profile.stats scripts/my_script.py

# Analyze results
python -m pstats profile.stats
> sort cumulative
> stats 20
```

### Memory Profiling

```bash
# Install memory_profiler
pip install memory-profiler

# Add @profile decorator to functions
# Run with:
python -m memory_profiler scripts/my_script.py
```

## Performance Targets

### Acceptable Latencies

- **API endpoints**: < 200ms (non-streaming)
- **Database queries**: < 50ms (simple), < 500ms (complex)
- **File I/O**: < 1s for typical log tailing
- **Training cycle**: 5-30 minutes (depends on dataset)

### Memory Guidelines

- **Log tailing**: O(k) where k = tail size, not O(n)
- **CSV processing**: Stream when possible, < 100MB in memory
- **Model inference**: < 2GB per model
- **Database connections**: Pool size ≤ 20 for typical workloads

### Parallelism Limits

- **Thread workers**: 3-5 for I/O-bound tasks
- **Process workers**: CPU count for CPU-bound tasks
- **Concurrent HTTP requests**: < 10 to avoid rate limits

## Summary

The Aria codebase follows these performance principles:

1. **Stream data** instead of loading everything into memory
2. **Use connection pooling** for databases and external services
3. **Parallelize I/O-bound** operations with ThreadPoolExecutor
4. **Cache expensive** computations and downloads
5. **Monitor health** with built-in observability

For questions or suggestions, see the development team.
