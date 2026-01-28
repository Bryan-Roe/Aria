-- Embeddings for chat messages to enable semantic memory retrieval
-- Uses VARBINARY(MAX) to store serialized float32 vector (little-endian)
-- If Azure SQL VECTOR type is available in target service version, this table
-- can be migrated to use VECTOR(<dim>) for native similarity operations.
CREATE TABLE [dbo].[ChatMessageEmbeddings]
(
    [EmbeddingId] UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
    [MessageId] UNIQUEIDENTIFIER NOT NULL, -- FK to ChatMessages.MessageId
    [EmbeddingModel] NVARCHAR(100) NOT NULL, -- e.g. text-embedding-3-small | local-hash-256
    [EmbeddingDim] INT NOT NULL,
    [EmbeddingVector] VARBINARY(MAX) NOT NULL, -- Raw bytes of float32 array
    [CreatedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT FK_ChatMessageEmbeddings_Message FOREIGN KEY ([MessageId])
        REFERENCES [dbo].[ChatMessages]([MessageId]) ON DELETE CASCADE,
    INDEX IX_ChatMessageEmbeddings_MessageId NONCLUSTERED ([MessageId]),
    INDEX IX_ChatMessageEmbeddings_Model NONCLUSTERED ([EmbeddingModel])
);
GO
