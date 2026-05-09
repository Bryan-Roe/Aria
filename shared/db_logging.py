"""Database logging helpers for QAI.

Centralized, fault-tolerant wrappers around stored procedures:
  - sp_LogQuantumTrainingRun
  - sp_LogLoRATrainingRun
  - sp_LogChatConversation
  - sp_RegisterDataset (used opportunistically for datasets)

Behavior:
  - If env var QAI_DB_CONN is missing, all functions become NO-OP.
  - If pyodbc or driver not available, errors are swallowed and a warning emitted once.
  - Each log_* function returns a dict with {success: bool, error: Optional[str], ids: {...}}.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

_WARNED = False  # Emit import/connection warnings only once
REPO_ROOT = Path(__file__).resolve().parents[1]


def _warn_once(msg: str) -> None:
    global _WARNED
    if not _WARNED:
        print(f"[db_logging] WARN: {msg}")
        _WARNED = True


def _get_conn():
    """Return a pyodbc connection or None if unavailable/not configured."""
    conn_str = os.getenv("QAI_DB_CONN")
    if not conn_str:
        return None
    try:
        import pyodbc  # noqa: WPS433

        return pyodbc.connect(conn_str, timeout=5)
    except Exception as e:  # noqa: BLE001
        _warn_once(f"DB unavailable: {e}")
        return None


def _safe_exec(cursor, sql: str, params: List[Any]) -> bool:
    try:
        cursor.execute(sql, params)
        return True
    except Exception as e:  # noqa: BLE001
        _warn_once(f"Exec failed: {e}")
        return False


def log_chat_message_safe(
    session_id: Optional[str],
    provider: str,
    model: Optional[str],
    role: str,
    content: str,
    token_count: Optional[int] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    execution_time_ms: Optional[int] = None,
    finish_reason: Optional[str] = None,
    log_file_path: Optional[str] = None,
) -> Dict[str, Any]:
    conn = _get_conn()
    if not conn:
        return {"success": False, "skipped": True}
    try:
        cursor = conn.cursor()
        sql = (
            "DECLARE @ConvId UNIQUEIDENTIFIER, @MsgId UNIQUEIDENTIFIER; "
            "EXEC sp_LogChatConversation "
            "@SessionId=?, @Provider=?, @Model=?, @Title=?, @Role=?, @Content=?, "
            "@TokenCount=?, @PromptTokens=?, @CompletionTokens=?, @TotalTokens=?, "
            "@ExecutionTimeMs=?, @FinishReason=?, @LogFilePath=?, "
            "@ConversationId=@ConvId OUTPUT, @MessageId=@MsgId OUTPUT; "
            "SELECT @ConvId AS ConversationId, @MsgId AS MessageId;"
        )
        params = [
            session_id,
            provider,
            model,
            None,  # Title (optional auto-title not implemented yet)
            role,
            content,
            token_count,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            execution_time_ms,
            finish_reason,
            log_file_path,
        ]
        ok = _safe_exec(cursor, sql, params)
        conv_id = msg_id = None
        if ok:
            row = cursor.fetchone()
            if row:
                conv_id, msg_id = row.ConversationId, row.MessageId
            conn.commit()
        return {"success": ok, "conversation_id": conv_id, "message_id": msg_id}
    except Exception as e:  # noqa: BLE001
        _warn_once(f"Chat log failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _parse_quantum_summary() -> Dict[str, Any]:
    summary_path = (
        REPO_ROOT
        / "ai-projects"
        / "quantum-ml"
        / "results"
        / "custom_training_summary.json"
    )
    if not summary_path.exists():
        return {}
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        return {
            "train_loss_last": data.get("metrics", {}).get("train_loss_last"),
            "val_loss_last": data.get("metrics", {}).get("val_loss_last"),
            "val_acc_last": data.get("metrics", {}).get("val_acc_last"),
            "val_acc_best": data.get("metrics", {}).get("val_acc_best"),
        }
    except Exception as e:  # noqa: BLE001
        _warn_once(f"Parse quantum summary failed: {e}")
        return {}


def log_quantum_run_safe(
    job, result: Dict[str, Any], dataset_name: str, log_path: str
) -> Dict[str, Any]:  # noqa: ANN001
    conn = _get_conn()
    if not conn:
        return {"success": False, "skipped": True}
    try:
        metrics = _parse_quantum_summary()
        cursor = conn.cursor()
        # Stored procedure requires many params; pass only the essentials, rely on defaults
        sql = (
            "DECLARE @RunId UNIQUEIDENTIFIER; EXEC sp_LogQuantumTrainingRun "
            "@JobName=?, @DatasetName=?, @Backend=?, @NumQubits=?, @NumLayers=?, @Entanglement=?, "
            "@LearningRate=?, @Epochs=?, @BatchSize=?, @TrainAccuracy=?, @ValAccuracy=?, @TestAccuracy=?, "
            "@TrainLoss=?, @ValLoss=?, @TestLoss=?, @TotalShots=?, @ExecutionTimeSeconds=?, @IsAzureHardware=?, "
            "@AzureJobId=?, @AzureProvider=?, @EstimatedCostUSD=?, @CircuitDepth=?, @NumParameters=?, "
            "@StatusJsonPath=?, @ResultsJsonPath=?, @Status=?, @ErrorMessage=?, @RunId=@RunId OUTPUT; "
            "SELECT @RunId AS RunId;"
        )
        backend = (
            job.azure_backend
            if getattr(job, "mode", "") == "azure_hardware"
            else "qiskit_aer"
        )
        params = [
            job.name,
            dataset_name,
            backend,
            getattr(job, "n_qubits", None) or 4,
            2,  # NumLayers (fixed in current HybridQNN)
            "linear",  # Entanglement (current circuit pattern)
            getattr(job, "learning_rate", None) or 0.001,
            getattr(job, "epochs", None) or 1,
            getattr(job, "batch_size", None) or 16,
            None,  # TrainAccuracy (not explicitly tracked)
            metrics.get("val_acc_last"),  # ValAccuracy
            # TestAccuracy (reuse best val acc as proxy)
            metrics.get("val_acc_best"),
            metrics.get("train_loss_last"),  # TrainLoss
            metrics.get("val_loss_last"),  # ValLoss
            None,  # TestLoss
            getattr(job, "azure_shots", None),  # TotalShots for hardware
            result.get("duration_sec"),
            1 if getattr(job, "mode", "") == "azure_hardware" else 0,
            result.get("meta", {}).get("azure_job_id"),
            job.azure_backend if getattr(job, "mode", "") == "azure_hardware" else None,
            None,  # EstimatedCostUSD (could be added later)
            None,  # CircuitDepth
            None,  # NumParameters
            str(Path(log_path).parent / "status.json"),
            log_path,
            result.get("status"),
            None if result.get("status") == "succeeded" else "Non-zero return code",
        ]
        ok = _safe_exec(cursor, sql, params)
        run_id = None
        if ok:
            row = cursor.fetchone()
            if row:
                run_id = row.RunId
            conn.commit()
        return {"success": ok, "run_id": run_id}
    except Exception as e:  # noqa: BLE001
        _warn_once(f"Quantum run log failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        import yaml  # noqa: WPS433

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def log_lora_run_safe(job, result: Dict[str, Any]) -> Dict[str, Any]:  # noqa: ANN001
    conn = _get_conn()
    if not conn:
        return {"success": False, "skipped": True}
    try:
        cursor = conn.cursor()
        cfg_path = (
            Path(job.config)
            if getattr(job, "config", None)
            else REPO_ROOT / "AI" / "microsoft_phi-silica-3.6_v1" / "lora" / "lora.yaml"
        )
        cfg = _load_yaml(cfg_path)
        # Extract values with fallbacks
        lora_rank = cfg.get("lora_rank", 8)  # Not present -> placeholder
        lora_alpha = cfg.get("lora_alpha", 16)
        lora_dropout = job.lora_dropout or cfg.get("lora_dropout", 0.1)
        sequence_len = cfg.get("finetune_train_seqlen", 512)
        learning_rate = job.learning_rate or cfg.get("learning_rate", 2e-4)
        target_modules = (
            cfg.get("lora_target_modules")
            or cfg.get("target_modules")
            or ["q_proj", "v_proj"]
        )
        dataset_path = job.dataset or cfg.get("finetune_dataset", "data")
        dataset_name = Path(str(dataset_path)).name
        sql = (
            "DECLARE @RunId UNIQUEIDENTIFIER; EXEC sp_LogLoRATrainingRun "
            "@JobName=?, @Model=?, @DatasetName=?, @DatasetPath=?, @MaxTrainSamples=?, @MaxEvalSamples=?, "
            "@Epochs=?, @BatchSize=?, @SequenceLength=?, @LearningRate=?, @LoraRank=?, @LoraAlpha=?, @LoraDropout=?, "
            "@TargetModules=?, @TrainLoss=?, @EvalLoss=?, @TrainPerplexity=?, @EvalPerplexity=?, @TotalSteps=?, @ActualEpochs=?, "
            "@ExecutionTimeSeconds=?, @GpuMemoryPeakGB=?, @AdapterSavePath=?, @ConfigYamlPath=?, @LogsPath=?, @IsStreaming=?, @Runner=?, @Status=?, "
            "@ErrorMessage=?, @RunId=@RunId OUTPUT; SELECT @RunId AS RunId;"
        )
        params = [
            job.name,
            job.hf_model_id or "Phi-3.6-mini-instruct",
            dataset_name,
            str(dataset_path),
            job.max_train_samples,
            job.max_eval_samples,
            job.epochs or cfg.get("epochs", 1),
            cfg.get("finetune_train_batch_size", 1),
            sequence_len,
            learning_rate,
            lora_rank,
            lora_alpha,
            lora_dropout,
            json.dumps(target_modules),
            # TrainLoss (available inside training script; could parse later)
            None,
            None,  # EvalLoss
            None,  # TrainPerplexity
            None,  # EvalPerplexity
            None,  # TotalSteps
            job.epochs or cfg.get("epochs", 1),
            result.get("duration_sec"),
            None,  # GpuMemoryPeakGB
            None,  # AdapterSavePath
            str(cfg_path),
            result.get("log"),
            1,  # IsStreaming (default behavior)
            job.runner,
            result.get("status"),
            None if result.get("status") == "succeeded" else "Non-zero return code",
        ]
        ok = _safe_exec(cursor, sql, params)
        run_id = None
        if ok:
            row = cursor.fetchone()
            if row:
                run_id = row.RunId
            conn.commit()
        return {"success": ok, "run_id": run_id}
    except Exception as e:  # noqa: BLE001
        _warn_once(f"LoRA run log failed: {e}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


__all__ = [
    "log_chat_message_safe",
    "log_quantum_run_safe",
    "log_lora_run_safe",
]
