"""
Query metrics retention cleanup script.

Automatically removes old query performance tracking data from QAI_QueryMetrics
table based on configurable retention period. Designed to run as scheduled task
or Azure Automation runbook.

Usage:
    python cleanup_query_metrics.py [--retention-days 7] [--dry-run]
    
Environment Variables:
    QAI_SQL_URL: Database connection string (required)
    QAI_QUERY_RETENTION_DAYS: Override retention period (default: 7)
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add shared modules to path
script_dir = Path(__file__).parent
repo_root = script_dir.parent
sys.path.insert(0, str(repo_root))

from shared.sql_engine import get_engine

# Allowlist of valid table names to prevent SQL injection
ALLOWED_TABLES = frozenset({"QAI_QueryMetrics", "QAI_QueryMetrics_Archive"})


def validate_table_name(table_name: str) -> str:
    """Validate table name against allowlist to prevent SQL injection.
    
    Args:
        table_name: The table name to validate
        
    Returns:
        The validated table name if valid
        
    Raises:
        ValueError: If table name is not in the allowlist
    """
    if table_name not in ALLOWED_TABLES:
        raise ValueError(
            f"Invalid table name: '{table_name}'. "
            f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}"
        )
    return table_name


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Cleanup old query metrics from QAI_QueryMetrics table"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=None,
        help="Number of days to retain metrics (default: 7 or QAI_QUERY_RETENTION_DAYS env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--table",
        type=str,
        default="QAI_QueryMetrics",
        help="Table name to cleanup (default: QAI_QueryMetrics)",
    )
    return parser.parse_args()


def get_retention_days(args_retention):
    """Get retention period from args, env var, or default."""
    if args_retention is not None:
        return args_retention
    
    env_retention = os.getenv("QAI_QUERY_RETENTION_DAYS")
    if env_retention:
        try:
            return int(env_retention)
        except ValueError:
            logger.warning(f"Invalid QAI_QUERY_RETENTION_DAYS value: {env_retention}, using default")
    
    return 7  # Default to 7 days


def count_old_records(engine, table_name, cutoff_timestamp):
    """Count records older than cutoff timestamp."""
    from sqlalchemy import text
    
    # Validate table name against allowlist to prevent SQL injection
    safe_table = validate_table_name(table_name)
    
    try:
        query = text(f"SELECT COUNT(*) FROM {safe_table} WHERE executed_at < :cutoff")
        
        with engine.connect() as conn:
            result = conn.execute(query, {"cutoff": cutoff_timestamp})
            count = result.scalar()
            return count
    except Exception as e:
        logger.error(f"Failed to count old records: {e}")
        return None


def delete_old_records(engine, table_name, cutoff_timestamp, dry_run=False):
    """Delete records older than cutoff timestamp."""
    from sqlalchemy import text
    
    # Validate table name against allowlist to prevent SQL injection
    safe_table = validate_table_name(table_name)
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete records from {safe_table} where executed_at < {cutoff_timestamp}")
        return True
    
    try:
        delete_query = text(f"DELETE FROM {safe_table} WHERE executed_at < :cutoff")
        
        with engine.begin() as conn:
            result = conn.execute(delete_query, {"cutoff": cutoff_timestamp})
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} records from {safe_table}")
            return deleted_count
    except Exception as e:
        logger.error(f"Failed to delete old records: {e}")
        return None


def get_table_stats(engine, table_name):
    """Get basic statistics about the table."""
    from sqlalchemy import text
    
    # Validate table name against allowlist to prevent SQL injection
    safe_table = validate_table_name(table_name)
    
    try:
        # Total count
        count_query = text(f"SELECT COUNT(*) FROM {safe_table}")
        with engine.connect() as conn:
            total_count = conn.execute(count_query).scalar()
        
        # Oldest and newest timestamps
        stats_query = text(f"""
            SELECT 
                MIN(executed_at) as oldest,
                MAX(executed_at) as newest
            FROM {safe_table}
        """)
        
        with engine.connect() as conn:
            result = conn.execute(stats_query).fetchone()
            if result:
                oldest, newest = result
                return {
                    "total_count": total_count,
                    "oldest": oldest,
                    "newest": newest,
                }
        
        return {"total_count": total_count}
    except Exception as e:
        logger.warning(f"Failed to get table stats: {e}")
        return {"total_count": 0}


def main():
    """Main cleanup execution."""
    args = parse_args()
    
    logger.info("========================================")
    logger.info("Query Metrics Retention Cleanup")
    logger.info("========================================")
    
    # Get retention period
    retention_days = get_retention_days(args.retention_days)
    logger.info(f"Retention period: {retention_days} days")
    logger.info(f"Target table: {args.table}")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    
    # Get database engine
    engine = get_engine()
    if not engine:
        logger.error("Database engine not available. Set QAI_SQL_URL or QAI_DB_CONN environment variable.")
        return 1
    
    # Calculate cutoff timestamp
    cutoff = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff.timestamp()
    logger.info(f"Cutoff date: {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get current table stats
    logger.info("")
    logger.info("Current table statistics:")
    stats = get_table_stats(engine, args.table)
    logger.info(f"  Total records: {stats.get('total_count', 'unknown')}")
    
    if stats.get("oldest"):
        logger.info(f"  Oldest record: {datetime.fromtimestamp(stats['oldest']).strftime('%Y-%m-%d %H:%M:%S')}")
    if stats.get("newest"):
        logger.info(f"  Newest record: {datetime.fromtimestamp(stats['newest']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Count records to delete
    logger.info("")
    logger.info("Analyzing records for deletion...")
    old_count = count_old_records(engine, args.table, cutoff_timestamp)
    
    if old_count is None:
        logger.error("Failed to count old records")
        return 1
    
    if old_count == 0:
        logger.info("No records found older than retention period. Nothing to delete.")
        return 0
    
    logger.info(f"Found {old_count} records older than {retention_days} days")
    
    if stats.get("total_count", 0) > 0:
        percentage = (old_count / stats["total_count"]) * 100
        logger.info(f"Will delete {percentage:.1f}% of total records")
    
    # Delete old records
    logger.info("")
    deleted = delete_old_records(engine, args.table, cutoff_timestamp, dry_run=args.dry_run)
    
    if deleted is None:
        logger.error("Cleanup failed")
        return 1
    
    # Final stats
    if not args.dry_run:
        logger.info("")
        logger.info("Final table statistics:")
        final_stats = get_table_stats(engine, args.table)
        logger.info(f"  Total records: {final_stats.get('total_count', 'unknown')}")
        
        if final_stats.get("oldest"):
            logger.info(f"  Oldest record: {datetime.fromtimestamp(final_stats['oldest']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    logger.info("")
    logger.info("========================================")
    logger.info("Cleanup Complete")
    logger.info("========================================")
    
    if args.dry_run:
        logger.info("This was a DRY RUN. Re-run without --dry-run to delete records.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
