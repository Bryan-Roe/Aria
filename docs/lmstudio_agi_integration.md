# Complete LM Studio + AGI Provider Integration Guide

## Architecture Overview
- **LMStudioProvider**: chat_providers.py line 829+ (already implemented)
- **AGI Provider Multi-Agent System**: agi_provider.py with agent registry
- **Integration Flow**:
  1. Query analysis → domain + intent detection
  2. _select_agent() scores all agents (line 412)
  3. _dispatch_to_agent() routes to specialist (line 481+)
  4. Calls detect_provider(explicit="lmstudio")
  5. LMStudioProvider handles the request

## Key Code Locations
- Agent Registry (_AGENT_REGISTRY): agi_provider.py around line 25-120
- select_agent(): agi_provider.py line 412
- dispatch_to_agent(): agi_provider.py line 481
- detect_provider(): chat_providers.py line 1257

## Agent Scoring Logic (from _select_agent)
```python
score = 0.0
if domain in agent_config.get("domains", []): score += 0.5
if intent in agent_config.get("intents", []): score += 0.3
if score > 0.0:
    score += agent_config.get("confidence_boost", 0.0) * confidence
    # learned pattern bonus (time-decay 24h half-life)
    if agent_name == learned_agent:
        score += learned_weight
```

## Agent Config Template
```python
"agent-name": {
    "domains": ["domain1", "domain2"],
    "intents": ["intent1", "intent2"],
    "provider": "provider_type",
    "confidence_boost": 0.1,
    "subtask_templates": ["step1", "step2"],
    "description": "...",
}
```

## Implementation Tasks

### TASK 1: Add LM Studio Agent to Registry
File: ai-projects/chat-cli/src/agi_provider.py
Location: In _AGENT_REGISTRY dict (around line 25-120)
Add new agent entry:
```python
"lmstudio-specialist": {
    "domains": [],
    "intents": ["explanation", "question", "coding", "creation"],
    "provider": "lmstudio",
    "confidence_boost": 0.05,
    "subtask_templates": [
        "Understand the query: identify key concepts and requirements",
        "Formulate response: structure thoughts logically",
        "Refine: ensure accuracy and clarity",
    ],
    "description": "Local LM Studio inference for general-purpose reasoning and Q&A",
},
```

### TASK 2: Update detect_provider to Handle "lmstudio"
File: ai-projects/chat-cli/src/chat_providers.py
Location: detect_provider() function at line 1257
Current flow: if explicit param, create that provider type
Need to update to handle explicit="lmstudio":
- Check _check_lmstudio_available() or equivalent
- Return LMStudioProvider instance with config

### TASK 3: Verify Agent Dispatch
File: ai-projects/chat-cli/src/agi_provider.py
Location: _dispatch_to_agent method (line 481)
Current: calls detect_provider(explicit=provider_name)
Should already work if detect_provider handles "lmstudio"

### TASK 4: Test Integration
- Create test query that routes to LM Studio specialist
- Verify streaming and non-streaming work
- Test with various domains/intents
- Verify fallback behavior if LM Studio unavailable

## Provider Configuration (Environment Variables)
- LMSTUDIO_BASE_URL: default http://127.0.0.1:1234/v1
- LMSTUDIO_MODEL: default "local-model"
- Already configured in .env file

## Expected Agent Selection Behavior
Queries like:
- "What is quantum computing?" → domain:ai, intent:explanation → code-specialist or lmstudio-specialist
- "Help me debug this code" → domain:technical, intent:coding → code-specialist or lmstudio-specialist
- General questions with no domain → falls back to general or lmstudio-specialist
- If LM Studio specialist selected but provider unavailable → falls back to AGI provider

## Files to Modify
1. ai-projects/chat-cli/src/agi_provider.py
   - Add "lmstudio-specialist" to _AGENT_REGISTRY
   - Possibly update _dispatch_to_agent logic

2. ai-projects/chat-cli/src/chat_providers.py
   - Update detect_provider() to handle explicit="lmstudio"
   - May need to add helper method like _check_lmstudio_provider_available()

## Success Criteria
- Agent registry includes "lmstudio-specialist"
- detect_provider(explicit="lmstudio") returns LMStudioProvider instance
- Appropriate queries route to LM Studio specialist
- Streaming responses from LM Studio work through AGI system
- Fallback to AGI provider when LM Studio unavailable
- Error handling prevents crashes on LM Studio connection failures
