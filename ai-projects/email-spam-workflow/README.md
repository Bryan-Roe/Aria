# Email Spam Workflow

Three-node email spam classification workflow built with Microsoft Agent Framework (Python).

## Workflow

```text
Raw email
   |
   v
SpamClassifier
   |-- SPAM -----> SpamConfirmation
   |
   '-- NOT_SPAM -> RawEmailDisplay
```

1. `SpamClassifier` uses an LLM to inspect the raw email for spam patterns and emits exactly `SPAM` or `NOT_SPAM`.
2. Conditional edges in `WorkflowBuilder` route the result.
3. `SpamConfirmation` returns a fixed confirmation when spam is detected.
4. `RawEmailDisplay` returns the original email body verbatim when the message is not spam.

## Setup

```bash
cd ai-projects/email-spam-workflow
/workspaces/Aria/.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with:

```env
AZURE_AI_PROJECT_ENDPOINT=<your-foundry-project-endpoint>
FOUNDRY_MODEL_DEPLOYMENT_NAME=<your-chat-model-deployment>
```

`gpt-oss-120b` is the recommended default deployment for this workflow in the current AI-1424 resource because it is the available GPT-family model there.

## Run

HTTP server mode for Agent Inspector:

```bash
/workspaces/Aria/.venv/bin/python main.py --server
```

CLI mode:

```bash
/workspaces/Aria/.venv/bin/python main.py --cli --email "Subject: Hello\n\nChecking in about tomorrow's meeting."
```

## Debugging with Agent Inspector

Open the repo in VS Code and use either:

- `Debug Email Spam Workflow HTTP Server` from the repo root debug list
- `Debug Email Spam Workflow HTTP Server` from this folder's local `.vscode/launch.json`

Both launch paths start `agentdev`, attach `debugpy`, and open AI Toolkit Agent Inspector on the configured port.

## Deploying to Foundry

This folder now includes the standard hosted-agent deployment artifacts:

- `agent.yaml` for Foundry-hosted agent metadata
- `Dockerfile` for container builds
- `docker-compose.yml` for local container smoke checks

Once Azure authentication is available, you can deploy this workflow as a hosted agent from the Foundry Toolkit or Foundry deployment flow using the files in this directory.
