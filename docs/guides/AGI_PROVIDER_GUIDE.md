# AGI Provider - Advanced Reasoning for Aria

The AGI (Artificial General Intelligence) provider adds advanced reasoning capabilities to the Aria platform, enabling more sophisticated and contextual responses.

## Overview

The AGI provider is a wrapper that enhances any underlying chat provider (Azure OpenAI, OpenAI, or Local) with:

- **Multi-step reasoning** (chain-of-thought)
- **Goal-oriented task decomposition**
- **Self-reflection and response improvement**
- **Memory/context management**
- **Automatic Aria movement tag generation**

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AGI Provider                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Query     │  │   Task      │  │  Chain-of-      │  │
│  │  Analysis   │──│ Decompose   │──│   Thought       │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│         │                                    │          │
│         ▼                                    ▼          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Response Generation                 │    │
│  │       (using underlying base provider)          │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │            Self-Reflection & Improvement         │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                              │
│                          ▼                              │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Context Memory Update               │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │    Base Provider         │
              │  (Azure/OpenAI/Local)    │
              └─────────────────────────┘
```

## Quick Start

### CLI Usage

```powershell
# Basic AGI chat
python .\talk-to-ai\src\chat_cli.py --provider agi

# One-shot with AGI reasoning
python .\talk-to-ai\src\chat_cli.py --provider agi --once "Explain how quantum entanglement works"

# Verbose mode (shows reasoning steps)
$env:AGI_VERBOSE = "true"
python .\talk-to-ai\src\chat_cli.py --provider agi
```

### Programmatic Usage

```python
from chat_providers import detect_provider

# Get AGI provider
provider, info = detect_provider(explicit="agi")

# Use with messages
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is machine learning?"}
]

response = provider.complete(messages, stream=False)
print(response)
```

### Direct Provider Instantiation

```python
from agi_provider import AGIProvider, create_agi_provider

# Create with default settings
provider, info = create_agi_provider()

# Create with custom settings
provider, info = create_agi_provider(
    temperature=0.5,
    max_output_tokens=2048,
    verbose=True
)

# Or instantiate directly with custom base provider
from chat_providers import LocalEchoProvider
base = LocalEchoProvider()
agi = AGIProvider(
    base_provider=base,
    enable_chain_of_thought=True,
    enable_self_reflection=True,
    reasoning_depth=3
)
```

## Features

### 1. Query Analysis

The AGI provider analyzes each query to determine:

- **Complexity**: simple, moderate, or complex
- **Intent**: explanation, coding, movement, creation, question
- **Domain**: general, quantum, ai, aria, technical
- **Confidence**: How certain the analysis is

```python
# Example analysis result
{
    "query": "Explain quantum computing step by step",
    "complexity": "complex",
    "intent": "explanation",
    "domain": "quantum",
    "has_question": False,
    "confidence": 0.6
}
```

### 2. Task Decomposition

For complex queries, the AGI provider breaks tasks into subtasks:

- **Explanation tasks**: Define concepts, provide examples, explain relationships, summarize
- **Coding tasks**: Understand requirements, design solution, implement, handle edge cases
- **Creation tasks**: Clarify requirements, plan structure, create, review

### 3. Chain-of-Thought Reasoning

Generates step-by-step reasoning:

```
🧠 AGI Reasoning Process

🔍 Step 1 (analyze): Complex explanation query about quantum
💡 Step 2 (synthesize): Understanding: This is a complex explanation request
💡 Step 3 (synthesize): Quantum context: Should explain concepts clearly
💡 Step 4 (synthesize): Approach: Will provide a complex-appropriate response
```

### 4. Self-Reflection

After generating a response, the AGI provider:

- Checks response length appropriateness
- Ensures questions are answered
- Adds missing Aria movement tags
- Logs improvements for learning

### 5. Context Management

The `AGIContext` class manages:

- **Conversation history**: Last 50 messages with system message preservation
- **Reasoning chains**: Last 10 reasoning chains for reference
- **Active goals**: Up to 5 tracked goals
- **Learned patterns**: Stored for future improvements

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGI_VERBOSE` | `false` | Include reasoning steps in output |
| `CHAT_TEMPERATURE` | `0.7` | Response randomness |

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_provider` | BaseChatProvider | None | Underlying provider (auto-detected if None) |
| `temperature` | float | 0.7 | Sampling temperature |
| `max_output_tokens` | int | 2048 | Maximum tokens |
| `enable_chain_of_thought` | bool | True | Enable step-by-step reasoning |
| `enable_self_reflection` | bool | True | Enable response evaluation |
| `enable_task_decomposition` | bool | True | Enable goal decomposition |
| `reasoning_depth` | int | 3 | Max reasoning steps (1-5) |
| `verbose` | bool | False | Include reasoning in output |

## Aria Integration

The AGI provider is specifically designed to work with Aria:

### Movement Commands

When detecting Aria movement intent, the provider:

1. Parses the movement command
2. Adds appropriate movement tags
3. Includes natural acknowledgment

```powershell
# Input: "Move Aria left"
# Output: "I'll move to the left! [aria:walk:left]"

# Input: "Make Aria dance"
# Output: "Time to dance! [aria:dance]"
```

### Supported Movement Tags

- `[aria:walk:left]`, `[aria:walk:right]` - Walking movements
- `[aria:jump]` - Jumping
- `[aria:wave]` - Waving
- `[aria:dance]` - Dancing

## API Reference

### AGIProvider

```python
class AGIProvider(BaseChatProvider):
    """AGI-enhanced chat provider with advanced reasoning capabilities."""
    
    def complete(self, messages: List[RoleMessage], stream: bool = True) -> Iterable[str] | str:
        """Generate an AGI-enhanced response."""
    
    def set_goal(self, goal: str) -> None:
        """Add a goal to the active goals list."""
    
    def clear_goals(self) -> None:
        """Clear all active goals."""
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get a summary of recent reasoning activity."""
```

### AGIContext

```python
@dataclass
class AGIContext:
    """Manages context and memory for AGI reasoning."""
    
    conversation_history: List[RoleMessage]
    reasoning_chains: List[List[ReasoningStep]]
    goals: List[str]
    learned_patterns: Dict[str, Any]
    
    def add_message(self, message: RoleMessage) -> None:
        """Add a message to conversation history with pruning."""
    
    def get_relevant_context(self, query: str) -> str:
        """Extract relevant context for the current query."""
```

### ReasoningStep

```python
@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning chain."""
    
    step_type: str  # 'decompose', 'analyze', 'synthesize', 'reflect', 'refine'
    content: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Testing

Run the AGI provider tests:

```powershell
python -m pytest tests/test_agi_provider.py -v
```

The test suite includes:

- Context initialization and memory management
- Reasoning step creation
- Query analysis
- Task decomposition
- Chain-of-thought generation
- Self-reflection
- Goal management
- Provider integration

## Examples

### Complex Explanation

```python
provider, _ = detect_provider(explicit="agi")
messages = [
    {"role": "user", "content": "Explain step by step how neural networks learn"}
]
response = provider.complete(messages, stream=False)
```

### Coding Task

```python
messages = [
    {"role": "user", "content": "Write a Python function to calculate fibonacci numbers"}
]
response = provider.complete(messages, stream=False)
```

### Aria Movement

```python
messages = [
    {"role": "user", "content": "Make Aria wave and then walk to the right"}
]
response = provider.complete(messages, stream=False)
# Response will include: [aria:wave] and [aria:walk:right]
```

## Troubleshooting

### AGI Provider Not Available

```python
from chat_providers import detect_provider
try:
    provider, info = detect_provider(explicit="agi")
except RuntimeError as e:
    print(f"AGI provider error: {e}")
```

### Base Provider Issues

The AGI provider automatically falls back to local responses if the base provider fails:

```python
# If Azure/OpenAI unavailable, AGI uses built-in fallback responses
provider = AGIProvider()  # Auto-detects or falls back
response = provider.complete(messages)  # Always returns something
```

### Verbose Debugging

Enable verbose mode to see the reasoning process:

```powershell
$env:AGI_VERBOSE = "true"
python .\talk-to-ai\src\chat_cli.py --provider agi --once "Debug this query"
```

## Performance Considerations

1. **Reasoning overhead**: AGI adds analysis steps before response generation
2. **Memory usage**: Context stores up to 50 messages and 10 reasoning chains
3. **Base provider calls**: Each query makes one call to the base provider
4. **Streaming**: Fully supported with word-by-word streaming

## Future Enhancements

Planned improvements:

- [ ] Persistent memory storage
- [ ] Multi-turn goal tracking
- [ ] Learning from user feedback
- [ ] Tool/function calling integration
- [ ] Parallel reasoning paths
