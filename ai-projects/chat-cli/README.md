# Talk-to-AI (CLI)

A lightweight, local-first chat app you can talk to from your terminal. It works out-of-the-box with a local fallback (no API keys needed), and can optionally connect to LM Studio, Ollama, OpenAI, or Azure OpenAI.

## Features

- Interactive terminal chat with message history
- Streaming responses (when using OpenAI-compatible providers)
- Local fallback provider (no internet or keys required)
- Auto-selects provider in this order: LM Studio -> Ollama -> Azure OpenAI -> OpenAI -> Local
- Saves conversations to `logs/*.jsonl`
- One-shot mode for quick prompts
- **AGI Provider** with advanced reasoning capabilities

## AGI Provider (Advanced Reasoning)

The AGI provider adds advanced reasoning capabilities to Aria:

### Capabilities

- **Chain-of-Thought Reasoning**: Breaks down complex queries into logical steps
- **Task Decomposition**: Identifies sub-goals for complex tasks
- **Self-Reflection**: Evaluates and improves responses before delivery
- **Context Management**: Maintains relevant memory across interactions
- **Aria Movement Integration**: Automatic movement tag generation

### Quick Start

```powershell
# Use AGI provider (wraps best available underlying provider)
python .\ai-projects\chat-cli\src\chat_cli.py --provider agi --once "Explain quantum computing step by step"

# Interactive AGI chat
python .\ai-projects\chat-cli\src\chat_cli.py --provider agi

# Verbose mode (shows reasoning steps)
$env:AGI_VERBOSE = "true"
python .\ai-projects\chat-cli\src\chat_cli.py --provider agi
```

### How It Works

The AGI provider wraps an underlying provider (LM Studio, Ollama, Azure OpenAI, OpenAI, or Local) and enhances responses through:

1. **Query Analysis**: Determines complexity, intent, and domain
2. **Task Decomposition**: Breaks complex queries into manageable subtasks
3. **Chain-of-Thought**: Generates step-by-step reasoning
4. **Response Generation**: Produces enhanced responses with context
5. **Self-Reflection**: Evaluates and improves the response

### Aria Movement Commands

When using AGI with Aria movement requests, the provider automatically generates movement tags:

```powershell
python .\ai-projects\chat-cli\src\chat_cli.py --provider agi --once "Move Aria left"
# Response: I'll move to the left! [aria:walk:left]
```

## Quick start (no keys required)

Run a single-turn chat using the built-in local provider:

```powershell
# From the repo root
python .\ai-projects\chat-cli\src\chat_cli.py --provider local --once "Hello there!"
```

Start continuous autonomous chat (local fallback, default behavior):

```powershell
python .\ai-projects\chat-cli\src\chat_cli.py --provider local
```

Force interactive stdin mode if you want to type messages manually:

```powershell
python .\ai-projects\chat-cli\src\chat_cli.py --provider local --interactive
```

## Use with OpenAI

Set your API key and pick a model, then run the chat. Example:

```powershell
$env:OPENAI_API_KEY = "<your-openai-api-key>"
$env:OPENAI_MODEL = "gpt-4o-mini"  # or another available chat model
python .\ai-projects\chat-cli\src\chat_cli.py
```

The app will automatically use OpenAI when `OPENAI_API_KEY` is present. You can force it:

```powershell
python .\ai-projects\chat-cli\src\chat_cli.py --provider openai
```

## Use with LM Studio

Required environment variables (defaults shown):

- `LMSTUDIO_BASE_URL` (default `http://127.0.0.1:1234/v1`)
- `LMSTUDIO_MODEL` (default `local-model`)

Optional authentication variables (for LM Studio servers with API token enabled):

- `LM_API_TOKEN` (preferred)
- `LMSTUDIO_API_KEY` (legacy compatibility)

Example:

```powershell
$env:LMSTUDIO_BASE_URL = "http://127.0.0.1:1234/v1"
$env:LMSTUDIO_MODEL = "qwen2.5-coder-7b-instruct"
$env:LM_API_TOKEN = "<your-lmstudio-token>"   # only if your LM Studio server requires auth
python .\ai-projects\chat-cli\src\chat_cli.py --provider lmstudio
```

## Use with Ollama

Required environment variables (defaults shown):

- `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434/v1`)
- `OLLAMA_MODEL` (default `llama2`)

Example:

```powershell
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434/v1"
$env:OLLAMA_MODEL = "llama3.2"
python .\ai-projects\chat-cli\src\chat_cli.py --provider ollama
```

## Use with Azure OpenAI

Required environment variables:

- `AZURE_OPENAI_API_KEY` – your Azure OpenAI key
- `AZURE_OPENAI_ENDPOINT` – e.g. `https://<your-resource>.openai.azure.com/`
- `AZURE_OPENAI_DEPLOYMENT` – the deployment name of your chat model
- `AZURE_OPENAI_API_VERSION` – e.g. `2024-08-01-preview`

Example:

```powershell
$env:AZURE_OPENAI_API_KEY = "<your-azure-key>"
$env:AZURE_OPENAI_ENDPOINT = "https://my-aoai.openai.azure.com/"
$env:AZURE_OPENAI_DEPLOYMENT = "gpt-4o-mini"
$env:AZURE_OPENAI_API_VERSION = "2024-08-01-preview"
python .\ai-projects\chat-cli\src\chat_cli.py --provider azure
```

## Usage

Basic default launch:

```powershell
python .\ai-projects\chat-cli\src\chat_cli.py
```

Useful flags:

- `--provider [auto|openai|azure|local|agi|quantum|lmstudio|ollama|lora]` – default: `auto`
- `--system "..."` – set a custom system prompt
- `--model <name>` – override model/deployment name (provider-specific)
- `--once "message"` – run one message and exit
- `--interactive` – use stdin-driven chat instead of the default autonomous loop
- `--autonomous` – run unattended continuous chat without prompting for stdin
- `--auto-seed "..."` – initial autonomous user message
- `--auto-followup "..."` – follow-up message reused after each autonomous turn
- `--auto-delay <seconds>` – pause between autonomous turns
- `--max-turns <n>` – cap autonomous turns for testing; omit to run forever

In interactive mode, commands:

- `/new` – start a new conversation
- `/save` – save current conversation to `logs/`
- `/exit` – quit

Autonomous mode is now the default. It uses a seed prompt for the first turn, then keeps sending a reusable follow-up prompt so the provider can continue without asking you for input. Stop it with `Ctrl+C`. Use `--interactive` to bring back manual stdin chat.

## Install dependencies

This project only needs a couple of small packages. If you prefer to install them manually:

```powershell
pip install -r .\ai-projects\chat-cli\requirements.txt
```

## Notes

- The local provider is simple and meant for offline testing; for best results, use OpenAI or Azure OpenAI.
- Conversations are stored in JSONL under `ai-projects/chat-cli/logs/`.
