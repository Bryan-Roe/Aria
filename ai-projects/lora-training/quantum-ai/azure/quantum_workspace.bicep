// Azure Quantum Workspace Bicep Template

@description('Name of the Azure Quantum workspace')
param workspaceName string

@description('Location for all resources')
param location string = resourceGroup().location

@description('Storage account name for quantum workspace')
param storageAccountName string

@description('Tags for the resources')
param tags object = {
  Environment: 'Development'
  Project: 'QuantumAI'
}

// Storage Account for Quantum Workspace
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
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// Azure Quantum Workspace
resource quantumWorkspace 'Microsoft.Quantum/Workspaces@2023-11-13-preview' = {
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

// Output values
output workspaceId string = quantumWorkspace.id
output workspaceName string = quantumWorkspace.name
output workspaceLocation string = quantumWorkspace.location
output storageAccountId string = storageAccount.id
output resourceId string = quantumWorkspace.id
