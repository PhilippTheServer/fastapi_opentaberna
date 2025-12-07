# Database Module

Generic, async database layer for PostgreSQL with SQLAlchemy 2.0.

## Overview

The database module provides a framework-agnostic, reusable database layer following SOLID principles. It supports async operations, connection pooling, transactions, migrations, and includes a generic repository pattern.

```
app/shared/database/
├── __init__.py          # Public API exports
├── utils.py             # Shared utilities and optional imports
├── base.py              # Base model and mixins
├── engine.py            # Engine and connection management
├── session.py           # Session factory and dependencies
├── repository.py        # Generic CRUD repository
├── transaction.py       # Transaction context manager
├── health.py            # Health checks
└── migrations.py        # Alembic migration utilities
```

## Features

- ✅ **Async First**: Built on SQLAlchemy 2.0 with asyncio support
- ✅ **Generic Repository**: Type-safe CRUD operations with BaseRepository
- ✅ **Connection Pooling**: Configurable pool with health checks
- ✅ **Transaction Management**: Context managers for explicit control
- ✅ **Mixins**: TimestampMixin and SoftDeleteMixin for common patterns
- ✅ **Health Checks**: Database connectivity monitoring
- ✅ **Migration Support**: Alembic integration utilities
- ✅ **Framework-Agnostic**: Optional FastAPI integration
- ✅ **SOLID Principles**: Clean architecture and dependency injection

## Quick Start

### Setup Database Connection

```python
from fastapi import FastAPI
from app.shared.database import init_database, close_database

app = FastAPI()

@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    await init_database()
    print("Database connected")

@app.on_event("shutdown")
async def shutdown():
    """Close database on shutdown."""
    await close_database()
    print("Database closed")
```

### Define Models

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.shared.database import Base, TimestampMixin, SoftDeleteMixin

class User(Base, TimestampMixin, SoftDeleteMixin):
    """User model with timestamps and soft delete."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
```

### Use Repository Pattern

```python
from app.shared.database import BaseRepository, get_session

# Using repository directly
async with get_session() as session:
    user_repo = BaseRepository(User, session)
    
    # Create
    user = await user_repo.create(
        name="John Doe",
        email="john@example.com"
    )
    
    # Read
    user = await user_repo.get(user.id)
    users = await user_repo.get_all(limit=10)
    
    # Update
    user = await user_repo.update(user.id, name="Jane Doe")
    
    # Delete
    await user_repo.delete(user.id)
```

### FastAPI Dependency Injection

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_session_dependency, BaseRepository
from app.shared.responses import success, error_from_exception
from app.shared.exceptions import NotFoundError

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session_dependency)
):
    """Get user by ID."""
    try:
        repo = BaseRepository(User, session)
        user = await repo.get_or_raise(user_id)
        return success(data=user.to_dict())
    except NotFoundError as e:
        return error_from_exception(e)
```

## Configuration

Database settings are loaded from config module:

```python
# .env file
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/dbname
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_PRE_PING=true
DATABASE_ECHO=false  # SQL logging
DATABASE_ECHO_POOL=false  # Pool logging
```

Access settings:

```python
from app.shared.config import get_settings

settings = get_settings()
print(settings.database_url)
print(settings.database_pool_size)
```

## Base Model

### Base Class

All models inherit from `Base`:

```python
from app.shared.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
```

**Features:**
- `to_dict()`: Convert model to dictionary
- `__repr__()`: String representation
- Abstract base (cannot instantiate directly)

```python
user = User(id=1, name="John")
print(user.to_dict())  # {"id": 1, "name": "John", "created_at": "..."}
print(user)  # User(id=1, name='John', created_at=...)
```

### TimestampMixin

Adds automatic timestamp fields:

```python
from app.shared.database import Base, TimestampMixin

class Article(Base, TimestampMixin):
    __tablename__ = "articles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    # Automatically adds: created_at, updated_at
```

**Fields:**
- `created_at`: Set automatically on creation (server-side default)
- `updated_at`: Updated automatically on modification (onupdate trigger)

Both use `DateTime(timezone=True)` for timezone-aware timestamps.

### SoftDeleteMixin

Adds soft delete functionality:

```python
from app.shared.database import Base, SoftDeleteMixin

class Product(Base, SoftDeleteMixin):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    # Automatically adds: deleted_at
```

**Usage:**

```python
product = await repo.get(1)

# Soft delete
product.soft_delete()
await session.commit()
print(product.is_deleted)  # True
print(product.deleted_at)  # datetime

# Restore
product.restore()
await session.commit()
print(product.is_deleted)  # False
```

**Note:** Soft delete sets `deleted_at` but doesn't filter queries. Implement filtering in your repository or queries.

## Repository Pattern

### BaseRepository

Generic CRUD repository with type safety:

```python
from app.shared.database import BaseRepository
from typing import Optional

# Create repository
user_repo = BaseRepository(User, session)

# All methods are async
user: Optional[User] = await user_repo.get(1)
```

### Create Operations

```python
# Create single
user = await repo.create(
    name="John Doe",
    email="john@example.com",
    is_active=True
)

# Create multiple
users = await repo.create_many([
    {"name": "John", "email": "john@example.com"},
    {"name": "Jane", "email": "jane@example.com"},
])

# All instances are flushed and refreshed
print(user.id)  # Auto-generated ID available
```

### Read Operations

```python
# Get by primary key
user = await repo.get(1)
if user:
    print(user.name)

# Get by filters
user = await repo.get_by(email="john@example.com")
user = await repo.get_by(name="John", is_active=True)

# Get all with pagination
users = await repo.get_all(skip=0, limit=10)

# Filter with pagination
active_users = await repo.filter(
    is_active=True,
    skip=0,
    limit=20
)

# Count
total = await repo.count()
active_count = await repo.count(is_active=True)

# Check existence
exists = await repo.exists(email="john@example.com")
```

### Update Operations

```python
# Update by ID
user = await repo.update(1, name="Jane Doe", is_active=False)
if user:
    print(user.name)  # "Jane Doe"

# Update many by filter
updated_count = await repo.update_many(
    filters={"is_active": False},
    name="Inactive User"
)
print(f"Updated {updated_count} users")
```

### Delete Operations

```python
# Delete by ID
deleted = await repo.delete(1)
print(deleted)  # True if deleted, False if not found

# Delete many by filter
deleted_count = await repo.delete_many(is_active=False)
print(f"Deleted {deleted_count} users")
```

### Exception-Raising Variants

For cleaner error handling:

```python
from app.shared.exceptions import NotFoundError

try:
    # Raises NotFoundError if not found
    user = await repo.get_or_raise(999)
except NotFoundError as e:
    return error_from_exception(e)

try:
    # Raises NotFoundError if not found
    user = await repo.get_by_or_raise(email="nonexistent@example.com")
except NotFoundError as e:
    return error_from_exception(e)
```

### Custom Queries

For complex queries beyond basic CRUD:

```python
from sqlalchemy import select, and_, or_
from datetime import datetime, timedelta

# Custom select
stmt = select(User).where(
    and_(
        User.is_active == True,
        User.created_at > datetime.now() - timedelta(days=7)
    )
).order_by(User.created_at.desc())

result = await repo.execute(stmt)
recent_users = result.scalars().all()

# Custom update
from sqlalchemy import update

stmt = update(User).where(
    User.last_login < datetime.now() - timedelta(days=30)
).values(is_active=False)

await repo.execute(stmt)
```

### Subclassing Repository

For model-specific methods:

```python
from app.shared.database import BaseRepository

class UserRepository(BaseRepository[User]):
    """User-specific repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return await self.get_by(email=email)
    
    async def get_active_users(self, limit: int = 10) -> list[User]:
        """Get active users."""
        return await self.filter(is_active=True, limit=limit)
    
    async def deactivate_old_users(self, days: int = 90) -> int:
        """Deactivate users inactive for N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return await self.update_many(
            filters={"last_login__lt": cutoff},
            is_active=False
        )

# Usage
repo = UserRepository(session)
user = await repo.get_by_email("john@example.com")
active = await repo.get_active_users(limit=5)
```

## Session Management

### Manual Session Control

```python
from app.shared.database import get_session

async with get_session() as session:
    # Session is automatically:
    # - Created
    # - Committed on success
    # - Rolled back on exception
    # - Closed in finally block
    
    repo = BaseRepository(User, session)
    user = await repo.create(name="John")
    # Automatic commit here
```

### FastAPI Dependency

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.database import get_session_dependency

@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_session_dependency)
):
    """Session is injected and managed by FastAPI."""
    repo = BaseRepository(User, session)
    users = await repo.get_all(limit=10)
    return success(data=[u.to_dict() for u in users])
```

### Session Factory

For custom session creation:

```python
from app.shared.database.session import create_session_factory

factory = create_session_factory()

async with factory() as session:
    # Use session
    result = await session.execute(select(User))
    users = result.scalars().all()
```

## Transaction Management

### Explicit Transactions

```python
from app.shared.database import transaction, get_session

async with get_session() as session:
    # Explicit transaction boundary
    async with transaction(session):
        user = User(name="John")
        session.add(user)
        
        post = Post(title="First Post", user_id=user.id)
        session.add(post)
        
        # Commits automatically if no exception
        # Rolls back automatically on exception
```

### Nested Transactions (Savepoints)

```python
async with get_session() as session:
    user = User(name="John")
    session.add(user)
    
    try:
        # Nested transaction uses savepoint
        async with transaction(session):
            post = Post(title="Bad Post", user=user)
            session.add(post)
            raise ValueError("Something went wrong")
    except ValueError:
        # Inner transaction rolled back to savepoint
        # Outer transaction continues
        pass
    
    # User is still saved
    await session.commit()
```

### Error Handling

```python
from app.shared.exceptions import DatabaseError

async with get_session() as session:
    try:
        async with transaction(session):
            # Database operations
            pass
    except DatabaseError as e:
        # Already logged and wrapped
        logger.error(f"Transaction failed: {e.message}")
        return error_from_exception(e)
```

## Health Checks

### Basic Health Check

```python
from app.shared.database import check_database_health

health = await check_database_health()

if health["healthy"]:
    print(f"Database OK (latency: {health['latency_ms']}ms)")
else:
    print(f"Database Error: {health['error']}")

# Response structure:
# {
#     "healthy": bool,
#     "latency_ms": float,
#     "timestamp": datetime,
#     "error": Optional[str]
# }
```

### FastAPI Health Endpoint

```python
from fastapi import APIRouter
from app.shared.database import check_database_health
from app.shared.responses import success, error

router = APIRouter()

@router.get("/health/database")
async def database_health():
    """Database health check endpoint."""
    health = await check_database_health()
    
    if health["healthy"]:
        return success(
            data={
                "status": "healthy",
                "latency_ms": health["latency_ms"]
            },
            message="Database is healthy"
        )
    else:
        return error(
            message="Database is unhealthy",
            status_code=503,
            details={"error": health["error"]}
        )
```

### Database Info

```python
from app.shared.database.health import get_database_info

info = await get_database_info()

print(info["version"])      # "PostgreSQL 15.3"
print(info["connections"])  # {"active": 5, "idle": 15}
print(info["pool_size"])    # 20
```

## Migrations with Alembic

### Initialize Alembic

```bash
# Create migrations directory
alembic init migrations

# Configure alembic.ini with database URL
# Edit migrations/env.py to import Base.metadata
```

### Using Migration Utilities

```python
from app.shared.database.migrations import (
    create_migration,
    run_migrations,
    rollback_migration,
    get_migration_history,
)
from pathlib import Path

migrations_dir = Path("migrations")

# Create migration
await create_migration(
    message="add users table",
    migrations_dir=migrations_dir,
    autogenerate=True  # Auto-detect model changes
)

# Run migrations
await run_migrations(
    revision="head",
    migrations_dir=migrations_dir
)

# Rollback
await rollback_migration(
    steps=1,
    migrations_dir=migrations_dir
)

# View history
history = await get_migration_history(migrations_dir)
print(f"Total migrations: {len(history)}")
```

### Manual Alembic Commands

```bash
# Create migration
alembic revision -m "add users table"

# Auto-generate migration
alembic revision --autogenerate -m "add users table"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View history
alembic history

# Current version
alembic current
```

## Error Handling

### Database Exceptions

The module integrates with the shared exceptions module:

```python
from app.shared.exceptions import DatabaseError, NotFoundError
from app.shared.responses import error_from_exception

@router.post("/users")
async def create_user(data: UserCreate, session: AsyncSession = Depends(get_session_dependency)):
    try:
        repo = BaseRepository(User, session)
        
        # Check for duplicates
        if await repo.exists(email=data.email):
            raise ValidationError(
                message="Email already exists",
                context={"email": data.email}
            )
        
        # Create user
        user = await repo.create(**data.dict())
        return success(data=user.to_dict(), message="User created")
        
    except DatabaseError as e:
        # Already logged with context
        return error_from_exception(e)
```

### Automatic Error Logging

All database errors are automatically logged with context:

```python
# Logs automatically on error:
# - Error message and type
# - Operation context (entity type, filters, etc.)
# - Original exception and stack trace
# - Request context if available

try:
    user = await repo.create(name="John")
except DatabaseError as e:
    # Already logged as:
    # ERROR: Failed to create User
    #   entity_type: User
    #   attributes: {"name": "John"}
    #   error: IntegrityError(...)
    pass
```

## Testing

### Test Database Setup

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from app.shared.database import Base, init_database, close_database
from app.shared.database.engine import create_test_engine

@pytest.fixture
async def test_engine():
    """Create test database engine."""
    # Use in-memory SQLite or test database
    engine = create_test_engine("sqlite+aiosqlite:///:memory:")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await init_database(engine)
    yield engine
    await close_database()

@pytest.fixture
async def session(test_engine):
    """Create test session."""
    from app.shared.database import get_session
    
    async with get_session() as session:
        yield session
```

### Testing Repository

```python
@pytest.mark.asyncio
async def test_create_user(session):
    """Test user creation."""
    repo = BaseRepository(User, session)
    
    user = await repo.create(
        name="John Doe",
        email="john@example.com"
    )
    
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@example.com"

@pytest.mark.asyncio
async def test_user_not_found(session):
    """Test NotFoundError is raised."""
    from app.shared.exceptions import NotFoundError
    
    repo = BaseRepository(User, session)
    
    with pytest.raises(NotFoundError):
        await repo.get_or_raise(999)
```

## Best Practices

### 1. Use Repository Pattern

```python
# ✅ Good - Repository pattern
repo = BaseRepository(User, session)
user = await repo.get(1)

# ❌ Bad - Raw SQLAlchemy
result = await session.execute(select(User).where(User.id == 1))
user = result.scalar_one_or_none()
```

### 2. Exception-Raising Methods

```python
# ✅ Good - Let exceptions propagate
user = await repo.get_or_raise(user_id)
return success(data=user.to_dict())

# ❌ Bad - Manual null checks everywhere
user = await repo.get(user_id)
if not user:
    raise NotFoundError("User not found")
return success(data=user.to_dict())
```

### 3. Use Mixins

```python
# ✅ Good - Leverage mixins
class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)

# ❌ Bad - Manual timestamp fields
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
```

### 4. Explicit Transactions

```python
# ✅ Good - Explicit transaction boundaries
async with transaction(session):
    user = await user_repo.create(name="John")
    post = await post_repo.create(user_id=user.id, title="Hello")

# ❌ Bad - Implicit commit points unclear
user = await user_repo.create(name="John")
await session.commit()
post = await post_repo.create(user_id=user.id, title="Hello")
await session.commit()
```

### 5. Subclass for Domain Logic

```python
# ✅ Good - Domain-specific repository
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.get_by(email=email)

# ❌ Bad - Generic repository everywhere
repo = BaseRepository(User, session)
user = await repo.get_by(email=email)  # Less discoverable
```

### 6. Connection Pooling

```python
# ✅ Good - Use connection pooling
await init_database()  # Uses pool

# ❌ Bad - New connection every request
engine = create_engine(url)  # Don't do this per request
```

### 7. Health Checks

```python
# ✅ Good - Monitor database health
@router.get("/health")
async def health():
    db_health = await check_database_health()
    return {"database": db_health}

# ❌ Bad - No health monitoring
# Users don't know if DB is down
```

## Troubleshooting

### Import Errors

```python
# ✅ Ensure conftest.py sets PYTHONPATH
# tests/conftest.py already handles this

# ✅ Import from main module
from app.shared.database import Base, BaseRepository

# ❌ Don't import internals directly
from app.shared.database.base import Base  # Avoid
```

### Connection Pool Exhausted

```python
# Check pool settings
settings = get_settings()
print(settings.database_pool_size)      # 20
print(settings.database_max_overflow)   # 40

# Increase if needed in .env
DATABASE_POOL_SIZE=50
DATABASE_MAX_OVERFLOW=100
```

### Migrations Not Found

```bash
# Ensure alembic.ini exists
ls migrations/alembic.ini

# Initialize if missing
alembic init migrations
```

### Session Not Committing

```python
# ✅ Use context manager (auto-commits)
async with get_session() as session:
    await repo.create(name="John")
    # Auto-commits here

# ❌ Don't forget manual commit
session = factory()
await repo.create(name="John")
await session.commit()  # Easy to forget!
await session.close()
```

## See Also

- [Config Module](./config.md) - Database configuration
- [Logger Module](./logger.md) - Logging database operations
- [Exception Module](./exceptions.md) - Error handling
- [Response Module](./responses.md) - API responses
- [Shared Modules Guide](./shared-modules.md) - Using all modules together
