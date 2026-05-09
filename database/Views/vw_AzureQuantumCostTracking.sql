-- Azure Quantum cost tracking and job statistics
CREATE VIEW [dbo].[vw_AzureQuantumCostTracking]
AS
SELECT
    Provider,
    Target,
    COUNT(*) AS TotalJobs,
    SUM(CASE WHEN Status = 'succeeded' THEN 1 ELSE 0 END) AS SuccessfulJobs,
    SUM(CASE WHEN Status = 'failed' THEN 1 ELSE 0 END) AS FailedJobs,
    SUM(NumShots) AS TotalShots,
    AVG(NumQubits) AS AvgQubits,
    AVG(CircuitDepth) AS AvgCircuitDepth,
    SUM(EstimatedCostUSD) AS TotalEstimatedCost,
    SUM(ActualCostUSD) AS TotalActualCost,
    AVG(ExecutionTimeSeconds) AS AvgExecutionTime,
    AVG(QueueTimeSeconds) AS AvgQueueTime,
    MIN(SubmittedAt) AS FirstSubmission,
    MAX(SubmittedAt) AS LastSubmission
FROM [dbo].[AzureQuantumJobs]
GROUP BY Provider, Target;
GO
