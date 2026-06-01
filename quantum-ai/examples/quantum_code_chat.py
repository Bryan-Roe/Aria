#!/usr/bin/env python3
"""quantum_code_chat.py — Interactive REPL for the Quantum Code LLM.

Trains (or loads a checkpoint), then lets you type code prompts and watch
the model complete them.

Usage
-----
    # Train fresh (10 epochs) then chat
    python ai-projects/quantum-ml/examples/quantum_code_chat.py

    # Load existing checkpoint and chat immediately
    python ai-projects/quantum-ml/examples/quantum_code_chat.py --load

    # Train more before chatting
    python ai-projects/quantum-ml/examples/quantum_code_chat.py --epochs 20

Commands inside the REPL
------------------------
    <any text>   — complete that code prompt
    /temp 0.6    — set temperature (default 0.8, lower = more focused)
    /topk 20     — set top-k (default 40)
    /tokens 100  — set max new tokens (default 80)
    /retrain     — run another 5 epochs of training then return to chat
    /save        — save checkpoint to data_out/quantum_code_llm/checkpoint.pt
    /load        — load checkpoint from data_out/quantum_code_llm/checkpoint.pt
    /stats       — show model info and backend
    /help        — show this list
    /quit        — exit
"""

from __future__ import annotations

import argparse
import os
import sys

# Add src directory to path before importing quantum_code_llm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import quantum_code_llm
except ImportError:
    print(f"Error: Could not import quantum_code_llm. Make sure it's installed in {sys.path[0]}")
    raise

CHECKPOINT = "data_out/quantum_code_llm/checkpoint.pt"

MODEL_CFG = {
    "n_qubits": 4,
    "d_model": 64,
    "n_heads": 4,
    "n_layers": 2,
    "n_var_layers": 2,
    "max_seq_len": 128,
    "dropout": 0.1,
    "backend": "auto",
}


def save_checkpoint(model: quantum_code_llm.QuantumCodeLLM, tokenizer: quantum_code_llm.CodeTokenizer) -> None:
    quantum_code_llm.save_checkpoint(model, tokenizer, CHECKPOINT)
    print(f"  ✓ Saved -> {CHECKPOINT}")


def load_checkpoint() -> tuple[quantum_code_llm.QuantumCodeLLM, quantum_code_llm.CodeTokenizer]:
    model, tokenizer, _metadata = quantum_code_llm.load_checkpoint(CHECKPOINT, map_location="cpu")
    print(f"  ✓ Loaded <- {CHECKPOINT}")
    return model, tokenizer


def retrain(
    model: quantum_code_llm.QuantumCodeLLM,
    tokenizer: quantum_code_llm.CodeTokenizer,
    n_epochs: int = 5,
) -> None:
    tcfg = quantum_code_llm.TrainConfig(n_epochs=n_epochs, batch_size=8, lr=1e-3, log_every=40)
    trainer = quantum_code_llm.QuantumCodeTrainer(model, tokenizer, tcfg)
    trainer.train()


def chat_loop(model: quantum_code_llm.QuantumCodeLLM, tokenizer: quantum_code_llm.CodeTokenizer) -> None:
    temperature = 0.8
    top_k = 40
    max_new = 80

    print()
    print("━" * 60)
    print("  Quantum Code LLM — Chat  (type /help for commands)")
    print(f"  backend: {model.backend}  |  params: {model.parameter_count()['total']:,}")
    print("━" * 60)
    print()

    while True:
        try:
            prompt = input("▶ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not prompt:
            continue

        # ── built-in commands ──────────────────────────────────────────
        if prompt == "/quit" or prompt == "/exit":
            print("Bye!")
            break

        elif prompt == "/help":
            print(__doc__)

        elif prompt == "/stats":
            p = model.parameter_count()
            print(f"  backend   : {model.backend}")
            print(f"  params    : {p['total']:,} total  {p['trainable']:,} trainable")
            print(f"  vocab     : {tokenizer.vocab_size}")
            cfg = model.config
            print(f"  d_model   : {cfg.d_model}  n_layers: {cfg.n_layers}  n_qubits: {cfg.n_qubits}")
            print(f"  temp      : {temperature}  top_k: {top_k}  max_tokens: {max_new}")

        elif prompt.startswith("/temp "):
            try:
                temperature = float(prompt.split()[1])
                print(f"  temperature → {temperature}")
            except ValueError:
                print("  usage: /temp 0.7")

        elif prompt.startswith("/topk "):
            try:
                top_k = int(prompt.split()[1])
                print(f"  top_k → {top_k}")
            except ValueError:
                print("  usage: /topk 30")

        elif prompt.startswith("/tokens "):
            try:
                max_new = int(prompt.split()[1])
                print(f"  max_new_tokens → {max_new}")
            except ValueError:
                print("  usage: /tokens 120")

        elif prompt == "/save":
            save_checkpoint(model, tokenizer)

        elif prompt == "/load":
            if os.path.exists(CHECKPOINT):
                model, tokenizer = load_checkpoint()
            else:
                print(f"  No checkpoint at {CHECKPOINT}")

        elif prompt.startswith("/retrain"):
            parts = prompt.split()
            n = int(parts[1]) if len(parts) > 1 else 5
            print(f"  Running {n} more epochs …")
            retrain(model, tokenizer, n_epochs=n)
            save_checkpoint(model, tokenizer)

        # ── generation ────────────────────────────────────────────────
        else:
            result = quantum_code_llm.generate(
                model,
                tokenizer,
                prompt=prompt,
                max_new_tokens=max_new,
                temperature=temperature,
                top_k=top_k,
            )
            print()
            print(result)
            print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantum Code LLM chat REPL")
    parser.add_argument("--load", action="store_true", help="load checkpoint instead of training")
    parser.add_argument("--epochs", type=int, default=15, help="epochs to train (default 15)")
    args = parser.parse_args()

    tokenizer = quantum_code_llm.CodeTokenizer()

    if args.load and os.path.exists(CHECKPOINT):
        model, tokenizer = load_checkpoint()
    else:
        if args.load:
            print(f"No checkpoint found at {CHECKPOINT}, training fresh ...\n")
        model, tokenizer = quantum_code_llm.train(
            model_cfg=MODEL_CFG,
            train_cfg={
                "n_epochs": args.epochs,
                "batch_size": 8,
                "lr": 3e-3,
                "log_every": 50,
            },
        )
        save_checkpoint(model, tokenizer)

    chat_loop(model, tokenizer)


if __name__ == "__main__":
    main()
