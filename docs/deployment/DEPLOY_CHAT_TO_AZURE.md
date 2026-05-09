# Deploy Chat Website to Azure Functions

This guide deploys the chat website (with Azure/OpenAI providers) to Azure Functions and configures app settings for cloud use.

## Prerequisites

- Azure CLI (`az`)
- Azure Functions Core Tools (`func`) for local publish
- Python 3.11 installed locally

## One-command deployment (recommended)

Use the helper script from the repo root:

```powershell
# Fill in values and run
./deploy-chat-to-azure.ps1 `
  -ResourceGroup rg-chat-web `
  -FunctionApp chat-web-app-123 `
  -Location eastus `
  -AzureOpenAIKey "<your-azure-openai-key>" `
  -AzureOpenAIEndpoint "https://<your-resource>.openai.azure.com/" `
  -AzureOpenAIDeployment "gpt-4o-mini"
```

Outputs:
- Chat UI: https://chat-web-app-123.azurewebsites.net/api/chat-web
- Health:   https://chat-web-app-123.azurewebsites.net/api/ai/status

If you use OpenAI instead of Azure OpenAI:
```powershell
./deploy-chat-to-azure.ps1 `
  -ResourceGroup rg-chat-web `
  -FunctionApp chat-web-app-123 `
  -Location eastus `
  -OpenAIKey "sk-..." `
  -OpenAIModel "gpt-4o-mini"
```

## Manual steps (expanded)

1) Resource Group and Storage
```powershell
az group create --name rg-chat-web --location eastus
az storage account create --name chatwebstorage123 --resource-group rg-chat-web --location eastus --sku Standard_LRS
```

2) Create Function App
```powershell
az functionapp create `
  --resource-group rg-chat-web `
  --name chat-web-app-123 `
  --storage-account chatwebstorage123 `
  --consumption-plan-location eastus `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --os-type Linux
```

3) Configure App Settings

Azure OpenAI:
```powershell
az functionapp config appsettings set `
  --name chat-web-app-123 `
  --resource-group rg-chat-web `
  --settings `
    AZURE_OPENAI_API_KEY="<key>" `
    AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/" `
    AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini" `
    AZURE_OPENAI_API_VERSION="2024-08-01-preview" `
    DEFAULT_AI_PROVIDER="auto" `
    CHAT_TEMPERATURE="0.7"
```

OpenAI:
```powershell
az functionapp config appsettings set `
  --name chat-web-app-123 `
  --resource-group rg-chat-web `
  --settings `
    OPENAI_API_KEY="sk-..." `
    OPENAI_MODEL="gpt-4o-mini" `
    DEFAULT_AI_PROVIDER="auto" `
    CHAT_TEMPERATURE="0.7"
```

4) Publish
```powershell
func azure functionapp publish chat-web-app-123
```

## Verify deployment

- Open the chat UI: `/api/chat-web`
- Call the health endpoint: `/api/ai/status`
  - Confirms the active provider and whether required env vars are detected

## Notes

- Locally, provider detection falls back to the free Local provider without keys.
- In Azure, set at least one provider’s keys as app settings for cloud inference.
- For persistence (chat logs, RAG, etc.), consider Azure Cosmos DB per `azurecosmosdb.instructions.md`.
