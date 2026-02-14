"""
Database configuration and session management for Grant Alignment Engine.

Provides async SQLAlchemy setup with connection pooling and session factory.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import declarative_base, DeclarativeBase
from sqlalchemy import event, pool, text
import logging

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class DatabaseManager:
    """Manages database connections and session lifecycle."""

    def __init__(self):
        """Initialize database manager."""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker | None = None

    async def initialize(self) -> None:
        """Initialize the database engine and session factory."""
        try:
            # Determine pooling strategy based on environment
            use_null_pool = settings.ENVIRONMENT == "development"
            
            # Build engine kwargs - only include pool_size and max_overflow for QueuePool
            engine_kwargs = {
                "echo": settings.DATABASE_ECHO,
                "poolclass": pool.NullPool if use_null_pool else pool.QueuePool,
                "pool_recycle": settings.DATABASE_POOL_RECYCLE,
                "pool_pre_ping": True,
                "connect_args": {
                    "timeout": 10,
                    "server_settings": {
                        "application_name": "foam_grant_engine",
                        "jit": "off",
                    }
                }
            }
            
            # Only add pool_size and max_overflow for QueuePool (not for NullPool)
            if not use_null_pool:
                engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
                engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
            
            self._engine = create_async_engine(
                settings.DATABASE_URL,
                **engine_kwargs
            )

            self._session_factory = async_sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )

            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    async def dispose(self) -> None:
        """Dispose of the database engine."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")

    async def create_all_tables(self) -> None:
        """Create all tables in the database."""
        if not self._engine:
            await self.initialize()

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("All database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_all_tables(self) -> None:
        """Drop all tables in the database. Use with caution."""
        if not self._engine:
            await self.initialize()

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("All database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    def get_session_factory(self) -> async_sessionmaker:
        """Get the session factory."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()

    async def health_check(self) -> bool:
        """Check database connection health."""
        try:
            if not self._engine:
                return False

            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.

    Yields:
        AsyncSession: A database session for use in request handlers.

    Raises:
        RuntimeError: If database is not initialized.
    """
    session = await db_manager.get_session()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        await session.close()


async def seed_default_admin() -> None:
    """Create a default admin user if none exists."""
    from sqlalchemy import select as sa_select
    from models import User, UserRoleEnum
    from services.auth_service import hash_password

    session = await db_manager.get_session()
    try:
        # Check if any admin user already exists
        result = await session.execute(
            sa_select(User).where(User.role == UserRoleEnum.ADMIN).limit(1)
        )
        existing_admin = result.scalar_one_or_none()

        if not existing_admin:
            admin = User(
                email="admin@foamgrants.org",
                name="FOAM Admin",
                hashed_password=hash_password("ChangeMe123!"),
                role=UserRoleEnum.ADMIN,
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created: admin@foamgrants.org")
        else:
            logger.info(f"Admin user already exists: {existing_admin.email}")
    except Exception as e:
        await session.rollback()
        logger.warning(f"Could not seed default admin (table may not support it yet): {e}")
    finally:
        await session.close()


async def init_db() -> None:
    """Initialize database on application startup."""
    await db_manager.initialize()
    await db_manager.create_all_tables()
    await seed_default_admin()
    logger.info("Database initialization complete")


async def close_db() -> None:
    """Close database connection on application shutdown."""
    await db_manager.dispose()
    logger.info("Database connection closed")
