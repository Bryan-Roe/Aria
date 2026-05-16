# Quantum-Powered LLM Module

A quantum-augmented LLM pipeline that fuses Qiskit / PennyLane quantum circuits with the Aria multi-provider chat backend.

## Architecture

```mermaid
graph TD
    A[User Prompt] --> B[QuantumRouter]
    B -->|selects provider| C[LLM Provider\nazure / openai / lmstudio / local]
    A --> D[QuantumEmbeddingTransformer]
    D -->|augmented embedding| C
    C -->|raw response / logits| E[QuantumSampler]
    E -->|re-weighted tokens| F[Final Response]
    F --> G[/api/quantum-llm/chat\nor stream]
```

## Components

| Component | File | Description |
| ----------- | ------ | ------------- |
| `QuantumSampler` | `quantum_sampler.py` | Re-weights LLM top-k logits via variational circuit |
| `QuantumEmbeddingTransformer` | `quantum_embeddings.py` | Amplitude-encoding + variational transform |
| `QuantumRouter` | `quantum_router.py` | QAOA-style provider routing |
| `QuantumLLMPipeline` | `pipeline.py` | Wires all components; exposes `generate` / `stream` |
| `QuantumLLMConfig` | `config.py` | Dataclass settings with env-var support |

## Backends

Detection order (when `backend="auto"`):

1. **PennyLane** (`default.qubit` simulator) — if `pennylane` is importable
2. **Qiskit + AerSimulator** — if `qiskit` and `qiskit-aer` are importable
3. **Classical fallback** — pure NumPy, always available

No hard dependencies are added to the base install.  Quantum packages remain optional (`[quantum]` extras in `requirements.txt`).

## Configuration

All settings can be overridden via environment variables:

| Env var | Default | Description |
| --------- | --------- | ------------- |
| `QUANTUM_LLM_BACKEND` | `auto` | `auto\ | pennylane\ | qiskit\ | classical` |
| `QUANTUM_LLM_QUBITS` | `4` | Number of qubits |
| `QUANTUM_LLM_SHOTS` | `512` | Measurement shots |
| `QUANTUM_LLM_LAYERS` | `2` | Variational circuit depth |
| `QUANTUM_LLM_TOP_K` | `10` | Top-k candidates for sampling |
| `QUANTUM_LLM_TEMP_BLEND` | `0.3` | Quantum / classical blend (0–1) |
| `QUANTUM_LLM_PROVIDER` | `auto` | Downstream LLM provider |
| `QUANTUM_LLM_MAX_TOKENS` | `512` | Max output tokens |
| `QUANTUM_LLM_MAX_PROMPT_CHARS` | `8000` | Prompt size limit |

Python usage:

```python
from quantum_llm import QuantumLLMConfig, QuantumLLMPipeline
import asyncio

cfg = QuantumLLMConfig(backend="classical", num_qubits=4, shots=512)
pipeline = QuantumLLMPipeline(config=cfg)

result = asyncio.run(pipeline.generate("Explain quantum entanglement"))
print(result["response"])
```

## API Endpoints

All endpoints are registered in `function_app.py` and served by Azure Functions.

### `GET /api/quantum-llm/status`

Returns the active backend, qubit count, fallback state, and downstream provider.

```bash
curl http://localhost:7071/api/quantum-llm/status
```

```json
{
  "status": "ok",
  "backend": "classical",
  "fallback": true,
  "num_qubits": 4,
  "shots": 512,
  "provider": "auto"
}
```

### `POST /api/quantum-llm/chat`

Non-streaming JSON completion.

```bash
curl -X POST http://localhost:7071/api/quantum-llm/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Aria!"}'
```

```json
{
  "response": "Hello! I am Aria...",
  "provider": "local-echo",
  "backend": "classical",
  "qubits": 4,
  "shots": 512,
  "latency_ms": 12.3,
  "quantum_augmented": true
}
```

Optional body fields:

| Field | Type | Description |
| ------- | ------ | ------------- |
| `prompt` | string | **Required** — user prompt |
| `provider` | string | Override provider (`azure`, `openai`, `lmstudio`, `local`) |
| `backend` | string | Override quantum backend |
| `num_qubits` | int | Override qubit count |
| `max_tokens` | int | Max output tokens |
| `seed` | int | Random seed for reproducibility |

### `POST /api/quantum-llm/stream`

SSE streaming response (same event format as `/api/chat/stream`).

```bash
curl -X POST http://localhost:7071/api/quantum-llm/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Tell me about quantum computing"}' \
  --no-buffer
```

Events:
```
event: meta
data: {"provider": "local-echo", "backend": "classical", "qubits": 4, "shots": 512}

data: {"delta": "Quantum computing "}

data: {"delta": "uses qubits..."}

data: {"latency_ms": 45.2, "quantum_augmented": true}

data: [DONE]
```

## Running Tests

Tests use the classical fallback so no quantum SDK is required:

```bash
# From repo root
python scripts/test_runner.py --unit

# Or directly
pytest tests/test_quantum_llm.py -v
```

## Web UI

The Aria chat interface (`apps/aria/index.html`) includes a **Quantum Mode** toggle.  When enabled, chat requests are routed through `/api/quantum-llm/stream` instead of `/api/chat/stream`.  Backend status is surfaced in the footer status bar.
