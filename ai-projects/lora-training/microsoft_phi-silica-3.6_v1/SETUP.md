Model training environment setup (AI/microsoft_phi-silica-3.6_v1)
===============================================================

This document describes how to prepare a model-specific Python virtual environment and install the heavy ML dependencies required for training (PyTorch, Transformers, PEFT, Accelerate, etc.). The repository provides a helper script at `AI/microsoft_phi-silica-3.6_v1/scripts/setup_model_env.sh` which automates the most common steps.

Quick checklist
---------------
1. Choose whether you'll use CPU-only training or a machine with CUDA GPUs.
   - For CPU-only machines run: `bash scripts/setup_model_env.sh --cpu`
   - For CUDA machines pick your CUDA runtime (e.g., `cu121` for CUDA 12.1) and run:
     `bash scripts/setup_model_env.sh --cuda cu121`

2. The script will create (or reuse) `AI/microsoft_phi-silica-3.6_v1/venv` and install packages from `AI/microsoft_phi-silica-3.6_v1/requirements.txt`.

3. The script will install torch separately (the script intentionally does not autoguess the torch wheel — you must tell it which wheel to install so it matches your OS/CUDA environment).

4. After installation, activate the venv and run a short smoke test by importing `torch`, `transformers`, `peft`, `accelerate` and confirming `torch.cuda.is_available()` output.

Important note: the setup script intentionally pins huggingface_hub to a version compatible with the installed
transformers/peft packages (e.g. huggingface_hub >=0.34.0,<1.0). This prevents accidental upgrades that would
break imports at runtime. If you need a newer `huggingface_hub` and upgraded `transformers`/`peft`, update
`AI/microsoft_phi-silica-3.6_v1/requirements.txt` and re-run `scripts/setup_model_env.sh --force`.

Activate and run a small training job
------------------------------------
Once venv is ready, you can start lightweight training for testing:

```bash
source AI/microsoft_phi-silica-3.6_v1/venv/bin/activate
python AI/microsoft_phi-silica-3.6_v1/scripts/train_lora.py --config AI/microsoft_phi-silica-3.6_v1/lora/lora.yaml --dataset datasets/chat/mixed_chat --max-train-samples 32 --epochs 1 --save-dir data_out/lora_training/test_small
```

Notes and troubleshooting
-------------------------
- On Windows the venv path created may be under `Scripts/python.exe`. The helper script and our runner scripts handle both `bin/python` and `Scripts/python.exe`.
- If you see missing package errors, re-run the setup script with `--force` to recreate and reinstall.
- For CUDA installations, ensure your driver supports the chosen CUDA runtime and that `nvidia-smi` is available.

If you'd like, I can also generate a one-shot install command for your exact environment (CPU vs GPU) or help you run a very small training job now (1 epoch, few samples) once your environment is ready.
