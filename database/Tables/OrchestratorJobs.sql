-- Orchestrator job tracking for quantum_autorun and autotrain
CREATE TABLE [dbo].[OrchestratorJobs]
(
    [OrchestratorJobId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [OrchestratorType] NVARCHAR(50) NOT NULL, -- quantum_autorun, autotrain, autonomous_training
    [JobName] NVARCHAR(255) NOT NULL,
    [ConfigYamlPath] NVARCHAR(500) NOT NULL,
    [Mode] NVARCHAR(100) NULL, -- train_custom_dataset, azure_hardware, hf, local, etc.
    [IsDryRun] BIT NOT NULL DEFAULT 0,
    [Status] NVARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, running, completed, failed, cancelled
    [StartedAt] DATETIME2 NULL,
    [CompletedAt] DATETIME2 NULL,
    [ExecutionTimeSeconds] FLOAT NULL,
    [TrainingRunId] UNIQUEIDENTIFIER NULL, -- FK to QuantumTrainingRuns or LoRATrainingRuns
    [StatusJsonPath] NVARCHAR(500) NULL,
    [ErrorMessage] NVARCHAR(MAX) NULL,
    [OutputSummary] NVARCHAR(MAX) NULL, -- JSON summary of key metrics
    INDEX IX_OrchestratorJobs_Type NONCLUSTERED ([OrchestratorType]),
    INDEX IX_OrchestratorJobs_JobName NONCLUSTERED ([JobName]),
    INDEX IX_OrchestratorJobs_Status NONCLUSTERED ([Status]),
    INDEX IX_OrchestratorJobs_StartedAt NONCLUSTERED ([StartedAt] DESC)
);
GO
