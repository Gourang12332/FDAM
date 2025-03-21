import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Create logs directory if it doesn't exist
logs_dir = Path(os.path.dirname(settings.LOG_FILE))
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            settings.LOG_FILE, 
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger
logger = logging.getLogger("fdam")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"fdam.{name}")