import time
import os
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import api_router
from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db
from app.services.rules import initialize_default_rules
from app.db.database import get_async_session

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Fraud Detection, Alert, and Monitoring System API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Generate request ID
    request_id = request.headers.get("X-Request-ID", f"req-{time.time()}")
    
    # Log the request
    logger.info(
        f"Request {request_id} started: {request.method} {request.url.path}"
    )
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        
        # Log the response
        logger.info(
            f"Request {request_id} completed: {response.status_code} in {process_time:.2f}ms"
        )
        
        # Add processing time header
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            f"Request {request_id} failed after {process_time:.2f}ms: {str(e)}"
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Startup event handler
@app.on_event("startup")
async def startup_event():
    logger.info("Starting FDAM API")
    
    # Ensure cache directory exists
    if settings.USE_CACHE and settings.CACHE_TYPE == "file":
        os.makedirs(settings.CACHE_DIR, exist_ok=True)
        logger.info(f"Initialized file cache at {settings.CACHE_DIR}")
    
    # Create model directory if it doesn't exist
    model_dir = os.path.dirname(settings.MODEL_PATH)
    os.makedirs(model_dir, exist_ok=True)
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
        
        # Initialize default rules if needed
        async for session in get_async_session():
            await initialize_default_rules(session)
            break
        
        logger.info("FDAM API startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise