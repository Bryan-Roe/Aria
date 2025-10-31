@description('Location for all resources')
param location string = resourceGroup().location

@description('Name of the Azure Quantum workspace')
param workspaceName string = 'quantum-ai-workspace'

@description('Name of the storage account')
param storageAccountName string = 'quantumstorage${uniqueString(resourceGroup().id)}'

@description('Tags for all resources')
param tags object = {
  Environment: 'Development'
  Project: 'Quantum-AI'
  ManagedBy: 'Bicep'
}

// Storage Account for Azure Quantum
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
      bypass: 'AzureServices'
    }
  }
}

// Azure Quantum Workspace
resource quantumWorkspace 'Microsoft.Quantum/workspaces@2023-11-13-preview' = {
  name: workspaceName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    storageAccount: storageAccount.id
    providers: [
      {
        providerId: 'ionq'
        providerSku: 'pay-as-you-go-cred'
      }
      {
        providerId: 'quantinuum'
        providerSku: 'pay-as-you-go-cred'
      }
      {
        providerId: 'microsoft-qc'
        providerSku: 'learn-and-develop'
      }
    ]
  }
}

// Log Analytics Workspace for monitoring
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${workspaceName}-logs'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Application Insights for quantum job monitoring
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${workspaceName}-insights'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

// Outputs
output workspaceName string = quantumWorkspace.name
output workspaceId string = quantumWorkspace.id
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output appInsightsConnectionString string = appInsights.properties.ConnectionString
output location string = location
