#!/usr/bin/env python
"""Interactive Aria Visual Command Demo"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(
    0, str(REPO_ROOT / "ai-projects" / "lora-training" / "microsoft_phi-silica-3.6_v1")
)

import re

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


class AriaCommandGenerator:
    def __init__(self, adapter_path: str):
        base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        print("🎨 Loading Aria Visual Model...")

        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        model = AutoModelForCausalLM.from_pretrained(
            base_model, torch_dtype=torch.float16, device_map="auto"
        )
        self.model = PeftModel.from_pretrained(model, adapter_path)
        print("✅ Model loaded!\n")

    def generate_command(self, user_input: str) -> list[str]:
        """Generate Aria command tags from natural language"""
        input_text = f"<|user|>\n{user_input}</s>\n<|assistant|>\n"
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=30,
                temperature=0.1,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.5,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            )

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True
        )
        tags = re.findall(r"\[aria:[^\]]+\]", response)
        return tags if tags else []

    def show_categories(self):
        """Display available command categories"""
        categories = {
            "🚶 Movement": ["move left", "walk right", "run up"],
            "😊 Expressions": ["smile", "look happy", "surprised face", "wink"],
            "👋 Gestures": ["wave", "thumbs up", "point left", "clap"],
            "💃 Animations": ["jump", "dance", "spin", "bow", "backflip"],
            "🧍 Poses": ["sit down", "stand up", "crouch"],
            "📷 Camera": ["center", "zoom in", "face left"],
            "✨ Effects": ["sparkle", "glow", "hearts"],
            "🎭 Combos": ["dance with sparkles", "jump and smile"],
        }

        print("=" * 80)
        print("🎨 ARIA VISUAL COMMAND CATEGORIES")
        print("=" * 80)
        for category, examples in categories.items():
            print(f"\n{category}")
            for ex in examples[:3]:
                print(f"  • {ex}")
        print("\n" + "=" * 80)


def main():
    adapter = (
        REPO_ROOT / "data_out" / "aria_models" / "aria_expanded_v2" / "lora_adapter"
    )

    if not adapter.exists():
        print(f"❌ Model not found: {adapter}")
        return

    aria = AriaCommandGenerator(str(adapter))
    aria.show_categories()

    print("\n🎮 Interactive Mode - Type commands or 'quit' to exit")
    print("💡 Try: 'aria smile', 'jump', 'dance with sparkles'\n")

    while True:
        try:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            tags = aria.generate_command(user_input)

            if tags:
                print(f"🎨 Aria: {' '.join(tags[:2])}\n")  # Show first 2 tags
            else:
                print("❓ No command tags generated. Try a different phrase.\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    main()
