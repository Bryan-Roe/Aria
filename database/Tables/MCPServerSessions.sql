-- MCP (Model Context Protocol) server session tracking for quantum-ai MCP server
CREATE TABLE [dbo].[MCPServerSessions]
(
    [SessionId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [ServerType] NVARCHAR(50) NOT NULL DEFAULT 'quantum-ai', -- quantum-ai, future MCP servers
    [ClientId] NVARCHAR(255) NULL, -- VS Code, Claude Desktop, etc.
    [StartedAt] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    [EndedAt] DATETIME2 NULL,
    [DurationSeconds] FLOAT NULL,
    [TotalToolCalls] INT NOT NULL DEFAULT 0,
    [CircuitsCached] INT NOT NULL DEFAULT 0,
    [Status] NVARCHAR(50) NOT NULL DEFAULT 'active', -- active, completed, failed
    INDEX IX_MCPServerSessions_ServerType NONCLUSTERED ([ServerType]),
    INDEX IX_MCPServerSessions_StartedAt NONCLUSTERED ([StartedAt] DESC)
);
GO

CREATE TABLE [dbo].[MCPToolCalls]
(
    [ToolCallId] UNIQUEIDENTIFIER NOT NULL PRIMARY KEY DEFAULT NEWID(),
    [SessionId] UNIQUEIDENTIFIER NOT NULL,
    [ToolName] NVARCHAR(255) NOT NULL, -- create_quantum_circuit, train_quantum_classifier, etc.
    [Parameters] NVARCHAR(MAX) NULL, -- JSON of input parameters
    [ExecutionTimeMs] INT NULL,
    [Success] BIT NOT NULL DEFAULT 1,
    [ResultSummary] NVARCHAR(MAX) NULL, -- JSON or text summary
    [ErrorMessage] NVARCHAR(MAX) NULL,
    [Timestamp] DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CONSTRAINT FK_MCPToolCalls_Session FOREIGN KEY ([SessionId]) 
        REFERENCES [dbo].[MCPServerSessions]([SessionId]) ON DELETE CASCADE,
    INDEX IX_MCPToolCalls_SessionId NONCLUSTERED ([SessionId], [Timestamp]),
    INDEX IX_MCPToolCalls_ToolName NONCLUSTERED ([ToolName]),
    INDEX IX_MCPToolCalls_Timestamp NONCLUSTERED ([Timestamp] DESC)
);
GO
