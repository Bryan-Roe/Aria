# Quantum Code LLM

Self-contained quantum-classical transformer language model for code generation.

## Architecture

```
Tokens → Embedding + Positional Encoding
       → N × QuantumTransformerBlock
           ├── QuantumKernelAttention
           │     Q, K projected through variational quantum circuit
           │     scores = φ(Q) · φ(K)ᵀ / √n_qubits
           └── QuantumFFN
                 Linear → quantum variational circuit → Linear
       → Output head (weight-tied to embedding)
```

## Quantum Backend Auto-Detection

| Priority | Backend | Requires |
|----------|---------|---------|
| 1st | `qiskit.aer` | `pennylane-qiskit` + `qiskit-aer` |
| 2nd | `default.qubit` | `pennylane` (already in repo) |
| 3rd | classical MLP | nothing (always available) |

## Quick Start

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("quantum-ai/src").resolve()))
from quantum_code_llm import generate, train

# Train on built-in Python code snippets
model, tokenizer = train(
    model_cfg={"n_qubits": 4, "d_model": 64, "n_layers": 2},
    train_cfg={"n_epochs": 5, "lr": 3e-3},
)

# Generate code
print(generate(model, tokenizer, "def factorial(n):"))
```

## Run Demo

```bash
python quantum-ai/examples/quantum_code_llm_demo.py

# Override settings via env vars
QLCM_EPOCHS=10 QLCM_QUBITS=6 python quantum-ai/examples/quantum_code_llm_demo.py

# Force classical backend
QLCM_BACKEND=classical python quantum-ai/examples/quantum_code_llm_demo.py
```

## Config Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_qubits` | 4 | qubits per quantum layer |
| `d_model` | 64 | model hidden dimension |
| `n_heads` | 4 | attention heads |
| `n_layers` | 2 | transformer blocks |
| `n_var_layers` | 2 | variational layers inside each circuit |
| `max_seq_len` | 128 | maximum context length |
| `backend` | `"auto"` | `"auto"` \| `"qiskit.aer"` \| `"default.qubit"` \| `"classical"` |

## Train with Custom Code

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("quantum-ai/src").resolve()))
from quantum_code_llm import generate, train

MY_CODE = [
    "def hello(name):\n    print('Hi ' + name)\n",
    "def bye(name):\n    print('Bye ' + name)\n",
]

model, tok = train(extra_snippets=MY_CODE)
print(generate(model, tok, "def greet("))
```

## Checkpoints

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("quantum-ai/src").resolve()))
from quantum_code_llm import load_checkpoint, save_checkpoint

checkpoint = Path("data_out/quantum_code_llm/checkpoint.pt")
save_checkpoint(model, tok, checkpoint, extra={"run": "quickstart"})
restored_model, restored_tok, metadata = load_checkpoint(checkpoint)
print(metadata["path"], metadata["backend"])
```

## Files

| File | Description |
|------|-------------|
| `src/quantum_code_llm.py` | Self-contained module (~700 lines) |
| `examples/quantum_code_llm_demo.py` | Training + generation demo |
