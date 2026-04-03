#!/usr/bin/env python3
"""
Implementation guide for integrating LM Studio with AGI Provider multi-agent system.

CRITICAL TASKS:
1. Add "lmstudio-specialist" agent to _AGENT_REGISTRY in agi_provider.py
2. Update detect_provider() in chat_providers.py to handle explicit="lmstudio"
3. Test routing and streaming with LM Studio backend

KEY FILES:
- ai-projects/chat-cli/src/agi_provider.py (agent registry + routing)
- ai-projects/chat-cli/src/chat_providers.py (provider detection)
"""

# ============================================================================
# CHANGE 1: Add LM Studio Agent to _AGENT_REGISTRY
# ============================================================================
# FILE: ai-projects/chat-cli/src/agi_provider.py
# LOCATION: In _AGENT_REGISTRY dict (around line 25-120)
# ACTION: Add this new agent entry

LMSTUDIO_AGENT_CONFIG = {
    "lmstudio-specialist": {
        "domains": [],
        "intents": ["explanation", "question", "coding", "creation"],
        "provider": "lmstudio",
        "confidence_boost": 0.05,
        "subtask_templates": [
            "Understand the query: identify key concepts and requirements",
            "Formulate response: structure thoughts logically and clearly",
            "Review: ensure accuracy, completeness, and helpful presentation",
        ],
        "description": "Local LM Studio inference for general-purpose reasoning and Q&A",
    }
}

# ============================================================================
# CHANGE 2: Update detect_provider() to Handle "lmstudio"
# ============================================================================
# FILE: ai-projects/chat-cli/src/chat_providers.py
# LOCATION: detect_provider() function at line 1257
# ACTION: Update to handle explicit="lmstudio"

"""
Existing detect_provider() logic:
  if explicit:
    if explicit in ("lora", "agi", ...):
      # create that provider

Need to add:
  elif explicit == "lmstudio":
    if _check_lmstudio_available():
      return LMStudioProvider(...), info
    else:
      raise error or return None
"""


# Check if this helper exists:
def _check_lmstudio_available():
    """Check if LM Studio server is running and accessible."""
    import os
    import urllib.request

    base_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    try:
        request = urllib.request.Request(f"{base_url}/models")
        with urllib.request.urlopen(request, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


# ============================================================================
# VERIFICATION: Agent Scoring & Dispatch Flow
# ============================================================================
# Files that don't need changes but are part of the integration:
#
# 1. _select_agent() [agi_provider.py:412]
#    - Already scores "lmstudio-specialist" if added to registry
#    - Matching logic: domain match +0.5, intent match +0.3
#    - Confidence boost applied if any match found
#
# 2. _dispatch_to_agent() [agi_provider.py:481]
#    - Already calls detect_provider(explicit=agent_provider)
#    - Will work once detect_provider handles "lmstudio"
#
# 3. Complete Flow:
#    User query
#      → _analyze_query() [determines intent, domain, confidence]
#      → _select_agent() [scores all agents, returns best]
#      → if best != "general":
#          → _dispatch_to_agent(agent_name)
#             → detect_provider(explicit="lmstudio")
#             → LMStudioProvider.stream() or .complete()
#             → response

# ============================================================================
# TESTING CHECKLIST
# ============================================================================
# 1. Unit test: Agent selection includes lmstudio-specialist
# 2. Unit test: detect_provider(explicit="lmstudio") returns LMStudioProvider
# 3. Integration test: Query routes to LM Studio specialist
# 4. Integration test: Streaming responses work
# 5. Error handling: LM Studio unavailable → fallback to AGI
# 6. Performance: Agent selection with new agent doesn't slow system

# ============================================================================
# ENVIRONMENT SETUP (Already in .env)
# ============================================================================
# LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
# LMSTUDIO_MODEL=local-model
#
# Verify LM Studio is running:
#   curl http://127.0.0.1:1234/v1/models
