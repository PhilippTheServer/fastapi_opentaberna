"""
Database Health Checks

Utilities for monitoring database connectivity and health.
"""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared.database.engine import get_engine

from app.shared.database.utils import get_logger

logger = get_logger(__name__)


async def check_database_health(
    engine: Optional[AsyncEngine] = None,
) -> dict[str, any]:
    """
    Check database connectivity and health.

    Performs a simple query to verify database is accessible
    and responsive. Useful for health check endpoints.

    Args:
        engine: Database engine (defaults to global engine)

    Returns:
        Health status dictionary with:
        - healthy: bool
        - latency_ms: float
        - timestamp: datetime
        - error: Optional[str]

    Example:
        >>> health = await check_database_health()
        >>> if health["healthy"]:
        ...     print(f"DB latency: {health['latency_ms']}ms")
        >>> else:
        ...     print(f"DB error: {health['error']}")
    """
    if engine is None:
        try:
            engine = get_engine()
        except (RuntimeError, Exception) as e:
            logger.warning(
                "Database engine not available for health check",
                extra={"error": str(e)},
            )
            return {
                "healthy": False,
                "latency_ms": None,
                "timestamp": datetime.now(UTC),
                "error": "Database not initialized",
            }

    start_time = datetime.now(UTC)

    try:
        async with engine.connect() as conn:
            # Simple query to verify connectivity
            await conn.execute(text("SELECT 1"))

        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        logger.debug(
            "Database health check passed",
            extra={"latency_ms": round(latency_ms, 2)},
        )

        return {
            "healthy": True,
            "latency_ms": round(latency_ms, 2),
            "timestamp": end_time,
            "error": None,
        }

    except Exception as e:
        end_time = datetime.now(UTC)
        latency_ms = (end_time - start_time).total_seconds() * 1000

        logger.error(
            "Database health check failed",
            extra={"error": str(e), "latency_ms": round(latency_ms, 2)},
            exc_info=True,
        )

        return {
            "healthy": False,
            "latency_ms": round(latency_ms, 2),
            "timestamp": end_time,
            "error": str(e),
        }


async def get_database_info(
    engine: Optional[AsyncEngine] = None,
) -> dict[str, any]:
    """
    Get database server information.

    Queries PostgreSQL for version and connection details.

    Args:
        engine: Database engine (defaults to global engine)

    Returns:
        Database information dictionary

    Example:
        >>> info = await get_database_info()
        >>> print(info["version"])  # "PostgreSQL 15.3"
    """
    if engine is None:
        engine = get_engine()

    try:
        async with engine.connect() as conn:
            # Get PostgreSQL version
            version_result = await conn.execute(text("SELECT version()"))
            version = version_result.scalar_one()

            # Get current database name
            db_result = await conn.execute(text("SELECT current_database()"))
            database = db_result.scalar_one()

            # Get current user
            user_result = await conn.execute(text("SELECT current_user"))
            user = user_result.scalar_one()

            # Get active connections count
            conn_result = await conn.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database()"
                )
            )
            active_connections = conn_result.scalar_one()

            logger.debug("Retrieved database info", extra={"database": database})

            return {
                "version": version,
                "database": database,
                "user": user,
                "active_connections": active_connections,
                "pool_size": engine.pool.size(),
                "pool_checked_in": engine.pool.checkedin(),
                "pool_checked_out": engine.pool.checkedout(),
                "pool_overflow": engine.pool.overflow(),
            }

    except Exception as e:
        logger.error(
            "Failed to retrieve database info",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise


async def check_database_tables(
    engine: Optional[AsyncEngine] = None,
) -> list[str]:
    """
    Get list of tables in database.

    Queries information_schema for table names.

    Args:
        engine: Database engine (defaults to global engine)

    Returns:
        List of table names

    Example:
        >>> tables = await check_database_tables()
        >>> if "users" not in tables:
        ...     print("Users table not found!")
    """
    if engine is None:
        engine = get_engine()

    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' "
                    "ORDER BY table_name"
                )
            )
            tables = [row[0] for row in result]

            logger.debug(
                "Retrieved database tables",
                extra={"count": len(tables)},
            )

            return tables

    except Exception as e:
        logger.error(
            "Failed to retrieve database tables",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise


__all__ = [
    "check_database_health",
    "get_database_info",
    "check_database_tables",
]
