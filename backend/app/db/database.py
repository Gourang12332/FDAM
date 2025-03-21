from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("database")

# Create SqlAlchemy base class
Base = declarative_base()

# Create async engine based on configuration
if "sqlite" in settings.SQLALCHEMY_DATABASE_URI:
    # SQLite specific configuration
    connect_args = {"check_same_thread": False}
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "sqlite+aiosqlite:///"),
        poolclass=NullPool,
        connect_args=connect_args
    )
else:
    # PostgreSQL with connection pooling
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        future=True,
        echo=False
    )

# Create async session factory
async_session = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_async_session() -> AsyncSession:
    """Dependency for getting async db session"""
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()