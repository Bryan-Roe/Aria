# Azure ML Cloud Training for Phi-3.6 LoRA

This guide shows how to run the LoRA fine-tuning script `scripts/train_lora.py` on Azure Machine Learning for scalable GPU training and optional hyperparameter optimization (HPO).

## 1. Prerequisites

1. Azure Subscription
2. Azure ML Workspace (Portal or CLI)
3. GPU Compute Cluster (e.g. `Standard_NC6s_v3`, `Standard_NC12`, `Standard_NC24`) or CPU for smoke tests.
4. Dataset uploaded (we use Dolly manifest example) to the default workspace datastore.
5. Azure CLI with ML extension: `az extension add -n ml`

### Workspace creation (CLI)
```powershell
az account set --subscription <SUBSCRIPTION_ID>
az group create -n <RESOURCE_GROUP> -l <REGION>
az ml workspace create -n <WORKSPACE_NAME> -g <RESOURCE_GROUP>
```

### Compute cluster (GPU)
```powershell
az ml compute create -n gpu-cluster --type amlcompute --size Standard_NC6s_v3 --min-instances 0 --max-instances 2 --idle-time-before-scale-down 120
```

## 2. Upload Dataset Manifest
The training script accepts `--train-manifest` and `--eval-manifest`. A manifest is a text file listing one JSONL path per line.

Upload Dolly JSONL and manifest:
```powershell
az ml data create --name dolly-manifest --path datasets/chat/dolly/manifest.txt --type uri_file --version 1
```
(Alternatively use `workspaceblobstore` path directly as shown in the job YAML.)

## 3. Single Training Job
`azureml/job-lora-train.yml` runs one LoRA training with moderate sample limits. Adjust inputs or override at submit time:
```powershell
az ml job create -f AI/microsoft_phi-silica-3.6_v1/azureml/job-lora-train.yml --set inputs.max_train_samples=256 inputs.max_eval_samples=64 compute=azureml:gpu-cluster
```
Stream logs until completion.

## 4. Hyperparameter Sweep (HPO)
`azureml/job-lora-sweep.yml` performs random search over learning rate, dropout, epochs, and batch sizes. Submit:
```powershell
az ml job create -f AI/microsoft_phi-silica-3.6_v1/azureml/job-lora-sweep.yml --set compute=azureml:gpu-cluster
```
Monitor trials:
```powershell
az ml job show -n <JOB_NAME>
az ml job stream -n <JOB_NAME>
```
Best trial metrics and artifacts are stored under the job outputs.

## 5. Artifacts & Outputs
The script writes adapters and tokenizer into the mounted output folder (`outputs/model_out/`). For sweeps each trial has its own child folder. Download after completion:
```powershell
az ml job download -n <JOB_NAME> --output-name model_out --download-path .\downloaded_artifacts
```

## 6. Metrics & Observability
Set environment variables in the job YAML or via `--set environment.variables.` prefix for:
- `AZURE_LOG_ANALYTICS_WORKSPACE_ID` / `AZURE_LOG_ANALYTICS_SHARED_KEY` for Log Analytics
- `APPLICATIONINSIGHTS_CONNECTION_STRING` for App Insights
- `OTEL_EXPORTER_OTLP_ENDPOINT` for OpenTelemetry

Metrics stream to `metrics.jsonl` and optionally Azure services.

## 7. GitHub Actions CI Trigger
Workflow file: `.github/workflows/azureml-train.yml`. Dispatch manually providing workspace, subscription, resource group, compute, and job YAML path.

## 8. Cost Optimization Tips
- Start with small `max_train_samples` (128–512) & `epochs=1`.
- Prefer `Standard_NC6s_v3` for low-cost experiments.
- Use sweeps with limited `max_total_trials` to cap spend.
- Turn cluster min nodes to 0 for auto-scale down.

## 9. Custom Environment
If curated PyTorch image unavailable, uncomment environment build section in job YAML and use `azureml/environment.yml`. This creates a Conda-based environment with pinned deps.

## 10. Resume / Further Training
To resume or stack adapters, download `lora_adapter` directory and re-launch job referencing it via a future script extension (not yet implemented). Keep track of perplexity trends in `metrics.jsonl`.

## 11. Troubleshooting
- Dependency errors: ensure curated image includes CUDA & torch. Otherwise build custom environment.
- `ResourceNotFound`: verify datastore path or use `az ml data create`.
- Slow startup: First pull of large GPU image; subsequent pulls are faster.
- OOM: Reduce `train_batch_size`, sequence length in `lora.yaml`, or switch to larger GPU.

## 12. Next Steps
- Add checkpoint resume parameter.
- Integrate model registry registration (az ml model create on completion).
- Automate evaluation & reporting.

Happy training!
