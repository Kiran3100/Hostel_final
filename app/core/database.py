from collections.abc import AsyncGenerator
import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Configure SSL for asyncpg - Render PostgreSQL requires SSL
ssl_context = ssl.create_default_context()
# Render uses self-signed certificates, so we need to disable hostname verification
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create engine with proper SSL configuration
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_timeout=settings.database_pool_timeout,
    pool_pre_ping=settings.database_pool_pre_ping,
    connect_args={
        "ssl": ssl_context,  # Proper SSL configuration for asyncpg
        "server_settings": {
            "application_name": "stayease_api"
        }
    }
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()