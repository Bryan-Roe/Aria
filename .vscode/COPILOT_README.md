# 🚀 Welcome to Aria with GitHub Copilot

GitHub Copilot is fully integrated into this workspace. Here's how to get started:

## 1 minute setup

```bash
# Just open the project - VS Code will prompt to install recommended extensions
code .

# Extensions will install automatically
# (If not, Ctrl+Shift+X → "Show Recommended" → Install All)
```

## Open Copilot Chat

Press **`Ctrl+Shift+I`** (or **`Cmd+Shift+I`** on Mac)

## Pick an Agent

Use `@` to select one:

- **`@ai`** — Primary agent (auto-routes to specialists)
- **`@aria-character`** — Control the interactive character
- **`@autonomous-trainer`** — AI model training & lifecycle
- **`@full-stack-debugger`** — Debug issues across the stack
- **`@quantum-ai`** — Quantum circuits & Azure Quantum
- **`@chat-provider`** — Multi-provider chat integration

## Examples

Try these in Copilot Chat:

```
@aria-character Make Aria walk to the table and pick up the sphere

@autonomous-trainer Start training the next LoRA model

@full-stack-debugger Why is the /api/chat endpoint returning 500?

@AI_model_training Evaluate the latest model against the test dataset
```

## Where to Learn More

- **Full Setup Guide**: `.github/COPILOT_SETUP_GUIDE.md`
- **Quick Reference**: `.github/copilot-instructions.md`
- **Detailed Patterns**: `.github/copilot-instructions.full.md`
- **Component Guides**: `.github/instructions/`

## MCP Tools (Direct Integration)

Ask Copilot to use these specialized servers:

- **`@quantum-ai`** — Quantum circuit design & simulation
- **`@llm-maker`** — Safe code & website generation
- **`@task-complete`** — Task tracking

## Quick Commands

Right in VS Code terminal:

```bash
# Validate setup
python3 scripts/pre_commit_check.py

# Run tests (Copilot can help fix failures!)
python3 scripts/test_runner.py --unit

# Start Aria character interface
cd apps/aria && python server.py

# Health check
curl http://localhost:7071/api/ai/status | jq
```

## Pro Tips

1. **Use agents for specialization** — Pick the most relevant agent for better results
2. **Provide context** — More details = better solutions
3. **Review code** — Ask Copilot to review your changes ('@github.copilot review my code')
4. **Use skills** — They load automatically based on context

## Troubleshooting

- **Chat not showing?** → Install GitHub Copilot Chat extension
- **Agents missing?** → Reload VS Code (Ctrl+Shift+P → "Reload Window")
- **MCP tools unavailable?** → Check `.vscode/mcp.json` is valid

---

**Ready to build with Copilot? Open Chat with Ctrl+Shift+I and type `@ai help me get started with Aria`. 🎉**
