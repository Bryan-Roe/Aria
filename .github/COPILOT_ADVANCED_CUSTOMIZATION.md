# Advanced GitHub Copilot Customization Guide

This guide covers advanced customization of GitHub Copilot Chat for the Aria project, including custom agents, user preferences, local extensions, and advanced workflow automation.

## Table of Contents

- [User-Level Customization](#user-level-customization)
- [Creating Custom Agents](#creating-custom-agents)
- [Custom Skills & Workflows](#custom-skills--workflows)
- [Prompt Engineering](#prompt-engineering)
- [Local Extensions](#local-extensions)
- [Debugging & Development](#debugging--development)
- [Performance Tuning](#performance-tuning)

## User-Level Customization

### Personal Copilot Instructions

Create a personal instruction file for your development preferences:

**Location**: `~/.config/copilot/instructions.md` (Linux/Mac) or `%APPDATA%\GitHub\Copilot\instructions.md` (Windows)

**Example**:
```markdown
# My Development Preferences

## Code Style
- Use type hints for all functions
- Follow PEP 8 strictly
- Prefer f-strings over .format()

## Architecture
- Prefer composition over inheritance
- Use dependency injection
- Prefer async/await over callbacks

## Testing
- Aim for >90% code coverage
- Test edge cases and error paths
- Use pytest for Python testing

## Performance
- Always consider time complexity
- Profile before optimizing
- Document performance-critical sections

## Security
- Validate all inputs
- Never hardcode secrets
- Use parameterized queries
```

### Personal Models Preference

Set your preferred models in VS Code settings:

```json
{
  "chat.mcp.serverSampling": {
    "Aria/.vscode/mcp.json: my-preference": {
      "allowedModels": [
        "copilot/gpt-4o",           // Primary choice
        "copilot/claude-opus-4.6",  // Fallback for reasoning
        "copilot/auto"              // Last resort
      ]
    }
  }
}
```

### Custom Keybindings

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+alt+c",
    "command": "workbench.action.quickOpen",
    "args": "@chat-provider"
  },
  {
    "key": "ctrl+alt+d",
    "command": "workbench.action.quickOpen",
    "args": "@full-stack-debugger"
  },
  {
    "key": "ctrl+alt+t",
    "command": "workbench.action.quickOpen",
    "args": "@task-complete"
  }
]
```

## Creating Custom Agents

### Agent File Structure

Create agents in `.github/agents/`:

```yaml
---
name: my-agent
description: "What this agent does and when to use it"
tools:
  - edit
  - execute/runInTerminal
  - execute/runTests
  - agent
---

# My Custom Agent

You are an expert at [domain].

## Your Capabilities

- [Capability 1]
- [Capability 2]
- [Capability 3]

## Constraints

- [Constraint 1]
- [Constraint 2]

## Decision Tree

When asked to [trigger], [response].
...
```

### Example: Custom Training Agent

Create `.github/agents/custom-training.agent.md`:

```yaml
---
name: custom-training
description: "Specialized training orchestration for custom datasets and models"
tools:
  - edit
  - execute/runInTerminal
  - execute/runTests
  - vscode/memory
---

# Custom Training Agent

You specialize in training optimization for the Aria platform.

## Responsibilities

- Analyze datasets for quality and balance
- recommend training parameters
- Execute training pipelines
- Evaluate model performance
- Suggest optimizations

## Workflow

1. **Dataset Validation** - Check data quality and size
2. **Configuration** - Recommend epochs, learning rate, batch size
3. **Execution** - Run training with progress monitoring
4. **Evaluation** - Test on validation set
5. **Optimization** - Suggest improvements

## Commands You Can Execute

```bash
python scripts/autotrain.py --config custom
python scripts/evaluate_model.py --model latest
python scripts/training_analytics.py --dataset [name]
```

## Decision Rules

- If dataset < 1000 samples: suggest data augmentation
- If loss plateau: suggest learning rate reduction
- If overfitting: suggest dropout or regularization
- If underfitting: suggest more epochs or model capacity
```

### Example: Custom Debugging Agent

Create `.github/agents/custom-debugger.agent.md`:

```yaml
---
name: custom-debugger
description: "Specialized debugging for our specific architecture"
tools:
  - execute/runInTerminal
  - edit
  - execute/runTests
  - read/problems
---

# Custom Debugger

You are specialized in debugging our Aria platform issues.

## Architecture Knowledge

- Aria uses Azure Functions for API backend
- Chat CLI has multi-provider architecture
- Quantum ML integrates with Azure Quantum
- Character system uses CSS animations

## Debugging Approach

1. **Reproducer** - Create minimal test case
2. **Logs** - Check function_app.py, provider logs
3. **State** - Verify system health and status
4. **Isolation** - Test in isolation first
5. **Fix** - Implement minimal fix
6. **Regression** - Run full test suite

## Common Issues & Fixes

### Provider Falls Back to Local
- Check env vars: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
- Test with: `curl http://localhost:7071/api/ai/status`

### Training Accuracy Plateaus
- Check learning rate: may need reduction
- Verify dataset quality: balanced classes?
- Increase model capacity: more layers?

### Aria Commands Not Executing
- Check server is running: `ps aux | grep aria`
- Verify port 8080 is free
- Check action parser: `@aria-character explain what you understand`
```

## Custom Skills & Workflows

### Creating Custom Skills

Create skill workflows in `.github/skills/`:

**Template**: `.github/skills/my-workflow/SKILL.md`

```markdown
# My Custom Workflow

This workflow handles [specific task].

## When to Use

Use this skill when:
- [Condition 1]
- [Condition 2]
- [Condition 3]

## Workflow Steps

### Phase 1: Analysis
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Phase 2: Implementation
1. [Step 1]
2. [Step 2]

### Phase 3: Validation
1. [Step 1]
2. [Step 2]

## Examples

```bash
# Example 1
[Example command or request]

# Example 2
[Example command or request]
```

## Troubleshooting

### Issue: [Common problem]
**Solution**: [How to resolve]

### Issue: [Common problem]
**Solution**: [How to resolve]

## References

- [Link 1]
- [Link 2]
```

### Auto-Loading Skills

Skills load automatically based on file paths. To ensure loading:

1. **Naming convention**: Descriptive, hyphenated names
2. **Placement**: `.github/skills/[workflow-name]/SKILL.md`
3. **Metadata**: Include "When to Use" and trigger phrases
4. **Testing**: Reference in prompts to validate

## Prompt Engineering

### Effective Prompt Patterns

#### Pattern 1: Role Definition
```
You are a [role] specialized in [domain].
Your expertise includes:
- [Expertise 1]
- [Expertise 2]
- [Expertise 3]

When I ask you to [task], you:
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

#### Pattern 2: Constraint-Based
```
[Task description]

Constraints:
- [Constraint 1]
- [Constraint 2]
- [Constraint 3]

Rules:
- [Rule 1]
- [Rule 2]
```

#### Pattern 3: Reasoning with Examples
```
I need you to [task].

Example 1:
- Input: [Example input]
- Output: [Example output]
- Reasoning: [Explanation]

Example 2:
- Input: [Example input]
- Output: [Example output]
- Reasoning: [Explanation]

Now apply this reasoning to: [Your request]
```

### Testing Prompts

Create `.github/prompts/test-my-prompt.md`:

```markdown
# Testing My Prompt

Test cases to validate prompt effectiveness:

## Test 1: Basic Functionality
**Input**: [Test input]
**Expected**: [Expected output]
**Actual**: [Copilot response]
**Pass**: [ ] Yes [ ] No

## Test 2: Edge Cases
**Input**: [Edge case]
**Expected**: [Expected output]
**Actual**: [Copilot response]
**Pass**: [ ] Yes [ ] No

## Test 3: Complex Scenario
**Input**: [Complex request]
**Expected**: [Expected output]
**Actual**: [Copilot response]
**Pass**: [ ] Yes [ ] No
```

## Local Extensions

### Custom Tools Integration

Add custom Python tools available to Copilot:

**Location**: `scripts/copilot_tools/`

**Example**: `scripts/copilot_tools/custom_analyzer.py`

```python
#!/usr/bin/env python3
"""Custom analysis tool for Copilot integration"""

import json
import sys
from pathlib import Path

def analyze_codebase():
    """Analyze codebase structure"""
    result = {
        "total_files": 0,
        "python_files": 0,
        "test_coverage": 0,
        # ... analysis results
    }
    return result

def analyze_performance():
    """Analyze recent performance metrics"""
    result = {
        "avg_response_time": 0.234,
        "model_accuracy": 0.942,
        # ... metrics
    }
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "codebase":
            print(json.dumps(analyze_codebase()))
        elif command == "performance":
            print(json.dumps(analyze_performance()))
```

### Custom Commands in VS Code

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Copilot: Analyze Code Quality",
      "type": "shell",
      "command": "python3 scripts/copilot_tools/custom_analyzer.py codebase",
      "problemMatcher": [],
      "presentation": { "echo": true, "reveal": "always" }
    },
    {
      "label": "Copilot: Check Performance",
      "type": "shell",
      "command": "python3 scripts/copilot_tools/custom_analyzer.py performance",
      "problemMatcher": [],
      "presentation": { "echo": true, "reveal": "always" }
    }
  ]
}
```

## Debugging & Development

### Copilot Chat Logging

Enable detailed logging:

**VS Code Settings**:
```json
{
  "github.copilot.debug": true,
  "debug.console": "integratedTerminal"
}
```

**Check Output**:
1. Open Command Palette: `Ctrl+Shift+P`
2. Type "Focus on Output"
3. Select "GitHub Copilot Chat"

### Developer Console

Access developer tools:

1. Press `Ctrl+Shift+P`
2. Type "Developer: Toggle Developer Tools"
3. Check console for errors and logs

### Testing Agent Responses

Create test prompts in `.github/test-prompts/`:

```markdown
# Testing Custom Agent Response

## Test Request
```
@my-agent Help me [task]
```

## Expected Behavior
- [Behavior 1]
- [Behavior 2]

## Validation
- [ ] Uses correct agent
- [ ] Applies relevant skills
- [ ] Follows constraints
- [ ] Returns valid output
```

## Performance Tuning

### Model Selection

Optimize model choice for different tasks:

```json
{
  "chat.mcp.serverSampling": {
    "quantum-tasks": {
      "allowedModels": ["copilot/gpt-4o"]  // Best for logic
    },
    "creative-tasks": {
      "allowedModels": ["copilot/claude-opus-4.6"]  // Best for creativity
    },
    "fast-responses": {
      "allowedModels": ["copilot/auto"]  // Fastest
    }
  }
}
```

### Memory Optimization

For large projects:

```json
{
  "chat.agent.maxRequests": 100,           // Reduced for memory
  "chat.mcp.serverSampling": {
    "allowedModels": ["copilot/auto"]      // Lighter model
  }
}
```

### Cache Configuration

Enable caching for faster responses:

```json
{
  "github.copilot.cache.enabled": true,
  "github.copilot.cache.ttl": 3600
}
```

### Concurrent Requests

Control parallel operations:

```bash
# Limit concurrent MCP server requests
export COPILOT_MAX_CONCURRENT_REQUESTS=3
```

## Workspace-Level vs User-Level

| Setting | Workspace Level | User Level |
| --------- | --- | --- |
| Location | `.vscode/settings.json` | `~/.vscode/settings.json` |
| Scope | This project only | All projects |
| Override | User settings | Workspace settings |
| Commit | Yes (in git) | No (local only) |

**Best Practice**: Use workspace-level for team settings, user-level for personal preferences.

## Integration with CI/CD

### Pre-Commit Hooks

Validate Copilot configurations:

`.git/hooks/pre-commit`:
```bash
#!/bin/bash

# Validate MCP configuration
python3 -m json.tool .vscode/mcp.json > /dev/null || {
    echo "Error: Invalid MCP configuration"
    exit 1
}

# Validate agent files
for agent in .github/agents/*.agent.md; do
    head -1 "$agent" | grep -q "^---" || {
        echo "Error: Invalid YAML frontmatter in $agent"
        exit 1
    }
done

exit 0
```

## Advanced Examples

### Example 1: Custom Training Prompt

Create `.github/prompts/train-custom.prompt.md`:

```markdown
# Custom Training Execution Prompt

You are executing a training job for the Aria platform.

## Phases

1. **Validation** - Ensure config is correct
2. **Preparation** - Set up environment, download data
3. **Training** - Run training with monitoring
4. **Evaluation** - Test and report metrics
5. **Promotion** - Move model to production (if ready)

## Safety Checks

- [ ] Verify all credentials are set
- [ ] Confirm dataset is available
- [ ] Check disk space is sufficient
- [ ] Validate model architecture

## Reporting

After completion, provide:
- Final metrics (accuracy, loss, etc.)
- Training time
- GPU memory used
- Recommendations for next iteration
```

### Example 2: Custom Architecture Agent

Create `.github/agents/custom-architect.agent.md`:

```yaml
---
name: custom-architect
description: "Custom architecture design for our platform"
tools:
  - edit
  - vscode/memory
  - agent
---

# Custom Architect

You design system architectures for Aria.

## Architecture Principles

1. **Modularity** - Independent, testable components
2. **Scalability** - Handle growth without redesign
3. **Resilience** - Graceful degradation
4. **Observability** - Comprehensive monitoring
5. **Security** - Defense in depth

## Component Model

Design using these components:
- Microservices (function-based)
- Data pipelines (batch and streaming)
- ML models (training and inference)
- Frontend (real-time, responsive)
- Infrastructure (cloud-native)

## Validation Checklist

- [ ] Single responsibility principle
- [ ] Clear interfaces between components
- [ ] Testability at all levels
- [ ] Documented assumptions
- [ ] Scalability analyzed
```

## Troubleshooting

### Custom Agent Not Appearing

1. Verify file location: `.github/agents/[name].agent.md`
2. Check YAML syntax: Run through YAML validator
3. Verify agent is listed in copilot-instructions.md
4. Reload VS Code: `Ctrl+Shift+P` → "Reload Window"

### Custom Skill Not Loading

1. Check location: `.github/skills/[name]/SKILL.md`
2. Verify file paths match in instructions
3. Check for syntax errors in markdown
4. Ensure proper heading structure

### Performance Issues

1. Reduce `chat.agent.maxRequests` (current: 200)
2. Use simpler prompts (shorter context)
3. Close unused VS Code windows
4. Monitor memory: `free -h` (Linux) or Task Manager (Windows)

---

**Happy customizing! Remember to validate configurations before publishing.**
