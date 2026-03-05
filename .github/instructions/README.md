# Instructions Index

This folder contains path-scoped instruction modules for Copilot agents.
Use this page as a quick router: find by file path first, then by task.

## Find by file path

- `function_app.py` → `functions.instructions.md`
- `shared/**/*.py` → `shared-python.instructions.md`
- `scripts/**/*.py` → `scripts-orchestrators.instructions.md`
- `tests/**/*.py` → `tests-python.instructions.md`
- `web/aria_web/**/*.py` → `aria-web-python.instructions.md`
- `web/aria_web/**/*.js` → `aria-web-js.instructions.md`
- `web/chat-web/**` → `chat-web.instructions.md`
- `web/chat-web/**/*.js` → `chat-web-js.instructions.md`
- `tools/talk-to-ai/**` → `talk-to-ai.instructions.md`
- `tools/talk-to-ai/src/**/*.py` → `talk-to-ai-python.instructions.md`
- `tools/llm-maker/**` → `llm-maker.instructions.md`
- `quantum/**` → `quantum-ai.instructions.md`
- `quantum/src/**/*.py` → `quantum-ai-python.instructions.md`
- `quantum/quantum_mcp_server.py` → `quantum-ai-mcp-python.instructions.md`
- `quantum/web_ui/**` → `quantum-web-ui.instructions.md`
- `quantum/azure/**` → `quantum-azure.instructions.md`
- `AI/microsoft_phi-silica-3.6_v1/**` → `lora.instructions.md`
- `AI/microsoft_phi-silica-3.6_v1/scripts/**/*.py` → `lora-python.instructions.md`
- `lora/azureml/**` → `lora-azureml.instructions.md`
- `cooking-ai/**/*.py` → `cooking-ai-python.instructions.md`
- `dashboard/**/*.py` → `dashboard-python.instructions.md`
- `dashboard/**/*.js` → `dashboard-js.instructions.md`
- `database/**` → `database-sql.instructions.md`
- `config/**` → `config-yaml.instructions.md`
- `deployed_models/**` → `deployed-models.instructions.md`
- `docs/**/*.md` → `docs-markdown.instructions.md`
- `templates/emails/**` → `templates-emails.instructions.md`
- root monetization pages (`pricing.html`, `checkout.html`, `account.html`, `my-subscription.html`, `subscription-success.html`, `referrals.html`, `monetization-index.html`) → `monetization-html.instructions.md`
- `.github/**/*.md` → `copilot-metadata.instructions.md`, `github-metadata.instructions.md`
- `.github/workflows/**` → `github-workflows.instructions.md`

## Find by task

- API route or readiness diagnostics updates → `functions.instructions.md`
- Shared infra, clients, telemetry, or memory updates → `shared-python.instructions.md`
- Chat frontend SSE/streaming behavior → `chat-web.instructions.md`, `chat-web-js.instructions.md`
- Provider detection or chat CLI behavior → `talk-to-ai.instructions.md`, `talk-to-ai-python.instructions.md`
- Aria runtime state/command behavior → `aria-web-python.instructions.md`, `aria-web-js.instructions.md`
- Orchestrator pipelines and status-driven automation → `scripts-orchestrators.instructions.md`
- Quantum workflows, MCP, Azure Quantum, or UI → `quantum-ai.instructions.md`, `quantum-ai-python.instructions.md`, `quantum-ai-mcp-python.instructions.md`, `quantum-azure.instructions.md`, `quantum-web-ui.instructions.md`
- LoRA training and AzureML jobs → `lora.instructions.md`, `lora-python.instructions.md`, `lora-azureml.instructions.md`
- Dashboard app and monitoring → `dashboard-python.instructions.md`, `dashboard-js.instructions.md`
- SQL/database changes → `database-sql.instructions.md`
- CI/CD workflow updates → `github-workflows.instructions.md`
- Documentation and metadata consistency → `docs-markdown.instructions.md`, `copilot-metadata.instructions.md`, `github-metadata.instructions.md`

## Instruction matrix

| Instruction file | applyTo scope | Use when |
| --- | --- | --- |
| `aria-web-js.instructions.md` | `web/aria_web/**/*.js` | Editing Aria runtime JS behavior/UI command handling |
| `aria-web-python.instructions.md` | `web/aria_web/**/*.py` | Editing Aria runtime Python endpoints/state logic |
| `chat-web-js.instructions.md` | `web/chat-web/**/*.js` | Editing chat-web JS SSE consumer/TTS behavior |
| `chat-web.instructions.md` | `web/chat-web/**` | Editing chat-web integration and stream contracts |
| `config-yaml.instructions.md` | `config/**` | Editing YAML/JSON pipeline configuration |
| `cooking-ai-python.instructions.md` | `cooking-ai/**/*.py` | Editing cooking-ai Python provider/CLI code |
| `copilot-metadata.instructions.md` | `.github/**/*.md` | Authoring prompts/agents/instructions metadata |
| `dashboard-js.instructions.md` | `dashboard/**/*.js` | Editing dashboard JS client/UI helpers |
| `dashboard-python.instructions.md` | `dashboard/**/*.py` | Editing dashboard backend and monitoring scripts |
| `database-sql.instructions.md` | `database/**` | Editing schema, migration, and SQL artifacts |
| `deployed-models.instructions.md` | `deployed_models/**` | Managing model registry/artifact metadata |
| `docs-markdown.instructions.md` | `docs/**/*.md` | Editing docs and pages content |
| `functions.instructions.md` | `**/function_app.py` | Editing Azure Functions routes, SSE, readiness |
| `github-metadata.instructions.md` | `.github/**/*.md` | Keeping `.github` docs/indexes synchronized |
| `github-workflows.instructions.md` | `.github/workflows/**` | Editing GitHub Actions workflow files |
| `llm-maker.instructions.md` | `tools/llm-maker/**` | Editing LLM maker tools and UI |
| `lora-azureml.instructions.md` | `lora/azureml/**` | Editing AzureML LoRA training job configs |
| `lora-python.instructions.md` | `AI/microsoft_phi-silica-3.6_v1/scripts/**/*.py` | Editing LoRA Python scripts |
| `lora.instructions.md` | `AI/microsoft_phi-silica-3.6_v1/**` | Editing LoRA workspace docs/config/layout |
| `monetization-html.instructions.md` | `{pricing,checkout,account,my-subscription,subscription-success,referrals,monetization-index}.html` | Editing monetization/subscription HTML pages |
| `quantum-ai-mcp-python.instructions.md` | `quantum/quantum_mcp_server.py` | Editing quantum MCP server Python behavior |
| `quantum-ai-python.instructions.md` | `quantum/src/**/*.py` | Editing core quantum Python source |
| `quantum-ai.instructions.md` | `quantum/**` | Editing broad quantum workspace assets |
| `quantum-azure.instructions.md` | `quantum/azure/**` | Editing Azure Quantum infra/pipelines/cost files |
| `quantum-web-ui.instructions.md` | `quantum/web_ui/**` | Editing quantum UI/visualization assets |
| `scripts-orchestrators.instructions.md` | `scripts/**/*.py` | Editing status-driven orchestrator scripts |
| `shared-python.instructions.md` | `shared/**/*.py` | Editing shared infra modules |
| `talk-to-ai-python.instructions.md` | `tools/talk-to-ai/src/**/*.py` | Editing provider implementation Python files |
| `talk-to-ai.instructions.md` | `tools/talk-to-ai/**` | Editing broader talk-to-ai workspace assets |
| `templates-emails.instructions.md` | `templates/emails/**` | Editing email templates |
| `tests-python.instructions.md` | `tests/**/*.py` | Editing or adding Python tests |

## Maintenance checklist

- Keep this index synchronized with all files matching `*.instructions.md` in this folder.
- Keep `applyTo` scopes in this document consistent with each instruction file frontmatter.
- Prefer linking to the narrowest applicable module first (path-specific before broad workspace-level).
- Avoid duplicated policy text across modules; centralize shared rules in metadata/governance modules.
