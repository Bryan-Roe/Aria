---
applyTo: "**/db_logging.py"
---

# DB Logging — Instruction Guide

## Fault-Tolerant Stored Procedure Wrappers

All logging functions follow the same fault-tolerance pattern:

```python
def log_*_safe(...) -> Dict:
    # 1. If QAI_DB_CONN not set → NO-OP (returns {success: False, skipped: True})
    # 2. If pyodbc unavailable → logs warning once, continues
    # 3. Try stored procedure call
    # 4. On any exception → returns {success: False, error: str}
    # 5. On success → returns {success: True, ...ids...}
```

## Available Functions

### log_chat_message_safe()
```python
log_chat_message_safe(
    session_id, provider, model, role, content,
    token_count=None, ...
) → {success: bool, conversation_id: str, message_id: str}
# Calls: sp_LogChatConversation
```

### log_quantum_run_safe()
```python
log_quantum_run_safe(
    job, result, dataset_name=None, log_path=None
) → {success: bool, run_id: str}
# Calls: sp_LogQuantumTrainingRun
```

### log_lora_run_safe()
```python
log_lora_run_safe(
    job, result
) → {success: bool}
# Calls: sp_LogLoRATrainingRun
# Extracts config from YAML automatically
```

## Return Structure

All functions return a dict with at minimum:
- `success: bool` — whether the log was written
- `skipped: bool` (optional) — True if DB is not configured
- `error: str` (optional) — error message if failed

## Coding Conventions

- **Never crash on logging failure** — logging is advisory, not critical path
- DB connection is optional (`QAI_DB_CONN` env var)
- All functions are safe to call even without a database
- Stored procedures are defined in `database/StoredProcedures/`
- Pool size configurable via `QAI_SQL_POOL_SIZE` (default: 10)
- Monitor pool saturation via `/api/ai/status` (warns at ≥80%)
