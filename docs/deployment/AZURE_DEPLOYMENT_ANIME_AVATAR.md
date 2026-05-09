# Azure Deployment Guide for Anime Avatar

## Quick Deploy Command

```powershell
.\deploy-chat-to-azure.ps1 `
  -ResourceGroup "qai-anime-avatar-rg" `
  -FunctionApp "qai-anime-avatar-app" `
  -Location "eastus" `
  -DefaultProvider "lora" `
  -ChatTemperature "0.7"
```

## Pre-Deployment Checklist

### 1. Install Prerequisites
- ✅ Azure CLI: `az --version`
- ✅ Azure Functions Core Tools: `func --version`
- ✅ Python 3.11: `python --version`

### 2. Prepare LoRA Model for Deployment
The trained anime avatar model needs to be packaged for Azure deployment:

```powershell
# Create deployment package
$modelPath = "deployed_models\checkpoint-32_20251125_233615"
$deployPackage = "azure_deploy_anime_avatar"

# Copy model files
New-Item -ItemType Directory -Path $deployPackage -Force
Copy-Item -Path $modelPath -Destination "$deployPackage\lora_adapter" -Recurse

# Copy required Python dependencies
Copy-Item -Path "requirements.txt" -Destination "$deployPackage\"

# Package for upload
Compress-Archive -Path "$deployPackage\*" -DestinationPath "anime_avatar_model.zip" -Force
```

### 3. Azure Configuration

#### Option A: Deploy with LoRA Model (Recommended for Production)

**Important:** Azure Functions has file size limits. For LoRA models:
- Use Azure Blob Storage to host the model
- Mount storage as a volume in Function App
- Update environment variables to point to mounted model

```powershell
# Create storage account for model hosting
az storage account create \
  --name qaianimemodels \
  --resource-group qai-anime-avatar-rg \
  --location eastus \
  --sku Standard_LRS

# Create container for models
az storage container create \
  --name models \
  --account-name qaianimemodels \
  --public-access off

# Upload model (requires Azure Storage Explorer or CLI)
az storage blob upload-batch \
  --destination models \
  --source deployed_models\checkpoint-32_20251125_233615 \
  --account-name qaianimemodels
```

#### Option B: Deploy with API Provider (Easier, but requires API keys)

Use Azure OpenAI or OpenAI API instead of local LoRA:

```powershell
.\deploy-chat-to-azure.ps1 `
  -ResourceGroup "qai-anime-avatar-rg" `
  -FunctionApp "qai-anime-avatar-app" `
  -Location "eastus" `
  -AzureOpenAIKey "YOUR_KEY" `
  -AzureOpenAIEndpoint "https://YOUR_ENDPOINT.openai.azure.com/" `
  -AzureOpenAIDeployment "gpt-4o" `
  -DefaultProvider "azure"
```

### 4. Environment Variables for LoRA Deployment

After deployment, configure these app settings:

```powershell
az functionapp config appsettings set \
  --name qai-anime-avatar-app \
  --resource-group qai-anime-avatar-rg \
  --settings \
    QAI_PROVIDER="lora" \
    QAI_LORA_MODEL="/mnt/models/checkpoint-32_20251125_233615" \
    CHAT_TEMPERATURE="0.7" \
    ENABLE_APP_INSIGHTS="true"
```

### 5. Deploy Function Code

```powershell
# Ensure you're in the workspace root
cd C:\Users\Bryan\OneDrive\AI

# Deploy
func azure functionapp publish qai-anime-avatar-app --python
```

### 6. Verify Deployment

```powershell
# Get Function App URL
$appUrl = az functionapp show \
  --name qai-anime-avatar-app \
  --resource-group qai-anime-avatar-rg \
  --query defaultHostName -o tsv

# Test endpoints
Invoke-RestMethod -Uri "https://$appUrl/api/ai/status"
Invoke-RestMethod -Uri "https://$appUrl/api/chat-web"
```

## Production Considerations

### Performance Optimization
1. **Use Premium or Dedicated Plan** for LoRA inference
   - Consumption plan may timeout for large models
   - Minimum: Premium P1V2 (3.5 GB RAM, 1 vCPU)
   - Recommended: Premium P2V2 (7 GB RAM, 2 vCPU)

2. **Enable Always On**
   ```powershell
   az functionapp config set \
     --name qai-anime-avatar-app \
     --resource-group qai-anime-avatar-rg \
     --always-on true
   ```

3. **Configure Scaling**
   - Set minimum instances: 1
   - Set maximum instances: 10
   - Configure based on expected load

### Security
1. **Enable HTTPS Only**
   ```powershell
   az functionapp update \
     --name qai-anime-avatar-app \
     --resource-group qai-anime-avatar-rg \
     --set httpsOnly=true
   ```

2. **Configure CORS** for web interface
   ```powershell
   az functionapp cors add \
     --name qai-anime-avatar-app \
     --resource-group qai-anime-avatar-rg \
     --allowed-origins "https://yourdomain.com"
   ```

3. **Use Key Vault** for sensitive settings
   - Store API keys in Azure Key Vault
   - Reference in app settings: `@Microsoft.KeyVault(SecretUri=...)`

### Monitoring
1. **Enable Application Insights**
   ```powershell
   az monitor app-insights component create \
     --app qai-anime-avatar-insights \
     --location eastus \
     --resource-group qai-anime-avatar-rg
   ```

2. **Configure Alerts**
   - Response time > 5s
   - Error rate > 5%
   - CPU usage > 80%

### Cost Optimization
- **Estimated Monthly Costs:**
  - Consumption Plan: $0-50 (first 1M executions free)
  - Premium P1V2: ~$146/month
  - Storage: ~$2-5/month
  - App Insights: ~$10-30/month (based on data ingestion)

## Troubleshooting

### Model Loading Issues
If LoRA model fails to load:
1. Check model path in QAI_LORA_MODEL
2. Verify model files are accessible
3. Check function timeout settings (increase if needed)
4. Review Application Insights logs

### Performance Issues
1. Upgrade to Premium plan
2. Enable GPU support (requires App Service Plan)
3. Optimize model size (quantization)
4. Implement caching layer

### Cold Start Mitigation
1. Enable Always On
2. Use Premium plan with pre-warmed instances
3. Implement health check endpoint
4. Consider Azure Container Instances for better cold start

## Alternative: Deploy to Azure Container Instances

For full control and GPU support:

```powershell
# Build Docker container
docker build -t qai-anime-avatar:latest .

# Push to Azure Container Registry
az acr create --name qaiacr --resource-group qai-anime-avatar-rg --sku Basic
az acr login --name qaiacr
docker tag qai-anime-avatar:latest qaiacr.azurecr.io/anime-avatar:latest
docker push qaiacr.azurecr.io/anime-avatar:latest

# Deploy to ACI with GPU (if needed)
az container create \
  --name qai-anime-avatar \
  --resource-group qai-anime-avatar-rg \
  --image qaiacr.azurecr.io/anime-avatar:latest \
  --cpu 2 \
  --memory 4 \
  --registry-login-server qaiacr.azurecr.io \
  --registry-username $(az acr credential show --name qaiacr --query username -o tsv) \
  --registry-password $(az acr credential show --name qaiacr --query "passwords[0].value" -o tsv) \
  --dns-name-label qai-anime-avatar \
  --ports 80
```

## Next Steps

1. ✅ Complete grid search to find best hyperparameters
2. ✅ Retrain model with optimal settings
3. ✅ Test locally before deploying
4. ✅ Choose deployment strategy (Functions vs Containers)
5. ✅ Deploy and monitor
6. ✅ Set up CI/CD pipeline for continuous deployment

---

**Created:** 2025-11-25
**Last Updated:** 2025-11-25
**Status:** Ready for deployment after hyperparameter optimization
