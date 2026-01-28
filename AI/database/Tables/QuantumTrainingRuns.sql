-- Quantum ML training runs metadata and results
CREATE TABLE [dbo].[QuantumTrainingRuns]
(
    [RunId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [JobName] NVARCHAR(255) NOT NULL,
    [DatasetName] NVARCHAR(255) NOT NULL,
    [Backend] NVARCHAR(100) NOT NULL, -- qiskit_aer, lightning.qubit, ionq, rigetti, etc.
    [NumQubits] INT NOT NULL,
    [NumLayers] INT NOT NULL,
    [Entanglement] NVARCHAR(50) NOT NULL, -- linear, circular, full
    [LearningRate] FLOAT NOT NULL,
    [Epochs] INT NOT NULL,
    [BatchSize] INT NOT NULL,
    [TrainAccuracy] FLOAT NULL,
    [ValAccuracy] FLOAT NULL,
    [TestAccuracy] FLOAT NULL,
    [TrainLoss] FLOAT NULL,
    [ValLoss] FLOAT NULL,
    [TestLoss] FLOAT NULL,
    [TotalShots] INT NULL,
    [ExecutionTimeSeconds] FLOAT NULL,
    [IsAzureHardware] BIT NOT NULL DEFAULT 0,
    [AzureJobId] NVARCHAR(255) NULL,
    [AzureProvider] NVARCHAR(100) NULL,
    [EstimatedCostUSD] DECIMAL(10, 4) NULL,
    [CircuitDepth] INT NULL,
    [NumParameters] INT NULL,
    [StatusJsonPath] NVARCHAR(500) NULL, -- Path to status.json file
    [ResultsJsonPath] NVARCHAR(500) NULL, -- Path to results/*.json file
    [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [Status] NVARCHAR(50) NOT NULL DEFAULT 'running', -- running, completed, failed, cancelled
    [ErrorMessage] NVARCHAR(MAX) NULL,
    INDEX IX_QuantumTrainingRuns_DatasetName NONCLUSTERED ([DatasetName]),
    INDEX IX_QuantumTrainingRuns_Backend NONCLUSTERED ([Backend]),
    INDEX IX_QuantumTrainingRuns_CreatedAt NONCLUSTERED ([CreatedAt] DESC),
    INDEX IX_QuantumTrainingRuns_Status NONCLUSTERED ([Status])
);
GO
