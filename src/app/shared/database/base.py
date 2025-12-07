"""
Database Base Models

Declarative base for SQLAlchemy models with common fields and utilities.
"""

from datetime import datetime, UTC
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all database models.

    Provides common functionality and timestamp fields.
    All models should inherit from this class.

    Example:
        >>> class User(Base):
        ...     __tablename__ = "users"
        ...
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...     name: Mapped[str] = mapped_column(String(100))
    """

    # Disable default constructor to avoid conflicts with Pydantic
    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of model

        Example:
            >>> user = User(id=1, name="John")
            >>> user.to_dict()
            {"id": 1, "name": "John", "created_at": "2025-12-07T..."}
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of model."""
        attrs = ", ".join(
            f"{k}={v!r}" for k, v in self.to_dict().items() if not k.startswith("_")
        )
        return f"{self.__class__.__name__}({attrs})"


class TimestampMixin:
    """
    Mixin for models that need created_at and updated_at timestamps.

    Example:
        >>> class User(Base, TimestampMixin):
        ...     __tablename__ = "users"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when record was last updated",
    )


class SoftDeleteMixin:
    """
    Mixin for models that support soft deletion.

    Example:
        >>> class User(Base, SoftDeleteMixin):
        ...     __tablename__ = "users"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        ...
        >>> user.soft_delete()
        >>> user.is_deleted  # True
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when record was soft deleted",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark record as deleted."""
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore soft deleted record."""
        self.deleted_at = None
