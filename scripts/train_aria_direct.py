"""
Direct Aria Movement Training Script
Simplified training that avoids orchestrator complexity
"""
import sys
import json
import torch
from pathlib import Path
from datetime import datetime
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType

def format_chat_for_training(example, tokenizer):
    """Convert chat format to training format"""
    messages = example['messages']
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
    return {'text': text}

def tokenize_function(examples, tokenizer, max_length=512):
    """Tokenize the text"""
    outputs = tokenizer(
        examples['text'],
        truncation=True,
        max_length=max_length,
        padding=False,
        return_tensors=None
    )
    outputs['labels'] = outputs['input_ids'].copy()
    return outputs

def main():
    print("=" * 70)
    print("ARIA MOVEMENT TRAINING - DIRECT METHOD")
    print("=" * 70)
    
    # Configuration
    model_id = "microsoft/Phi-3.5-mini-instruct"
    dataset_path = "datasets/chat/aria_movement"
    output_dir = "data_out/aria_models/aria_direct"
    
    max_train_samples = 40
    max_eval_samples = 10
    epochs = 2
    learning_rate = 0.0003
    batch_size = 2
    
    print(f"\n[CONFIG] Configuration:")
    print(f"  Model: {model_id}")
    print(f"  Dataset: {dataset_path}")
    print(f"  Output: {output_dir}")
    print(f"  Samples: {max_train_samples} train, {max_eval_samples} eval")
    print(f"  Epochs: {epochs}")
    print(f"  Learning rate: {learning_rate}")
    print(f"  Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    # Load tokenizer
    print("\n[LOAD] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    print("[OK] Tokenizer loaded")
    
    # Load dataset
    print("\n[DATA] Loading dataset...")
    dataset = load_dataset('json', data_files={
        'train': f'{dataset_path}/train.json',
        'test': f'{dataset_path}/test.json'
    })
    
    print(f"  Train: {len(dataset['train'])} examples")
    print(f"  Test: {len(dataset['test'])} examples")
    
    # Format and tokenize
    print(f"\n[FORMAT] Formatting chat messages...")
    dataset = dataset.map(
        lambda x: format_chat_for_training(x, tokenizer),
        remove_columns=dataset['train'].column_names
    )
    
    print("[TOKENIZE] Tokenizing...")
    dataset = dataset.map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        remove_columns=['text']
    )
    
    # Limit samples
    train_dataset = dataset['train'].select(range(min(max_train_samples, len(dataset['train']))))
    eval_dataset = dataset['test'].select(range(min(max_eval_samples, len(dataset['test']))))
    
    print(f"[OK] Prepared {len(train_dataset)} train, {len(eval_dataset)} eval samples")
    
    # Load model
    print("\n[MODEL] Loading base model...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
        low_cpu_mem_usage=True
    )
    print("[OK] Base model loaded")
    
    # Configure LoRA
    print("\n[LORA] Configuring LoRA...")
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    print("[OK] LoRA configured")
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=4,
        learning_rate=learning_rate,
        lr_scheduler_type="cosine",
        warmup_steps=10,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        fp16=torch.cuda.is_available(),
        report_to="none",
        remove_unused_columns=False,
        gradient_checkpointing=False,  # Disabled - causes issues with LoRA
        optim="adamw_torch"
    )
    
    # Data collator - use for sequence classification to handle chat format properly
    from transformers import DataCollatorForSeq2Seq
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True
    )
    
    # Trainer
    print("\n[TRAINER] Initializing trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator
    )
    
    # Train!
    print("\n[TRAIN] Starting training...")
    print("=" * 70)
    
    start_time = datetime.now()
    trainer.train()
    end_time = datetime.now()
    
    print("=" * 70)
    print(f"[COMPLETE] Training completed in {(end_time - start_time).total_seconds():.1f} seconds")
    
    # Save
    print("\n[SAVE] Saving model...")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    # Save training info
    info = {
        "model_id": model_id,
        "dataset": dataset_path,
        "train_samples": len(train_dataset),
        "eval_samples": len(eval_dataset),
        "epochs": epochs,
        "learning_rate": learning_rate,
        "training_time_seconds": (end_time - start_time).total_seconds(),
        "completed_at": end_time.isoformat()
    }
    
    with open(Path(output_dir) / "training_info.json", 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"[OK] Model saved to: {output_dir}")
    
    # Test generation
    print("\n[TEST] Testing generation...")
    test_prompts = [
        "Move Aria left",
        "Make her wave",
        "Walk right"
    ]
    
    model.eval()
    for prompt in test_prompts:
        messages = [{"role": "user", "content": prompt}]
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
        has_tag = '[aria:' in response.lower()
        
        print(f"\n  Prompt: {prompt}")
        print(f"  Response: {response}")
        print(f"  Tag present: {'[YES]' if has_tag else '[NO]'}")
    
    print("\n" + "=" * 70)
    print("[SUCCESS] TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"1. Test with chat CLI:")
    print(f"   python .\\talk-to-ai\\src\\chat_cli.py --provider lora --model {output_dir}")
    print(f"\n2. Deploy to production:")
    print(f"   Copy-Item -Recurse {output_dir} data_out\\lora_training\\lora_adapter")
    print(f"\n3. Restart Azure Functions to load new model")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Training interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
