import asyncio
import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import init_db
from app.core.logging import logger
from app.services.rules import initialize_default_rules
from app.db.database import async_session

async def init_database():
    """Initialize the database and create default rules"""
    try:
        logger.info("Initializing database...")
        await init_db()
        
        logger.info("Creating default rules...")
        async with async_session() as session:
            await initialize_default_rules(session)
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())