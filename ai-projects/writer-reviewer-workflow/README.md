# Writer-Reviewer Multi-Agent Workflow

A multi-agent workflow built with **Microsoft Agent Framework** (Python) where a
**Writer** and a **Reviewer** collaborate to create and refine content.

## How It Works

```text
User request
     │
     ▼
┌──────────┐       ┌──────────────┐
│  Writer  │──────▶│   Reviewer   │
│  Agent   │       │    Agent     │
└──────────┘       └──────────────┘
     │                    │
     ▼ AgentResponseUpdate ▼ AgentResponseUpdate (final refined text)
           Workflow Output
```

1. **Writer** receives the user request and drafts the initial content.
2. **Reviewer** receives the Writer's content (full conversation history) and
   delivers a polished, refined final version.
3. Both agents are *output executors* — the workflow yields their responses so
   you can observe the full collaboration. The Reviewer's output is the final
   refined text.

## Prerequisites

- Python **3.10+**
- An **Azure AI Foundry** project with a deployed chat model
  (e.g. `gpt-4o`, `gpt-4o-mini`)
- `az login` (or another credential source for `DefaultAzureCredential`)

> **No deployed model?**
> Open **AI Toolkit** → Model Catalog → deploy a model, then paste its
> deployment name in `.env`.

## Setup

```bash
# 1. Navigate to this directory
cd ai-projects/writer-reviewer-workflow

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
#    NOTE: agent-framework packages are in preview — pin versions to avoid
#    breaking changes.
pip install -r requirements.txt

# 4. Configure environment
#    Edit .env and fill in FOUNDRY_MODEL_DEPLOYMENT_NAME
#    (FOUNDRY_PROJECT_ENDPOINT is already set)
```

## Configuration

Edit `.env`:

```env
AZURE_AI_PROJECT_ENDPOINT=https://AI-1424-resource.services.ai.azure.com/api/projects/AI-1424
FOUNDRY_MODEL_DEPLOYMENT_NAME=<your-deployment-name>
```

## Running

### HTTP Server mode (default — recommended)

```bash
python main.py
# or explicitly:
python main.py --server
```

The server starts on `http://localhost:8000`. Send a POST request with your
message and the workflow streams the Writer → Reviewer collaboration back.

### CLI mode (quick smoke test)

```bash
python main.py --cli --prompt "Write a short post about the benefits of reading."
```

### Prototype monitor mode (local, no model calls)

This repository also includes an **operational prototype** for Python-based
automation that monitors a folder, generates Python code dynamically, and emits
matching pytest tests.

1. Copy or create a JSON request file in `prototype_specs/inbox/`.
2. Run the monitor once or keep it polling.
3. Generated modules, tests, and reports appear under `prototype_specs/generated/`.

```bash
# One-shot processing of the inbox
python main.py --prototype-monitor --prototype-run-once --prototype-run-generated-tests

# Continuous polling every 2 seconds
python main.py --prototype-monitor --prototype-run-generated-tests
```

Example request format:

```json
{
  "module_name": "math_helpers",
  "function_name": "add_numbers",
  "description": "Add two integers and return the sum.",
  "arguments": [
    {"name": "left", "type": "int"},
    {"name": "right", "type": "int"}
  ],
  "return_type": "int",
  "expression": "left + right",
  "examples": [
    {"inputs": {"left": 2, "right": 3}, "output": 5}
  ]
}
```

A ready-to-copy sample lives at `prototype_specs/examples/add_numbers.json`.

## Debugging with VS Code + AI Toolkit Agent Inspector

1. Open this folder in VS Code.
2. Press **F5** → select **"Debug Writer-Reviewer HTTP Server"**.
3. AI Toolkit Agent Inspector opens automatically at `http://localhost:8088`.
4. Type a prompt in the Inspector to see the full multi-agent message flow,
   tool calls, and token usage — all visualised in real time.

> The Inspector is provided by **AI Toolkit** (`agent-dev-cli` + `debugpy`).

## Project Structure

```text
writer-reviewer-workflow/
├── main.py              # Entry point (Foundry modes + local prototype mode)
├── workflow.py          # Workflow definition (Writer & Reviewer agents)
├── prototype_workflow.py# Folder monitor that generates Python code + pytest tests
├── prototype_specs/
│   └── examples/
│       └── add_numbers.json
├── .env                 # Environment config (not committed)
├── requirements.txt     # Pinned dependencies
├── README.md
└── .vscode/
    ├── launch.json      # VS Code debugger configurations
    └── tasks.json       # VS Code task runner configurations
```

## Notes

- Agent Framework packages are in **preview**. Versions are pinned in
  `requirements.txt` to avoid breakage from preview renaming changes.
- `DefaultAzureCredential` is used for auth. Run `az login` locally, or use a
  Managed Identity / Service Principal in production.
- Both agents share the same Foundry model deployment but use **separate
  `AzureAIClient` instances** — the agent name is registered at the client
  level, so a shared client would overwrite the previous agent's identity.
