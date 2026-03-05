## Run it now

From repo root (`/home/bryan/Aria/Aria`), with your `.venv` active:

python tools/talk-to-ai/src/chat_cli.py --provider lmstudio

If your model in LM Studio has a specific name:

python tools/talk-to-ai/src/chat_cli.py --provider lmstudio --model "your-model-name"

Then type at the `you>` prompt and chat.
Exit with:

/exit

## If LM Studio isn’t running yet

Use the built-in local fallback:

python tools/talk-to-ai/src/chat_cli.py --provider local

## Quick health check (optional)

curl -s http://127.0.0.1:1234/v1/models

If that returns models, LM Studio is reachable.

## Notes for refinement

- Primary target: real custom local model via LM Studio provider.
- Safe fallback: local provider with no external dependencies.
- Keep terminal-first workflow and minimal setup friction.
