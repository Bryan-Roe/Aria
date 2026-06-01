#!/usr/bin/env python
"""Test Aria model with proper generation constraints"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ai-projects" /
                "lora-training" / "microsoft_phi-silica-3.6_v1"))

import torch  # noqa: E402
from peft import PeftModel  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402


def test_aria_final(adapter_path: str):
    base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

    print(f"🔍 Loading model with adapter: {Path(adapter_path).name}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, device_map="auto")
    model = PeftModel.from_pretrained(model, adapter_path)

    test_commands = [
        "move left",
        "aria smile",
        "jump",
        "wave hello",
        "look surprised",
        "dance with sparkles",
        "thumbs up",
        "spin around",
    ]

    print("\n" + "=" * 80)
    print("🎨 ARIA VISUAL COMMANDS TEST")
    print("=" * 80)

    for prompt in test_commands:
        input_text = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=20,  # Short - just need the tag
                temperature=0.1,  # Low temperature = more deterministic
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.5,  # Penalize repeating tokens
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)

        # Extract first command tag
        import re

        tags = re.findall(r"\[aria:[^\]]+\]", response)

        print(f"\n📝 Command: {prompt}")
        print(f"   Raw output: {response[:100]}")
        if tags:
            # Show first 2 tags
            print(f"   ✅ Tags found: {' '.join(tags[:2])}")
        else:
            print("   ❌ No command tags detected")
        print("-" * 80)


if __name__ == "__main__":
    adapter = REPO_ROOT / "data_out" / "aria_models" / \
        "aria_expanded_v2" / "lora_adapter"
    test_aria_final(str(adapter))
