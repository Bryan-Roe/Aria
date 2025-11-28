param(
  [Parameter(Mandatory = $true)] [string]$ResourceGroup,
  [Parameter(Mandatory = $true)] [string]$FunctionApp,
  [Parameter(Mandatory = $true)] [string]$Location,
  [string]$StorageAccount = "",
  [string]$AzureOpenAIKey = "",
  [string]$AzureOpenAIEndpoint = "",
  [string]$AzureOpenAIDeployment = "",
  [string]$AzureOpenAIAPIVersion = "2024-08-01-preview",
  [string]$OpenAIKey = "",
  [string]$OpenAIModel = "gpt-4o-mini",
  [string]$DefaultProvider = "auto",
  [string]$ChatTemperature = "0.7"
)

Write-Host "--- QAI: Deploy Chat Website to Azure Functions ---" -ForegroundColor Cyan

# Check prerequisites
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
  Write-Error "Azure CLI (az) not found. Install from https://aka.ms/getazcli"; exit 1
}
if (-not (Get-Command func -ErrorAction SilentlyContinue)) {
  Write-Warning "Azure Functions Core Tools (func) not found. Publishing step will be skipped. Install from https://learn.microsoft.com/azure/azure-functions/functions-run-local" 
}

# Ensure unique storage account if not provided
if (-not $StorageAccount -or $StorageAccount -eq "") {
  $rand = Get-Random -Maximum 99999999
  $StorageAccount = ("chatweb" + $rand.ToString()).ToLower()
  $StorageAccount = $StorageAccount.Substring(0, [Math]::Min(24, $StorageAccount.Length))
}

Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Function App : $FunctionApp" -ForegroundColor Yellow
Write-Host "Location    : $Location" -ForegroundColor Yellow
Write-Host "Storage     : $StorageAccount" -ForegroundColor Yellow

# Login (no-op if already logged in)
az account show > $null 2>&1
if ($LASTEXITCODE -ne 0) { az login | Out-Null }

# Create resource group
az group create --name $ResourceGroup --location $Location | Out-Null

# Create storage account
az storage account create `
  --name $StorageAccount `
  --resource-group $ResourceGroup `
  --location $Location `
  --sku Standard_LRS | Out-Null

# Create Function App (Linux, Python 3.11, v4)
az functionapp create `
  --resource-group $ResourceGroup `
  --name $FunctionApp `
  --storage-account $StorageAccount `
  --consumption-plan-location $Location `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --os-type Linux | Out-Null

# Configure app settings (provider defaults)
az functionapp config appsettings set `
  --name $FunctionApp `
  --resource-group $ResourceGroup `
  --settings DEFAULT_AI_PROVIDER=$DefaultProvider CHAT_TEMPERATURE=$ChatTemperature | Out-Null

# Configure Azure OpenAI if provided
if ($AzureOpenAIKey -and $AzureOpenAIEndpoint -and $AzureOpenAIDeployment) {
  az functionapp config appsettings set `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --settings `
      AZURE_OPENAI_API_KEY=$AzureOpenAIKey `
      AZURE_OPENAI_ENDPOINT=$AzureOpenAIEndpoint `
      AZURE_OPENAI_DEPLOYMENT=$AzureOpenAIDeployment `
      AZURE_OPENAI_API_VERSION=$AzureOpenAIAPIVersion | Out-Null
}

# Configure OpenAI if provided
if ($OpenAIKey) {
  az functionapp config appsettings set `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --settings OPENAI_API_KEY=$OpenAIKey OPENAI_MODEL=$OpenAIModel | Out-Null
}

# Publish code (if func available)
if (Get-Command func -ErrorAction SilentlyContinue) {
  Write-Host "Publishing Function App..." -ForegroundColor Cyan
  func azure functionapp publish $FunctionApp
} else {
  Write-Warning "Skipping publish: 'func' not found. To publish later, run:`n  func azure functionapp publish $FunctionApp"
}

$baseUrl = "https://$FunctionApp.azurewebsites.net"
Write-Host "--- Deployment complete ---" -ForegroundColor Green
Write-Host "Open Chat UI:     $baseUrl/api/chat-web" -ForegroundColor Green
Write-Host "Health endpoint:  $baseUrl/api/ai/status" -ForegroundColor Green
