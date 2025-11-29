-- Chat conversations and messages for talk-to-ai and Azure Functions chat endpoints
CREATE TABLE [dbo].[ChatConversations]
(
    [ConversationId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [SessionId] NVARCHAR(255) NULL, -- User session identifier
    [Provider] NVARCHAR(50) NOT NULL, -- local, azure, openai, lora, quantum
    [Model] NVARCHAR(255) NULL, -- gpt-4o-mini, phi-3.6-mini, etc.
    [Title] NVARCHAR(500) NULL, -- Auto-generated or user-provided title
    [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [UpdatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [MessageCount] INT NOT NULL DEFAULT 0,
    [IsArchived] BIT NOT NULL DEFAULT 0,
    [LogFilePath] NVARCHAR(500) NULL, -- Path to logs/chat_*.jsonl
    INDEX IX_ChatConversations_SessionId NONCLUSTERED ([SessionId]),
    INDEX IX_ChatConversations_Provider NONCLUSTERED ([Provider]),
    INDEX IX_ChatConversations_CreatedAt NONCLUSTERED ([CreatedAt] DESC)
);
GO

CREATE TABLE [dbo].[ChatMessages]
(
    [MessageId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [ConversationId] UNIQUEIDENTIFIER NOT NULL,
    [Role] NVARCHAR(20) NOT NULL, -- user, assistant, system
    [Content] NVARCHAR(MAX) NOT NULL,
    [TokenCount] INT NULL,
    [PromptTokens] INT NULL,
    [CompletionTokens] INT NULL,
    [TotalTokens] INT NULL,
    [ExecutionTimeMs] INT NULL,
    [Timestamp] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [Model] NVARCHAR(255) NULL, -- May differ from conversation default for multi-model chats
    [FinishReason] NVARCHAR(50) NULL, -- stop, length, content_filter, etc.
    CONSTRAINT FK_ChatMessages_Conversation FOREIGN KEY ([ConversationId]) 
        REFERENCES [dbo].[ChatConversations]([ConversationId]) ON DELETE CASCADE,
    INDEX IX_ChatMessages_ConversationId NONCLUSTERED ([ConversationId], [Timestamp]),
    INDEX IX_ChatMessages_Timestamp NONCLUSTERED ([Timestamp] DESC)
);
GO
