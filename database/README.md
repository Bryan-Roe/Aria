# QAI Database Project

SQL database schema for tracking and managing QAI workspace activities including quantum training, LoRA fine-tuning, chat conversations, datasets, and Azure Quantum jobs.

## Overview

This database project provides comprehensive tracking and analytics for the QAI multi-AI/ML workspace. It's designed for **Azure SQL Database** but can be adapted for SQL Server or other Azure SQL variants.

## Schema Components

### Tables

#### Training & Execution

- **QuantumTrainingRuns** - Quantum ML training metadata, results, and hardware tracking
- **LoRATrainingRuns** - LoRA fine-tuning runs with hyperparameters and metrics
- **AzureQuantumJobs** - Azure Quantum job submissions, status, and cost tracking
- **OrchestratorJobs** - Orchestrator execution history (quantum_autorun, autotrain)

#### Chat & Conversations

- **ChatConversations** - Chat session metadata for talk-to-ai and Azure Functions
- **ChatMessages** - Individual messages with token usage and timing

#### Semantic Memory (Embeddings)

- **ChatMessageEmbeddings** - Per-message embedding vectors (VARBINARY float32 array) enabling semantic retrieval. Populated automatically by Azure Function `/api/chat` and the backfill script `scripts/ingest_chat_logs_to_sql.py`. Supports future migration to native `VECTOR` type when available.

Memory retrieval flow:

1. User sends message to `/api/chat` (optional `session_id` in POST body).
2. Endpoint generates embedding (Azure OpenAI > OpenAI > local hash fallback) and queries recent embeddings for similar past messages.
3. Top-K similar messages are injected as system memory prompts to enhance contextual continuity.
4. User and assistant messages are logged via `sp_LogChatConversation` and embeddings stored in `ChatMessageEmbeddings`.

Embedding configuration:

| Priority | Method | Env Vars Required |
| ---------- | -------- | ------------------- |
| 1 | Azure OpenAI Embeddings | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` |
| 2 | OpenAI Embeddings | `OPENAI_API_KEY` |
| 3 | Local Hash Fallback (dim=256) | None |

Backfill existing logs:

```powershell
python .\scripts\ingest_chat_logs_to_sql.py --logs-dir talk-to-ai\logs --embed-assistant
```

Table schema excerpt:

```sql
CREATE TABLE [dbo].[ChatMessageEmbeddings] (
  EmbeddingId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
  MessageId UNIQUEIDENTIFIER NOT NULL REFERENCES dbo.ChatMessages(MessageId) ON DELETE CASCADE,
  EmbeddingModel NVARCHAR(100) NOT NULL,
  EmbeddingDim INT NOT NULL,
  EmbeddingVector VARBINARY(MAX) NOT NULL,
  CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE()
);
```

Retrieval (Python-side cosine similarity) selects recent rows (TOP 500) optionally filtered by `SessionId` for targeted personalization.

#### Datasets & Usage

- **Datasets** - Dataset registry with licensing and validation status
- **DatasetUsage** - Dataset usage tracking across training runs

#### MCP Server

- **MCPServerSessions** - Model Context Protocol server session tracking
- **MCPToolCalls** - Individual MCP tool invocations and results

### Views

- **vw_TrainingRunsSummary** - Unified view of all training runs (Quantum + LoRA)
- **vw_DatasetUsageStats** - Dataset popularity and usage statistics
- **vw_AzureQuantumCostTracking** - Azure Quantum cost analysis by provider/target

### Stored Procedures

- **sp_LogQuantumTrainingRun** - Log quantum training with automatic dataset usage tracking
- **sp_LogLoRATrainingRun** - Log LoRA training with automatic dataset usage tracking
- **sp_LogChatConversation** - Log chat messages with automatic conversation management
- **sp_RegisterDataset** - Register or update dataset metadata

## Deployment

### Prerequisites

- Azure SQL Database or SQL Server 2019+
- SQL Database Project extension for VS Code
- .NET SDK 6.0+ (for SQL Database Projects)

### Using VS Code

1. Install the [SQL Database Projects extension](https://marketplace.visualstudio.com/items?itemName=ms-mssql.sql-database-projects-vscode)
2. Open this folder in VS Code
3. Use the SQL Database Projects view to:
   - **Build**: Validate schema without deployment
   - **Publish**: Deploy to Azure SQL or local SQL Server
   - **Generate Script**: Create deployment SQL script

### Manual Deployment

```powershell
# Build the project
dotnet build database.sqlproj

# Or deploy directly to Azure SQL
SqlPackage.exe /Action:Publish `
  /SourceFile:bin\Debug\database.dacpac `
  /TargetConnectionString:"Server=tcp:your-server.database.windows.net,1433;Database=qai-db;User ID=your-user;Password=your-password;Encrypt=True;"
```

### Deploy to Azure SQL Database

```powershell
# Create resource group (if needed)
az group create --name rg-qai-db --location eastus

# Create Azure SQL server
az sql server create `
  --name qai-sql-server `
  --resource-group rg-qai-db `
  --location eastus `
  --admin-user qai-admin `
  --admin-password 'YourSecurePassword123!'

# Create database
az sql db create `
  --resource-group rg-qai-db `
  --server qai-sql-server `
  --name qai-db `
  --service-objective S0  # Basic tier for dev/test

# Configure firewall (allow your IP)
az sql server firewall-rule create `
  --resource-group rg-qai-db `
  --server qai-sql-server `
  --name AllowMyIP `
  --start-ip-address YOUR_IP `
  --end-ip-address YOUR_IP

# Publish from VS Code SQL Database Projects extension
# Or use SqlPackage CLI as shown above
```

## Integration with QAI Workspace

### Python Integration

Install dependencies:

```powershell
pip install pyodbc sqlalchemy
```

Example usage:

```python
import pyodbc
from datetime import datetime

# Connection string (use Azure Key Vault in production)
conn_str = (
  "Driver={ODBC Driver 18 for SQL Server};"
  "Server=tcp:qai-sql-server.database.windows.net,1433;"
  "Database=qai-db;"
  "Uid=qai-admin;"
  "Pwd={your_password};"
  "Encrypt=yes;"
  "TrustServerCertificate=no;"
)

# Log quantum training run
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

cursor.execute("""
  DECLARE @RunId UNIQUEIDENTIFIER;
  EXEC sp_LogQuantumTrainingRun
    @JobName = ?,
    @DatasetName = ?,
    @Backend = ?,
    @NumQubits = ?,
    @NumLayers = ?,
    @Entanglement = ?,
    @LearningRate = ?,
    @Epochs = ?,
    @BatchSize = ?,
    @TestAccuracy = ?,
    @ExecutionTimeSeconds = ?,
    @Status = ?,
    @RunId = @RunId OUTPUT;
  SELECT @RunId;
""", 'heart_quick', 'heart_disease', 'qiskit_aer', 4, 2, 'linear',
   0.01, 10, 16, 0.85, 45.2, 'completed')

run_id = cursor.fetchone()[0]
conn.commit()
print(f"Logged run: {run_id}")
```

### Orchestrator Integration

Modify `scripts/quantum_autorun.py` and `scripts/autotrain.py` to log runs:

```python
# Add to quantum_autorun.py after successful training
import pyodbc

def log_to_database(job_config, results):
  conn = pyodbc.connect(DB_CONNECTION_STRING)
  cursor = conn.cursor()

  cursor.execute("""
    DECLARE @RunId UNIQUEIDENTIFIER;
    EXEC sp_LogQuantumTrainingRun
      @JobName = ?, @DatasetName = ?, @Backend = ?,
      @NumQubits = ?, @NumLayers = ?, @Entanglement = ?,
      @LearningRate = ?, @Epochs = ?, @BatchSize = ?,
      @TestAccuracy = ?, @TestLoss = ?, @ExecutionTimeSeconds = ?,
      @StatusJsonPath = ?, @ResultsJsonPath = ?,
      @Status = ?, @RunId = @RunId OUTPUT;
  """, job_config['name'], job_config['dataset'], job_config['backend'],
     job_config['n_qubits'], job_config['n_layers'], job_config['entanglement'],
     job_config['learning_rate'], job_config['epochs'], job_config['batch_size'],
     results['test_accuracy'], results['test_loss'], results['execution_time'],
     results['status_json_path'], results['results_json_path'], 'completed')

  conn.commit()
```

### Azure Functions Integration

Add database logging to `function_app.py`:

```python
import pyodbc
from azure.identity import DefaultAzureCredential

# Use managed identity in production
def get_db_connection():
  credential = DefaultAzureCredential()
  token = credential.get_token("https://database.windows.net/")

  conn_str = (
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:qai-sql-server.database.windows.net,1433;"
    f"Database=qai-db;"
    f"Authentication=ActiveDirectoryMsi;"
  )
  return pyodbc.connect(conn_str)

@app.route(route="chat", methods=["POST"])
async def chat_endpoint(req: func.HttpRequest) -> func.HttpResponse:
  # ... existing chat logic ...

  # Log conversation
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
    DECLARE @ConvId UNIQUEIDENTIFIER, @MsgId UNIQUEIDENTIFIER;
    EXEC sp_LogChatConversation
      @SessionId = ?, @Provider = ?, @Model = ?,
      @Role = ?, @Content = ?, @TotalTokens = ?,
      @ConversationId = @ConvId OUTPUT, @MessageId = @MsgId OUTPUT;
  """, session_id, provider, model, 'user', user_message, token_count)
  conn.commit()
```

## Cost Optimization

### Azure SQL Tiers

- **Dev/Test**: S0 (10 DTUs, ~$15/month) or Basic (5 DTUs, ~$5/month)
- **Production**: S1-S3 (20-100 DTUs, $30-$200/month)
- **Serverless**: Auto-pause after inactivity, pay per second (~$150/month active)

### Data Retention

Implement retention policies to control costs:

```sql
-- Archive old training runs (keep last 90 days)
DELETE FROM QuantumTrainingRuns
WHERE CreatedAt < DATEADD(day, -90, GETUTCDATE())
  AND Status IN ('completed', 'failed');

-- Archive chat messages (keep last 30 days)
DELETE FROM ChatMessages
WHERE Timestamp < DATEADD(day, -30, GETUTCDATE());
```

## Monitoring & Analytics

### Power BI Integration

Connect Power BI Desktop to Azure SQL:

1. Get Data → Azure → Azure SQL Database
2. Server: `qai-sql-server.database.windows.net`
3. Database: `qai-db`
4. Use views for pre-aggregated data

### Sample Queries

```sql
-- Training success rate by dataset
SELECT
    DatasetName,
    COUNT(*) AS TotalRuns,
    AVG(TestAccuracy) AS AvgAccuracy,
    SUM(CASE WHEN Status = 'completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS SuccessRate
FROM vw_TrainingRunsSummary
WHERE TrainingType = 'Quantum'
GROUP BY DatasetName
ORDER BY AvgAccuracy DESC;

-- Azure Quantum cost by month
SELECT
    DATEPART(year, SubmittedAt) AS Year,
    DATEPART(month, SubmittedAt) AS Month,
    Provider,
    SUM(ActualCostUSD) AS TotalCost,
    COUNT(*) AS JobCount
FROM AzureQuantumJobs
WHERE Status = 'succeeded'
GROUP BY DATEPART(year, SubmittedAt), DATEPART(month, SubmittedAt), Provider
ORDER BY Year DESC, Month DESC;

-- Most active chat providers
SELECT
    Provider,
    COUNT(DISTINCT ConversationId) AS TotalConversations,
    COUNT(*) AS TotalMessages,
    AVG(CAST(ExecutionTimeMs AS FLOAT)) AS AvgResponseTimeMs
FROM ChatConversations c
JOIN ChatMessages m ON c.ConversationId = m.ConversationId
WHERE m.Role = 'assistant'
GROUP BY Provider
ORDER BY TotalConversations DESC;
```

## Security Best Practices

1. **Authentication**: Use Azure AD Managed Identity in production
2. **Encryption**: Enable Transparent Data Encryption (TDE) on Azure SQL
3. **Network**: Configure VNet service endpoints or Private Link
4. **Secrets**: Store connection strings in Azure Key Vault
5. **Auditing**: Enable Azure SQL auditing for compliance

```powershell
# Enable TDE (enabled by default on Azure SQL)
az sql db tde set --resource-group rg-qai-db `
  --server qai-sql-server `
  --database qai-db `
  --status Enabled

# Enable auditing
az sql server audit-policy update `
  --resource-group rg-qai-db `
  --name qai-sql-server `
  --state Enabled `
  --blob-storage-target-state Enabled `
  --storage-account your-storage-account
```

## Troubleshooting

### Connection Issues

```powershell
# Test connection
sqlcmd -S qai-sql-server.database.windows.net -d qai-db -U qai-admin -P 'YourPassword'

# Check firewall rules
az sql server firewall-rule list `
  --resource-group rg-qai-db `
  --server qai-sql-server
```

### Build Errors

```powershell
# Clean and rebuild
Remove-Item -Recurse -Force bin, obj
dotnet build database.sqlproj
```

## Roadmap

- [ ] Add full-text search indexes for chat content
- [ ] Implement temporal tables for audit history
- [ ] Create Azure Function triggers for real-time dashboards
- [ ] Add Graph DB tables for model dependency tracking
- [ ] Cosmos DB integration for high-throughput logging
- [ ] Stream Analytics for real-time metrics

## License

Part of the QAI project. See root LICENSE for details.
