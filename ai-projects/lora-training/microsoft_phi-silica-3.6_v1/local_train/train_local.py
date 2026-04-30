#!/usr/bin/env python3
"""
Local LoRA fine-tuning script - simplified for rapid local iteration.
No Azure dependencies, focused on consumer hardware (single GPU or CPU).
"""
import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

try:
    import yaml
except ImportError:
    raise SystemExit("Install pyyaml: pip install pyyaml") from None

try:
    import torch
    from peft import (LoraConfig, PeftModel, get_peft_model,
                      prepare_model_for_kbit_training)
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              DataCollatorForLanguageModeling, Trainer,
                              TrainingArguments)

    from datasets import load_dataset
except ImportError as e:
    raise SystemExit(
        f"Missing training dependencies: {e}\nInstall with: pip install -r requirements.txt"
    ) from e


@dataclass
class LocalConfig:
    """Local training configuration"""

    model_id: str = "microsoft/Phi-3.5-mini-instruct"
    train_file: str = "train.json"
    eval_file: str = "test.json"
    output_dir: str = "outputs"

    # Training params
    num_epochs: int = 3
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    max_seq_length: int = 512
    warmup_steps: int = 100

    # LoRA params
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05

    # Optimization
    use_fp16: bool = False
    use_bf16: bool = True
    gradient_checkpointing: bool = True
    use_8bit: bool = False
    use_4bit: bool = False

    # Logging
    logging_steps: int = 10
    eval_steps: int = 50
    save_steps: int = 100
    save_total_limit: int = 3

    seed: int = 42


def load_config(config_path: Path) -> LocalConfig:
    """Load config from YAML or use defaults"""
    if config_path.exists():
        with config_path.open("r") as f:
            cfg_dict = yaml.safe_load(f) or {}
        return LocalConfig(
            **{k: v for k, v in cfg_dict.items() if hasattr(LocalConfig, k)}
        )
    return LocalConfig()


def format_chat_messages(messages: List[Dict[str, str]], tokenizer) -> str:
    """Format chat messages using tokenizer template or fallback"""
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )

    # Fallback formatting
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            parts.append(f"<|system|>\n{content}\n")
        elif role == "user":
            parts.append(f"<|user|>\n{content}\n")
        elif role == "assistant":
            parts.append(f"<|assistant|>\n{content}\n")
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Local LoRA fine-tuning")
    parser.add_argument(
        "--config", type=str, default="local_config.yaml", help="Config file"
    )
    parser.add_argument(
        "--data-dir", type=str, default="../data", help="Dataset directory"
    )
    parser.add_argument("--model", type=str, help="Override model ID")
    parser.add_argument("--output", type=str, help="Override output directory")
    parser.add_argument("--epochs", type=int, help="Override epochs")
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument("--max-samples", type=int, help="Limit samples for testing")
    parser.add_argument("--resume", type=str, help="Resume from checkpoint")
    parser.add_argument("--eval-only", action="store_true", help="Only run evaluation")
    args = parser.parse_args()

    # Load config
    config_path = Path(__file__).parent / args.config
    cfg = load_config(config_path)

    # Apply CLI overrides
    if args.model:
        cfg.model_id = args.model
    if args.output:
        cfg.output_dir = args.output
    if args.epochs:
        cfg.num_epochs = args.epochs
    if args.batch_size:
        cfg.batch_size = args.batch_size

    # Setup paths
    data_dir = Path(args.data_dir).resolve()
    train_path = data_dir / cfg.train_file
    eval_path = data_dir / cfg.eval_file
    output_dir = Path(cfg.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("LOCAL LORA FINE-TUNING")
    print(f"{'='*60}")
    print(f"Model: {cfg.model_id}")
    print(f"Train: {train_path}")
    print(f"Eval: {eval_path}")
    print(f"Output: {output_dir}")
    print(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    print(f"{'='*60}\n")

    # Load tokenizer
    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Preprocessing function
    def preprocess_function(examples):
        texts = []
        for msgs in examples["messages"]:
            text = format_chat_messages(msgs, tokenizer)
            texts.append(text)

        return tokenizer(
            texts,
            truncation=True,
            max_length=cfg.max_seq_length,
            padding=False,
        )

    # Load datasets
    print("Loading datasets...")
    dataset = load_dataset(
        "json",
        data_files={"train": str(train_path), "validation": str(eval_path)},
    )

    if args.max_samples:
        dataset["train"] = dataset["train"].select(
            range(min(args.max_samples, len(dataset["train"])))
        )
        dataset["validation"] = dataset["validation"].select(
            range(min(args.max_samples // 4, len(dataset["validation"])))
        )

    print(f"Train samples: {len(dataset['train'])}")
    print(f"Eval samples: {len(dataset['validation'])}")

    # Tokenize
    print("Tokenizing...")
    tokenized_datasets = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset["train"].column_names,
    )

    # Load model
    print(f"Loading model: {cfg.model_id}")

    quantization_config = None
    if cfg.use_4bit:
        from transformers import BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16 if cfg.use_bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )
    elif cfg.use_8bit:
        from transformers import BitsAndBytesConfig

        quantization_config = BitsAndBytesConfig(load_in_8bit=True)

    model = AutoModelForCausalLM.from_pretrained(
        cfg.model_id,
        quantization_config=quantization_config,
        device_map="auto" if torch.cuda.is_available() else None,
        trust_remote_code=True,
        torch_dtype=(
            torch.bfloat16
            if cfg.use_bf16
            else (torch.float16 if cfg.use_fp16 else torch.float32)
        ),
    )

    if quantization_config:
        model = prepare_model_for_kbit_training(model)

    if cfg.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    # Configure LoRA
    print("Configuring LoRA...")
    lora_config = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        target_modules=[
            "q_proj",
            "v_proj",
            "k_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )

    if args.resume:
        print(f"Resuming from: {args.resume}")
        model = PeftModel.from_pretrained(model, args.resume)
    else:
        model = get_peft_model(model, lora_config)

    model.print_trainable_parameters()

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=cfg.num_epochs,
        per_device_train_batch_size=cfg.batch_size,
        per_device_eval_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        warmup_steps=cfg.warmup_steps,
        logging_steps=cfg.logging_steps,
        eval_steps=cfg.eval_steps,
        save_steps=cfg.save_steps,
        eval_strategy="steps",
        save_strategy="steps",
        save_total_limit=cfg.save_total_limit,
        fp16=cfg.use_fp16 and not cfg.use_bf16,
        bf16=cfg.use_bf16,
        gradient_checkpointing=cfg.gradient_checkpointing,
        dataloader_pin_memory=True,
        dataloader_num_workers=0,
        remove_unused_columns=False,
        seed=cfg.seed,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        report_to="none",  # Disable W&B, tensorboard, etc.
    )

    # Data collator
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # Evaluate before training
    if not args.resume:
        print("\nPre-training evaluation...")
        pre_metrics = trainer.evaluate()
        try:
            ppl = math.exp(pre_metrics["eval_loss"])
            print(f"Pre-training perplexity: {ppl:.2f}")
        except Exception:
            pass

    # Train or evaluate
    if args.eval_only:
        print("\nRunning evaluation...")
        metrics = trainer.evaluate()
        print("\nEvaluation results:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
    else:
        print("\nStarting training...")
        trainer.train(resume_from_checkpoint=args.resume if args.resume else None)

        # Post-training evaluation
        print("\nPost-training evaluation...")
        post_metrics = trainer.evaluate()
        try:
            ppl = math.exp(post_metrics["eval_loss"])
            print(f"Post-training perplexity: {ppl:.2f}")
        except Exception:
            pass

        # Save final model
        final_dir = output_dir / "final"
        print(f"\nSaving final model to: {final_dir}")
        trainer.model.save_pretrained(final_dir)
        tokenizer.save_pretrained(final_dir)

        # Save metrics
        metrics_file = output_dir / "metrics.json"
        with metrics_file.open("w") as f:
            json.dump(post_metrics, f, indent=2)

        print(f"\n{'='*60}")
        print("Training complete!")
        print(f"Model saved to: {final_dir}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
