# Phi-3.6 LoRA Fine-Tuning (Scalable)

This directory contains a production-ready path to train the Phi-3.x family with LoRA on very large datasets. It supports:

- Huge datasets using JSONL with streaming ingestion
- Simple dataset prep from JSONL or CSV
- Local training via Hugging Face + PEFT
- Azure deployment via the included infra (Container Apps + File Share) when ready

The configs under `lora/` and `soft_prompt/` are Azure AI Toolkit–compatible. The scripts here let you validate and train locally first.

## Dataset format

Use JSONL where each line is a JSON object with a `messages` array:

```json
{"messages": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]}
```

This repo includes tiny samples in `data/train.json` and `data/test.json` (JSONL with `.json` extension).

If you have CSV (columns `prompt,response` or `input,output`), the prep script converts it to the same chat schema.

## Setup (Windows PowerShell)

Create a virtual environment and install dependencies. The script gracefully handles missing imports for dry-run mode, but full training requires all packages from `requirements.txt`.

```powershell
# From the repo root
cd AI\microsoft_phi-silica-3.6_v1
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Required packages for training:**

- `datasets>=2.19.0` - Dataset loading and streaming
- `transformers>=4.43.0` - Model and training infrastructure
- `peft>=0.12.0` - LoRA and parameter-efficient fine-tuning
- `accelerate>=0.33.0` - Multi-GPU and distributed training
- `torch` - Install version matching your CUDA (see requirements.txt)
- `pyyaml>=6.0` - Configuration parsing

**Note:** The script allows dry-run validation without these packages. Install them only when ready to train.

## Prepare a large dataset

```powershell
# Convert CSV/JSONL to chat JSONL and split train/test
python .\scripts\prepare_dataset.py --input <path-to-your-data> --output-dir .\data --train-ratio 0.99
```

The output will be `data/train.json` and `data/test.json` (JSONL).

## Validate (no downloads)

```powershell
python .\scripts\train_lora.py --dry-run --dataset .\data --config .\lora\lora.yaml
```

This checks dataset shape and counts without loading a model.

## Train locally (small smoke test)

```powershell
# Use a smaller, available HF model if needed
$env:HF_MODEL_ID = "microsoft/Phi-3.5-mini-instruct"
python .\scripts\train_lora.py --dataset .\data --config .\lora\lora.yaml --max-train-samples 64 --max-eval-samples 32 --no-stream
```

Outputs are saved under the `save_dir` specified in `lora\lora.yaml` (by default, it will create the folder).

## Multi-GPU training

- Accelerate launcher (recommended for simple multi-GPU):

```powershell
accelerate launch --multi_gpu .\scripts\train_lora.py --dataset .\data --config .\lora\lora.yaml --max-train-samples 512 --max-eval-samples 128
```

- DeepSpeed (ZeRO-3). First, create or use the provided config:

```powershell
# Provided example config
cat .\scripts\deepspeed_zero3.json | Out-Host

# Run with DeepSpeed
python .\scripts\train_lora.py --dataset .\data --config .\lora\lora.yaml --deepspeed .\scripts\deepspeed_zero3.json
```

The trainer computes and prints perplexity before and after training using the evaluation loss.

## Train at scale on Azure (optional)

1. Provision resources using the bicep in `lora/infra/provision`. Fill in `finetuning.config.json` and run the documented deployment steps (see the top-level workspace docs).
## Train on Azure Machine Learning (Recommended for GPU Training)

Azure ML provides managed GPU compute with auto-scaling for cost-effective training.

### Quick Start

```powershell
# 1. Install Azure dependencies
pip install -r azure-requirements.txt

# 2. Setup (one-time)
.\setup_azure_ml.ps1 -SubscriptionId "<your-subscription-id>"

# 3. Upload dataset
python azure_ml_training.py --action upload `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace

# 4. Start training (quick test)
python azure_ml_training.py --action train `
  --subscription-id "<your-subscription-id>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --max-train-samples 64
```

**Benefits:**
- **GPU acceleration**: 1-4x V100 GPUs (Standard_NC6s_v3 @ ~$3/hour)
- **Auto-scaling**: Scales to 0 when idle (no cost)
- **Monitoring**: Real-time metrics in Azure ML Studio
- **Cost-effective**: Pay only for training time (~$9 for full 8000-sample run)

See **[AZURE_ML_TRAINING_GUIDE.md](./AZURE_ML_TRAINING_GUIDE.md)** for complete documentation.

## Train at scale on Azure Container Apps (Alternative)
2. Upload your dataset to the mounted file share path expected by the job (the infra uses `mount/<run_id>/dataset`).
3. Ensure `lora.yaml` points to `finetune_dataset: "mount/<run_id>/dataset"` and `save_dir` is also under `mount/<run_id>/...`.
4. Start the job. The standard runner will read `lora.yaml` and train using LoRA.

### Read data directly from Azure Blob via manifest (Container Apps Job)

Use the alternate Bicep `lora/infra/provision/finetuning_blob_manifest.bicep`, which adds an init container that downloads your dataset directly from Blob Storage before training starts.

Manifest format: plain text file where each line is a SAS URL to a dataset part file (e.g., .jsonl). Example:

```text
https://mystorage.blob.core.windows.net/mycontainer/part-0001.jsonl?<SAS>
https://mystorage.blob.core.windows.net/mycontainer/part-0002.jsonl?<SAS>
```

Deploy (PowerShell):

```powershell
$rg = "rg-quantum-ai"
$params = "AI\microsoft_phi-silica-3.6_v1\lora\infra\provision\finetuning_blob_manifest.parameters.json"
az deployment group create `
  --resource-group $rg `
  --template-file AI\microsoft_phi-silica-3.6_v1\lora\infra\provision\finetuning_blob_manifest.bicep `
  --parameters @$params
```

### Notes

- The init container downloads each URL in `manifestUrl` into `/mount/dataset` in the job.
- Ensure your SAS token stays valid for the job duration.
- The main container still reads from `mount/<run_id>/dataset` per `lora.yaml`.

## Additional notes

- For huge datasets, prefer `--no-stream` only for deterministic local experiments. Streaming is better for very large files.
- Use BF16 on GPUs that support it for speed and stability. The script auto-selects BF16 on CUDA, FP16 otherwise.
- Reduce `eval_steps` and `save_steps` for faster checkpoints on massive runs.
- If gradient checkpointing is enabled, we disable `use_cache` on the model to avoid correctness issues.

## Direct streaming from Blob during training (no pre-download)

You can stream remote JSONL files directly during training using manifests. Supported manifest formats (local path or HTTPS URL):

- Plain text: one SAS URL per line
- JSONL: each line is either a string URL or an object with a `url` field
- JSON: either an array of URLs, or an object with `train`, `validation`, `urls`, or `files` arrays

Examples:

```powershell
# Train streaming directly from Blob (SAS URLs in text manifests)
python .\scripts\train_lora.py `
  --train-manifest https://mystorage.blob.core.windows.net/mycontainer/train_manifest.txt?sv=... `
  --eval-manifest  https://mystorage.blob.core.windows.net/mycontainer/eval_manifest.txt?sv=... `
  --config .\lora\lora.yaml
```

When using manifests, the trainer keeps streaming enabled by default for best scalability.

## Metrics logging (file and Azure Monitor)

- All evaluation metrics are appended to `<save_dir>/metrics.jsonl`.
- If the following environment variables are set, the same metrics are also sent to Azure Log Analytics via the HTTP Data Collector API:
  - `AZURE_LOG_ANALYTICS_WORKSPACE_ID`
  - `AZURE_LOG_ANALYTICS_SHARED_KEY`
  - Optional: `AZURE_LOG_TYPE` (default: `LLMTrainingMetrics`)

Each record contains a UTC `timestamp` plus fields like `eval_loss`, `eval_perplexity`, and `step`.

### Application Insights

To send metrics to Application Insights, install the optional package and set the connection string:

```powershell
pip install applicationinsights

$env:APPLICATIONINSIGHTS_CONNECTION_STRING = "InstrumentationKey=...;IngestionEndpoint=https://..."
```

Metrics are tracked as custom events and metrics (eval_loss, eval_perplexity).

### OpenTelemetry tracing

To emit distributed traces to an OTLP-compatible backend (e.g., Jaeger, Azure Monitor, Grafana Tempo), install the optional packages:

```powershell
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-grpc

# Point to your OTLP endpoint
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4317"
$env:OTEL_SERVICE_NAME = "lora-training"
```

The trainer will emit spans for:

- `training_run` (entire training session with hyperparameters)
- `training_step` (every 100 steps to reduce overhead)
- `evaluation` (each eval with metrics)
- `log_event` (training loss)

These traces can be visualized in tools like Jaeger or Application Insights.

## Troubleshooting

- Missing packages: `pip install -r requirements.txt`.
- Large downloads: Try `--dry-run` first. For actual training, set `HF_MODEL_ID` to a smaller model.
- Dataset errors: Re-run `prepare_dataset.py` and check the first few lines of `data/train.json`.
