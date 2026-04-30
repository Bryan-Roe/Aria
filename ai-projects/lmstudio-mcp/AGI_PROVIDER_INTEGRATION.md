# LM Studio + AGI Provider Integration Guide

## Overview

The **AGI Provider** in Aria is a multi-agent reasoning system that:
- Analyzes queries to determine intent and domain
- Routes to specialized agents
- Performs task decomposition and reasoning chains
- Provides self-reflection and improvement

**LM Studio** can now seamlessly integrate as a specialized agent within this system, handling technical, coding, and AI domains with fast local inference.

## Architecture

```
User Query
    ↓
[AGI Provider Analysis]
  • Intent analysis
  • Domain classification
  • Complexity assessment
    ↓
[Agent Router]
  • Check LM Studio health
  • Analyze query suitability
  • Route to appropriate agent
    ↓
[LM Studio Agent] ← Fast, private, local
OR
[Other Agents]   ← Quantum, Code, etc.
    ↓
[Chain-of-Thought Reasoning]
[Task Decomposition]
[Self-Reflection]
    ↓
Response
```

## Integration Levels

### Level 1: Basic Routing (Easiest)

LM Studio as a provider option:

```python
from agi_provider import AGIProvider, detect_provider

# Create provider with LM Studio
provider, choice = detect_provider("lmstudio")
agi = AGIProvider(base_provider=provider)

# Use AGI reasoning with LM Studio backend
response = agi.complete([
    {"role": "user", "content": "Explain generators in Python"}
])
```

### Level 2: Agent Registry Integration

Register LM Studio as a specialized agent:

```python
from agi_provider import AGIProvider, _AGENT_REGISTRY
from lmstudio_agi_integration import get_lmstudio_agent_registry_entry

# Add to agent registry
_AGENT_REGISTRY["lmstudio-local"] = get_lmstudio_agent_registry_entry()

# AGI provider now routes to LM Studio for suitable queries
agi = AGIProvider()
response = agi.complete([
    {"role": "user", "content": "Write a Python decorator"}
])
# Routes to lmstudio because: domain=technical, intent=coding
```

### Level 3: Custom Routing

Fine-grained control over LM Studio selection:

```python
from lmstudio_agi_integration import AGILMStudioRouter
from agi_provider import AGIProvider

router = AGILMStudioRouter()
agi = AGIProvider()

# Analyze query
query = "Optimize this function for speed"
analysis = agi._analyze_query(query)

# Route intelligently
if router.should_use_lmstudio(analysis):
    response = await router.route_query(query, [], analysis)
else:
    response = agi.complete([...])
```

### Level 4: Full Multi-Agent Workflow

Use LM Studio with task decomposition and reasoning:

```python
from lmstudio_agi_integration import (
    decompose_task_with_lmstudio,
    reason_with_lmstudio_chain_of_thought,
)

# Decompose complex task
task = "Implement a transformer from scratch"
subtasks = await decompose_task_with_lmstudio(task, domain="ai")

# Reason through implementation
for subtask in subtasks:
    reasoning = await reason_with_lmstudio_chain_of_thought(
        subtask['task'],
        depth=3
    )
    print(f"Subtask: {subtask['task']}")
    print(f"Reasoning: {reasoning['conclusion']}")
```

## Quick Start

### 1. Add to Agent Registry

```python
# In agi_provider.py or init code
from lmstudio_agi_integration import get_lmstudio_agent_registry_entry

_AGENT_REGISTRY["lmstudio-local"] = get_lmstudio_agent_registry_entry()
```

### 2. Use with AGI Provider

```python
from agi_provider import AGIProvider

agi = AGIProvider()

# Automatically routes to LM Studio for suitable queries
response = agi.complete([
    {"role": "user", "content": "Explain neural networks"}
])

print(response)
```

### 3. Configure Routing

```bash
# Ensure LM Studio is running
python -m lmstudio_mcp_server.py

# Set model preference if needed
export LMSTUDIO_MODEL=mistral-7b
export LMSTUDIO_TEMPERATURE=0.7
```

## AGI Provider Features + LM Studio

### Chain-of-Thought Reasoning

The AGI provider chains reasoning steps. LM Studio participates:

```python
agi = AGIProvider(enable_chain_of_thought=True)

# Generates multi-step reasoning
response = agi.complete([
    {"role": "user", "content": "Why does deep learning work?"}
])

# Reasoning chain is tracked:
# 1. Understand question
# 2. Break into components (with LM Studio)
# 3. Explain each component
# 4. Summarize insights
```

### Task Decomposition

Complex tasks are broken into subtasks:

```python
# AGI provider decomposes "Implement a RAG system"
# and routes subtasks to appropriate agents:
#   - Research: LM Studio (technical explanation)
#   - Implementation: Code specialist
#   - Testing: Testing agent
#   - Documentation: Technical writer

agi = AGIProvider(enable_task_decomposition=True)
response = agi.complete([
    {"role": "user", "content": "Implement a RAG system"}
])
```

### Self-Reflection

AGI provider reviews and improves responses:

```python
agi = AGIProvider(enable_self_reflection=True)

response = agi.complete([
    {"role": "user", "content": "Explain LSTM networks"}
])

# Process:
# 1. LM Studio generates initial response
# 2. AGI evaluates completeness
# 3. AGI requests improvements if needed
# 4. Final response returned
```

## Router Decision Logic

The `AGILMStudioRouter` determines when to use LM Studio:

### ✅ Use LM Studio For:

**Explicit requests:**
- "Explain XYZ locally"
- "Use offline models for this"
- "Private inference please"

**Technical domains:**
- Domain = "technical"
- Domain = "coding"
- Domain = "ai"

**Code-related intents:**
- Intent = "coding"
- Intent = "creation"
- Intent = "explanation" (for tech topics)

### ❌ Don't Use LM Studio For:

- Quantum-specific queries (route to quantum-specialist)
- Aria movement/action commands (route to aria-character)
- Domains requiring real-time data (route to appropriate agent)

### Example Logic

```python
router = AGILMStudioRouter()

# Will use LM Studio
analysis = {"domain": "technical", "intent": "coding", "query": "write python code"}
router.should_use_lmstudio(analysis)  # → True

# Won't use LM Studio
analysis = {"domain": "quantum", "intent": "explanation", "query": "explain qubits"}
router.should_use_lmstudio(analysis)  # → False (use quantum-specialist)
```

## Configuration

### Environment Variables

```bash
# LM Studio endpoint
export LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1

# Default model
export LMSTUDIO_MODEL=mistral-7b

# Sampling temperature (lower = more deterministic)
export LMSTUDIO_TEMPERATURE=0.7

# Max response tokens
export LMSTUDIO_MAX_TOKENS=2048
```

### AGI Provider Settings

```python
agi = AGIProvider(
    # Base provider (LM Studio or other)
    base_provider=None,  # Auto-detect

    # Reasoning features
    enable_chain_of_thought=True,
    enable_self_reflection=True,
    enable_task_decomposition=True,

    # Reasoning depth (1-5)
    reasoning_depth=3,

    # Output control
    temperature=0.7,
    max_output_tokens=2048,

    # Verbosity
    verbose=False,
)
```

## API Reference

### AGILMStudioRouter

```python
router = AGILMStudioRouter(fallback_provider="agi")

# Check if LM Studio is available
await router.ensure_healthy()

# Determine if query suits LM Studio
router.should_use_lmstudio(query_analysis)

# Route query to LM Studio
response = await router.route_query(query, messages, analysis)
```

### Helper Functions

```python
# Get LM Studio agent registry entry
entry = get_lmstudio_agent_registry_entry()

# Complete with LM Studio routing
response = await complete_with_lmstudio_routing(
    agi_provider,
    messages,
    stream=True,
    prefer_lmstudio=False
)

# Decompose task into subtasks
subtasks = await decompose_task_with_lmstudio(task, domain="technical")

# Generate reasoning chain
reasoning = await reason_with_lmstudio_chain_of_thought(
    query,
    depth=3
)
```

## Examples

### Example 1: Technical Explanation

```python
from agi_provider import AGIProvider

agi = AGIProvider()

# Query perfect for LM Studio (domain=technical)
response = agi.complete([
    {"role": "user", "content": "Explain backpropagation in neural networks"}
])

# Flow:
# 1. Query analyzed: technical domain, explanation intent
# 2. LM Studio available: route to local model
# 3. Response generated locally (fast!)
# 4. Optional: AGI reflection improves response
print(response)
```

### Example 2: Code Generation

```python
from agi_provider import AGIProvider

agi = AGIProvider(
    enable_task_decomposition=True,
    enable_self_reflection=True
)

# Perfect for code specialist + LM Studio
response = agi.complete([
    {"role": "user", "content": "Write a Python async decorator with error handling"}
])

# Flow:
# 1. Analyzed: coding intent, technical domain
# 2. Decomposed: interface design → implementation → testing
# 3. LM Studio generates code for each subtask
# 4. Self-reflection checks correctness
# 5. Final code returned
```

### Example 3: Multi-Agent Workflow

```python
from lmstudio_agi_integration import (
    decompose_task_with_lmstudio,
    reason_with_lmstudio_chain_of_thought,
)

# Complex task needing multiple agents
task = "Build a recommendation system using collaborative filtering"

# LM Studio decomposes
subtasks = await decompose_task_with_lmstudio(
    task,
    domain="ai"
)
# Returns:
# 1. Understand collaborative filtering
# 2. Design data structures
# 3. Implement similarity metrics
# 4. Build recommendation logic
# 5. Add caching for performance

# Route each subtask appropriately
for subtask in subtasks:
    print(f"\nSubtask: {subtask['task']}")

    # Get reasoning from LM Studio
    reasoning = await reason_with_lmstudio_chain_of_thought(
        subtask['task'],
        depth=2
    )
    print(f"Analysis: {reasoning['conclusion']}")
```

### Example 4: Conditional Routing

```python
from lmstudio_agi_integration import AGILMStudioRouter
from agi_provider import AGIProvider

router = AGILMStudioRouter()
agi = AGIProvider()

# Different queries, different routing decisions
queries = [
    "Explain quantum entanglement",      # → quantum-specialist
    "Write a sorting algorithm",         # → lmstudio-local (coding)
    "What is the weather?",              # → general agent
    "Optimize this function locally",    # → lmstudio-local (local mention)
]

for query in queries:
    analysis = agi._analyze_query(query)
    use_lmstudio = router.should_use_lmstudio(analysis)

    print(f"\nQuery: {query}")
    print(f"  Domain: {analysis['domain']}")
    print(f"  Intent: {analysis['intent']}")
    print(f"  Route: {'LM Studio' if use_lmstudio else 'Other agent'}")
```

## Monitoring & Diagnostics

### Check Router Health

```python
router = AGILMStudioRouter()

# Verify LM Studio is available
is_healthy = await router.ensure_healthy()
print(f"LM Studio available: {is_healthy}")

# Get agent info
info = get_lmstudio_agent_info()
print(f"Agent status: {info['status']}")
print(f"Capabilities: {info['capabilities']}")
```

### Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)

# Now see routing decisions, health checks, fallbacks
agi = AGIProvider(verbose=True)
response = agi.complete([...])
```

## Troubleshooting

### LM Studio Not Available

```
✗ LM Studio not detected on localhost:1234
  Make sure LM Studio is running:
    1. Open LM Studio app (https://lmstudio.ai)
    2. Load a model (Mistral 7B recommended)
    3. Enable Local Server
```

### Fallback Behavior

If LM Studio is unavailable, the system automatically falls back to the configured fallback provider (default: "agi").

### Performance Tuning

```python
# For faster responses, reduce max tokens:
export LMSTUDIO_MAX_TOKENS=256

# For more deterministic responses:
export LMSTUDIO_TEMPERATURE=0.3

# For more creative responses:
export LMSTUDIO_TEMPERATURE=1.0
```

## Integration Checklist

- [ ] LM Studio MCP server installed (`pip install -r mcp-requirements.txt`)
- [ ] `lmstudio_agi_integration.py` placed in lmstudio-mcp directory
- [ ] LM Studio app running with model loaded
- [ ] Local Server enabled in LM Studio
- [ ] Environment variables set (or using defaults)
- [ ] `lmstudio_agi_integration` imported in your code
- [ ] Agent registry entry added (if using multi-agent routing)
- [ ] Verified with `verify_agent_integration.py`

## Next Steps

1. **Start LM Studio** — Open app, load model, enable server
2. **Start MCP Server** — `python lmstudio_mcp_server.py`
3. **Test Basic Routing** — See examples above
4. **Add to Agent Registry** — Enable automatic routing
5. **Monitor with Logging** — Enable debug logging
6. **Optimize Configuration** — Tune tokens, temperature, model

## References

- **AGI Provider**: `ai-projects/chat-cli/src/agi_provider.py`
- **LM Studio MCP Integration**: `ai-projects/lmstudio-mcp/lmstudio_agi_integration.py`
- **Agent Integration**: `ai-projects/lmstudio-mcp/AGENT_INTEGRATION.md`
- **LM Studio Docs**: https://lmstudio.ai

---

**Powerful local AI reasoning with the AGI provider!** 🚀
