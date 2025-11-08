import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Iterable, List

try:
    import yaml  # type: ignore
except Exception as e:
    raise SystemExit("pyyaml is required. Install with: pip install pyyaml")

# Optional imports for real training
try:
    import torch
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        DataCollatorForLanguageModeling,
    )
    from peft import LoraConfig, get_peft_model, PeftModel
    from transformers import TrainerCallback
except Exception:
    # We'll allow dry-run without these
    torch = None  # type: ignore
    load_dataset = None  # type: ignore
    AutoModelForCausalLM = AutoTokenizer = Trainer = TrainingArguments = DataCollatorForLanguageModeling = None  # type: ignore
    LoraConfig = get_peft_model = PeftModel = None  # type: ignore
    TrainerCallback = None  # type: ignore


@dataclass
class Config:
    model: str
    finetune_dataset: str
    save_dir: str
    finetune_train_nsamples: int | None
    finetune_test_nsamples: int | None
    finetune_train_batch_size: int
    finetune_test_batch_size: int
    finetune_train_seqlen: int
    finetune_test_seqlen: int
    learning_rate: float
    lora_dropout: float
    epochs: int
    eval_steps: int
    save_steps: int
    gradient_checkpointing: bool
    seed: int


def read_yaml(yaml_path: Path) -> Dict[str, Any]:
    with yaml_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_path(p: str) -> Path:
    # allow tokens like mount/<run_id>/dataset to be overridden by --dataset
    return Path(p).expanduser()


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def count_records(path: Path) -> int:
    n = 0
    for _ in iter_jsonl(path):
        n += 1
    return n


def validate_sample(path: Path) -> Dict[str, Any]:
    for obj in iter_jsonl(path):
        msgs = obj.get("messages")
        if isinstance(msgs, list) and len(msgs) >= 2:
            return obj
    raise RuntimeError(f"No valid chat records found in {path}")


def build_text_from_messages(messages: List[Dict[str, str]]) -> str:
    # Generic fallback: simple chat turn format
    parts: List[str] = []
    for m in messages:
        role = m.get("role", "").lower()
        content = m.get("content", "")
        if role == "system":
            parts.append(f"<|system|>\n{content}\n")
        elif role == "user":
            parts.append(f"<|user|>\n{content}\n")
        elif role == "assistant":
            parts.append(f"<|assistant|>\n{content}\n")
        else:
            parts.append(f"<|user|>\n{content}\n")
    return "\n".join(parts).strip()


def make_hf_dataset_from_files(train_files: List[str], eval_files: List[str], streaming: bool = True):
    if load_dataset is None:
        raise RuntimeError("HuggingFace datasets not available. Install 'datasets' to load datasets.")
    data_files = {"train": train_files, "validation": eval_files}
    ds = load_dataset("json", data_files=data_files, streaming=streaming)
    return ds


def _read_text_source(path_or_url: str) -> Iterable[str]:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        import urllib.request
        with urllib.request.urlopen(path_or_url) as resp:  # nosec B310
            for line in resp.read().decode("utf-8").splitlines():
                yield line
    else:
        p = Path(path_or_url)
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                yield line.rstrip("\n")


def parse_manifest(path_or_url: str) -> List[str]:
    urls: List[str] = []
    lower = path_or_url.lower()
    if lower.endswith(".json"):
        import json as _json
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            import urllib.request
            with urllib.request.urlopen(path_or_url) as resp:  # nosec B310
                obj = _json.loads(resp.read().decode("utf-8"))
        else:
            with Path(path_or_url).open("r", encoding="utf-8") as f:
                obj = _json.load(f)
        if isinstance(obj, dict):
            for key in ("train", "validation", "urls", "files"):
                v = obj.get(key)
                if isinstance(v, list):
                    urls.extend([str(x) for x in v])
            if not urls and "url" in obj:
                urls.append(str(obj["url"]))
        elif isinstance(obj, list):
            urls.extend([str(x) for x in obj])
    elif lower.endswith(".jsonl"):
        import json as _json
        for line in _read_text_source(path_or_url):
            if not line.strip():
                continue
            try:
                rec = _json.loads(line)
                if isinstance(rec, str):
                    urls.append(rec)
                elif isinstance(rec, dict) and "url" in rec:
                    urls.append(str(rec["url"]))
            except Exception:
                urls.append(line.strip())
    else:
        for line in _read_text_source(path_or_url):
            if line.strip():
                urls.append(line.strip())
    # Dedupe
    seen = set()
    uniq: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def main():
    ap = argparse.ArgumentParser(description="Train LoRA on chat dataset using lora.yaml config")
    ap.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "lora" / "lora.yaml"))
    ap.add_argument("--dataset", default=str(Path(__file__).resolve().parents[1] / "data"))
    ap.add_argument("--dry-run", action="store_true", help="Validate dataset/config only; no model download")
    ap.add_argument("--max-train-samples", type=int, default=None, help="Limit train examples (for smoke test)")
    ap.add_argument("--max-eval-samples", type=int, default=None, help="Limit eval examples (for smoke test)")
    ap.add_argument("--hf-model-id", default=None, help="Override HF model id (e.g., microsoft/Phi-3.5-mini-instruct)")
    ap.add_argument("--no-stream", action="store_true", help="Disable streaming mode for datasets")
    ap.add_argument("--deepspeed", default=None, help="Path to DeepSpeed config JSON to enable ZeRO (multi-GPU)")
    ap.add_argument("--train-manifest", default=None, help="Path or URL to manifest of training files (txt/json/jsonl)")
    ap.add_argument("--eval-manifest", default=None, help="Path or URL to manifest of eval files (txt/json/jsonl)")
    ap.add_argument("--save-dir", default=None, help="Override output directory (else from config or defaults)")
    # Optional overrides for HPO/cloud runs
    ap.add_argument("--learning-rate", type=float, default=None, help="Override learning_rate from config")
    ap.add_argument("--lora-dropout", type=float, default=None, help="Override lora_dropout from config")
    ap.add_argument("--epochs", type=int, default=None, help="Override epochs from config")
    ap.add_argument("--train-batch-size", type=int, default=None, help="Override finetune_train_batch_size from config")
    ap.add_argument("--eval-batch-size", type=int, default=None, help="Override finetune_test_batch_size from config")
    ap.add_argument("--seed", type=int, default=None, help="Override seed from config")
    args = ap.parse_args()

    cfg_raw = read_yaml(Path(args.config))
    cfg = Config(
        model=cfg_raw.get("model") or "Phi-3.6-mini-instruct",
        finetune_dataset=cfg_raw.get("finetune_dataset") or str(Path(args.dataset)),
        save_dir=(args.save_dir or cfg_raw.get("save_dir") or str(Path(__file__).resolve().parents[1] / "outputs")),
        finetune_train_nsamples=cfg_raw.get("finetune_train_nsamples"),
        finetune_test_nsamples=cfg_raw.get("finetune_test_nsamples"),
        finetune_train_batch_size=int(cfg_raw.get("finetune_train_batch_size") or 2),
        finetune_test_batch_size=int(cfg_raw.get("finetune_test_batch_size") or 2),
        finetune_train_seqlen=int(cfg_raw.get("finetune_train_seqlen") or 1024),
        finetune_test_seqlen=int(cfg_raw.get("finetune_test_seqlen") or 2048),
        learning_rate=float(cfg_raw.get("learning_rate") or 2e-4),
        lora_dropout=float(cfg_raw.get("lora_dropout") or 0.1),
        epochs=int(cfg_raw.get("epochs") or 1),
        eval_steps=int(cfg_raw.get("eval_steps") or cfg_raw.get("eval_steps", 64)),
        save_steps=int(cfg_raw.get("save_steps") or 64),
        gradient_checkpointing=bool(cfg_raw.get("gradient_checkpointing") or False),
        seed=int(cfg_raw.get("seed") or 42),
    )

    # Apply CLI overrides for HPO or cloud jobs
    if getattr(args, "learning_rate", None) is not None:
        cfg.learning_rate = float(args.learning_rate)
    if getattr(args, "lora_dropout", None) is not None:
        cfg.lora_dropout = float(args.lora_dropout)
    if getattr(args, "epochs", None) is not None:
        cfg.epochs = int(args.epochs)
    if getattr(args, "train_batch_size", None) is not None:
        cfg.finetune_train_batch_size = int(args.train_batch_size)
    if getattr(args, "eval_batch_size", None) is not None:
        cfg.finetune_test_batch_size = int(args.eval_batch_size)
    if getattr(args, "seed", None) is not None:
        cfg.seed = int(args.seed)

    # Resolve data sources: manifests or local files
    train_files: List[str] = []
    eval_files: List[str] = []
    # CLI overrides take precedence
    train_manifest = getattr(args, "train_manifest", None)
    eval_manifest = getattr(args, "eval_manifest", None)
    if train_manifest or eval_manifest:
        if train_manifest:
            train_files = parse_manifest(train_manifest)
        if eval_manifest:
            eval_files = parse_manifest(eval_manifest)
        if not train_files:
            raise RuntimeError("No train files found from manifest")
        if not eval_files:
            # Fallback: use a small subset of train for eval
            eval_files = train_files[:1]
    else:
        dataset_dir = Path(args.dataset) if args.dataset else resolve_path(cfg.finetune_dataset)
        train_path = dataset_dir / "train.json"
        test_path = dataset_dir / "test.json"
        if not train_path.exists() or not test_path.exists():
            raise FileNotFoundError(f"Expected dataset files at: {train_path} and {test_path}")
        train_files = [str(train_path)]
        eval_files = [str(test_path)]

    # Dry run: count/validate records only (no model/tokenizer downloads)
    if args.dry_run:
        # For remote manifests we won't fetch all content; just display sources
        if train_manifest or eval_manifest:
            print("Dry run OK.")
            print({
                "train_files": train_files[:5],
                "eval_files": eval_files[:5],
                "note": "Counting skipped for remote manifests"
            })
            return
        n_train = count_records(Path(train_files[0]))
        n_test = count_records(Path(eval_files[0]))
        sample = validate_sample(Path(train_files[0]))
        print("Dry run OK.")
        print({
            "train_examples": n_train,
            "test_examples": n_test,
            "sample": sample,
        })
        return

    # Real training requires heavy deps
    if AutoTokenizer is None or AutoModelForCausalLM is None or load_dataset is None or torch is None:
        raise RuntimeError("Training dependencies not installed. Install: transformers, datasets, peft, accelerate, torch")

    # Resolve model id
    hf_model_id = args.hf_model_id or os.environ.get("HF_MODEL_ID")
    if hf_model_id is None:
        # Best-effort mapping for local runs
        # If the configured model isn't an HF id, default to a widely-available one
        hf_model_id = {
            "Phi-3.6-mini-instruct": "microsoft/Phi-3.5-mini-instruct",
        }.get(cfg.model, cfg.model)

    tokenizer = AutoTokenizer.from_pretrained(hf_model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    def preprocess(examples):
        # Handle both single example and batched mapping
        texts = []
        if isinstance(examples, dict) and "messages" in examples:
            msgs = examples["messages"]
            # Batched: list of lists
            if isinstance(msgs, list) and msgs and isinstance(msgs[0], list):
                for obj in msgs:
                    if obj and isinstance(obj[0], dict):
                        text = tokenizer.apply_chat_template(
                            obj,
                            tokenize=False,
                            add_generation_prompt=False,
                        ) if hasattr(tokenizer, "apply_chat_template") else build_text_from_messages(obj)
                        texts.append(text)
            # Single example: list of dicts
            elif isinstance(msgs, list) and msgs and isinstance(msgs[0], dict):
                text = tokenizer.apply_chat_template(
                    msgs,
                    tokenize=False,
                    add_generation_prompt=False,
                ) if hasattr(tokenizer, "apply_chat_template") else build_text_from_messages(msgs)
                texts.append(text)

        if not texts:
            return {}
        tokenized = tokenizer(texts, truncation=True, max_length=cfg.finetune_train_seqlen, padding=False)
        return tokenized

    ds = make_hf_dataset_from_files(train_files, eval_files, streaming=not args.no_stream)

    # For streaming datasets, map with batched=False
    train_ds = ds["train"]
    eval_ds = ds["validation"]

    if args.max_train_samples:
        train_ds = train_ds.take(args.max_train_samples)
    if args.max_eval_samples:
        eval_ds = eval_ds.take(args.max_eval_samples)

    # Load base model
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    base_model = AutoModelForCausalLM.from_pretrained(
        hf_model_id,
        torch_dtype=dtype,
        device_map="auto",
    )

    if cfg.gradient_checkpointing:
        base_model.gradient_checkpointing_enable()
        if hasattr(base_model.config, "use_cache"):
            base_model.config.use_cache = False

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "fc1", "fc2"],
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base_model, lora_config)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    out_dir = Path(cfg.save_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=cfg.finetune_train_batch_size,
        per_device_eval_batch_size=cfg.finetune_test_batch_size,
        eval_strategy="steps",
        eval_steps=cfg.eval_steps,
        save_steps=cfg.save_steps,
        num_train_epochs=cfg.epochs,
        learning_rate=cfg.learning_rate,
        logging_steps=max(1, cfg.eval_steps // 2),
        bf16=torch.cuda.is_available(),
        fp16=not torch.cuda.is_available(),
        gradient_checkpointing=cfg.gradient_checkpointing,
        remove_unused_columns=False,
        save_total_limit=3,
        seed=cfg.seed,
        deepspeed=args.deepspeed if args.deepspeed else None,
        ddp_find_unused_parameters=False,
    )

    # Metrics logger
    from metrics_logger import MetricsLogger  # local import
    out_dir = Path(cfg.save_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    logger = MetricsLogger(out_dir)

    class PerplexityLoggingCallback(TrainerCallback if TrainerCallback else object):  # type: ignore
        def on_evaluate(self, args, state, control, metrics=None, **kwargs):  # type: ignore[no-redef]
            if metrics and "eval_loss" in metrics and metrics["eval_loss"] is not None:
                try:
                    ppl = math.exp(float(metrics["eval_loss"]))
                    rec = {"step": int(getattr(state, "global_step", 0)), "eval_loss": float(metrics["eval_loss"]), "eval_perplexity": float(ppl)}
                    logger.log(rec)
                except Exception:
                    pass

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds.map(preprocess) if hasattr(train_ds, "map") else train_ds,
        eval_dataset=eval_ds.map(preprocess) if hasattr(eval_ds, "map") else eval_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )
    if TrainerCallback is not None:
        trainer.add_callback(PerplexityLoggingCallback())
        # Add OpenTelemetry tracing callback if available
        try:
            from otel_callback import OpenTelemetryTrainerCallback
            trainer.add_callback(OpenTelemetryTrainerCallback())
        except Exception:
            pass

    # Pre-training evaluation (perplexity)
    pre_metrics = trainer.evaluate()
    if "eval_loss" in pre_metrics and pre_metrics["eval_loss"] is not None:
        try:
            ppl = math.exp(float(pre_metrics["eval_loss"]))
            rec = {"phase": "pre", "eval_loss": float(pre_metrics["eval_loss"]), "eval_perplexity": float(ppl)}
            print(rec)
            logger.log(rec)
        except Exception:
            pass

    trainer.train()
    # Post-training evaluation (perplexity)
    post_metrics = trainer.evaluate()
    if "eval_loss" in post_metrics and post_metrics["eval_loss"] is not None:
        try:
            ppl = math.exp(float(post_metrics["eval_loss"]))
            rec = {"phase": "post", "eval_loss": float(post_metrics["eval_loss"]), "eval_perplexity": float(ppl)}
            print(rec)
            logger.log(rec)
        except Exception:
            pass
    # Save adapters only
    trainer.model.save_pretrained(str(out_dir / "lora_adapter"))
    tokenizer.save_pretrained(str(out_dir / "tokenizer"))

    print(f"Training complete. Artifacts saved to: {out_dir}")


if __name__ == "__main__":
    main()
