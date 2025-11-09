# Talk-to-AI (CLI)

A lightweight, local-first chat app you can talk to from your terminal. It works out-of-the-box with a local fallback (no API keys needed), and can optionally connect to OpenAI or Azure OpenAI for higher quality responses.

## Features

- Interactive terminal chat with message history
- Streaming responses (when using OpenAI/Azure OpenAI)
- Local fallback provider (no internet or keys required)
- Auto-selects provider based on available environment variables
- Saves conversations to `logs/*.jsonl`
- One-shot mode for quick prompts

## Quick start (no keys required)

Run a single-turn chat using the built-in local provider:

```powershell
# From the repo root (AI/)
python .\talk-to-ai\src\chat_cli.py --provider local --once "Hello there!"
```

Start an interactive chat (local fallback):

```powershell
python .\talk-to-ai\src\chat_cli.py --provider local
```

## Use with OpenAI

Set your API key and pick a model, then run the chat. Example:

```powershell
$env:OPENAI_API_KEY = "<your-openai-api-key>"
$env:OPENAI_MODEL = "gpt-4o-mini"  # or another available chat model
python .\talk-to-ai\src\chat_cli.py
```

The app will automatically use OpenAI when `OPENAI_API_KEY` is present. You can force it:

```powershell
python .\talk-to-ai\src\chat_cli.py --provider openai
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
python .\talk-to-ai\src\chat_cli.py --provider azure
```

## Usage

Basic interactive chat:

```powershell
python .\talk-to-ai\src\chat_cli.py
```

Useful flags:

- `--provider [auto|openai|azure|local]` – default: `auto`
- `--system "..."` – set a custom system prompt
- `--model <name>` – override model/deployment name (provider-specific)
- `--once "message"` – run one message and exit

In interactive mode, commands:

- `/new` – start a new conversation
- `/save` – save current conversation to `logs/`
- `/exit` – quit

## Install dependencies

This project only needs a couple of small packages. If you prefer to install them manually:

```powershell
pip install -r .\talk-to-ai\requirements.txt
```

## Notes

- The local provider is simple and meant for offline testing; for best results, use OpenAI or Azure OpenAI.
- Conversations are stored in JSONL under `talk-to-ai/logs/`.
