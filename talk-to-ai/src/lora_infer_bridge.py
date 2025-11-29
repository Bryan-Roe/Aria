from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path


def _read_stdin_json() -> dict:
    data = sys.stdin.read()
    if not data:
        return {}
    try:
        return json.loads(data)
    except Exception:
        return {}


def _build_prompt(messages):
    """Build prompt string from messages.
    
    Uses list join instead of string += for O(n) instead of O(n²) complexity.
    """
    parts = []
    for msg in messages or []:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            parts.append(f"[SYSTEM] {content}")
        elif role == "user":
            parts.append(f"User: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
    
    # Build final prompt: messages joined by newlines, ending with "Assistant: "
    if parts:
        return "\n".join(parts) + "\nAssistant: "
    return "Assistant: "


def main() -> int:
    payload = _read_stdin_json()
    adapter_dir = Path(payload.get("adapter_dir", ""))
    messages = payload.get("messages", [])
    max_new_tokens = int(payload.get("max_new_tokens", 256))
    temperature = float(payload.get("temperature", 0.7))

    if not adapter_dir or not adapter_dir.exists():
        print("Adapter path not found", file=sys.stderr)
        return 2

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
    except Exception as e:
        print(f"Bridge missing ML deps: {e}", file=sys.stderr)
        return 3

    # Determine base model id from adapter config
    adapter_cfg_path = adapter_dir / "adapter_config.json"
    if not adapter_cfg_path.exists():
        print(f"adapter_config.json not found in {adapter_dir}", file=sys.stderr)
        return 4
    try:
        with open(adapter_cfg_path, "r", encoding="utf-8") as f:
            adapter_cfg = json.load(f)
    except Exception as e:
        print(f"Failed to read adapter_config.json: {e}", file=sys.stderr)
        return 5

    base_model_id = adapter_cfg.get("base_model_name_or_path", "microsoft/Phi-3.5-mini-instruct")
    if base_model_id == "Phi-3.6-mini-instruct":
        base_model_id = "microsoft/Phi-3.5-mini-instruct"

    try:
        # Prefer local tokenizer if present next to adapter_dir/../tokenizer
        tokenizer_source = adapter_dir.parent / "tokenizer"
        if tokenizer_source.exists():
            tokenizer = AutoTokenizer.from_pretrained(tokenizer_source)
        else:
            tokenizer = AutoTokenizer.from_pretrained(base_model_id)

        # CPU-first load for broad compatibility
        model = AutoModelForCausalLM.from_pretrained(
            base_model_id,
            torch_dtype=torch.float32,
        )
        model = PeftModel.from_pretrained(model, adapter_dir)
        model.to("cpu").eval()

        prompt = _build_prompt(messages)
        inputs = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Strip the prompt portion and decode only the completion
        response = tokenizer.decode(
            output[0][inputs["input_ids"].shape[-1]:],
            skip_special_tokens=True,
        )
        sys.stdout.write(response)
        sys.stdout.flush()
        return 0
    except Exception as e:
        print(f"Bridge inference error: {e}", file=sys.stderr)
        return 6


if __name__ == "__main__":
    sys.exit(main())
