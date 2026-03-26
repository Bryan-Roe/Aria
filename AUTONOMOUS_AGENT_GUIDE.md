# Autonomous Code Agent System

A local LLM-based agent that can autonomously work on repository tasks, including:

- Planning work based on task descriptions
- Identifying affected files
- Running tests to validate changes
- Committing results to git

## Quick Start

### 1. Install Local LLM

Choose one of the following:

#### Option A: Ollama (Recommended - Simple)

```bash
# Download and install from https://ollama.ai
# Or on macOS/Linux with Homebrew:
brew install ollama

# Start Ollama daemon
ollama serve

# In another terminal, pull a model:
ollama pull mistral  # or llama2, neural-chat, etc.
```

#### Option B: LM Studio

```bash
# Download from https://lmstudio.ai
# Launch the app and:
# 1. Download a model (Mistral recommended)
# 2. Go to "Developer" tab
# 3. Select "Local Server" and start it on port 1234
```

### 2. Configure Agent

Set environment variables based on your choice:

**For Ollama:**

```bash
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_MODEL="mistral"  # or llama2, neural-chat, etc.
```

**For LM Studio:**

```bash
export LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
export LMSTUDIO_MODEL="local-model"
```

### 3. Run Agent

```bash
# Dry-run mode (analyze only, don't modify files)
python scripts/autonomous_code_agent.py \
  --task "fix failing tests in test_quantum_mcp_server_security.py" \
  --llm-type ollama \
  --dry-run

# Full mode (makes changes, runs tests, commits if tests pass)
python scripts/autonomous_code_agent.py \
  --task "improve code comments in shared/chat_memory.py" \
  --llm-type ollama

# With custom model
python scripts/autonomous_code_agent.py \
  --task "refactor function_app.py error handling" \
  --llm-type lmstudio \
  --model "llama2"
```

## How It Works

The agent operates in 5 phases:

1. **Planning**: Uses the local LLM to understand the task and create a structured plan
2. **File Identification**: Identifies which files in the repo are relevant to the task
3. **Implementation**: (In production) Makes code changes based on the plan
4. **Testing**: Runs the test suite to validate changes
5. **Committing**: If tests pass, commits changes to git with a meaningful message

## Architecture

### Core Components

- **CodeAgent**: Main orchestrator that runs the 5-phase workflow
- **LocalLLMClient**: HTTP wrapper for Ollama and LM Studio APIs
- **RepositoryContext**: Utilities for reading files, running tests, and git operations
- **AgentState**: Tracks progress and saves status to JSON

### Data Flow

```text
Task Description
    ↓
CodeAgent.execute_task()
    ├─ Plan Phase → Local LLM generates plan
    ├─ Identify Phase → Local LLM identifies files
    ├─ Implement Phase → (dry-run: skip; real: make changes)
    ├─ Test Phase → Run test_runner.py
    └─ Commit Phase → git commit if tests pass
    ↓
AgentState saved to data_out/autonomous_agent/status.json
```

### Safety Gates

- Max file size: 100KB (prevents reading huge files)
- Max changes per file: 5 (prevents massive rewrites)
- Test validation: Must pass before committing
- Git check: Validates git is available before committing
- Dry-run mode: Default is analysis-only until flags are set

## Configuration

### Environment Variables

```bash
# Ollama settings
OLLAMA_BASE_URL="http://127.0.0.1:11434"
OLLAMA_MODEL="mistral"

# LM Studio settings
LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
LMSTUDIO_MODEL="local-model"
```

### Settings in Code

Edit [autonomous_code_agent.py](./scripts/autonomous_code_agent.py):

- `MAX_FILE_SIZE`: Maximum file size to read (default: 100KB)
- `MAX_CHANGES_PER_FILE`: Limit changes per file (default: 5)
- `MAX_TASK_TOKENS`: Max tokens for planning (default: 2000)
- `MIN_TEST_PASSING_RATE`: Required pass rate (default: 0.8)

## Status and Logs

### Status File

Every task is saved to: `data_out/autonomous_agent/status.json`

Example status:

```json
{
  "task_id": "20260320_143022",
  "task_description": "fix failing test",
  "status": "complete",
  "llm_type": "ollama",
  "files_modified": ["tests/test_example.py"],
  "tests_run": 42,
  "tests_passed": 42,
  "tests_failed": 0,
  "reasoning": "...",
  "commits": ["abc123def456"],
  "errors": [],
  "started_at": "2026-03-20T14:30:22",
  "updated_at": "2026-03-20T14:32:15"
}
```

### Logs

Agent logs go to: `data_out/autonomous_agent/agent.log`

View live logs:

```bash
tail -f data_out/autonomous_agent/agent.log
```

## Example Tasks

### 1. Fix a Failing Test

```bash
python scripts/autonomous_code_agent.py \
  --task "Fix the test_submit_job_stale_allowlist_miss_refreshes_once test in test_quantum_mcp_server_security.py" \
  --llm-type ollama \
  --dry-run
```

### 2. Improve Code Quality

```bash
python scripts/autonomous_code_agent.py \
  --task "Add docstrings and type hints to function_app.py" \
  --llm-type ollama \
  --dry-run
```

### 3. Refactor Legacy Code

```bash
python scripts/autonomous_code_agent.py \
  --task "Refactor chat_providers.py to use a factory pattern for provider creation" \
  --llm-type lmstudio
```

### 4. Database Schema Changes

```bash
python scripts/autonomous_code_agent.py \
  --task "Add nullable birthday and phone_number columns to user table, update migrations" \
  --llm-type ollama
```

## Troubleshooting

### "Cannot connect to Ollama"

```text
Error: Cannot connect to Ollama at http://127.0.0.1:11434
```

**Solution:**

```bash
# Check if Ollama is running
ps aux | grep ollama

# If not, start it:
ollama serve

# Verify connectivity:
curl http://127.0.0.1:11434/api/tags
```

### "Cannot connect to LM Studio"

```text
Error: Cannot connect to LM Studio at http://127.0.0.1:1234/v1
```

**Solution:**

1. Open LM Studio
2. Go to "Developer" tab
3. Select a model and click "Start Server"
4. Verify port 1234 is shown

### Agent Getting Stuck

```bash
# Kill the agent process
pkill -f autonomous_code_agent

# Check what went wrong
tail -f data_out/autonomous_agent/agent.log
```

### Out of Memory

If the LLM server runs out of memory:

**For Ollama:**

```bash
# Stop Ollama
killall ollama

# Start with memory limits (adjust as needed)
OLLAMA_MAX_LOADED_MODELS=1 ollama serve
```

**For LM Studio:**

- Use Settings tab to reduce context window
- Load smaller model

## Advanced Usage

### Batch Processing Tasks

```bash
#!/bin/bash
tasks=(
  "add error handling to quantum_autorun.py"
  "add logging to function_app.py"
  "improve test coverage in tests/"
)

for task in "${tasks[@]}"; do
  python scripts/autonomous_code_agent.py --task "$task" --llm-type ollama --dry-run
done
```

### Integration with CI/CD

```bash
# In .github/workflows/auto-agent.yml
- name: Run autonomous code agent
  run: |
    python scripts/autonomous_code_agent.py \
      --task "Fix issues found by pre-commit checks" \
      --llm-type ollama
```

### Monitor Multiple Agents

```bash
python scripts/autonomous_code_agent.py --task "task1" &
python scripts/autonomous_code_agent.py --task "task2" &
python scripts/autonomous_code_agent.py --task "task3" &

# Monitor progress
watch -n 5 'cat data_out/autonomous_agent/status.json | python -m json.tool'
```

## Performance Tips

1. **Use Faster Models**: Mistral and Neural-Chat are fast; Llama-13B is slower
2. **Increase Context Window**: Larger context allows better planning
3. **Run on GPU**: If available, offload to GPU for 5-10x speedup
4. **Batch Tasks**: Run multiple agents in parallel on different tasks

## Security Considerations

- Agent runs as same user that starts it — use appropriate permissions
- Git credentials must be configured (agent uses existing git config)
- No secrets by default — handle carefully if added to prompts
- Code changes are validated by tests before committing
- Review first commit carefully before letting agent run unsupervised

## Next Steps

1. ✅ [Basic Agent](./scripts/autonomous_code_agent.py) — DONE
2. [Advanced Capabilities](./scripts/autonomous_agent_tasks.py) — In progress
   - Specific task types (refactoring, bug fixes, tests)
   - Multi-file coordinated changes
   - Rollback on test failure
3. Agent Learning (planned module)
   - Track success/failure of task types
   - Learn which patterns work
   - Improve prompts based on feedback
4. Team Agents (planned module)
   - Multiple agents coordinating work
   - Task distribution and prioritization
   - Conflict resolution

## See Also

- [Chat Providers](./ai-projects/chat-cli/src/chat_providers.py) — LLM provider implementations
- [Test Runner](./scripts/test_runner.py) — Validation infrastructure
- [Repo Automation](./scripts/repo_automation.py) — Other orchestration examples
- [AGI Provider](./agi_provider.py) — Advanced reasoning system
