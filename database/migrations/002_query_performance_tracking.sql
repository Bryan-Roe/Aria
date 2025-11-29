-- Migration: 002_query_performance_tracking.sql
-- Purpose: Create optional table for tracking SQL query execution metrics over time.
-- Use case: Identify patterns in slow queries, frequently-run queries, and performance degradation.
-- Notes:
--   - Optional: Only create if QAI_ENABLE_QUERY_TRACKING env var is set.
--   - Vendor-agnostic DDL; minor syntax adjustments may be needed for specific databases.
--   - Retention: Consider adding TTL/cleanup job for production (e.g., keep last 7 days).

-- For SQL Server (if using MSSQL dialect):
-- IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='QAI_QueryMetrics')
-- BEGIN
--     CREATE TABLE dbo.QAI_QueryMetrics (
--         id BIGINT IDENTITY(1,1) PRIMARY KEY,
--         query_hash VARCHAR(64) NOT NULL,  -- SHA256 of normalized SQL
--         sql_snippet NVARCHAR(500),         -- First 500 chars for quick inspection
--         vendor VARCHAR(50),
--         execution_time_ms DECIMAL(10,2),
--         executed_at DATETIME2 DEFAULT SYSUTCDATETIME(),
--         INDEX idx_query_hash (query_hash),
--         INDEX idx_executed_at (executed_at)
--     );
-- END

-- For PostgreSQL / MySQL / SQLite (standard approach):
CREATE TABLE IF NOT EXISTS QAI_QueryMetrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Use SERIAL for PostgreSQL, AUTO_INCREMENT for MySQL
    query_hash TEXT NOT NULL,
    sql_snippet TEXT,
    vendor TEXT,
    execution_time_ms REAL,
    executed_at TEXT DEFAULT (datetime('now'))  -- Use TIMESTAMP for PostgreSQL/MySQL
);

CREATE INDEX IF NOT EXISTS idx_qai_querymetrics_hash ON QAI_QueryMetrics (query_hash);
CREATE INDEX IF NOT EXISTS idx_qai_querymetrics_executed ON QAI_QueryMetrics (executed_at);
