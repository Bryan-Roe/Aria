"""
Quick test script to validate aria movement dataset and test command generation
"""
import json
import sys
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_dataset(dataset_path):
    """Load and display aria movement dataset"""
    train_file = Path(dataset_path) / "train.json"
    test_file = Path(dataset_path) / "test.json"
    
    with open(train_file, 'r', encoding='utf-8') as f:
        train_data = json.load(f)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    
    print(f"✅ Loaded {len(train_data)} training examples")
    print(f"✅ Loaded {len(test_data)} test examples")
    
    # Show sample
    print("\n=== Sample Training Example ===")
    sample = train_data[0]
    for msg in sample['messages']:
        print(f"{msg['role'].upper()}: {msg['content']}")
    
    return train_data, test_data

def test_base_model_generation(model_id="microsoft/Phi-3.5-mini-instruct"):
    """Test if base model can generate movement-like responses"""
    print(f"\n=== Testing Base Model: {model_id} ===")
    print("Loading model...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        
        print("✅ Model loaded successfully")
        
        # Test prompts
        test_prompts = [
            "Move Aria to the left",
            "Make Aria wave",
            "Walk right",
            "Center the character"
        ]
        
        print("\n=== Base Model Responses (BEFORE training) ===")
        for prompt in test_prompts:
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            input_text = tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
            inputs = tokenizer(input_text, return_tensors="pt")
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
            
            # Check for aria tags
            has_aria_tag = '[aria:' in response.lower()
            tag_indicator = "✅ HAS TAG" if has_aria_tag else "❌ NO TAG"
            
            print(f"\nPrompt: {prompt}")
            print(f"Response: {response}")
            print(f"{tag_indicator}")
        
        print("\n=== Summary ===")
        print("Base model tested. After training on aria_movement dataset,")
        print("responses should consistently include [aria:...] tags.")
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        return False
    
    return True

def validate_command_coverage(dataset):
    """Validate that dataset covers all command types"""
    print("\n=== Validating Command Coverage ===")
    
    commands = {
        'move': 0,
        'walk': 0,
        'center': 0,
        'wave': 0,
        'jump': 0,
        'dance': 0
    }
    
    directions = {
        'left': 0,
        'right': 0,
        'up': 0,
        'down': 0
    }
    
    for example in dataset:
        response = example['messages'][-1]['content'].lower()
        
        for cmd in commands.keys():
            if f'[aria:{cmd}' in response:
                commands[cmd] += 1
        
        for direction in directions.keys():
            if direction in response:
                directions[direction] += 1
    
    print("\nCommand Type Coverage:")
    for cmd, count in commands.items():
        status = "✅" if count >= 3 else "⚠️"
        print(f"  {status} {cmd}: {count} examples")
    
    print("\nDirection Coverage:")
    for direction, count in directions.items():
        status = "✅" if count >= 5 else "⚠️"
        print(f"  {status} {direction}: {count} examples")
    
    total_commands = sum(commands.values())
    print(f"\nTotal command tags: {total_commands}")
    
    return all(count >= 3 for count in commands.values())

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test aria movement dataset and generation")
    parser.add_argument("--dataset", default="datasets/chat/aria_movement", help="Path to dataset")
    parser.add_argument("--test-model", action="store_true", help="Test base model generation (slow)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate dataset")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("ARIA MOVEMENT DATASET VALIDATION")
    print("=" * 70)
    
    # Load dataset
    try:
        train_data, test_data = load_dataset(args.dataset)
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return 1
    
    # Validate coverage
    if not validate_command_coverage(train_data):
        print("\n⚠️  Warning: Some command types have low coverage")
    else:
        print("\n✅ All command types have sufficient coverage")
    
    if args.validate_only:
        return 0
    
    # Test model generation (optional)
    if args.test_model:
        test_base_model_generation()
    else:
        print("\n💡 Tip: Run with --test-model to see base model responses before training")
    
    print("\n" + "=" * 70)
    print("VALIDATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Train model: python .\\scripts\\autotrain.py --config autotrain_aria.yaml --job aria_movement_quick")
    print("2. Test trained model: python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model data_out\\aria_models\\aria_quick")
    print("3. Deploy: Copy adapter to data_out\\lora_training\\lora_adapter")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
