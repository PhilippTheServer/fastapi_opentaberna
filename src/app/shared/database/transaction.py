"""
Transaction Management

Context manager for explicit transaction control.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database.utils import get_logger, DatabaseError

logger = get_logger(__name__)


@asynccontextmanager
async def transaction(
    session: AsyncSession,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Transaction context manager with automatic rollback.

    Provides explicit transaction boundaries with:
    - Automatic commit on success
    - Automatic rollback on exception
    - Nested transaction support via savepoints

    Args:
        session: Database session to use

    Yields:
        Same session within transaction

    Example:
        >>> async with get_session() as session:
        ...     async with transaction(session):
        ...         user = User(name="John")
        ...         session.add(user)
        ...         # Automatically commits if no exception

        >>> # Nested transactions
        >>> async with get_session() as session:
        ...     user = User(name="John")
        ...     session.add(user)
        ...
        ...     async with transaction(session):
        ...         # This uses a savepoint
        ...         post = Post(user=user)
        ...         session.add(post)
        ...         # Inner transaction commits to savepoint
        ...
        ...     # Outer transaction commits
    """
    # Check if already in transaction
    if session.in_transaction():
        # Use savepoint for nested transaction
        logger.debug("Starting nested transaction (savepoint)")
        async with session.begin_nested():
            yield session
            logger.debug("Nested transaction committed")
    else:
        # Start new transaction
        logger.debug("Starting transaction")
        try:
            async with session.begin():
                yield session
                logger.debug("Transaction committed")
        except DatabaseError:
            # Already a DatabaseError, just log and re-raise
            logger.warning("Transaction rolled back due to DatabaseError")
            raise
        except Exception as e:
            logger.error(
                "Transaction rolled back due to unexpected error",
                extra={"error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            # Wrap in DatabaseError for consistency
            raise DatabaseError(
                message="Transaction failed",
                context={"error_type": type(e).__name__},
                original_exception=e,
            )


__all__ = ["transaction"]
