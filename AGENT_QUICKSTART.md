# 🤖 Autonomous Code Agent System

A **local LLM-based code agent** that autonomously works on repository tasks using Ollama or LM Studio. No cloud APIs required.

## Why This Matters

Instead of:
```
1. Issue description
2. Manual code review
3. Edit files
4. Run tests
5. Commit
6. Create PR
```

With the autonomous agent:
```
python scripts/autonomous_code_agent.py --task "Your task"
```

The agent handles: planning, file identification, implementation, testing, and committing.

## 30-Second Setup

### 1. Install Local LLM (Pick One)

**Ollama (Recommended - Fastest Setup)**
```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh
ollama pull mistral

# Windows / other
# Download from https://ollama.ai
```

**OR LM Studio**
```bash
# Download from https://lmstudio.ai
# Launch app → Download Model → Developer Tab → Start Server
```

### 2. Run Agent

```bash
python scripts/autonomous_code_agent.py \
  --task "Add docstrings to chat_providers.py" \
  --llm-type ollama \
  --dry-run  # Analyze only, don't modify files
```

### 3. Check Results

```bash
cat data_out/autonomous_agent/status.json | python -m json.tool
tail -f data_out/autonomous_agent/agent.log
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│        User Task Description                        │
│  "Fix failing quantum_autorun tests"                │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │   CodeAgent.execute()   │
        └────────────┬────────────┘
                     │
     ┌───────────────┼───────────────┐
     │               │               │
     ▼               ▼               ▼
 ┌───────┐     ┌─────────┐    ┌──────────┐
 │ PLAN  │────▶│ IDENTIFY│───▶│IMPLEMENT │
 │ (LLM) │     │ (LLM)   │    │ (Code)   │
 └───────┘     └─────────┘    └──────┬───┘
                                     │
                     ┌───────────────┼───────────────┐
                     │               │               │
                     ▼               ▼               ▼
                 ┌───────┐       ┌────────┐   ┌──────────────┐
                 │ TEST  │◀──────│  GIT   │   │ Save Status  │
                 │ (Py)  │       │(commit)│   │ (JSON)       │
                 └───────┘       └────────┘   └──────────────┘
```

## How It Works

### Phase 1: Planning
Uses local LLM to understand task and create structured plan
```
Input: "Fix the auth system to handle JWT tokens"
Output:
  - Goal: Implement JWT authentication
  - Files: shared/auth.py, tests/test_auth.py, function_app.py
  - Steps: [1. Add JWT parsing, 2. Add token validation, 3. Add tests, ...]
```

### Phase 2: File Identification
Uses local LLM to identify relevant files in repo
```
Input: Task description
Output: [chat_providers.py, tests/test_chat_*.py, shared/...]
```

### Phase 3: Implementation
(In real mode) Makes code changes based on plan
```
- Reads relevant files
- Applies code changes
- Validates syntax
- (In dry-run: skipped)
```

### Phase 4: Testing
Runs test suite to validate changes
```
python scripts/test_runner.py --unit
→ Success: changes are good
→ Failure: agent reports error
```

### Phase 5: Committing
If tests pass, commits to git with meaningful message
```
git commit -m "Task {id}: {description}"
```

## Commands

### Quick Test (No LLM Required)
```bash
# Uses built-in echo mode for testing
python scripts/test_autonomous_agent.py
```

### With Ollama
```bash
# Start Ollama (in separate terminal)
ollama serve

# Run agent
python scripts/autonomous_code_agent.py \
  --task "Your task description" \
  --llm-type ollama \
  --dry-run
```

### With LM Studio
```bash
# Start LM Studio
# 1. Open app
# 2. Go to Developer tab
# 3. Select model and click "Start Server"

# Run agent
python scripts/autonomous_code_agent.py \
  --task "Your task description" \
  --llm-type lmstudio
```

### Using Shell Launcher
```bash
# Check if LLM is running
bash scripts/agent.sh --check-llm

# Setup instructions
bash scripts/agent.sh --setup-ollama

# Run task
bash scripts/agent.sh --task "Your task" --dry-run
```

## Examples

### 1. Fix Failing Test
```bash
python scripts/autonomous_code_agent.py \
  --task "Fix test_quantum_autorun_unit::test_valid_azure_ionq_provider_flow test in tests/" \
  --llm-type ollama
```

### 2. Add Documentation
```bash
python scripts/autonomous_code_agent.py \
  --task "Add comprehensive docstrings to LocalLLMClient and RepositoryContext classes" \
  --llm-type ollama \
  --dry-run  # Analyze first
```

### 3. Improve Code Quality
```bash
python scripts/autonomous_code_agent.py \
  --task "Refactor chat_providers.py to reduce duplication between OpenAIProvider and AzureOpenAIProvider" \
  --llm-type lmstudio
```

### 4. Add Security Tests
```bash
python scripts/autonomous_code_agent.py \
  --task "Add security validation tests for whitespace-only inputs in quantum_mcp_server.py handlers" \
  --llm-type ollama \
  --dry-run
```

## Status & Monitoring

### Live Status
```bash
# Watch status updates
watch -n 2 'cat data_out/autonomous_agent/status.json | python -m json.tool'

# Or tail logs
tail -f data_out/autonomous_agent/agent.log
```

### Status File Format
```json
{
  "task_id": "20260320_143022",
  "task_description": "Add docstrings...",
  "status": "complete",
  "llm_type": "ollama",
  "files_modified": ["chat_providers.py"],
  "tests_run": 42,
  "tests_passed": 42,
  "tests_failed": 0,
  "reasoning": "...",
  "commits": ["abc123"],
  "errors": [],
  "started_at": "2026-03-20T14:30:22",
  "updated_at": "2026-03-20T14:32:15"
}
```

## Configuration

### Environment Variables
```bash
# Ollama
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_MODEL="mistral"

# LM Studio
export LMSTUDIO_BASE_URL="http://127.0.0.1:1234/v1"
export LMSTUDIO_MODEL="local-model"
```

### Customize in Code
Edit [autonomous_code_agent.py](./scripts/autonomous_code_agent.py):
```python
MAX_FILE_SIZE = 100_000              # Max bytes to read
MAX_CHANGES_PER_FILE = 5             # File modification limit
MAX_TASK_TOKENS = 2000               # Planning token budget
MIN_TEST_PASSING_RATE = 0.8          # 80% tests must pass
```

## Features

✅ **Autonomous Planning** - LLM understands task and creates plan
✅ **Smart File ID** - Identifies relevant files without hardcoding
✅ **Safety Validated** - Tests must pass before committing
✅ **Git Integration** - Automatic commits with meaningful messages
✅ **Dry-Run Mode** - Analyze without modifying files
✅ **Local Only** - No cloud API calls needed
✅ **Task Categories** - Specialized prompts for bug fixes, features, tests, etc.
✅ **Progress Tracking** - JSON status updates and detailed logs
✅ **Error Recovery** - Graceful handling of failures

## Supported Task Types

| Category | Example | Risk |
| ---------- | --------- | ------ |
| Bug Fix | "Fix failing test_chat.py" | Medium |
| Feature | "Add OAuth2 support" | High |
| Refactor | "Extract common code to utility" | Medium |
| Test | "Add unit tests for edge cases" | Low |
| Security | "Validate user inputs" | High |
| Documentation | "Add docstrings to module" | Low |
| Performance | "Optimize database queries" | Medium |
| Cleanup | "Remove unused imports" | Low |

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if running
ps aux | grep ollama

# Start it
ollama serve

# Verify
curl http://127.0.0.1:11434/api/tags
```

### "Cannot connect to LM Studio"
```bash
# Verify server is running in app
curl http://127.0.0.1:1234/v1/models

# If not, open LM Studio and start server in Developer tab
```

### Agent Getting Stuck
```bash
# Kill the process
pkill -f autonomous_code_agent

# Check logs
tail -100 data_out/autonomous_agent/agent.log
```

### Out of Memory
- Use smaller model (mistral is recommended)
- Reduce context window in settings
- Kill other apps to free RAM

## Files & Structure

```
scripts/
  autonomous_code_agent.py        # Main agent implementation (600+ lines)
  autonomous_agent_tasks.py       # Task definitions and prompts
  agent.sh                         # Shell launcher wrapper
  test_autonomous_agent.py        # Test suite

AUTONOMOUS_AGENT_GUIDE.md         # Detailed guide with examples
data_out/autonomous_agent/
  status.json                      # Task status and results
  agent.log                        # Detailed execution logs
```

## Advanced Usage

### Batch Multiple Tasks
```bash
#!/bin/bash
for task in \
  "Add type hints to shared/chat_memory.py" \
  "Fix error handling in quantum_mcp_server.py" \
  "Add docstrings to scripts/autotrain.py"
do
  python scripts/autonomous_code_agent.py --task "$task" --dry-run
done
```

### Monitor Progress
```bash
# Terminal 1: Run agent
python scripts/autonomous_code_agent.py --task "..."

# Terminal 2: Watch progress
watch -n 1 'tail -5 data_out/autonomous_agent/agent.log'

# Terminal 3: Check results
watch -n 2 'cat data_out/autonomous_agent/status.json | python -m json.tool'
```

### CI/CD Integration
```yaml
# .github/workflows/agent.yml
- name: Run autonomous agent fix
  run: |
    python scripts/autonomous_code_agent.py \
      --task "Fix issues found by linters" \
      --llm-type ollama
```

## Performance

| Model | Speed | Quality | Memory | Recommendation |
| ------- | ------- | --------- | -------- | ----------------- |
| Mistral | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 4GB | **Best for agent** |
| Neural-Chat | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 8GB | Good |
| Llama-7B | ⭐⭐ | ⭐⭐⭐ | 8GB | Slower |
| GPT-4 (cloud) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | N/A | No - uses API |

## Security

- Agent runs with your user permissions
- Code changes validated by tests before committing
- No secrets sent to LLM (LLM runs locally)
- Git credentials use existing git config
- Add `[skip agent]` to commit messages to prevent auto-commits

## Roadmap

- [x] **Phase 1**: Basic agent with planning/identification/testing
- [x] **Phase 2**: Task definition templates (8 categories)
- [ ] **Phase 3**: Multi-agent coordination
- [ ] **Phase 4**: Learning from task history
- [ ] **Phase 5**: Team collaboration features
- [ ] **Phase 6**: GitHub PR integration

## Contributing

Ideas for improvements:
1. Better prompts for specific task types
2. Multi-model fallback (try mistral, then llama, then fail)
3. Parallel testing of different agents
4. Performance metrics collection
5. Automatic prompt optimization

### Note on CLI scripts

When adding or changing Python CLI scripts that may be executed directly (for example via `python scripts/foo.py` or invoked in subprocesses), ensure the repository root is added to `sys.path` before importing local packages. This avoids ModuleNotFoundError when the script is run as a subprocess or from other working directories.

Recommended pattern:

```python
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
  sys.path.insert(0, str(REPO_ROOT))

# Now safe to import local packages, e.g.:
from shared.json_utils import load_status_json
```

## Resources

- **Ollama**: https://ollama.ai
- **LM Studio**: https://lmstudio.ai
- **Models**: https://huggingface.co/models
- **This Repo**: [Aria](https://github.com/Bryan-Roe/Aria)

## FAQ

**Q: Can I use cloud LLMs like GPT-4?**
A: Current version is local-only for privacy. Cloud support planned for Phase 3.

**Q: What if my local LLM runs out of memory?**
A: Use a smaller model (mistral recommended) or reduce context window.

**Q: Can multiple agents work simultaneously?**
A: Yes, each agent gets its own task ID and status file. They don't interfere.

**Q: How do I stop an agent?**
A: `pkill -f autonomous_code_agent` or interrupt with Ctrl+C.

**Q: Can agent commit directly to main branch?**
A: Yes, by default. Protect main branch in GitHub settings for safety.

**Q: Is my code safe?**
A: Changes are validated by tests before committing. Review the plan before running.

---

**Built with ❤️ for the Aria project**

Start building with: `python scripts/autonomous_code_agent.py --task "your idea" --llm-type ollama --dry-run`
