param timeout int
param location string = resourceGroup().location

param resourceSuffix string = substring(uniqueString(resourceGroup().id), 0, 5)
param storageAccountName string = 'aistorage${resourceSuffix}'
param fileShareName string = 'aifileshare${resourceSuffix}'
param acaEnvironmentName string = 'aienv${resourceSuffix}'
param acaEnvironmentStorageName string = 'aienvstorage${resourceSuffix}'
param acaJobName string = 'aiacajoblora${resourceSuffix}'
param acaLogAnalyticsName string = 'ailog${resourceSuffix}'
param manifestUrl string

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  name: storageAccountName
  location: location
  properties: {
    largeFileSharesState: 'Enabled'
  }
}

resource defaultFileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    protocolSettings: {
      smb: {}
    }
    cors: {
      corsRules: []
    }
    shareDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource fileShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: defaultFileService
  name: fileShareName
  properties: {
    shareQuota: 1024
  }
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: acaLogAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource environment 'Microsoft.App/managedEnvironments@2023-11-02-preview' = {
  name: acaEnvironmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
    workloadProfiles: [
      {
        workloadProfileType: 'Consumption-GPU-NC24-A100'
        name: 'GPU'
      }
    ]
  }
}

resource envStorage 'Microsoft.App/managedEnvironments/storages@2023-11-02-preview' = {
  parent: environment
  name: acaEnvironmentStorageName
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: fileShare.name
      accessMode: 'ReadWrite'
    }
  }
}

resource acajob 'Microsoft.App/jobs@2023-11-02-preview' = {
  name: acaJobName
  location: location
  properties: {
    environmentId: environment.id
    workloadProfileName: 'GPU'
    configuration: {
      secrets: null
      triggerType: 'Manual'
      replicaTimeout: timeout
      replicaRetryLimit: 0
      manualTriggerConfig: {
        replicaCompletionCount: 1
        parallelism: 1
      }
    }
    template: {
      containers: [
        {
          image: 'crsdcbuild2025.azurecr.io/artifact/e9623811-ed23-4d6c-8c56-a27494f2c808/buddy/phi-silica-fine-tune-containers-lora:20250730.1'
          name: acaJobName
          resources: {
            cpu: 24
            memory: '220Gi'
          }
          volumeMounts: [
            {
              volumeName: '${fileShareName}volume'
              mountPath: '/mount'
            }
          ]
        }
      ]
      initContainers: [
        {
          name: 'dataset-init'
          image: 'python:3.11-slim'
          resources: {
            cpu: 1
            memory: '2Gi'
          }
          env: [
            {
              name: 'MANIFEST_URL'
              value: manifestUrl
            }
          ]
          volumeMounts: [
            {
              volumeName: '${fileShareName}volume'
              mountPath: '/mount'
            }
          ]
          command: [ '/bin/sh', '-c' ]
      args: [
      '''set -euo pipefail
python - <<'PY'
import os, urllib.request, pathlib, json
manifest = os.environ.get('MANIFEST_URL')
if not manifest:
  raise SystemExit('MANIFEST_URL is required')
mp = '/tmp/manifest.manifest'
urllib.request.urlretrieve(manifest, mp)
out_dir = '/mount/dataset'
pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)

def download(u: str):
  import os
  name = os.path.basename(u.split('?')[0]) or 'file.jsonl'
  dest = os.path.join(out_dir, name)
  print(f'Downloading {u} -> {dest}', flush=True)
  try:
    urllib.request.urlretrieve(u, dest)
  except Exception as e:
    print(f'Failed to download {u}: {e}', flush=True)

def handle_text(fp: str):
  with open(fp, 'r', encoding='utf-8') as f:
    for line in f:
      u = line.strip()
      if u:
        download(u)

def handle_json(fp: str):
  with open(fp, 'r', encoding='utf-8') as f:
    obj = json.load(f)
  urls = []
  if isinstance(obj, dict):
    for key in ('train','validation','urls','files'):
      v = obj.get(key)
      if isinstance(v, list):
        urls.extend([str(x) for x in v])
    if not urls and 'url' in obj:
      urls.append(str(obj['url']))
  elif isinstance(obj, list):
    urls.extend([str(x) for x in obj])
  for u in urls:
    download(u)

ext = os.path.splitext(mp)[1].lower()
if ext == '.json':
  handle_json(mp)
else:
  # treat as plain text lines or jsonl
  try:
    # try jsonl (one json per line)
    with open(mp, 'r', encoding='utf-8') as f:
      for line in f:
        line = line.strip()
        if not line:
          continue
        try:
          rec = json.loads(line)
          if isinstance(rec, str):
            download(rec)
          elif isinstance(rec, dict) and 'url' in rec:
            download(str(rec['url']))
        except Exception:
          download(line)
  except Exception:
    handle_text(mp)
PY
      '''
      ]
        }
      ]
      volumes: [
        {
          name: '${fileShareName}volume'
          storageType: 'AzureFile'
          storageName: envStorage.name
        }
      ]
    }
  }
  identity: {
    type: 'None'
  }
}

output SUBSCRIPTION_ID string = subscription().subscriptionId
output RESOURCE_GROUP_NAME string = resourceGroup().name
output STORAGE_ACCOUNT_NAME string = storageAccount.name
output FILE_SHARE_NAME string = fileShare.name
output ACA_JOB_NAME string = acajob.name
output LOG_ANALYTICS_NAME string = logAnalytics.name
output COMMANDS array = []
output ARGS array = ['mount/<run_id>/lora.yaml']
