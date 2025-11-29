-- Stored procedure to log a quantum training run
CREATE PROCEDURE [dbo].[sp_LogQuantumTrainingRun]
    @JobName NVARCHAR(255),
    @DatasetName NVARCHAR(255),
    @Backend NVARCHAR(100),
    @NumQubits INT,
    @NumLayers INT,
    @Entanglement NVARCHAR(50),
    @LearningRate FLOAT,
    @Epochs INT,
    @BatchSize INT,
    @TrainAccuracy FLOAT = NULL,
    @ValAccuracy FLOAT = NULL,
    @TestAccuracy FLOAT = NULL,
    @TrainLoss FLOAT = NULL,
    @ValLoss FLOAT = NULL,
    @TestLoss FLOAT = NULL,
    @TotalShots INT = NULL,
    @ExecutionTimeSeconds FLOAT = NULL,
    @IsAzureHardware BIT = 0,
    @AzureJobId NVARCHAR(255) = NULL,
    @AzureProvider NVARCHAR(100) = NULL,
    @EstimatedCostUSD DECIMAL(10, 4) = NULL,
    @CircuitDepth INT = NULL,
    @NumParameters INT = NULL,
    @StatusJsonPath NVARCHAR(500) = NULL,
    @ResultsJsonPath NVARCHAR(500) = NULL,
    @Status NVARCHAR(50) = 'completed',
    @ErrorMessage NVARCHAR(MAX) = NULL,
    @RunId UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @RunId = NEWID();
    
    INSERT INTO [dbo].[QuantumTrainingRuns] (
        RunId, JobName, DatasetName, Backend, NumQubits, NumLayers, Entanglement,
        LearningRate, Epochs, BatchSize, TrainAccuracy, ValAccuracy, TestAccuracy,
        TrainLoss, ValLoss, TestLoss, TotalShots, ExecutionTimeSeconds,
        IsAzureHardware, AzureJobId, AzureProvider, EstimatedCostUSD,
        CircuitDepth, NumParameters, StatusJsonPath, ResultsJsonPath,
        Status, ErrorMessage, CreatedAt, UpdatedAt
    )
    VALUES (
        @RunId, @JobName, @DatasetName, @Backend, @NumQubits, @NumLayers, @Entanglement,
        @LearningRate, @Epochs, @BatchSize, @TrainAccuracy, @ValAccuracy, @TestAccuracy,
        @TrainLoss, @ValLoss, @TestLoss, @TotalShots, @ExecutionTimeSeconds,
        @IsAzureHardware, @AzureJobId, @AzureProvider, @EstimatedCostUSD,
        @CircuitDepth, @NumParameters, @StatusJsonPath, @ResultsJsonPath,
        @Status, @ErrorMessage, GETUTCDATE(), GETUTCDATE()
    );
    
    -- Log dataset usage
    DECLARE @DatasetId UNIQUEIDENTIFIER;
    SELECT @DatasetId = DatasetId FROM [dbo].[Datasets] WHERE Name = @DatasetName;
    
    IF @DatasetId IS NOT NULL
    BEGIN
        INSERT INTO [dbo].[DatasetUsage] (DatasetId, UsageType, ReferenceId, UsageDate)
        VALUES (@DatasetId, 'quantum_training', @RunId, GETUTCDATE());
    END
END;
GO
