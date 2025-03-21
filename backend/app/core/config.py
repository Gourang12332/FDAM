import os
import secrets
from typing import Any, Dict, List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "FDAM System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", "sqlite:///./fdam.db")
    POSTGRES_SERVER: Optional[str] = os.getenv("POSTGRES_SERVER")
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Caching
    USE_CACHE: bool = os.getenv("USE_CACHE", "False").lower() == "true"
    CACHE_TYPE: str = os.getenv("CACHE_TYPE", "file")  # "file" or "redis"
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DIR: str = os.getenv("CACHE_DIR", "./cache")
    
    # ML Model
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/ml/models/fraud_model.pkl")
    ENSEMBLE_MODEL_PATH: str = os.getenv("ENSEMBLE_MODEL_PATH", "app/ml/models/fraud_ensemble.pkl")
    MODEL_VERSION: str = os.getenv("MODEL_VERSION", "1.0.0")
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "20"))
    WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", "120"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/fdam.log")
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if v:
            return v
        
        if values.get("DATABASE_TYPE") == "sqlite":
            return values.get("DATABASE_URL")
        
        if values.get("POSTGRES_SERVER"):
            return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB') or ''}"
        return None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()