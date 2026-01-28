-- Stored procedure to log a LoRA training run
CREATE PROCEDURE [dbo].[sp_LogLoRATrainingRun]
    @JobName NVARCHAR(255),
    @Model NVARCHAR(255),
    @DatasetName NVARCHAR(255),
    @DatasetPath NVARCHAR(500),
    @MaxTrainSamples INT = NULL,
    @MaxEvalSamples INT = NULL,
    @Epochs INT,
    @BatchSize INT,
    @SequenceLength INT,
    @LearningRate FLOAT,
    @LoraRank INT,
    @LoraAlpha INT,
    @LoraDropout FLOAT,
    @TargetModules NVARCHAR(500),
    @TrainLoss FLOAT = NULL,
    @EvalLoss FLOAT = NULL,
    @TrainPerplexity FLOAT = NULL,
    @EvalPerplexity FLOAT = NULL,
    @TotalSteps INT = NULL,
    @ActualEpochs INT = NULL,
    @ExecutionTimeSeconds FLOAT = NULL,
    @GpuMemoryPeakGB FLOAT = NULL,
    @AdapterSavePath NVARCHAR(500) = NULL,
    @ConfigYamlPath NVARCHAR(500) = NULL,
    @LogsPath NVARCHAR(500) = NULL,
    @IsStreaming BIT = 1,
    @Runner NVARCHAR(50) = 'hf',
    @Status NVARCHAR(50) = 'completed',
    @ErrorMessage NVARCHAR(MAX) = NULL,
    @RunId UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @RunId = NEWID();
    
    INSERT INTO [dbo].[LoRATrainingRuns] (
        RunId, JobName, Model, DatasetName, DatasetPath,
        MaxTrainSamples, MaxEvalSamples, Epochs, BatchSize, SequenceLength,
        LearningRate, LoraRank, LoraAlpha, LoraDropout, TargetModules,
        TrainLoss, EvalLoss, TrainPerplexity, EvalPerplexity,
        TotalSteps, ActualEpochs, ExecutionTimeSeconds, GpuMemoryPeakGB,
        AdapterSavePath, ConfigYamlPath, LogsPath,
        IsStreaming, Runner, Status, ErrorMessage, CreatedAt, UpdatedAt
    )
    VALUES (
        @RunId, @JobName, @Model, @DatasetName, @DatasetPath,
        @MaxTrainSamples, @MaxEvalSamples, @Epochs, @BatchSize, @SequenceLength,
        @LearningRate, @LoraRank, @LoraAlpha, @LoraDropout, @TargetModules,
        @TrainLoss, @EvalLoss, @TrainPerplexity, @EvalPerplexity,
        @TotalSteps, @ActualEpochs, @ExecutionTimeSeconds, @GpuMemoryPeakGB,
        @AdapterSavePath, @ConfigYamlPath, @LogsPath,
        @IsStreaming, @Runner, @Status, @ErrorMessage, GETUTCDATE(), GETUTCDATE()
    );
    
    -- Log dataset usage
    DECLARE @DatasetId UNIQUEIDENTIFIER;
    SELECT @DatasetId = DatasetId FROM [dbo].[Datasets] WHERE Name = @DatasetName;
    
    IF @DatasetId IS NOT NULL
    BEGIN
        INSERT INTO [dbo].[DatasetUsage] (DatasetId, UsageType, ReferenceId, UsageDate, NumSamplesUsed)
        VALUES (@DatasetId, 'lora_training', @RunId, GETUTCDATE(), @MaxTrainSamples);
    END
END;
GO
