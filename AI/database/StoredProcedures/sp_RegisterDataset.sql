-- Stored procedure to register or update a dataset
CREATE PROCEDURE [dbo].[sp_RegisterDataset]
    @Name NVARCHAR(255),
    @Category NVARCHAR(50),
    @Type NVARCHAR(50),
    @Path NVARCHAR(500),
    @Description NVARCHAR(MAX) = NULL,
    @Source NVARCHAR(500) = NULL,
    @License NVARCHAR(100) = NULL,
    @IsCommercialOk BIT = 0,
    @SizeBytes BIGINT = NULL,
    @NumSamples INT = NULL,
    @NumFeatures INT = NULL,
    @NumClasses INT = NULL,
    @Format NVARCHAR(MAX) = NULL,
    @DatasetId UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if dataset already exists
    SELECT @DatasetId = DatasetId FROM [dbo].[Datasets] WHERE Name = @Name;
    
    IF @DatasetId IS NULL
    BEGIN
        -- Insert new dataset
        SET @DatasetId = NEWID();
        
        INSERT INTO [dbo].[Datasets] (
            DatasetId, Name, Category, Type, Path, Description, Source,
            License, IsCommercialOk, SizeBytes, NumSamples, NumFeatures,
            NumClasses, Format, CreatedAt, UpdatedAt
        )
        VALUES (
            @DatasetId, @Name, @Category, @Type, @Path, @Description, @Source,
            @License, @IsCommercialOk, @SizeBytes, @NumSamples, @NumFeatures,
            @NumClasses, @Format, GETUTCDATE(), GETUTCDATE()
        );
    END
    ELSE
    BEGIN
        -- Update existing dataset
        UPDATE [dbo].[Datasets]
        SET Category = @Category,
            Type = @Type,
            Path = @Path,
            Description = COALESCE(@Description, Description),
            Source = COALESCE(@Source, Source),
            License = COALESCE(@License, License),
            IsCommercialOk = @IsCommercialOk,
            SizeBytes = COALESCE(@SizeBytes, SizeBytes),
            NumSamples = COALESCE(@NumSamples, NumSamples),
            NumFeatures = COALESCE(@NumFeatures, NumFeatures),
            NumClasses = COALESCE(@NumClasses, NumClasses),
            Format = COALESCE(@Format, Format),
            UpdatedAt = GETUTCDATE()
        WHERE DatasetId = @DatasetId;
    END
END;
GO
