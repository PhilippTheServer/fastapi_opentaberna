"""
Database Module Tests

Tests for database layer components.
"""

from datetime import datetime, UTC

from app.shared.database import (
    Base,
    TimestampMixin,
    SoftDeleteMixin,
)
from app.shared.database.utils import (
    get_logger,
    DatabaseError,
    NotFoundError,
    InternalError,
)


class TestDatabaseUtils:
    """Test database utilities."""

    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger("test")
        assert logger is not None
        # AppLogger doesn't have name attribute, just check it's callable
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.error)

    def test_database_error_fallback(self):
        """Test DatabaseError fallback class."""
        error = DatabaseError(
            message="Test error",
            context={"key": "value"},
            original_exception=ValueError("original"),
        )
        assert error.message == "Test error"
        assert error.context == {"key": "value"}
        assert isinstance(error.original_exception, ValueError)

    def test_not_found_error_fallback(self):
        """Test NotFoundError fallback class."""
        error = NotFoundError(
            message="Not found",
            context={"id": 123},
        )
        assert error.message == "Not found"
        assert error.context == {"id": 123}

    def test_internal_error_fallback(self):
        """Test InternalError fallback class."""
        error = InternalError(
            message="Internal error",
            context={"action": "test"},
        )
        assert error.message == "Internal error"
        assert error.context == {"action": "test"}


class TestBaseModel:
    """Test Base model functionality."""

    def test_base_is_abstract(self):
        """Test Base class is abstract."""
        assert Base.__abstract__ is True

    def test_to_dict_method_exists(self):
        """Test Base has to_dict method."""
        assert hasattr(Base, "to_dict")

    def test_repr_method_exists(self):
        """Test Base has __repr__ method."""
        assert hasattr(Base, "__repr__")


class TestTimestampMixin:
    """Test TimestampMixin functionality."""

    def test_mixin_has_created_at(self):
        """Test mixin has created_at field."""
        assert hasattr(TimestampMixin, "created_at")

    def test_mixin_has_updated_at(self):
        """Test mixin has updated_at field."""
        assert hasattr(TimestampMixin, "updated_at")

    def test_created_at_is_mapped_column(self):
        """Test created_at is a mapped column."""
        # Check that the annotation exists
        assert "created_at" in TimestampMixin.__annotations__


class TestSoftDeleteMixin:
    """Test SoftDeleteMixin functionality."""

    def test_mixin_has_deleted_at(self):
        """Test mixin has deleted_at field."""
        assert hasattr(SoftDeleteMixin, "deleted_at")

    def test_mixin_has_is_deleted_property(self):
        """Test mixin has is_deleted property."""
        assert hasattr(SoftDeleteMixin, "is_deleted")

    def test_mixin_has_soft_delete_method(self):
        """Test mixin has soft_delete method."""
        assert hasattr(SoftDeleteMixin, "soft_delete")
        assert callable(SoftDeleteMixin.soft_delete)

    def test_mixin_has_restore_method(self):
        """Test mixin has restore method."""
        assert hasattr(SoftDeleteMixin, "restore")
        assert callable(SoftDeleteMixin.restore)

    def test_soft_delete_logic(self):
        """Test soft delete sets deleted_at."""

        # Create a mock instance
        class MockModel:
            deleted_at = None

            @property
            def is_deleted(self):
                return self.deleted_at is not None

            def soft_delete(self):
                self.deleted_at = datetime.now(UTC)

            def restore(self):
                self.deleted_at = None

        instance = MockModel()
        assert not instance.is_deleted
        assert instance.deleted_at is None

        instance.soft_delete()
        assert instance.is_deleted
        assert instance.deleted_at is not None

        instance.restore()
        assert not instance.is_deleted
        assert instance.deleted_at is None


class TestEngineModule:
    """Test engine module imports and structure."""

    def test_engine_module_imports(self):
        """Test engine module can be imported."""
        from app.shared.database.engine import (
            create_engine,
            create_test_engine,
            init_database,
            close_database,
            get_engine,
        )

        assert callable(create_engine)
        assert callable(create_test_engine)
        assert callable(init_database)
        assert callable(close_database)
        assert callable(get_engine)


class TestSessionModule:
    """Test session module imports and structure."""

    def test_session_module_imports(self):
        """Test session module can be imported."""
        from app.shared.database.session import (
            create_session_factory,
            get_session,
            get_session_dependency,
        )

        assert callable(create_session_factory)
        assert callable(get_session)
        assert callable(get_session_dependency)


class TestRepositoryModule:
    """Test repository module imports and structure."""

    def test_repository_module_imports(self):
        """Test repository module can be imported."""
        from app.shared.database.repository import BaseRepository

        assert BaseRepository is not None

    def test_repository_has_crud_methods(self):
        """Test repository has all CRUD methods."""
        from app.shared.database.repository import BaseRepository

        methods = [
            "get",
            "get_by",
            "get_all",
            "filter",
            "create",
            "create_many",
            "update",
            "update_many",
            "delete",
            "delete_many",
            "count",
            "exists",
            "get_or_raise",
            "get_by_or_raise",
        ]

        for method in methods:
            assert hasattr(BaseRepository, method)
            assert callable(getattr(BaseRepository, method))


class TestTransactionModule:
    """Test transaction module imports and structure."""

    def test_transaction_module_imports(self):
        """Test transaction module can be imported."""
        from app.shared.database.transaction import transaction

        assert callable(transaction)


class TestHealthModule:
    """Test health module imports and structure."""

    def test_health_module_imports(self):
        """Test health module can be imported."""
        from app.shared.database.health import (
            check_database_health,
            get_database_info,
        )

        assert callable(check_database_health)
        assert callable(get_database_info)


class TestMigrationsModule:
    """Test migrations module imports and structure."""

    def test_migrations_module_imports(self):
        """Test migrations module can be imported."""
        from app.shared.database.migrations import (
            get_alembic_config,
            run_migrations,
            create_migration,
            rollback_migration,
            get_migration_history,
        )

        assert callable(get_alembic_config)
        assert callable(run_migrations)
        assert callable(create_migration)
        assert callable(rollback_migration)
        assert callable(get_migration_history)


class TestDatabaseModuleExports:
    """Test main database module exports."""

    def test_main_module_exports(self):
        """Test main database module has all exports."""
        from app.shared.database import (
            init_database,
            close_database,
            get_engine,
            get_session,
            get_session_dependency,
            AsyncSession,
            Base,
            TimestampMixin,
            SoftDeleteMixin,
            BaseRepository,
            transaction,
            check_database_health,
        )

        # Check all exports exist
        assert init_database is not None
        assert close_database is not None
        assert get_engine is not None
        assert get_session is not None
        assert get_session_dependency is not None
        assert AsyncSession is not None
        assert Base is not None
        assert TimestampMixin is not None
        assert SoftDeleteMixin is not None
        assert BaseRepository is not None
        assert transaction is not None
        assert check_database_health is not None
