# Quantum-Enabled GGUF Infrastructure

Complete infrastructure for training, converting, and serving quantum-enhanced GGUF (GPT-Generated Unified Format) models.

## 🎯 Overview

This infrastructure provides an end-to-end pipeline for creating quantum-enhanced language models:

```
LoRA Training 
    ↓
GGUF Conversion & Quantization
    ↓
Quantum Circuit Injection
    ↓
Validation & Benchmarking
    ↓
Deployment & Serving
    ↓
Monitoring & Registry
```

## 🏗️ Infrastructure Components

### 1. **Configuration** (`config/training/quantum_gguf.yaml`)
- Training configurations with quantum enhancements
- Quantization strategies (q4_0, q5_0, q8_0, f16)
- Quantum feature specifications
- Validation metrics and thresholds
- Deployment strategies

### 2. **Orchestrator** (`scripts/quantum_gguf/gguf_orchestrator.py`)
- Main pipeline orchestration engine
- Phase management (training → conversion → quantum → validation → deployment)
- Status tracking and error recovery
- Dry-run capability for validation

**Usage:**
```bash
# Dry-run validation
python scripts/quantum_gguf/gguf_orchestrator.py --dry-run

# Full pipeline
python scripts/quantum_gguf/gguf_orchestrator.py --full

# Quick test mode
python scripts/quantum_gguf/gguf_orchestrator.py --quick

# Check status
python scripts/quantum_gguf/gguf_orchestrator.py --status

# View registry
python scripts/quantum_gguf/gguf_orchestrator.py --registry
```

### 3. **Quantum Integration** (`scripts/quantum_gguf/quantum_gguf_integration.py`)
- Quantum circuit creation (entanglement patterns, VQE ansatz, QAOA patterns)
- Amplitude encoding for classical-quantum bridges
- Feature injection into training datasets
- Quantum gate optimization

**Key Features:**
- `QuantumGGUFIntegrator` - Main integration class
- Entanglement patterns (linear, circular, full)
- VQE ansatz (Variational Quantum Eigensolver)
- QAOA patterns (Quantum Approximate Optimization Algorithm)
- Amplitude encoding for data-to-quantum conversion

### 4. **Model Registry** (`scripts/quantum_gguf/gguf_registry.py`)
- Centralized GGUF model metadata management
- Track quantization types, performance metrics, deployment status
- Query models by various filters
- Export summaries and statistics

**Usage:**
```python
from scripts.quantum_gguf.gguf_registry import GGUFRegistry, GGUFMetadata

registry = GGUFRegistry()

# Register a model
metadata = GGUFMetadata(
    model_id="phi3.5-quantum-q4_0",
    name="Phi-3.5 Quantum Chat",
    base_model="microsoft/Phi-3.5-mini-instruct",
    quantization_type="q4_0",
    file_path=Path("deployed_models/phi3.5-quantum.gguf"),
    file_size_mb=3570.0,
    created_at="2025-01-19T12:00:00Z",
    model_hash="abc123def456",
    quantum_enhanced=True,
    quantum_features=["entanglement", "amplitude_encoding"],
    quantum_fidelity=0.95,
    inference_speed_tokens_per_sec=45.2,
    perplexity=12.5
)

registry.register_model(metadata)

# Query models
quantum_models = registry.list_models(quantum_enhanced=True)
best_q4_model = registry.get_best_model(quantization_type="q4_0")

# Export summary
registry.print_summary()
```

### 5. **Model Serving** (`scripts/quantum_gguf/gguf_serving.py`)
- Multi-platform GGUF serving
- Quantum-enhanced inference
- Support for llama.cpp, vLLM, Azure Inference

**Platforms:**
- `llama-cpp` - Local CPU/GPU inference with llama.cpp
- `vllm` - High-performance batched inference
- `azure_inference` - Azure Container Instance serving

**Usage:**
```python
from scripts.quantum_gguf.gguf_serving import create_server, ServingPlatform
from pathlib import Path

# Create llama.cpp server
server = create_server(
    platform="llama-cpp",
    model_path=Path("deployed_models/best_model.gguf"),
    port=8000,
    llama_cpp_config={
        'n_gpu_layers': 50,
        'n_threads': 8,
        'ctx_size': 2048
    }
)

server.start()

# Run inference
result = server.inference("Hello, how are you?", max_tokens=256)

# Run quantum-enhanced inference
quantum_result = server.quantum_inference(
    prompt="Explain quantum computing",
    circuit_features=[...]
)

server.stop()
```

### 6. **Validation & Benchmarking** (`scripts/quantum_gguf/gguf_validation.py`)
- File integrity validation
- Quantization format verification
- Quantum feature validation
- Performance benchmarking (speed, memory, perplexity)

**Usage:**
```python
from scripts.quantum_gguf.gguf_validation import GGUFValidator, GGUFBenchmark
from pathlib import Path

model_path = Path("deployed_models/phi3.5-quantum.gguf")

# Validate
validator = GGUFValidator(model_path)
results = validator.run_all_validations()

# Benchmark
benchmark = GGUFBenchmark(model_path)
benchmark_result = benchmark.run_full_benchmark()

print(f"Speed: {benchmark_result.inference_speed_tokens_per_sec} tok/s")
print(f"Perplexity: {benchmark_result.perplexity}")
print(f"Passed: {benchmark_result.passed}")
```

## 📊 Configuration Guide

### Training Config
```yaml
training:
  configs:
    - name: "phi3.5-quantum-chat"
      base_model: "microsoft/Phi-3.5-mini-instruct"
      dataset_path: "datasets/chat"
      quantum_enhanced: true
      quantum_features:
        - "entanglement_patterns"
        - "circuit_embeddings"
        - "amplitude_encoding"
```

### Quantization Strategies
```yaml
conversion:
  quantization_strategies:
    - type: "q4_0"      # 4-bit, highest compression
      use_case: "edge_devices"
    - type: "q5_0"      # 5-bit, good compression
      use_case: "mobile"
    - type: "q8_0"      # 8-bit, high precision
      use_case: "servers"
    - type: "f16"       # 16-bit, reference quality
      use_case: "validation"
```

### Quantum Features
```yaml
quantum_enhancement:
  features:
    entanglement_patterns:
      enabled: true
      num_qubits: 4
      pattern_type: "linear"  # or circular, full
    
    amplitude_encoding:
      enabled: true
      normalization: "softmax"
    
    vqe_embeddings:
      enabled: true
      ansatz: "efficient_su2"
      reps: 1
    
    qaoa_patterns:
      enabled: true
      p: 1
```

## 🚀 Quick Start

### 1. **Dry-Run Validation**
```bash
python scripts/quantum_gguf/gguf_orchestrator.py --dry-run
```

### 2. **Create Quantum-Enhanced Dataset**
```bash
python -c "
from scripts.quantum_gguf.quantum_gguf_integration import create_quantum_enhanced_dataset
from pathlib import Path

output = create_quantum_enhanced_dataset(
    input_dataset=Path('datasets/chat/train.jsonl'),
    output_dir=Path('data_out/quantum_datasets'),
    quantum_features=[
        'entanglement_patterns',
        'amplitude_encoding',
        'vqe_embeddings'
    ]
)
print(f'Created: {output}')
"
```

### 3. **Run Full Pipeline**
```bash
python scripts/quantum_gguf/gguf_orchestrator.py --full
```

### 4. **Check Model Registry**
```bash
python scripts/quantum_gguf/gguf_orchestrator.py --registry
```

### 5. **Serve a Model**
```bash
python -c "
from scripts.quantum_gguf.gguf_serving import create_server
from pathlib import Path

server = create_server(
    platform='llama-cpp',
    model_path=Path('deployed_models/best_model.gguf')
)
server.start()
print('Server running on http://localhost:8000')
"
```

### 6. **Validate & Benchmark**
```bash
python -c "
from scripts.quantum_gguf.gguf_validation import GGUFValidator, GGUFBenchmark
from pathlib import Path

model = Path('deployed_models/best_model.gguf')

# Validate
validator = GGUFValidator(model)
validator.run_all_validations()

# Benchmark
benchmark = GGUFBenchmark(model)
result = benchmark.run_full_benchmark()
"
```

## 📊 Output Structure

```
data_out/quantum_gguf_training/
├── orchestrator.log              # Main orchestrator logs
├── status.json                   # Current orchestration status
├── gguf_registry.json            # Model registry
├── lora_models/                  # LoRA checkpoint models
│   ├── phi3.5-quantum-chat/
│   └── qwen-quantum-coding/
├── gguf_models/                  # Converted GGUF models
│   ├── phi3.5-quantum-q4_0.gguf
│   ├── phi3.5-quantum-q5_0.gguf
│   └── qwen-quantum-q4_0.gguf
├── quantum_data/                 # Quantum circuit data
│   ├── entanglement_patterns.json
│   ├── vqe_ansatz.json
│   └── qaoa_patterns.json
├── metrics/                      # Performance metrics
│   ├── benchmark_results.json
│   └── performance_stats.json
└── reports/                      # Human-readable reports
    ├── pipeline_summary.md
    └── validation_report.md

deployed_models/                  # Production models
├── best_model.gguf
├── best_model_q4.gguf
└── best_model_metadata.json
```

## ⚙️ Advanced Configuration

### Custom Quantum Provider
```yaml
quantum:
  provider: "pennylane"           # or qiskit
  backend: "default.qubit"
  num_qubits: 4
  max_circuit_depth: 10
  enable_error_mitigation: true
```

### Azure Quantum Integration
```yaml
quantum:
  azure_quantum:
    enabled: true
    subscription_id: "${AZURE_SUBSCRIPTION_ID}"
    resource_group: "${AZURE_RESOURCE_GROUP}"
    workspace_name: "${AZURE_QUANTUM_WORKSPACE}"
    provider_id: "ionq"            # or rigetti
    min_cost_usd: 1.0
    dry_run_first: true
```

### Custom Serving Config
```yaml
deployment:
  serving:
    - platform: "llama-cpp"
      config:
        n_gpu_layers: 50
        n_threads: 8
        ctx_size: 2048
    
    - platform: "vllm"
      config:
        dtype: "float16"
        gpu_memory_util: 0.9
        max_model_len: 2048
```

## 🔍 Monitoring & Status

### Check Orchestration Status
```bash
python scripts/quantum_gguf/gguf_orchestrator.py --status
```

### Monitor Model Registry
```bash
python scripts/quantum_gguf/gguf_orchestrator.py --registry
```

### Export Registry Summary
```bash
python -c "
from scripts.quantum_gguf.gguf_registry import GGUFRegistry
registry = GGUFRegistry()
summary = registry.export_summary()
import json
print(json.dumps(summary, indent=2))
"
```

## 🧪 Testing

### Test Quantum Integration
```bash
python scripts/quantum_gguf/quantum_gguf_integration.py
```

### Test GGUF Validation
```bash
python scripts/quantum_gguf/gguf_validation.py
```

### Test Model Serving
```bash
python scripts/quantum_gguf/gguf_serving.py
```

## 📋 Integration with Existing Systems

### With LoRA Training
The orchestrator automatically integrates with `scripts/training/autotrain.py` for LoRA training.

### With Aria Character
Deploy quantized models to Aria for efficient on-device inference:
```python
# aria_web/server.py integration
model_path = Path("deployed_models/best_model.gguf")
server = create_server(platform="llama-cpp", model_path=model_path)
```

### With Azure Functions
Expose GGUF models via `function_app.py` endpoints:
```python
# function_app.py
from scripts.quantum_gguf.gguf_registry import GGUFRegistry

@app.route('api/quantum-gguf/list', auth_level=func.AuthLevel.ANONYMOUS)
def list_gguf_models(req: func.HttpRequest):
    registry = GGUFRegistry()
    models = registry.list_models(quantum_enhanced=True)
    return func.HttpResponse(json.dumps([m.to_dict() for m in models]))
```

## 🛠️ Troubleshooting

### Model not found in registry
- Check that model was properly registered during training
- Verify model files exist in output directory
- Run `gguf_orchestrator.py --registry` to see all registered models

### Quantization failed
- Check input model format is valid LoRA or PyTorch
- Verify available disk space for conversion
- Try with smaller model first

### Quantum features not injecting
- Verify quantum features are enabled in config
- Check PennyLane is installed: `pip install pennylane`
- Review feature compatibility with model architecture

### Serving port already in use
- Change port in serving config
- Or kill existing process: `lsof -ti:8000 | xargs kill -9`

## 📚 References

- [GGUF Format Specification](https://github.com/philpax/ggml/blob/master/docs/gguf.md)
- [llama.cpp Project](https://github.com/ggerganov/llama.cpp)
- [PennyLane Quantum ML](https://pennylane.ai)
- [Qiskit Framework](https://qiskit.org)
- [Phi-3.5 Model](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)

## 📄 License

Part of the Aria AI Platform. See LICENSE for details.

## 🤝 Contributing

Report issues or suggest improvements by creating a GitHub issue.
