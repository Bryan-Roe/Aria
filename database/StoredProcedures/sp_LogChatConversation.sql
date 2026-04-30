-- Stored procedure to log a chat conversation and message
CREATE PROCEDURE [dbo].[sp_LogChatConversation]
    @SessionId NVARCHAR(255) = NULL,
    @Provider NVARCHAR(50),
    @Model NVARCHAR(255) = NULL,
    @Title NVARCHAR(500) = NULL,
    @Role NVARCHAR(20),
    @Content NVARCHAR(MAX),
    @TokenCount INT = NULL,
    @PromptTokens INT = NULL,
    @CompletionTokens INT = NULL,
    @TotalTokens INT = NULL,
    @ExecutionTimeMs INT = NULL,
    @FinishReason NVARCHAR(50) = NULL,
    @LogFilePath NVARCHAR(500) = NULL,
    @ConversationId UNIQUEIDENTIFIER OUTPUT,
    @MessageId UNIQUEIDENTIFIER OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    -- Check if conversation exists for this session
    IF @SessionId IS NOT NULL
    BEGIN
        SELECT @ConversationId = ConversationId
        FROM [dbo].[ChatConversations]
        WHERE SessionId = @SessionId AND IsArchived = 0
        ORDER BY UpdatedAt DESC;
    END

    -- Create new conversation if needed
    IF @ConversationId IS NULL
    BEGIN
        SET @ConversationId = NEWID();

        INSERT INTO [dbo].[ChatConversations] (
            ConversationId, SessionId, Provider, Model, Title,
            CreatedAt, UpdatedAt, MessageCount, LogFilePath
        )
        VALUES (
            @ConversationId, @SessionId, @Provider, @Model, @Title,
            GETUTCDATE(), GETUTCDATE(), 0, @LogFilePath
        );
    END

    -- Insert message
    SET @MessageId = NEWID();

    INSERT INTO [dbo].[ChatMessages] (
        MessageId, ConversationId, Role, Content, TokenCount,
        PromptTokens, CompletionTokens, TotalTokens, ExecutionTimeMs,
        Timestamp, Model, FinishReason
    )
    VALUES (
        @MessageId, @ConversationId, @Role, @Content, @TokenCount,
        @PromptTokens, @CompletionTokens, @TotalTokens, @ExecutionTimeMs,
        GETUTCDATE(), COALESCE(@Model, (SELECT Model FROM [dbo].[ChatConversations] WHERE ConversationId = @ConversationId)),
        @FinishReason
    );

    -- Update conversation stats
    UPDATE [dbo].[ChatConversations]
    SET MessageCount = MessageCount + 1,
        UpdatedAt = GETUTCDATE()
    WHERE ConversationId = @ConversationId;
END;
GO
