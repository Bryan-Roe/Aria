# Quantum-Powered LLM Module

## Overview

The Quantum-Powered LLM module integrates quantum computing circuits with large language model inference to create a hybrid quantum-classical system. The pipeline combines:

- **QuantumRouter** — Intelligently selects the best downstream LLM provider based on prompt analysis
- **QuantumEmbeddingTransformer** — Applies quantum amplitude encoding and variational transformations to augment embeddings
- **QuantumSampler** — Re-weights token sampling probabilities using quantum circuit measurement outcomes
- **Multi-Provider Chat Backend** — Supports Azure OpenAI, OpenAI, LMStudio, LoRA, and local fallback

## Architecture

```
User Prompt
    │
    ├──→ QuantumRouter (selects provider: azure/openai/lmstudio/local/lora)
    │
    ├──→ QuantumEmbeddingTransformer (applies quantum-augmented encoding)
    │
    ├──→ Chat Provider (generates response: azure/openai/lmstudio/local)
    │
    └──→ QuantumSampler (re-weights token probabilities with quantum circuit)
         │
         └──→ Final Response (SSE stream or JSON response)
```

## Quick Start

### Installation

```bash
cd /workspaces/Aria
python -m pip install -q -e ai-projects/quantum-ml

# Optional quantum backends
python -m pip install -q qiskit pennylane  # for real quantum backends
```

### Basic Usage

```python
from ai_projects.quantum_ml.src.quantum_llm import QuantumLLMPipeline, QuantumLLMConfig
import asyncio

# Create pipeline with default config
pipeline = QuantumLLMPipeline()

# Non-streaming completion
result = asyncio.run(
    pipeline.generate(
        prompt="What is quantum computing?",
        provider="auto",  # auto-detect or specify azure/openai/lmstudio/local
    )
)
print(result)
# Output: {
#   "response": "...",
#   "provider": "...",
#   "backend": "classical|pennylane|qiskit",
#   "qubits": 4,
#   "shots": 512,
#   "latency_ms": 45.2,
#   "quantum_augmented": True
# }


# Streaming completion
async def stream_example():
    async for chunk in pipeline.stream("Tell me about quantum entanglement"):
        print(chunk, end="", flush=True)


asyncio.run(stream_example())
```

## Configuration

### Environment Variables

Configure the pipeline via environment variables:

```bash
# Quantum backend selection
export QUANTUM_LLM_BACKEND=auto  # auto|qiskit|pennylane|classical

# Circuit parameters
export QUANTUM_LLM_QUBITS=4
export QUANTUM_LLM_SHOTS=512
export QUANTUM_LLM_LAYERS=2

# Sampling parameters
export QUANTUM_LLM_TOP_K=10
export QUANTUM_LLM_TEMP_BLEND=0.3  # 0=classical, 1=quantum

# LLM provider settings
export QUANTUM_LLM_PROVIDER=auto  # auto|azure|openai|lmstudio|local|lora
export QUANTUM_LLM_MODEL=gpt-4
export QUANTUM_LLM_TEMPERATURE=0.7
export QUANTUM_LLM_MAX_TOKENS=512

# Security / validation
export QUANTUM_LLM_MAX_PROMPT_CHARS=8000
export QUANTUM_LLM_MAX_TOKENS_CAP=2048

# Circuit caching (new)
export QUANTUM_LLM_CACHE_ENABLED=true
export QUANTUM_LLM_CACHE_MAX_SIZE=256
export QUANTUM_LLM_CACHE_TTL_SECONDS=3600
```

### Programmatic Configuration

```python
from ai_projects.quantum_ml.src.quantum_llm import QuantumLLMConfig, QuantumLLMPipeline

config = QuantumLLMConfig(
    backend="classical",  # "auto", "qiskit", "pennylane", "classical"
    num_qubits=4,
    shots=512,
    num_layers=2,
    top_k=10,
    temperature_blend=0.3,  # 0 = classical, 1 = quantum
    provider="auto",
    model="gpt-4",
    temperature=0.7,
    max_tokens=512,
    max_prompt_chars=8000,
    cache_enabled=True,
    cache_max_size=256,
    cache_ttl_seconds=3600.0,
)

pipeline = QuantumLLMPipeline(config=config)
```

## API Endpoints

The quantum LLM is exposed through Azure Functions via `function_app.py`:

### GET /api/quantum-llm/status

Returns the current quantum backend, provider configuration, and circuit cache statistics.

```bash
curl http://localhost:7071/api/quantum-llm/status | jq
```

**Response:**

```json
{
    "status": "ok",
    "backend": "classical",
    "fallback": false,
    "num_qubits": 4,
    "shots": 512,
    "num_layers": 2,
    "provider": "auto",
    "cache": {
        "enabled": true,
        "stats": {
            "size": 42,
            "max_size": 256,
            "hits": 127,
            "misses": 35,
            "hit_rate": 0.784,
            "evictions": 0,
            "expirations": 2
        }
    }
}
```

### POST /api/quantum-llm/chat

Non-streaming quantum-augmented completion.

**Request:**

```json
{
    "prompt": "What is entanglement?",
    "provider": "auto",
    "backend": "auto",
    "max_tokens": 512,
    "seed": null
}
```

**Response:**

```json
{
    "response": "Quantum entanglement is...",
    "provider": "local",
    "backend": "classical",
    "qubits": 4,
    "shots": 512,
    "latency_ms": 23.5,
    "quantum_augmented": true
}
```

### POST /api/quantum-llm/stream

SSE-based streaming quantum-augmented completion.

**Request (same schema as /chat):**

```json
{
    "prompt": "Explain superposition",
    "provider": "auto",
    "seed": 42
}
```

**Response (SSE stream):**

```
event: meta
data: {"provider": "local", "backend": "classical", "qubits": 4, "shots": 512}

data: {"delta": "Quantum "}

data: {"delta": "superposition "}

data: {"delta": "is..."}

data: {"latency_ms": 12.3, "quantum_augmented": true}

data: [DONE]
```

## Components

### QuantumRouter

Selects the best LLM provider based on prompt features (length, language, latency budget) using QAOA-inspired scoring.

```python
from ai_projects.quantum_ml.src.quantum_llm.quantum_router import QuantumRouter

router = QuantumRouter(backend="classical", num_qubits=4)
provider = router.route("What is quantum computing?")
print(provider)  # "azure", "openai", "lmstudio", or "local"
```

### QuantumEmbeddingTransformer

Applies quantum amplitude encoding and variational circuit transformations to augment text embeddings.

```python
from ai_projects.quantum_ml.src.quantum_llm.quantum_embeddings import QuantumEmbeddingTransformer
import numpy as np

embedder = QuantumEmbeddingTransformer(backend="classical", num_qubits=4, num_layers=2)
text_embedding = np.random.randn(10)
transformed = embedder.transform(text_embedding)
print(transformed.shape)  # (10,)
```

### QuantumSampler

Re-weights token sampling probabilities using a parameterized variational circuit.

```python
from ai_projects.quantum_ml.src.quantum_llm.quantum_sampler import QuantumSampler

sampler = QuantumSampler(backend="classical", num_qubits=4, shots=512)
logits = [10.0, 2.0, 1.0, 0.5]  # Top-k logits from LLM
sampled_idx = sampler.sample(logits, blend_factor=0.3, seed=42)
print(sampled_idx)  # 0, 1, 2, or 3

# Check cache stats
stats = sampler.cache_stats()
print(stats)  # {"size": 10, "max_size": 256, "hits": 100, "misses": 5, ...}
```

### CircuitCache

LRU cache with TTL expiration for storing quantum circuit results.

```python
from ai_projects.quantum_ml.src.quantum_llm.circuit_cache import CircuitCache
import numpy as np

cache = CircuitCache(max_size=256, max_age_seconds=3600)

# Store
params = np.array([0.5, 1.0, 1.5])
probs = np.array([0.25, 0.25, 0.25, 0.25])
cache.put(params, num_qubits=2, probs=probs)

# Retrieve
cached_probs = cache.get(params, num_qubits=2)
print(cached_probs)

# Stats
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Quantum Backends

### Auto (Recommended)

```python
config = QuantumLLMConfig(backend="auto")
# Automatically selects: PennyLane > Qiskit > Classical
```

### Classical (Default / Always Available)

```python
config = QuantumLLMConfig(backend="classical")
# Pure numpy simulation, no external dependencies
```

### PennyLane

```bash
pip install pennylane
```

```python
config = QuantumLLMConfig(backend="pennylane")
# Supports PennyLane devices: default.qubit, default.qubit.jax, etc.
```

### Qiskit

```bash
pip install qiskit qiskit-aer
```

```python
config = QuantumLLMConfig(backend="qiskit")
# Uses Qiskit Aer simulator
```

### Azure Quantum (Future)

Planned support for Azure Quantum via Azure Quantum hardware providers (IonQ, Quantinuum).

## Circuit Caching (New Feature)

The module includes LRU caching with TTL expiration to avoid recomputing identical quantum circuits:

```python
config = QuantumLLMConfig(
    cache_enabled=True,  # Enable caching
    cache_max_size=256,  # Max 256 cached circuits
    cache_ttl_seconds=3600.0,  # Expire after 1 hour
)
pipeline = QuantumLLMPipeline(config=config)

# Check cache performance
status = pipeline.status()
print(status["cache"]["stats"])
# {
#   "size": 42,
#   "max_size": 256,
#   "hits": 127,
#   "misses": 35,
#   "hit_rate": 0.784,
#   "evictions": 0,
#   "expirations": 2,
# }
```

## Performance Optimization

### Token Blending

Control the weight between classical and quantum sampling:

```python
# 0 = pure classical (default)
config = QuantumLLMConfig(temperature_blend=0.0)

# 1 = pure quantum
config = QuantumLLMConfig(temperature_blend=1.0)

# Balanced (recommended)
config = QuantumLLMConfig(temperature_blend=0.3)
```

### Circuit Parameters

Reduce compute time with fewer qubits/layers:

```python
# Fast (1-2ms per call)
config = QuantumLLMConfig(num_qubits=4, num_layers=1, shots=256)

# Balanced (5-10ms per call)
config = QuantumLLMConfig(num_qubits=4, num_layers=2, shots=512)

# Accurate (20-50ms per call)
config = QuantumLLMConfig(num_qubits=8, num_layers=3, shots=1024)
```

### Provider Fallback Chain

The router intelligently selects providers based on prompt analysis:

1. **QuantumRouter** evaluates prompt features (length, complexity, latency budget)
2. **Provider Detection Chain**: Azure OpenAI → OpenAI → LMStudio → Local
3. **Fallback**: Always returns a valid provider (local echo fallback)

## Testing

### Unit Tests

```bash
pytest tests/unit/test_quantum_llm_config.py -v
pytest tests/unit/test_quantum_llm_components.py -v
```

### Integration Tests

```bash
pytest tests/integration/test_quantum_llm_pipeline.py -v
```

### Manual Testing

```bash
# Start Azure Functions
func host start

# Test status endpoint
curl http://localhost:7071/api/quantum-llm/status | jq

# Test chat endpoint
curl -X POST http://localhost:7071/api/quantum-llm/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'

# Test streaming endpoint
curl -X POST http://localhost:7071/api/quantum-llm/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me about quantum computing"}' | jq -Rs 'split("\n") | .[]'
```

## Monitoring & Observability

### Health Check

```python
pipeline = QuantumLLMPipeline()
status = pipeline.status()

print(f"Backend: {status['backend']}")
print(f"Fallback: {status['fallback']}")
print(f"Cache hit rate: {status['cache']['stats']['hit_rate']:.1%}")
```

### Logging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

### Metrics

Track pipeline performance:

```python
import time
import asyncio


async def benchmark():
    pipeline = QuantumLLMPipeline()
    times = []

    for i in range(10):
        t0 = time.monotonic()
        result = await pipeline.generate(f"Test prompt {i}")
        t1 = time.monotonic()
        times.append((t1 - t0) * 1000)

    print(f"Mean: {sum(times) / len(times):.1f}ms")
    print(f"Min: {min(times):.1f}ms")
    print(f"Max: {max(times):.1f}ms")


asyncio.run(benchmark())
```

## Troubleshooting

### Pipeline initialization fails

```python
pipeline = QuantumLLMPipeline()
if pipeline.effective_backend == "classical":
    print("⚠️  Falling back to classical backend")
    print("Install quantum libraries: pip install qiskit pennylane")
```

### Provider detection returns "local-echo"

```python
result = await pipeline.generate("test")
if result["provider"] == "local-echo":
    print("⚠️  No real provider available")
    print("Configure: OPENAI_API_KEY, AZURE_OPENAI_*, or LMSTUDIO_BASE_URL")
```

### Cache not working

```python
status = pipeline.status()
if not status["cache"]["enabled"]:
    print("Cache is disabled")

stats = status["cache"]["stats"]
if stats.get("hit_rate", 0) < 0.1:
    print("Low cache hit rate, consider adjusting parameters")
```

## Advanced Usage

### Custom Prompt Analysis

```python
from ai_projects.quantum_ml.src.quantum_llm.quantum_router import _extract_prompt_features

prompt = "Explain quantum entanglement in detail"
features = _extract_prompt_features(prompt)
print(features)
# [length, words, has_question, has_code, latency_budget]
```

### Manual Component Usage

```python
from ai_projects.quantum_ml.src.quantum_llm.quantum_sampler import QuantumSampler
from ai_projects.quantum_ml.src.quantum_llm.quantum_embeddings import QuantumEmbeddingTransformer
from ai_projects.quantum_ml.src.quantum_llm.quantum_router import QuantumRouter

# Use components independently
sampler = QuantumSampler(backend="classical")
embedder = QuantumEmbeddingTransformer(backend="classical")
router = QuantumRouter(backend="classical")
```

## References

- [PennyLane Documentation](https://pennylane.ai/)
- [Qiskit Documentation](https://qiskit.org/)
- [Variational Quantum Algorithms](https://arxiv.org/abs/2012.09265)
- [QAOA on Classical Hardware](https://arxiv.org/abs/1602.07674)

## Related Files

- `pipeline.py` — Main orchestrator
- `config.py` — Configuration management
- `quantum_sampler.py` — Token re-weighting
- `quantum_embeddings.py` — Embedding transformation
- `quantum_router.py` — Provider selection
- `circuit_cache.py` — Result caching
- `/workspaces/Aria/function_app.py` — Azure Functions endpoints

## Future Enhancements

- [ ] Azure Quantum backend support (IonQ, Quantinuum)
- [ ] Circuit optimization and transpilation
- [ ] Custom unitary decomposition
- [ ] Quantum metric learning for provider selection
- [ ] Cost estimation for Azure Quantum jobs
- [ ] Multi-circuit batching
- [ ] Distributed quantum sampling
