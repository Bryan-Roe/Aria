#!/usr/bin/env python
"""Debug Aria model output to see what it's generating"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1"))

from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

def test_aria_debug(adapter_path: str):
    base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    
    print(f"🔍 Loading base model: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16, device_map="auto")
    
    print(f"🔍 Loading adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)
    
    # Test with raw prompt
    test_prompts = [
        "move left",
        "aria smile",
        "jump",
        "wave hello"
    ]
    
    print("\n" + "=" * 80)
    print("🧪 RAW MODEL OUTPUT DEBUG")
    print("=" * 80)
    
    for prompt in test_prompts:
        # Try simple format
        input_text = f"<|user|>\n{prompt}</s>\n<|assistant|>\n"
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=50,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        clean_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"\n📝 Prompt: {prompt}")
        print(f"📤 Full output:\n{response}")
        print(f"🧹 Clean output:\n{clean_response}")
        print("-" * 80)

if __name__ == "__main__":
    adapter = REPO_ROOT / "data_out" / "aria_models" / "aria_expanded_v2" / "lora_adapter"
    test_aria_debug(str(adapter))
