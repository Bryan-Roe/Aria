-- Azure Quantum job submissions and status tracking
CREATE TABLE [dbo].[AzureQuantumJobs]
(
    [JobId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [AzureJobId] NVARCHAR(255) NOT NULL UNIQUE,
    [LocalRunId] UNIQUEIDENTIFIER NULL, -- FK to QuantumTrainingRuns if applicable
    [WorkspaceName] NVARCHAR(255) NOT NULL,
    [ResourceGroup] NVARCHAR(255) NOT NULL,
    [SubscriptionId] NVARCHAR(255) NOT NULL,
    [Provider] NVARCHAR(100) NOT NULL, -- ionq, rigetti, quantinuum, microsoft
    [Target] NVARCHAR(100) NOT NULL, -- ionq.qpu, rigetti.sim.qvm, etc.
    [CircuitName] NVARCHAR(255) NULL,
    [NumQubits] INT NOT NULL,
    [CircuitDepth] INT NULL,
    [NumShots] INT NOT NULL,
    [EstimatedCostUSD] DECIMAL(10, 4) NULL,
    [ActualCostUSD] DECIMAL(10, 4) NULL,
    [Status] NVARCHAR(50) NOT NULL, -- submitted, waiting, executing, succeeded, failed, cancelled
    [AzureStatus] NVARCHAR(50) NULL, -- Raw status from Azure
    [SubmittedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [StartedAt] DATETIME2 NULL,
    [CompletedAt] DATETIME2 NULL,
    [ExecutionTimeSeconds] FLOAT NULL,
    [QueueTimeSeconds] FLOAT NULL,
    [ResultsCounts] NVARCHAR(MAX) NULL, -- JSON histogram of measurement results
    [Metadata] NVARCHAR(MAX) NULL, -- JSON metadata from Azure
    [ErrorMessage] NVARCHAR(MAX) NULL,
    [LocalResultsPath] NVARCHAR(500) NULL, -- Path to local results JSON
    CONSTRAINT FK_AzureQuantumJobs_LocalRun FOREIGN KEY ([LocalRunId]) 
        REFERENCES [dbo].[QuantumTrainingRuns]([RunId]) ON DELETE SET NULL,
    INDEX IX_AzureQuantumJobs_AzureJobId NONCLUSTERED ([AzureJobId]),
    INDEX IX_AzureQuantumJobs_Provider NONCLUSTERED ([Provider]),
    INDEX IX_AzureQuantumJobs_Status NONCLUSTERED ([Status]),
    INDEX IX_AzureQuantumJobs_SubmittedAt NONCLUSTERED ([SubmittedAt] DESC)
);
GO
