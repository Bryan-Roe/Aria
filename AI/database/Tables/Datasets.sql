-- Dataset registry and usage tracking
CREATE TABLE [dbo].[Datasets]
(
    [DatasetId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [Name] NVARCHAR(255) NOT NULL UNIQUE,
    [Category] NVARCHAR(50) NOT NULL, -- quantum, chat, vision, raw, processed
    [Type] NVARCHAR(50) NOT NULL, -- csv, jsonl, parquet, etc.
    [Path] NVARCHAR(500) NOT NULL,
    [Description] NVARCHAR(MAX) NULL,
    [Source] NVARCHAR(500) NULL, -- URL or origin
    [License] NVARCHAR(100) NULL, -- CC BY-SA 3.0, Apache 2.0, CC BY-NC 4.0, etc.
    [IsCommercialOk] BIT NOT NULL DEFAULT 0,
    [SizeBytes] BIGINT NULL,
    [NumSamples] INT NULL,
    [NumFeatures] INT NULL,
    [NumClasses] INT NULL,
    [Format] NVARCHAR(MAX) NULL, -- JSON schema or description
    [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [LastValidated] DATETIME2 NULL,
    [ValidationStatus] NVARCHAR(50) NULL, -- valid, invalid, not_validated
    INDEX IX_Datasets_Category NONCLUSTERED ([Category]),
    INDEX IX_Datasets_Name NONCLUSTERED ([Name])
);
GO

CREATE TABLE [dbo].[DatasetUsage]
(
    [UsageId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [DatasetId] UNIQUEIDENTIFIER NOT NULL,
    [UsageType] NVARCHAR(50) NOT NULL, -- quantum_training, lora_training, chat_inference, validation
    [ReferenceId] UNIQUEIDENTIFIER NULL, -- FK to QuantumTrainingRuns or LoRATrainingRuns
    [UsageDate] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [NumSamplesUsed] INT NULL,
    [Notes] NVARCHAR(MAX) NULL,
    CONSTRAINT FK_DatasetUsage_Dataset FOREIGN KEY ([DatasetId]) 
        REFERENCES [dbo].[Datasets]([DatasetId]) ON DELETE CASCADE,
    INDEX IX_DatasetUsage_DatasetId NONCLUSTERED ([DatasetId], [UsageDate] DESC),
    INDEX IX_DatasetUsage_UsageType NONCLUSTERED ([UsageType])
);
GO
