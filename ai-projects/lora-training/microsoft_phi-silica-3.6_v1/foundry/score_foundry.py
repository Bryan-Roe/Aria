"""Scoring script for Azure AI Foundry managed online endpoint.
Loads base model and applies LoRA adapter for inference.
Environment variables:
  BASE_MODEL_ID      - Hugging Face model id (e.g. microsoft/Phi-3.5-mini-instruct)
  ADAPTER_SUBPATH    - Relative path to LoRA adapter inside model asset (default: lora_adapter)
  MAX_NEW_TOKENS     - Generation cap (default: 128)
  USE_BF16           - '1' to prefer bfloat16 if available
Input JSON:
  {"messages": [{"role":"user","content":"Hello"}]}
Output JSON:
  {"output":"..."}
"""

import json
import os
from pathlib import Path
from typing import Dict, List

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

_model = None
_tokenizer = None


def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return
    base_id = os.environ.get("BASE_MODEL_ID", "microsoft/Phi-3.5-mini-instruct")
    adapter_sub = os.environ.get("ADAPTER_SUBPATH", "lora_adapter")
    adapter_path = Path(__file__).resolve().parent / adapter_sub
    dtype = (
        torch.bfloat16
        if (os.environ.get("USE_BF16") == "1" and torch.cuda.is_available())
        else torch.float16
    )
    _tokenizer = AutoTokenizer.from_pretrained(base_id, use_fast=True)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(
        base_id, torch_dtype=dtype, device_map="auto"
    )
    if adapter_path.exists():
        _model = PeftModel.from_pretrained(base, str(adapter_path))
    else:
        _model = base
    _model.eval()


def init():  # Azure ML entrypoint
    _load_model()
    print("Model + adapter loaded.")


def _apply_chat_template(messages: List[Dict[str, str]]) -> str:
    # Fallback simple format if tokenizer lacks chat template
    if hasattr(_tokenizer, "apply_chat_template"):
        return _tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        parts.append(f"<|{role}|>\n{content}\n")
    parts.append("<|assistant|>\n")
    return "\n".join(parts)


def run(raw: str) -> str:  # Azure ML entrypoint
    _load_model()
    try:
        obj = json.loads(raw)
        messages = obj.get("messages")
        if not isinstance(messages, list) or not messages:
            return json.dumps({"error": "Missing messages"})
        prompt = _apply_chat_template(messages)
        max_new = int(os.environ.get("MAX_NEW_TOKENS", "128"))
        inputs = _tokenizer(prompt, return_tensors="pt").to(_model.device)
        with torch.no_grad():
            gen = _model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=0.8,
                top_p=0.95,
            )
        full = _tokenizer.decode(gen[0], skip_special_tokens=True)
        # Extract assistant portion if template used
        if "<|assistant|>" in full:
            assistant_part = full.split("<|assistant|>")[-1].strip()
        else:
            assistant_part = full
        return json.dumps({"output": assistant_part})
    except Exception as e:
        return json.dumps({"error": str(e)})
