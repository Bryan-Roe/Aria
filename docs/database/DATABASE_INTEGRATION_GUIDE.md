# Database Integration Guide

This document provides step-by-step instructions for integrating the QAI database with the existing codebase.

## Overview

The database integration adds automatic logging of:
- **Quantum training runs** → `QuantumTrainingRuns` table
- **LoRA training runs** → `LoRATrainingRuns` table  
- **Chat messages** → `ChatConversations` + `ChatMessages` tables

## Files Created

✅ **Database Schema** (in `database/`):
- `Tables/*.sql` - 7 tables for core data
- `Views/*.sql` - 3 views for analytics
- `StoredProcedures/*.sql` - 4 SPs for easy logging
- `README.md` - Deployment and usage guide
- `database.sqlproj` - VS Code SQL Database Project

✅ **Shared Module**:
- `shared/db_logging.py` - Safe, fault-tolerant logging helpers

✅ **Configuration**:
- `requirements.txt` - Added `pyodbc` and `sqlalchemy`
- `local.settings.json` - Added `QAI_DB_CONN` placeholder
- `.env` - Environment variable template

✅ **Script Patches**:
- `scripts/quantum_autorun.py` - Logs quantum runs after success
- `scripts/autotrain.py` - Logs LoRA runs after success

## Files That Need Manual Editing

### 1. `function_app.py` - Add Chat Logging

**Step 1:** Add imports at the top (after line 8):

```python
import azure.functions as func
import json
import logging
import os
import sys
from pathlib import Path
import subprocess
import importlib.util as _iu
from uuid import uuid4  # ADD THIS

# Optional DB logging (safe no-op if not configured)  # ADD THIS BLOCK
try:  # noqa: SIM105
    from shared.db_logging import log_chat_message_safe  # type: ignore
except Exception:  # noqa: BLE001
    def log_chat_message_safe(*_a, **_kw):  # type: ignore
        return {"success": False, "skipped": True}

# Add talk-to-ai to path so we can import chat_providers
talk_to_ai_path = Path(__file__).resolve().parent / "talk-to-ai" / "src"
sys.path.insert(0, str(talk_to_ai_path))
```

**Step 2:** In the `chat()` function (around line 200), replace the response_data section:

**FIND:**
```python
        # Get completion (non-streaming for HTTP simplicity)
        result = provider.complete(pruned_messages, stream=False)
        
        # If result is still a generator, consume it
        if hasattr(result, '__iter__') and not isinstance(result, str):
            result = ''.join(result)

        response_data = {
            "response": result,
            "provider": info.name,
            "model": info.model,
            "pruning": {
                "original_tokens": stats.original_tokens,
                "pruned_tokens": stats.pruned_tokens,
                "removed_count": stats.removed_count,
                "budget": stats.budget,
                "reserve_output_tokens": stats.reserve_output_tokens,
            }
        }
```

**REPLACE WITH:**
```python
        # Get completion (non-streaming for HTTP simplicity)
        result = provider.complete(pruned_messages, stream=False)
        
        # If result is still a generator, consume it
        if hasattr(result, '__iter__') and not isinstance(result, str):
            result = ''.join(result)

        # Session handling (client may pass session_id to maintain conversation linkage)
        session_id = req_body.get("session_id") or req.headers.get("X-Session-Id") or str(uuid4())

        # Log latest user message (last in list) BEFORE assistant reply
        try:
            if messages:
                last_user = messages[-1]
                if last_user.get("role") == "user":
                    log_chat_message_safe(
                        session_id=session_id,
                        provider=info.name,
                        model=info.model,
                        role="user",
                        content=str(last_user.get("content", ""))[:4000],  # truncate safety
                    )
        except Exception as e:  # noqa: BLE001
            logging.warning(f"User chat log skipped: {e}")

        # Log assistant reply
        try:
            log_resp = log_chat_message_safe(
                session_id=session_id,
                provider=info.name,
                model=info.model,
                role="assistant",
                content=str(result)[:8000],  # truncate safety
            )
        except Exception as e:  # noqa: BLE001
            logging.warning(f"Assistant chat log skipped: {e}")
            log_resp = {"success": False}

        response_data = {
            "response": result,
            "provider": info.name,
            "model": info.model,
            "session_id": session_id,
            "conversation_id": log_resp.get("conversation_id"),
            "pruning": {
                "original_tokens": stats.original_tokens,
                "pruned_tokens": stats.pruned_tokens,
                "removed_count": stats.removed_count,
                "budget": stats.budget,
                "reserve_output_tokens": stats.reserve_output_tokens,
            }
        }
```

**Step 3:** In the `chat_stream()` function (around line 280), add session handling:

**FIND:**
```python
        gen = provider.complete(pruned_messages, stream=True)

        def sse_iterable():  # generator yielding bytes
            try:
                # Send a prelude event with meta
                pre = {
                    "provider": info.name,
                    "model": info.model,
                    "pruning": {
                        "original_tokens": stats.original_tokens,
                        "pruned_tokens": stats.pruned_tokens,
                        "removed_count": stats.removed_count,
                        "budget": stats.budget,
                        "reserve_output_tokens": stats.reserve_output_tokens,
                    }
                }
                yield (f"event: meta\n" f"data: {json.dumps(pre)}\n\n").encode("utf-8")

                for chunk in gen:
                    if not chunk:
                        continue
                    payload = json.dumps({"delta": chunk})
                    yield (f"data: {payload}\n\n").encode("utf-8")

                yield b"event: done\ndata: {}\n\n"
```

**REPLACE WITH:**
```python
        gen = provider.complete(pruned_messages, stream=True)
        session_id = body.get("session_id") or req.headers.get("X-Session-Id") or str(uuid4())
        
        # Log initial user prompt once
        try:
            if pruned_messages and pruned_messages[-1].role == "user":
                log_chat_message_safe(
                    session_id=session_id,
                    provider=info.name,
                    model=info.model,
                    role="user",
                    content=str(pruned_messages[-1].content)[:4000],
                )
        except Exception as e:  # noqa: BLE001
            logging.warning(f"Stream user log skipped: {e}")

        def sse_iterable():  # generator yielding bytes
            try:
                # Send a prelude event with meta
                pre = {
                    "provider": info.name,
                    "model": info.model,
                    "pruning": {
                        "original_tokens": stats.original_tokens,
                        "pruned_tokens": stats.pruned_tokens,
                        "removed_count": stats.removed_count,
                        "budget": stats.budget,
                        "reserve_output_tokens": stats.reserve_output_tokens,
                    }
                }
                yield (f"event: meta\n" f"data: {json.dumps(pre)}\n\n").encode("utf-8")

                assistant_accum = []
                for chunk in gen:
                    if not chunk:
                        continue
                    payload = json.dumps({"delta": chunk})
                    yield (f"data: {payload}\n\n").encode("utf-8")
                    assistant_accum.append(chunk)

                # Log full assistant reply at end
                full_reply = "".join(assistant_accum)
                try:
                    log_chat_message_safe(
                        session_id=session_id,
                        provider=info.name,
                        model=info.model,
                        role="assistant",
                        content=str(full_reply)[:8000],
                    )
                except Exception as e:  # noqa: BLE001
                    logging.warning(f"Stream assistant log skipped: {e}")
                
                yield b"event: done\ndata: {}\n\n"
```

## Database Deployment

### Option 1: Azure SQL Database (Recommended for Production)

```powershell
# 1. Create Azure SQL resources
az group create --name rg-qai-db --location eastus
az sql server create --name qai-sql-server --resource-group rg-qai-db --admin-user qai-admin --admin-password 'YourSecurePassword123!'
az sql db create --resource-group rg-qai-db --server qai-sql-server --name qai-db --service-objective S0

# 2. Configure firewall
az sql server firewall-rule create --resource-group rg-qai-db --server qai-sql-server --name AllowMyIP --start-ip-address YOUR_IP --end-ip-address YOUR_IP

# 3. Build and deploy using VS Code SQL Database Projects extension
# - Open database/ folder in VS Code
# - Use "Publish" command from SQL Database Projects view
# - Target: qai-sql-server.database.windows.net, qai-db

# 4. Set connection string in environment
$env:QAI_DB_CONN = "Server=tcp:qai-sql-server.database.windows.net,1433;Database=qai-db;Uid=qai-admin;Pwd=YourSecurePassword123!;Encrypt=yes;TrustServerCertificate=no;"
```

### Option 2: Local SQL Server (Development)

```powershell
# 1. Install SQL Server Express (free)
# Download from: https://www.microsoft.com/en-us/sql-server/sql-server-downloads

# 2. Deploy schema using SqlPackage or VS Code extension

# 3. Set local connection string
$env:QAI_DB_CONN = "Server=localhost;Database=qai-db;Trusted_Connection=yes;"
```

## Testing the Integration

### 1. Test without database (default behavior)

```powershell
# No QAI_DB_CONN set → all logging is NO-OP
python .\scripts\quantum_autorun.py --job heart_quick
# Output: [quantum_autorun] DB logging skipped (QAI_DB_CONN not set)
```

### 2. Test with database

```powershell
# Set connection string
$env:QAI_DB_CONN = "Server=tcp:your-server.database.windows.net,1433;Database=qai-db;Uid=qai-admin;Pwd=YourPassword;Encrypt=yes;TrustServerCertificate=no;"

# Run quantum training
python .\scripts\quantum_autorun.py --job heart_quick
# Output: [quantum_autorun] Logged quantum run to DB (run_id=GUID)

# Run LoRA training
python .\scripts\autotrain.py --job phi36_mixed_chat
# Output: [autotrain] Logged LoRA run to DB (run_id=GUID)

# Test chat endpoint
func host start
curl -X POST http://localhost:7071/api/chat -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"Hello"}]}'
# Response includes: "conversation_id": "GUID"
```

### 3. Verify data in database

```sql
-- Check quantum runs
SELECT TOP 10 * FROM QuantumTrainingRuns ORDER BY CreatedAt DESC;

-- Check LoRA runs
SELECT TOP 10 * FROM LoRATrainingRuns ORDER BY CreatedAt DESC;

-- Check chat conversations
SELECT TOP 10 * FROM ChatConversations ORDER BY CreatedAt DESC;

-- Check chat messages
SELECT TOP 50 * FROM ChatMessages ORDER BY Timestamp DESC;

-- Unified training summary
SELECT * FROM vw_TrainingRunsSummary ORDER BY CreatedAt DESC;

-- Dataset usage stats
SELECT * FROM vw_DatasetUsageStats ORDER BY TotalUsageCount DESC;
```

## Cost Estimates

### Azure SQL Database

- **Basic (5 DTU)**: ~$5/month - Good for dev/test
- **S0 (10 DTU)**: ~$15/month - Small production
- **S1 (20 DTU)**: ~$30/month - Medium production
- **Serverless**: ~$150/month active, auto-pause when idle

### Recommendation

- **Development**: Use local SQL Server Express (FREE)
- **Production**: Start with S0, scale up as needed
- **High traffic**: Use serverless with auto-pause for cost optimization

## Troubleshooting

### "pyodbc not found"

```powershell
pip install pyodbc
```

### "ODBC Driver not found"

Download and install: [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### Connection timeout

- Check firewall rules in Azure Portal
- Verify server name and credentials
- Test with `sqlcmd` or Azure Data Studio first

### Logging is silent

- Expected behavior when `QAI_DB_CONN` not set
- Check warning messages: `[db_logging] WARN: DB unavailable: ...`
- Verify connection string format

## Next Steps

1. ✅ Complete manual edits to `function_app.py` (3 sections above)
2. Deploy database schema to Azure SQL or local SQL Server
3. Set `QAI_DB_CONN` environment variable
4. Run test training jobs and chat requests
5. Query database to verify logging
6. Set up Power BI dashboards for analytics (see `database/README.md`)

## Architecture Benefits

- **Fault-tolerant**: If DB unavailable, training/chat continues normally
- **Zero-config default**: Works without any database (NO-OP mode)
- **Pay-as-you-go**: Only incur costs when database is provisioned
- **Analytics-ready**: Views and stored procedures enable rich insights
- **Audit trail**: Complete history of all training runs and conversations

## Reference

- Database schema: `database/README.md`
- Stored procedures: `database/StoredProcedures/*.sql`
- Helper module: `shared/db_logging.py`
- Azure SQL docs: https://learn.microsoft.com/azure/azure-sql/
