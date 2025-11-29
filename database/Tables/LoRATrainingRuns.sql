-- LoRA fine-tuning training runs metadata and results
CREATE TABLE [dbo].[LoRATrainingRuns]
(
    [RunId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [JobName] NVARCHAR(255) NOT NULL,
    [Model] NVARCHAR(255) NOT NULL, -- Phi-3.6-mini-instruct, Llama-3.2-1B-Instruct, etc.
    [DatasetName] NVARCHAR(255) NOT NULL,
    [DatasetPath] NVARCHAR(500) NOT NULL,
    [MaxTrainSamples] INT NULL,
    [MaxEvalSamples] INT NULL,
    [Epochs] INT NOT NULL,
    [BatchSize] INT NOT NULL,
    [SequenceLength] INT NOT NULL,
    [LearningRate] FLOAT NOT NULL,
    [LoraRank] INT NOT NULL,
    [LoraAlpha] INT NOT NULL,
    [LoraDropout] FLOAT NOT NULL,
    [TargetModules] NVARCHAR(500) NOT NULL, -- JSON array as string
    [TrainLoss] FLOAT NULL,
    [EvalLoss] FLOAT NULL,
    [TrainPerplexity] FLOAT NULL,
    [EvalPerplexity] FLOAT NULL,
    [TotalSteps] INT NULL,
    [ActualEpochs] INT NULL,
    [ExecutionTimeSeconds] FLOAT NULL,
    [GpuMemoryPeakGB] FLOAT NULL,
    [AdapterSavePath] NVARCHAR(500) NULL,
    [ConfigYamlPath] NVARCHAR(500) NULL,
    [LogsPath] NVARCHAR(500) NULL,
    [IsStreaming] BIT NOT NULL DEFAULT 1,
    [Runner] NVARCHAR(50) NOT NULL, -- hf (Hugging Face) or local
    [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [Status] NVARCHAR(50) NOT NULL DEFAULT 'running', -- running, completed, failed, cancelled
    [ErrorMessage] NVARCHAR(MAX) NULL,
    INDEX IX_LoRATrainingRuns_Model NONCLUSTERED ([Model]),
    INDEX IX_LoRATrainingRuns_DatasetName NONCLUSTERED ([DatasetName]),
    INDEX IX_LoRATrainingRuns_CreatedAt NONCLUSTERED ([CreatedAt] DESC),
    INDEX IX_LoRATrainingRuns_Status NONCLUSTERED ([Status])
);
GO
