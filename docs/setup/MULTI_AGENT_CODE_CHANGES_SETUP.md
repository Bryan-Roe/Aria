# Multi-Agent Mode with Real Code Changes - Setup Guide

## Current Status
- ✅ Multi-agent system: Fully operational
- ✅ Master orchestrator: Running (daemon mode)
- ✅ Consensus engine: Ready
- ✅ Test framework: 1,243+ tests passing
- ❌ Real LLM backend: Not configured
- ❌ Code changes: Currently disabled (echo mode safe)

## Why Code Changes Require a Real LLM

The multi-agent system can only make actual code modifications when connected to a real LLM that understands:
- Code syntax and patterns
- Project structure and conventions
- Safety boundaries and rollback triggers
- Test case generation and validation

**Echo mode** (current) is intentionally safe:
- Zero code files modified
- Tasks run as analysis/audits only
- 100% consensus voting on safety
- Automatic rollback on any test failure

## Setup Options (Pick One)

### Option A: Ollama (RECOMMENDED - Easiest, Free, Local)

**Host Machine Setup** (one-time):
```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama service
ollama serve &

# 3. Pull a model (Mistral recommended for code)
ollama pull mistral
# or
ollama pull neural-chat

# 4. Verify it's running
curl http://localhost:11434/api/tags
```

**Container Execution** (this dev container):
```bash
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --tasks-file data_out/multi_agent_run_tasks.json \
  --workers 5 \
  --llm-type ollama \
  --model mistral \
  --verbose 2>&1 | tee data_out/multi_agent_code_changes.log
```

**Benefits:**
- ✅ Free (no API costs)
- ✅ Runs locally on your machine
- ✅ Full code access (private)
- ✅ Works offline
- ✅ No API credentials needed

---

### Option B: Azure OpenAI (Enterprise)

**Setup:**
```bash
# 1. Edit local.settings.json and add:
{
  "AZURE_OPENAI_API_KEY": "your-key-here",
  "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
  "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
  "AZURE_OPENAI_API_VERSION": "2024-02-15-preview"
}

# 2. Run with Azure
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --tasks-file data_out/multi_agent_run_tasks.json \
  --workers 5 \
  --llm-type azure \
  --verbose 2>&1 | tee data_out/multi_agent_code_changes.log
```

---

### Option C: OpenAI API (Official)

**Setup:**
```bash
# 1. Edit local.settings.json and add:
{
  "OPENAI_API_KEY": "sk-your-key-here"
}

# 2. Run with OpenAI
cd /workspaces/Aria
PYTHONPATH=/workspaces/Aria:/workspaces/Aria/scripts python3 scripts/multi_agent.py \
  --tasks-file data_out/multi_agent_run_tasks.json \
  --workers 5 \
  --llm-type openai \
  --model gpt-4 \
  --verbose 2>&1 | tee data_out/multi_agent_code_changes.log
```

---

## Safety Mechanisms (Always Active)

✅ **Automatic Rollback**
- Any test failure → automatic rollback
- Failed changes are reverted
- Original code preserved

✅ **Consensus Voting**
- All 5 agents vote on each change
- Unanimous agreement required
- Single dissent blocks the change

✅ **Dry-Run Preview**
- Use `--dry-run` flag to preview changes
- See what would change WITHOUT applying it
- Perfect for review before commit

✅ **Test Validation**
- 1,343 tests run per task
- 0 tests fail = change accepted
- Any failure = automatic rollback

## Monitoring Code Changes

```bash
# Watch changes in real-time
tail -f data_out/multi_agent_code_changes.log

# View consensus decisions
cat data_out/multi_agent/latest.json | python3 -m json.tool | grep -A 5 "consensus"

# Check modified files
cd /workspaces/Aria && git diff HEAD

# Review specific changes
git diff HEAD -- shared/chat_memory.py
```

## Audit Tasks That Make Changes

When code changes are enabled, multi-agent will:

1. **Add type hints** to shared/chat_memory.py
2. **Modernize error handling** in shared/chat_providers.py
3. **Add docstrings** to scripts/autonomous_training_orchestrator.py
4. **Improve type safety** in function_app.py
5. **Enhance logging** in apps/aria/server.py
6. **Refactor duplicates** in shared/sql_engine.py
7. **Optimize performance** in shared/chat_memory.py
8. **Add safety gates** to quantum_mcp_server.py
9. **Improve test coverage** across core modules
10. **Harden error handling** in db_logging.py

Each change is:
- Reviewed by 5 agents
- Validated by 1,343 tests
- Consensus-voted on
- Automatically rolled back if tests fail

## Next Steps

1. **Choose an option above** (Ollama recommended)
2. **Complete the setup** on your host machine
3. **Run the multi-agent command** from this container
4. **Monitor progress** with tail or view reports

---

## Questions?

- Check `/workspaces/Aria/scripts/multi_agent.py --help`
- Review audit logs: `cat data_out/multi_agent/*.log`
- Check consensus reports: `cat data_out/multi_agent/latest.json`

**Status:** Ready to make code changes once LLM backend is configured! 🚀
