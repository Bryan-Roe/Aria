-- Migration: 001_keyvalue_index.sql
-- Purpose: Add index on key column for key-value table to improve lookup performance.
-- Applies to all supported vendors (syntax chosen for broad compatibility).
-- NOTE: For SQL Server the default schema (dbo) is assumed; adjust if custom schema used.

CREATE INDEX idx_qai_keyvalue_k ON QAI_KeyValue (k);
