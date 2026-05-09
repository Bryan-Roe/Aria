---
title: Aria
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "6.12.0"
app_file: app.py
pinned: false
---

# Aria — Interactive AI Character Platform

[![CI Pipeline](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/ci-pipeline.yml)
[![Code Quality](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/code-quality.yml)
[![CodeQL](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/codeql.yml)
[![E2E Tests](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml/badge.svg)](https://github.com/Bryan-Roe/Aria/actions/workflows/e2e-tests.yml)
[![Codespaces Prebuilds](https://github.com/Bryan-Roe/Aria/actions/workflows/codespaces/create_codespaces_prebuilds/badge.svg?branch=main)](https://github.com/Bryan-Roe/Aria/actions/workflows/codespaces/create_codespaces_prebuilds)
**An intelligent, animated AI character with movement, gestures, and natural language interaction.**

[Live Demo](https://bryan-roe.github.io/Aria) · [Aria Web UI](apps/aria/) · [Quick Start](#-quick-start)

---

## What is Aria?

Aria is a full-stack interactive AI character platform. She lives on a virtual 3D stage, responds to natural language commands ("wave", "pick up the ball", "dance"), speaks via text-to-speech, and is powered by a multi-provider AI backend that supports LM Studio, Ollama, Azure OpenAI, OpenAI, local models, and LoRA fine-tuned adapters.

The project is organized around four core areas:

| Area | Folder | Description |
| --- | --- | --- |
| **Character interface** | `apps/aria/` | Animated 3D character stage with object interaction |
| **Chat / AI backends** | `ai-projects/chat-cli/` | Multi-provider CLI and streaming chat API |
| **Quantum ML** | `ai-projects/quantum-ml/` | Hybrid quantum-classical training (experimental) |
| **Model fine-tuning** | `AI/` | LoRA fine-tuning for Aria's language understanding |

Supporting infrastructure lives in `shared/`, `scripts/`, `config/`, and `function_app.py` (Azure Functions API layer).

---

## 🤗 Hugging Face Spaces

This repository is also configured to run as a **Gradio Hugging Face Space**.

- Spaces entry point: `app.py`
- Reusable demo helper: `scripts/gradio_hello.py`
- SDK: `gradio`

The Spaces deployment now exposes a **lightweight AI chat app** backed by the repository's existing provider abstraction. It can use the same provider layer as the rest of Aria (`auto`, local fallback, OpenAI, Azure OpenAI, LM Studio, Ollama, and AGI where configured), while remaining simpler than the full local Aria stack (`apps/aria/`, Azure Functions, training scripts, and quantum components).

If you want to run the Space locally:

```bash
./.venv/bin/python app.py
```

If you want the full Aria platform instead, use the Quick Start steps below.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git

### 1 — Run the Aria character web UI

```bash
cd apps/aria
pip install -r ../../requirements.txt   # only needed once
python server.py
# Open http://localhost:8080
```

Type commands in the chat box: `move left`, `wave`, `jump`, `pick up the ball`, `dance`.

### 2 — Chat via CLI (no UI required)

```bash
# Local mode — no API keys required
python ai-projects/chat-cli/src/chat_cli.py --provider local --once "Hello Aria!"

# OpenAI
OPENAI_API_KEY=sk-... python ai-projects/chat-cli/src/chat_cli.py --provider openai

# Azure OpenAI (requires all four env vars — see Configuration below)
python ai-projects/chat-cli/src/chat_cli.py --provider azure
```

Interactive session commands: `/new`, `/save`, `/exit`.

### 3 — Start the Azure Functions API host

```bash
func host start
# Endpoints: /api/chat, /api/chat-web, /api/tts, /api/quantum/*, /api/ai/status
curl http://localhost:7071/api/ai/status | python -m json.tool   # health check
```

---

## 🏗️ Project Structure

```
apps/aria/          Animated character stage (HTML/CSS/JS + Python API server)
apps/chat/          Browser-based streaming chat UI
ai-projects/chat-cli/ Multi-provider chat CLI
ai-projects/quantum-ml/ Quantum ML platform (circuits, MCP server, Azure Quantum)
ai-projects/llm-maker/ Autonomous tool-creation system
ai-projects/cooking-ai/ Cooking-focused AI assistant
AI/                 LoRA fine-tuning workspace (Phi / TinyLlama)
shared/             Shared Python modules (providers, DB, telemetry, Cosmos)
scripts/            Orchestration, training, evaluation, and utility scripts
config/             YAML configs for orchestrators
datasets/           Read-only training datasets
data_out/           All generated outputs (git-ignored)
function_app.py     Azure Functions entry point (all /api/* endpoints)
```

---

## 🎭 Aria Character

The Aria character runs at `http://localhost:8080` (or the [GitHub Pages demo](https://bryan-roe.github.io/Aria)).

**Natural language commands (examples):**

| Command | Effect |
| --- | --- |
| `move left` / `move right` | Walk to stage edge |
| `wave` / `dance` / `jump` | Trigger gesture |
| `pick up the ball` | Pick up a nearby object |
| `throw the ball` | Throw held object with physics |
| `say hello` | Aria speaks the text aloud via TTS |

The auto-execute system parses complex multi-step requests ("walk to the table and pick up the apple") into a structured sequence of 8 core actions: `move`, `say`, `pickup`, `drop`, `throw`, `gesture`, `look`, `wait`.

**Aria web server API (port 8080):**

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/aria/state` | Current stage state (position, objects, expressions) |
| `POST` | `/api/aria/command` | Process a natural language command |
| `POST` | `/api/aria/execute` | Auto-execute an action sequence |
| `POST` | `/api/aria/object` | Add / update / remove an object |
| `POST` | `/api/aria/world` | Generate a themed world via LLM |

---

## 💬 Chat Providers

Provider auto-detection order:

```
LM Studio → Ollama → Azure OpenAI → OpenAI → Local (zero-dependency echo)
```

Pass `--provider` to override: `local`, `openai`, `azure`, `lmstudio`, `ollama`, `lora`, `quantum`, `agi`.

**Azure OpenAI** — all four variables required:

```
AZURE_OPENAI_API_KEY
AZURE_OPENAI_ENDPOINT
AZURE_OPENAI_DEPLOYMENT
AZURE_OPENAI_API_VERSION
```

**LoRA adapter** — adapter directory must contain:

```
adapter_config.json
adapter_model.safetensors
```

```bash
python ai-projects/chat-cli/src/chat_cli.py --provider lora --model data_out/lora_training/lora_adapter
```

All providers implement `BaseChatProvider.complete(messages, stream)`. Add a new provider by subclassing `BaseChatProvider` in `shared/chat_providers.py`.

---

## ⚛️ Quantum ML (Experimental)

Local Qiskit Aer simulation is free and unlimited. Azure simulator backends are also free. Real QPU hardware is billed per gate-shot — always simulate first.

**Workflow:** Test locally → Validate on Azure simulator → Run on QPU (set `azure_confirm_cost: true` in YAML first)

```bash
# Validate config without running anything
python scripts/quantum_autorun.py --dry-run

# Interactive training dashboard
cd ai-projects/quantum-ml && ./start_dashboard.sh   # http://localhost:5000

# Start the MCP server (8 quantum tools)
python ai-projects/quantum-ml/quantum_mcp_server.py
```

**MCP tools:** `create_quantum_circuit`, `simulate_quantum_circuit`, `get_quantum_circuit_properties`, `connect_azure_quantum`, `list_quantum_backends`, `submit_quantum_job`, `estimate_quantum_cost`, `train_quantum_classifier`.

---

## 🧠 LoRA Fine-Tuning

Train a small model on Aria-specific datasets using LoRA adapters.

```bash
# Quick training run (TinyLlama, CPU-friendly, ~10–15 s)
python scripts/automated_training_pipeline.py --models tinyllama --quick

# Full train → evaluate → auto-promote best checkpoint
python scripts/train_and_promote.py --quick --auto-promote

# Validate configs without running
python scripts/autotrain.py --dry-run
```

Training datasets are in `datasets/chat/aria_movement/`, `aria_expanded/`, and `aria_simple/` (read-only).
Outputs are written to `data_out/lora_training/`.

---

## 🤖 Autonomous Training

A background orchestrator continuously discovers datasets, trains, and evaluates models on a 30-minute cycle.

```bash
# Start the autonomous loop (runs indefinitely)
nohup python scripts/autonomous_training_orchestrator.py > data_out/autonomous_training.log 2>&1 &

# Check live status
cat data_out/autonomous_training_status.json | python -m json.tool
tail -f data_out/autonomous_training.log
```

---

## 🔧 LLM Tool Maker

An autonomous system where an LLM generates, validates, and sandboxes Python tools at runtime.

```bash
cd llm-maker
python examples/quick_start.py        # create a tool from a description
python llm_maker_mcp_server.py        # expose tools via MCP
```

Security: no dangerous imports, no filesystem or network access, no `eval`/`exec`, sandboxed execution with resource limits.

---

## 🧪 Testing

```bash
# Fast unit tests (~0.5 s, no external services)
python scripts/test_runner.py --unit

# All fast tests (unit + integration, ~10 s)
python scripts/test_runner.py --all

# With coverage report
python scripts/test_runner.py --all --coverage

# One-command integration contract gate (local)
bash ./scripts/integration_contract_gate.sh

# Strict gate (requires local Functions host at :7071)
bash ./scripts/integration_contract_gate.sh --strict-endpoints

# Direct pytest
pytest -m "not slow and not azure" tests/
```

VS Code users: open the Test Explorer (🧪 beaker icon) for interactive test running and debugging.

---

## 🌐 Live Demo

**[https://bryan-roe.github.io/Aria](https://bryan-roe.github.io/Aria)**

The demo runs in mock mode with simulated API responses — no API keys needed. For full AI capabilities, run the project locally.

---

## 🔒 Configuration & Secrets

Copy the example files to get started:

```bash
cp .env.example .env
cp local.settings.json.example local.settings.json
# Fill in API keys as needed
```

Never commit secrets. All keys belong in environment variables or `local.settings.json` (development only).

**Optional services** (feature-flagged — safe to leave unset):

| Service | How to enable |
| --- | --- |
| SQL persistence | `QAI_DB_CONN` env var (SQLite, PostgreSQL, or Azure SQL) |
| Cosmos DB | `QAI_ENABLE_COSMOS=true` + `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`, `COSMOS_CONTAINER` |
| Application Insights | `APPLICATIONINSIGHTS_CONNECTION_STRING` |
| Azure Speech TTS | `AZURE_SPEECH_KEY` + `AZURE_SPEECH_REGION` |
| Local TTS fallback | `QAI_ENABLE_LOCAL_TTS=true` (uses pyttsx3 or gTTS when Azure credentials are absent) |

---

## 📚 Documentation

| Document | Purpose |
| --- | --- |
| [apps/aria/README.md](apps/aria/README.md) | Character stage API reference |
| [ai-projects/quantum-ml/README.md](ai-projects/quantum-ml/README.md) | Quantum ML platform guide |
| [ai-projects/chat-cli/README.md](ai-projects/chat-cli/README.md) | Chat CLI reference |
| [ai-projects/llm-maker/README.md](ai-projects/llm-maker/README.md) | Tool maker guide |
| [docs/aria/](docs/aria/) | Aria movement & training documentation |
| [MONETIZATION_GUIDE.md](MONETIZATION_GUIDE.md) | Subscription and revenue system |
| [docs/guides/REPO_AUTOMATION_GUIDE.md](docs/guides/REPO_AUTOMATION_GUIDE.md) | Full repository automation reference |
| [QUANTUM_LLM_TRAINING.md](QUANTUM_LLM_TRAINING.md) | Quantum-LLM concurrent training |

---

## 🤝 Contributing

- Update `README.md` when adding configuration options, changing CLI flags, introducing new providers, or modifying cost behaviour.
- All output files go under `data_out/` (git-ignored). Never modify files under `datasets/`.
- Always run `--dry-run` on orchestrators before executing GPU or QPU workloads.

---

## 📄 License

See individual project directories for license information.

## PLAN (pseudocode)

## 1) Validate OPENAI_API_KEY

## 2) Read prompt from CLI args or stdin

## 3) Call OpenAI Responses API

## 4) Extract text safely from response.output_text with fallback parsing

## 5) Print final text; fail gracefully on errors

import os
import sys
from openai import OpenAI

MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = "You are a concise AI coding assistant. Return practical code-focused responses."

def _extract_text(resp) -> str:
    if getattr(resp, "output_text", None):
        return resp.output_text.strip()

    parts = []
    for item in getattr(resp, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if getattr(content, "type", "") == "output_text":
                text = getattr(content, "text", "")
                if text:
                    parts.append(text)
    return "\n".join(parts).strip()

def ask_ai(client: OpenAI, prompt: str) -> str:
    resp = client.responses.create(
        model=MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return _extract_text(resp)

def main() -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY environment variable.")

    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        prompt = input("Prompt: ").strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty.")

    client = OpenAI(api_key=api_key)

    try:
        output = ask_ai(client, prompt)
        print(output or "(No text returned.)")
    except Exception as exc:
        print(f"AI request failed: {exc}", file=sys.stderr)
        sys.exit(1)

if **name** == "**main**":
    main()
