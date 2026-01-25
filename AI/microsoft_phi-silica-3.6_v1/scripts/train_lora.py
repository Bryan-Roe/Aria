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
    # Optional: install torch if missing
    try:
        import torch  # pip install torch  # type: ignore[reportMissingImports]
    except ImportError:
        raise SystemExit(
            "PyTorch is required. Install with: pip install torch")
    from datasets import load_dataset  # type: ignore[import]
    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
            DataCollatorForLanguageModeling,
        )
        from peft import LoraConfig, get_peft_model, PeftModel
        from transformers import TrainerCallback, EarlyStoppingCallback
    except ImportError:
        raise SystemExit(
            "Transformers is required. Install with: pip install transformers"
        )
except Exception as e:
    # Provide visibility into which dependency import failed
    import traceback
    print(f"[import-debug] training dependency import failed: {e}")
    traceback.print_exc()
    # We'll allow dry-run without these by nulling all symbols
    torch = None  # type: ignore
    load_dataset = None  # type: ignore
    AutoModelForCausalLM = AutoTokenizer = Trainer = TrainingArguments = DataCollatorForLanguageModeling = None  # type: ignore
    LoraConfig = get_peft_model = PeftModel = None  # type: ignore
    TrainerCallback = None  # type: ignore
    EarlyStoppingCallback = None  # type: ignore


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
    warmup_steps: int
    gradient_accumulation_steps: int
    max_grad_norm: float
    early_stopping_patience: int
    early_stopping_threshold: float


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
    """Convert messages to training text with improved formatting and end tokens."""
    parts: List[str] = []
    for m in messages:
        role = m.get("role", "").lower()
        content = m.get("content", "").strip()
        if not content:  # Skip empty messages
            continue
        if role == "system":
            parts.append(f"<|system|>\n{content}<|end|>\n")
        elif role == "user":
            parts.append(f"<|user|>\n{content}<|end|>\n")
        elif role == "assistant":
            parts.append(f"<|assistant|>\n{content}<|end|>\n")
    return "".join(parts)


def make_hf_dataset_from_files(train_files: List[str], eval_files: List[str], streaming: bool = True):
    if load_dataset is None:
        raise RuntimeError(
            "HuggingFace datasets not available. Install 'datasets' to load datasets.")
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
    ap = argparse.ArgumentParser(
        description="Train LoRA on chat dataset using lora.yaml config")
    ap.add_argument(
        "--config", default=str(Path(__file__).resolve().parents[1] / "lora" / "lora.yaml"))
    ap.add_argument(
        "--dataset", default=str(Path(__file__).resolve().parents[1] / "data"))
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate dataset/config only; no model download")
    ap.add_argument("--max-train-samples", type=int, default=None,
                    help="Limit train examples (for smoke test)")
    ap.add_argument("--max-eval-samples", type=int, default=None,
                    help="Limit eval examples (for smoke test)")
    ap.add_argument("--hf-model-id", default=None,
                    help="Override HF model id (e.g., microsoft/Phi-3.5-mini-instruct)")
    ap.add_argument("--no-stream", action="store_true",
                    help="Disable streaming mode for datasets")
    ap.add_argument("--deepspeed", default=None,
                    help="Path to DeepSpeed config JSON to enable ZeRO (multi-GPU)")
    ap.add_argument("--train-manifest", default=None,
                    help="Path or URL to manifest of training files (txt/json/jsonl)")
    ap.add_argument("--eval-manifest", default=None,
                    help="Path or URL to manifest of eval files (txt/json/jsonl)")
    ap.add_argument("--save-dir", default=None,
                    help="Override output directory (else from config or defaults)")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu", "directml", "mps"],
                    help="Device preference: auto selects best available (cuda>mps>directml>cpu)")
    # Optional overrides for HPO/cloud runs
    ap.add_argument("--learning-rate", type=float, default=None,
                    help="Override learning_rate from config")
    ap.add_argument("--lora-dropout", type=float, default=None,
                    help="Override lora_dropout from config")
    ap.add_argument("--epochs", type=int, default=None,
                    help="Override epochs from config")
    ap.add_argument("--train-batch-size", type=int, default=None,
                    help="Override finetune_train_batch_size from config")
    ap.add_argument("--eval-batch-size", type=int, default=None,
                    help="Override finetune_test_batch_size from config")
    ap.add_argument("--seed", type=int, default=None,
                    help="Override seed from config")
    args = ap.parse_args()

    # Initialize tracing (best-effort). This allows the optional
    # OpenTelemetryTrainerCallback to get an active tracer if available.
    # Optional tracing import (ignore if missing)
    try:
        from shared.tracing import init_tracing  # type: ignore
        init_tracing(service_name="train_lora")
    except Exception as _e:
        print(f"[tracing] init skipped in train_lora: {_e}")

    cfg_raw = read_yaml(Path(args.config))
    cfg = Config(
        model=cfg_raw.get("model") or "Phi-3.6-mini-instruct",
        finetune_dataset=cfg_raw.get(
            "finetune_dataset") or str(Path(args.dataset)),
        save_dir=(args.save_dir or cfg_raw.get("save_dir") or str(
            Path(__file__).resolve().parents[1] / "outputs")),
        finetune_train_nsamples=cfg_raw.get("finetune_train_nsamples"),
        finetune_test_nsamples=cfg_raw.get("finetune_test_nsamples"),
        finetune_train_batch_size=int(
            cfg_raw.get("finetune_train_batch_size") or 2),
        finetune_test_batch_size=int(
            cfg_raw.get("finetune_test_batch_size") or 2),
        finetune_train_seqlen=int(cfg_raw.get(
            "finetune_train_seqlen") or 1024),
        finetune_test_seqlen=int(cfg_raw.get("finetune_test_seqlen") or 2048),
        learning_rate=float(cfg_raw.get("learning_rate") or 2e-4),
        lora_dropout=float(cfg_raw.get("lora_dropout") or 0.1),
        epochs=int(cfg_raw.get("epochs") or 1),
        eval_steps=int(cfg_raw.get("eval_steps", 64)),
        save_steps=int(cfg_raw.get("save_steps") or 64),
        gradient_checkpointing=bool(cfg_raw.get(
            "gradient_checkpointing") or False),
        seed=int(cfg_raw.get("seed") or 42),
        warmup_steps=int(cfg_raw.get("warmup_steps") or 100),
        gradient_accumulation_steps=int(
            cfg_raw.get("gradient_accumulation_steps") or 4),
        max_grad_norm=float(cfg_raw.get("max_grad_norm") or 1.0),
        early_stopping_patience=int(
            cfg_raw.get("early_stopping_patience") or 3),
        early_stopping_threshold=float(
            cfg_raw.get("early_stopping_threshold") or 0.01),
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
        dataset_path = Path(args.dataset) if args.dataset else resolve_path(
            cfg.finetune_dataset)
        if dataset_path.is_file():
            # Allow direct file usage (.json or .jsonl)
            if dataset_path.suffix.lower() in (".json", ".jsonl"):
                train_files = [str(dataset_path)]
                eval_files = [str(dataset_path)]
            else:
                raise FileNotFoundError(
                    f"Unsupported dataset file type: {dataset_path}")
        else:
            # Directory: accept train.json/test.json or train.jsonl/test.jsonl; fallback to single train file present
            candidates = [
                (dataset_path / "train.json", dataset_path / "test.json"),
                (dataset_path / "train.jsonl", dataset_path / "test.jsonl"),
            ]
            found = False
            for t_path, v_path in candidates:
                if t_path.exists() and v_path.exists():
                    train_files = [str(t_path)]
                    eval_files = [str(v_path)]
                    found = True
                    break
            if not found:
                # Fallbacks: if any train.* exists, use it for both train/val
                t_candidates = [dataset_path / "train.json",
                                dataset_path / "train.jsonl"]
                t_use = next((p for p in t_candidates if p.exists()), None)
                if t_use is None:
                    raise FileNotFoundError(
                        f"Expected dataset files at: {dataset_path}/train.json[.l] and optionally test.json[.l]")
                train_files = [str(t_use)]
                eval_candidates = [dataset_path /
                                   "test.json", dataset_path / "test.jsonl"]
                v_use = next((p for p in eval_candidates if p.exists()), None)
                eval_files = [str(v_use)] if v_use else [str(t_use)]

    # Determine and report device early (even for dry-run)
    chosen_device = "cpu"
    if args.device == "auto":
        if torch is not None and getattr(torch, "cuda", None) and getattr(torch.cuda, "is_available", lambda: False)():
            chosen_device = "cuda"
        elif torch is not None and getattr(torch, "backends", None) and getattr(torch.backends, "mps", None) and getattr(torch.backends.mps, "is_available", lambda: False)():
            chosen_device = "mps"
        else:
            # Optional DirectML detection
            try:
                import torch_directml  # type: ignore
                chosen_device = "directml"
            except Exception:
                chosen_device = "cpu"
    else:
        chosen_device = args.device
    print(
        f"[device] selection={args.device} resolved={chosen_device} cuda_available={(getattr(torch, 'cuda', None) and getattr(torch.cuda, 'is_available', lambda: False)() if torch else False)}")

    # Dry run: count/validate records only (no model/tokenizer downloads)
    if args.dry_run:
        if train_manifest or eval_manifest:
            print("Dry run OK.")
            print({
                "device": chosen_device,
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
            "device": chosen_device,
            "train_examples": n_train,
            "test_examples": n_test,
            "sample": sample,
        })
        return

    # Real training requires heavy deps
    if AutoTokenizer is None or AutoModelForCausalLM is None or load_dataset is None or torch is None:
        missing = []
        if torch is None:
            missing.append("torch")
        if load_dataset is None:
            missing.append("datasets")
        if AutoTokenizer is None or AutoModelForCausalLM is None:
            missing.append("transformers")
        if LoraConfig is None:
            missing.append("peft")
        model_venv = Path(__file__).resolve().parents[1] / "venv"
        root_venv = Path(__file__).resolve().parents[3] / "venv"
        raise RuntimeError(
            "Training dependencies not installed or import failed.\n"
            f"missing={missing}\n"
            f"To fix (model env): {model_venv / 'Scripts' / 'pip.exe'} install transformers datasets peft accelerate torch\n"
            f"Alt (root env): {root_venv / 'Scripts' / 'pip.exe'} install transformers datasets peft accelerate torch\n"
            "After installing, re-run this script."
        )

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
            try:
                print(f"[preprocess] messages type: {type(msgs)}")
                if isinstance(msgs, dict):
                    print(
                        f"[preprocess] messages dict keys: {list(msgs.keys())}")
                    # Attempt to reconstruct per-sample conversations if messages is a dict of lists
                    # Expect shape: msgs[key][i] gives ith sample's list of that field
                    keys = list(msgs.keys())
                    batch_size = len(msgs[keys[0]]) if keys and isinstance(
                        msgs[keys[0]], list) else 0
                    print(
                        f"[preprocess] inferred batch_size from dict: {batch_size}")
                    for i in range(batch_size):
                        # Reconstruct sample i as list of dicts using available fields
                        sample_messages = []
                        # Try common fields 'role' and 'content'
                        roles = msgs.get('role', [])[
                            i] if 'role' in msgs else None
                        contents = msgs.get('content', [])[
                            i] if 'content' in msgs else None
                        if isinstance(roles, list) and isinstance(contents, list) and len(roles) == len(contents):
                            for r, c in zip(roles, contents):
                                sample_messages.append(
                                    {"role": r, "content": c})
                        else:
                            # Fallback: try to rebuild from a generic list of dicts if present
                            # msgs may have a single key representing the full objects
                            for k in keys:
                                candidate = msgs[k][i] if isinstance(
                                    msgs[k], list) else None
                                if isinstance(candidate, list) and candidate and isinstance(candidate[0], dict):
                                    sample_messages = candidate
                                    break
                        if sample_messages:
                            text = tokenizer.apply_chat_template(
                                sample_messages,
                                tokenize=False,
                                add_generation_prompt=False,
                            ) if hasattr(tokenizer, "apply_chat_template") else build_text_from_messages(sample_messages)
                            texts.append(text)
                # Batched: list of lists
                elif isinstance(msgs, list) and msgs and isinstance(msgs[0], list):
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
            except Exception as e:
                print(f"[preprocess] error reconstructing messages: {e}")
        # When using input_columns=["messages"], the function may receive just the messages column values
        elif isinstance(examples, list):
            msgs = examples
            if isinstance(msgs, list) and msgs and isinstance(msgs[0], list):
                for obj in msgs:
                    if obj and isinstance(obj[0], dict):
                        text = tokenizer.apply_chat_template(
                            obj,
                            tokenize=False,
                            add_generation_prompt=False,
                        ) if hasattr(tokenizer, "apply_chat_template") else build_text_from_messages(obj)
                        texts.append(text)

        if not texts:
            # Return empty dict for batch
            print("[preprocess] empty texts batch")
            return {"input_ids": [], "attention_mask": []}
        tokenized = tokenizer(
            texts, truncation=True, max_length=cfg.finetune_train_seqlen, padding=False)
        try:
            n_in = len(texts)
            n_out = len(tokenized.get("input_ids", []))
            print(
                f"[preprocess] batch texts={n_in} -> tokenized input_ids={n_out}")
        except Exception:
            pass
        # Return as dict of lists for batched mapping
        return tokenized

    ds = make_hf_dataset_from_files(
        train_files, eval_files, streaming=not args.no_stream)

    # For streaming datasets, map with batched=False
    train_ds = ds["train"]
    eval_ds = ds["validation"]
    # Debug raw dataset structure
    try:
        print(f"[debug] raw train columns: {train_ds.column_names}")
        sample0 = train_ds[0]
        print(f"[debug] raw train sample0 keys: {list(sample0.keys())}")
        if "messages" in sample0:
            print(
                f"[debug] raw train sample0 messages type: {type(sample0['messages'])}")
            if isinstance(sample0["messages"], list) and sample0["messages"]:
                print(
                    f"[debug] raw train sample0 messages[0] type: {type(sample0['messages'][0])}")
    except Exception as e:
        print(f"[debug] error inspecting raw dataset: {e}")

    if args.max_train_samples:
        train_ds = train_ds.take(args.max_train_samples)
    if args.max_eval_samples:
        eval_ds = eval_ds.take(args.max_eval_samples)

    # Load base model
    # DType selection: prefer bfloat16 on CUDA, else float32. (MPS/directml kept at float32 for stability.)
    use_cuda = (chosen_device == "cuda" and torch.cuda.is_available())
    dtype = torch.bfloat16 if use_cuda and hasattr(
        torch, "bfloat16") else torch.float32
    # Use explicit device for single GPU to avoid meta device issues with device_map="auto"
    device_map_param = "cuda:0" if use_cuda and torch.cuda.device_count() == 1 else "auto"
    base_model = AutoModelForCausalLM.from_pretrained(
        hf_model_id,
        torch_dtype=dtype,
        device_map=device_map_param,
    )

    if cfg.gradient_checkpointing:
        base_model.gradient_checkpointing_enable()
        if hasattr(base_model.config, "use_cache"):
            base_model.config.use_cache = False

    # Use target_modules from config if present, else default to Phi-3.5 list
    default_target_modules = ["q_proj", "v_proj",
                              "k_proj", "o_proj", "fc1", "fc2"]
    config_target_modules = getattr(cfg, "target_modules", None)
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=config_target_modules if config_target_modules else default_target_modules,
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base_model, lora_config)

    class FilteringDataCollator(DataCollatorForLanguageModeling):
        def torch_call(self, features):  # type: ignore[override]
            # Keep only model-relevant keys to avoid nested fields like 'messages'
            filtered = []
            for f in features:
                if isinstance(f, dict):
                    filtered.append({k: v for k, v in f.items() if k in (
                        "input_ids", "attention_mask", "labels")})
                else:
                    filtered.append(f)
            return super().torch_call(filtered)

    data_collator = FilteringDataCollator(tokenizer=tokenizer, mlm=False)

    out_dir = Path(cfg.save_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine if dataset is streaming (IterableDataset) which lacks __len__
    def is_iterable_dataset(ds) -> bool:
        # Robustly check for streaming dataset
        try:
            from datasets import IterableDataset
            if isinstance(ds, IterableDataset):
                return True
        except ImportError:
            pass  # datasets not installed, fallback to attribute check
        # Fallback: has __iter__ but not __len__ (common for streaming datasets)
        return hasattr(ds, "__iter__") and not hasattr(ds, "__len__")

    streaming_train = is_iterable_dataset(train_ds)
    # If streaming, Trainer requires max_steps for LR scheduler. Heuristic: derive from max-train-samples if provided.
    max_steps_override = None
    if streaming_train:
        # Steps per epoch based on desired sample count and batch size
        # Use max_train_samples if provided, else finetune_train_nsamples from config, else fallback to 1000
        target_samples = (
            args.max_train_samples
            or getattr(cfg, "finetune_train_nsamples", None)
            or 1000
        )
        steps_per_epoch = max(1, math.ceil(
            target_samples / max(1, cfg.finetune_train_batch_size)))
        max_steps_override = max(1, steps_per_epoch * max(1, cfg.epochs))

    # Precision flags: enable bf16 if supported, otherwise leave fp16 False on CPU to avoid errors
    bf16_flag = use_cuda and getattr(
        torch.cuda, "is_bf16_supported", lambda: False)()
    fp16_flag = use_cuda and not bf16_flag
    training_args = TrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=cfg.finetune_train_batch_size,
        per_device_eval_batch_size=cfg.finetune_test_batch_size,
        eval_strategy="steps",
        eval_steps=cfg.eval_steps,
        save_steps=cfg.save_steps,
        num_train_epochs=cfg.epochs,
        max_steps=(max_steps_override if max_steps_override is not None else -1),
        learning_rate=cfg.learning_rate,
        logging_steps=max(1, cfg.eval_steps // 2),
        bf16=bf16_flag,
        fp16=fp16_flag,
        gradient_checkpointing=cfg.gradient_checkpointing,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        warmup_steps=cfg.warmup_steps,
        max_grad_norm=cfg.max_grad_norm,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        remove_unused_columns=False,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        seed=cfg.seed,
        deepspeed=args.deepspeed if args.deepspeed else None,
        ddp_find_unused_parameters=False,
    )

    # Metrics logger
    from metrics_logger import MetricsLogger  # local import

    logger = MetricsLogger(out_dir)

    # Callback to log evaluation perplexity records
    class PerplexityLoggingCallback(TrainerCallback if TrainerCallback else object):
        # type: ignore[no-redef]
        def __init__(self, logger_obj):
            self._logger = logger_obj

        def on_evaluate(self, args, state, control, metrics=None, **kwargs):
            if not metrics:
                return
            try:
                if "eval_loss" in metrics and metrics["eval_loss"] is not None:
                    ppl = math.exp(float(metrics["eval_loss"]))
                    rec = {
                        "step": int(getattr(state, "global_step", 0)),
                        "eval_loss": float(metrics["eval_loss"]),
                        "eval_perplexity": float(ppl),
                    }
                    try:
                        self._logger.log(rec)
                    except Exception:
                        # Don't allow logging issues to break training
                        pass
            except Exception:
                # Swallow unexpected callback errors
                pass

    is_streaming = is_iterable_dataset(train_ds)
    # Remove 'messages' column so only tokenized output is kept
    # Note: IterableDataset.map() has limited parameter support compared to Dataset.map()
    is_streaming = hasattr(
        train_ds, "__class__") and "Iterable" in train_ds.__class__.__name__

    map_kwargs_train = {
        "batched": True,
        "input_columns": ["messages"],
    }
    map_kwargs_eval = {
        "batched": True,
        "input_columns": ["messages"],
    }

    # Only add these parameters for non-streaming datasets
    if not is_streaming:
        map_kwargs_train["load_from_cache_file"] = False
        map_kwargs_train["desc"] = "Tokenizing train"
        map_kwargs_eval["load_from_cache_file"] = False
        map_kwargs_eval["desc"] = "Tokenizing eval"

    train_dataset = train_ds.map(
        preprocess, **map_kwargs_train) if hasattr(train_ds, "map") else train_ds
    eval_dataset = eval_ds.map(
        preprocess, **map_kwargs_eval) if hasattr(eval_ds, "map") else eval_ds
    # Remove all non-model columns to avoid DataCollator confusion
    # Note: IterableDataset doesn't support column_names or remove_columns
    keep_cols = {"input_ids", "attention_mask"}
    if hasattr(train_dataset, "column_names") and train_dataset.column_names is not None:
        drop_train = [
            c for c in train_dataset.column_names if c not in keep_cols]
        if drop_train:
            train_dataset = train_dataset.remove_columns(drop_train)
    if hasattr(eval_dataset, "column_names") and eval_dataset.column_names is not None:
        drop_eval = [
            c for c in eval_dataset.column_names if c not in keep_cols]
        if drop_eval:
            eval_dataset = eval_dataset.remove_columns(drop_eval)
    # Debug dataset sizes and sample
    try:
        print(f"[debug] train_dataset len: {len(train_dataset)}")
        print(f"[debug] eval_dataset len: {len(eval_dataset)}")
        # Show first sample keys if available
        if len(train_dataset) > 0:
            first = train_dataset[0]
            print(f"[debug] first train sample keys: {list(first.keys())}")
            for k in ("input_ids", "attention_mask"):
                if k in first:
                    print(
                        f"[debug] first train sample {k} len: {len(first[k])}")
    except Exception as e:
        print(f"[debug] dataset inspection error: {e}")

    # Initialize early stopping callback to prevent overfitting
    callbacks_list = []
    if TrainerCallback is not None:
        try:
            # Early stopping: configured via YAML/config values
            early_stopping = EarlyStoppingCallback(
                early_stopping_patience=cfg.early_stopping_patience,
                early_stopping_threshold=cfg.early_stopping_threshold,
            )
            callbacks_list.append(early_stopping)
            print(
                f"[training] Early stopping enabled (patience={cfg.early_stopping_patience}, threshold={cfg.early_stopping_threshold})")
        except Exception as e:
            print(f"[debug] Failed to configure EarlyStoppingCallback: {e}")

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=callbacks_list,
    )
    if TrainerCallback is not None:
        # Add perplexity logging callback
        trainer.add_callback(PerplexityLoggingCallback(logger))
        # Add OpenTelemetry tracing callback if available and compatible
        try:
            from otel_callback import OpenTelemetryTrainerCallback  # type: ignore
            if hasattr(OpenTelemetryTrainerCallback, "on_prediction_step"):
                trainer.add_callback(OpenTelemetryTrainerCallback())
            else:
                print(
                    "[debug] Skipping OpenTelemetryTrainerCallback: missing on_prediction_step")
        except Exception as e:
            print(f"[debug] Skipping OpenTelemetryTrainerCallback: {e}")

    # Pre-training evaluation (perplexity)
    pre_metrics = trainer.evaluate()
    if "eval_loss" in pre_metrics and pre_metrics["eval_loss"] is not None:
        try:
            ppl = math.exp(float(pre_metrics["eval_loss"]))
            rec = {"phase": "pre", "eval_loss": float(
                pre_metrics["eval_loss"]), "eval_perplexity": float(ppl)}
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
            rec = {"phase": "post", "eval_loss": float(
                post_metrics["eval_loss"]), "eval_perplexity": float(ppl)}
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
