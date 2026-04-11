-- Unified view of all training runs (Quantum + LoRA)
CREATE VIEW [dbo].[vw_TrainingRunsSummary]
AS
SELECT
    q.RunId,
    'Quantum' AS TrainingType,
    q.JobName,
    q.DatasetName,
    q.Backend AS ModelOrBackend,
    q.Epochs,
    q.TestAccuracy AS FinalAccuracy,
    q.TestLoss AS FinalLoss,
    q.ExecutionTimeSeconds,
    q.IsAzureHardware AS IsCloudResource,
    q.EstimatedCostUSD,
    q.CreatedAt,
    q.Status,
    q.ErrorMessage
FROM [dbo].[QuantumTrainingRuns] q

UNION ALL

SELECT
    l.RunId,
    'LoRA' AS TrainingType,
    l.JobName,
    l.DatasetName,
    l.Model AS ModelOrBackend,
    l.Epochs,
    NULL AS FinalAccuracy,
    l.EvalLoss AS FinalLoss,
    l.ExecutionTimeSeconds,
    0 AS IsCloudResource,
    NULL AS EstimatedCostUSD,
    l.CreatedAt,
    l.Status,
    l.ErrorMessage
FROM [dbo].[LoRATrainingRuns] l;
GO
