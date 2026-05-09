#!/usr/bin/env python
"""Test trained Aria model - instant feedback"""
import sys
from pathlib import Path
from typing import Any

__test__ = False

# Add paths
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(
    0, str(REPO_ROOT / "ai-projects" / "lora-training" / "microsoft_phi-silica-3.6_v1")
)


def _load_optional_dependencies() -> tuple[Any, Any, Any, Any]:
    """Load heavyweight optional ML dependencies only when the script is executed."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        raise RuntimeError(f"Missing dependencies: {e}") from e

    return AutoTokenizer, AutoModelForCausalLM, PeftModel, torch


def run_aria_model_test(adapter_path: str):
    """Quick test of Aria movement model."""
    AutoTokenizer, AutoModelForCausalLM, PeftModel, torch = (
        _load_optional_dependencies()
    )
    adapter_path = Path(adapter_path)
    if not adapter_path.exists():
        print(f"❌ Adapter not found: {adapter_path}")
        return False

    print(f"🔍 Loading model from: {adapter_path}")

    # Load base model
    base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=torch.float16, device_map="auto"
    )

    # Load LoRA adapter
    model = PeftModel.from_pretrained(model, str(adapter_path))
    model.eval()

    # Test commands - expanded visual features
    test_prompts = [
        "Move Aria left",
        "Make Aria smile",
        "Aria jump",
        "Thumbs up",
        "Aria dance with sparkles",
        "Look surprised",
        "Wave hello",
        "Spin around",
    ]

    print("\n" + "=" * 70)
    print("🎭 Testing Aria Commands:")
    print("=" * 70)

    for prompt in test_prompts:
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(**inputs, max_new_tokens=50, do_sample=False)

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract just the assistant's response
        if "<|assistant|>" in response:
            response = response.split("<|assistant|>")[-1].strip()

        print(f"\n👤 User: {prompt}")
        print(f"🤖 Aria: {response}")

        # Check for command tags
        if "[aria:" in response.lower():
            print("   ✅ Command detected!")
        else:
            print("   ⚠️  No command tag found")

    print("\n" + "=" * 70)
    return True


if __name__ == "__main__":
    adapter = (
        REPO_ROOT / "data_out" / "aria_models" / "aria_expanded_v2" / "lora_adapter"
    )
    try:
        run_aria_model_test(str(adapter))
    except RuntimeError as exc:
        print(f"❌ {exc}")
        sys.exit(1)
