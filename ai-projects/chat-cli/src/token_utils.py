from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Dict, Optional, Tuple

RoleMessage = Dict[str, str]

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover - optional
    tiktoken = None  # type: ignore

try:
    from transformers import AutoTokenizer  # type: ignore
except Exception:  # pragma: no cover - optional
    AutoTokenizer = None  # type: ignore


# Reasonable default context sizes by popular models/deployments
MODEL_CONTEXT_DEFAULTS: Dict[str, int] = {
    # OpenAI
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4.1": 128000,
    "gpt-4.1-mini": 128000,
    "gpt-3.5-turbo": 16385,
    # Azure OpenAI often uses custom deployment names; fall back to a safe default
    "azure-default": 16384,
    # Local models (Phi etc.)
    "phi": 4096,
}


def _match_model_default(model: Optional[str]) -> int:
    m = (model or "").lower()
    for key, ctx in MODEL_CONTEXT_DEFAULTS.items():
        if key in m:
            return ctx
    return 8192  # safe general default


@dataclass
class PruneStats:
    original_tokens: int
    pruned_tokens: int
    removed_count: int
    budget: int
    reserve_output_tokens: int


def _get_text_encoder(provider: str, model: Optional[str]) -> Callable[[str], int]:
    """Return a function that approximates token count for a given text.

    Priority: tiktoken (OpenAI/Azure) -> transformers tokenizer (if available) -> heuristic.
    """
    prov = (provider or "").lower()
    mdl = (model or "").lower()

    # Try tiktoken for OpenAI/Azure
    if tiktoken is not None and (prov in ("openai", "azure") or any(k in mdl for k in ("gpt-", "-o"))):
        try:
            from tiktoken import encoding_for_model
            enc = None
            try:
                enc = encoding_for_model(model or "gpt-4o-mini")
            except Exception:
                enc = tiktoken.get_encoding("cl100k_base")
            def _count(text: str) -> int:
                return len(enc.encode(text or ""))
            return _count
        except Exception:
            pass

    # Try transformers tokenizer for local models
    if AutoTokenizer is not None and mdl:
        try:
            tok = AutoTokenizer.from_pretrained(model, use_fast=True)
            def _count(text: str) -> int:
                return len(tok.encode(text or ""))
            return _count
        except Exception:
            pass

    # Fallback heuristic: 1 token ~ 4 characters in English text
    def _heuristic(text: str) -> int:
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    return _heuristic


def count_messages_tokens(messages: List[RoleMessage], provider: str, model: Optional[str], system_prompt: Optional[str] = None) -> int:
    enc = _get_text_encoder(provider, model)
    total = 0
    if system_prompt:
        total += enc(system_prompt) + 4  # small framing cost
    for m in messages or []:
        total += enc(m.get("role", "")) + enc(m.get("content", "")) + 4
    return total


def prune_messages(
    messages: List[RoleMessage],
    provider: str,
    model: Optional[str],
    max_context_tokens: Optional[int],
    reserve_output_tokens: int = 1024,
    system_prompt: Optional[str] = None,
) -> Tuple[List[RoleMessage], PruneStats, Optional[RoleMessage]]:
    """Prune conversation to fit within model context budget.

    Returns: (pruned_messages, stats, system_message)
    
    Performance: Uses O(n) algorithm by pre-computing token counts per message
    and maintaining a running total, avoiding repeated tokenization.
    """
    budget = max_context_tokens or _match_model_default(model)
    enc = _get_text_encoder(provider, model)

    # Build a working copy and ensure last message is user for safety
    msgs = list(messages or [])

    # Separate system messages from others; keep one combined system message for clarity
    system_msgs = [m for m in msgs if m.get("role") == "system"]
    non_system = [m for m in msgs if m.get("role") != "system"]

    system_text = system_prompt or "\n\n".join(m.get("content", "") for m in system_msgs)
    system_msg = {"role": "system", "content": system_text} if system_text else None

    original_tokens = count_messages_tokens(msgs, provider, model, system_prompt)

    if budget <= reserve_output_tokens + 256:  # ensure minimal space
        reserve_output_tokens = max(128, budget // 4)

    # Pre-compute token counts for each message (O(n) - done once)
    # Each message costs: role tokens + content tokens + 4 (framing)
    message_token_counts = [
        enc(m.get("role", "")) + enc(m.get("content", "")) + 4
        for m in non_system
    ]
    
    # Calculate base system token cost (done once)
    system_tokens = (enc(system_text) + 4) if system_text else 0
    
    # Calculate initial total tokens
    total_tokens = system_tokens + sum(message_token_counts)
    
    # Prune from front (oldest messages) while over budget
    # Uses running total instead of recalculating each iteration (O(n) total)
    start_idx = 0
    while start_idx < len(non_system) and (total_tokens + reserve_output_tokens) > budget:
        total_tokens -= message_token_counts[start_idx]
        start_idx += 1
    
    # Get pruned messages
    pruned = non_system[start_idx:]
    pruned_tokens = total_tokens
    removed_count = start_idx

    # Reassemble with system (if any)
    final_messages = []
    if system_msg and system_msg["content"].strip():
        final_messages.append(system_msg)
    final_messages.extend(pruned)

    stats = PruneStats(
        original_tokens=original_tokens,
        pruned_tokens=pruned_tokens,
        removed_count=removed_count,
        budget=budget,
        reserve_output_tokens=reserve_output_tokens,
    )

    return final_messages, stats, system_msg
