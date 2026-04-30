-- Dataset usage statistics and popularity
CREATE VIEW [dbo].[vw_DatasetUsageStats]
AS
SELECT
    d.DatasetId,
    d.Name,
    d.Category,
    d.License,
    d.IsCommercialOk,
    d.NumSamples,
    COUNT(u.UsageId) AS TotalUsageCount,
    SUM(CASE WHEN u.UsageType = 'quantum_training' THEN 1 ELSE 0 END) AS QuantumTrainingCount,
    SUM(CASE WHEN u.UsageType = 'lora_training' THEN 1 ELSE 0 END) AS LoRATrainingCount,
    MAX(u.UsageDate) AS LastUsedDate,
    d.LastValidated,
    d.ValidationStatus
FROM [dbo].[Datasets] d
LEFT JOIN [dbo].[DatasetUsage] u ON d.DatasetId = u.DatasetId
GROUP BY
    d.DatasetId, d.Name, d.Category, d.License, d.IsCommercialOk,
    d.NumSamples, d.LastValidated, d.ValidationStatus;
GO
