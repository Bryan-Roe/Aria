Summary
-------
Resolve friendly Hugging Face model aliases in the LoRA training script and default the LoRA config to `gpt-oss`.

Changes
-------
- Add `resolve_hf_model_id()` helper to `ai-projects/lora-training/microsoft_phi-silica-3.6_v1/scripts/train_lora.py`.
  - Supports alias mapping (e.g., `gpt-oss` -> `openai/gpt-oss-20b`).
  - Honors precedence: env var > CLI arg > config value > alias mapping > fallback.
  - Accepts local checkpoint paths.
- Update `ai-projects/lora-training/microsoft_phi-silica-3.6_v1/lora/lora.yaml` to default `model: gpt-oss` and include `model_aliases`.
- Add `tests/test_train_lora_model_resolution.py` with unit tests for alias resolution and path precedence.

Verification
------------
- Ran focused pytest: `tests/test_train_lora_model_resolution.py`, `tests/test_training_integration.py`, `tests/test_training_integration_validation.py` — all passed.
- Ran `scripts/test_runner.py --unit` — full unit suite passed: 2661 passed, 5 skipped.
- Dry-runed training: `scripts/train_lora.py --dry-run` against `datasets/chat/github_actions` (works even when optional deps missing).

Notes
-----
- `train_lora.py` contains pre-existing PEP8/line-length warnings; this change avoids broad reformatting.
- If you want the PR opened automatically I attempted to push the feature branch; it is available at `feature/lora-model-alias`.

How to test locally
-------------------
1. Run unit tests:

```bash
.venv/bin/python scripts/test_runner.py --unit
```

2. Dry-run training (no heavy deps required for dry-run):

```bash
cd ai-projects/lora-training/microsoft_phi-silica-3.6_v1
/../.venv/bin/python scripts/train_lora.py --dry-run --dataset /workspaces/Aria/datasets/chat/github_actions --config lora/lora.yaml
```

Follow-ups
----------
- Optionally map additional friendly aliases via `model_aliases` in `lora.yaml`.
- If you prefer a different default HF model, update `DEFAULT_MODEL_ALIASES` in `train_lora.py`.

Signed-off-by: GitHub Copilot
