# Azure AI Foundry Deployment (Managed Online Endpoint)

This guide shows how to deploy your LoRA adapter with a Phi-3.x base model to an Azure AI Foundry endpoint (backed by Azure ML Managed Online Endpoints).

## Prerequisites

- You completed training and have a LoRA adapter folder, e.g.: `AI/microsoft_phi-silica-3.6_v1/data_out/lora_training/lora_adapter`
- Azure CLI installed and logged in (`az login`)
- Azure ML workspace created (see AZURE_ML_TRAINING_GUIDE.md)
- Python deps installed:

```powershell
cd AI\microsoft_phi-silica-3.6_v1
pip install -r azure-requirements.txt
```

## Quick Deploy

```powershell
# Set your subscription
az account set --subscription "<SUBSCRIPTION_ID>"

# Deploy endpoint (GPU instance)
python azure_foundry_deploy.py `
  --subscription-id "<SUBSCRIPTION_ID>" `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --adapter-path .\data_out\lora_training\lora_adapter `
  --endpoint-name phi36-lora-ep `
  --base-model-id microsoft/Phi-3.5-mini-instruct `
  --instance-type Standard_NC6s_v3
```

Output includes:
- Endpoint scoring URL
- Primary key for auth

## Invoke the endpoint

```powershell
$endpoint = "<scoring-url-from-output>"
$key = "<primary-key-from-output>"
$body = '{"messages":[{"role":"user","content":"Write a haiku about quantum computing"}]}'

Invoke-RestMethod `
  -Uri $endpoint `
  -Method Post `
  -Headers @{"Content-Type"="application/json"; "Authorization" = "Bearer $key"} `
  -Body $body | ConvertTo-Json -Depth 5
```

## Notes

- The deployment downloads the base model (`BASE_MODEL_ID`) at startup; the LoRA adapter is mounted from the registered model asset.
- GPU size default is `Standard_NC6s_v3` (1x V100). Adjust with `--instance-type`.
- Environment uses a curated huggingface GPU image + pip installs for `transformers`, `peft`, `accelerate`, `torch`.
- Scoring script lives at `foundry/score_foundry.py`.

## Cost

- You pay for the GPU instance while the endpoint is running.
- To save costs, reduce instance_count to 0 (stop) when not in use:

```powershell
az ml online-deployment update `
  --name blue `
  --endpoint-name phi36-lora-ep `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --set instance_count=0
```

## Cleanup

```powershell
# Delete endpoint (stops billing)
az ml online-endpoint delete `
  --name phi36-lora-ep `
  --resource-group rg-phi36-ml `
  --workspace-name phi36-ml-workspace `
  --yes
```
