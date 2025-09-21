#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI Main Application for Enterprise Download System
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator

# Import configuration
from config.settings import settings

# Import core components
from core.database import DatabaseManager
from core.download_manager import DownloadManager
from core.auth import AuthManager

# Import API routes
from api.routes import auth, files, download, system, admin

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemState:
    """Global system state"""
    def __init__(self):
        self.db_manager: DatabaseManager = None
        self.download_manager: DownloadManager = None
        self.auth_manager: AuthManager = None
        self.is_ready = False


# Global state instance
system_state = SystemState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("🚀 Starting Enterprise Download System...")
    
    try:
        # Initialize database
        system_state.db_manager = DatabaseManager()
        await system_state.db_manager.init_database()
        logger.info("✅ Database initialized")
        
        # Initialize managers
        system_state.auth_manager = AuthManager(settings.SECRET_KEY, system_state.db_manager)
        system_state.download_manager = DownloadManager(system_state.db_manager)
        logger.info("✅ Managers initialized")
        
        # Mark system as ready
        system_state.is_ready = True
        logger.info("🎉 System ready to serve requests")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start system: {e}")
        raise
    
    # Shutdown
    logger.info("🛑 Shutting down Enterprise Download System...")
    
    try:
        if system_state.download_manager:
            await system_state.download_manager.shutdown()
        
        system_state.is_ready = False
        logger.info("✅ System shut down gracefully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="Enterprise Telegram Download System",
    description="سیستم دانلود حرفه‌ای فایل‌های تلگرام با قابلیت‌های پیشرفته",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Prometheus metrics
if settings.ENABLE_METRICS:
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/health", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="inprogress",
        inprogress_labels=True,
    )
    instrumentator.instrument(app).expose(app)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": exc.errors(),
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Middleware for dependency injection
@app.middleware("http")
async def inject_dependencies(request: Request, call_next):
    """Inject dependencies into request state"""
    request.state.db_manager = system_state.db_manager
    request.state.download_manager = system_state.download_manager
    request.state.auth_manager = system_state.auth_manager
    request.state.system_ready = system_state.is_ready
    
    response = await call_next(request)
    return response


# Rate limiting middleware (basic implementation)
from collections import defaultdict
import time

request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting"""
    if not settings.RATE_LIMIT_PER_MINUTE:
        return await call_next(request)
    
    client_ip = request.client.host
    current_time = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < 60  # Last minute
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute"
            }
        )
    
    # Add current request
    request_counts[client_ip].append(current_time)
    
    return await call_next(request)


# Include API routes
app.include_router(auth.router, prefix=settings.API_PREFIX + "/auth", tags=["Authentication"])
app.include_router(files.router, prefix=settings.API_PREFIX + "/files", tags=["Files"])
app.include_router(download.router, prefix=settings.API_PREFIX + "/download", tags=["Download"])
app.include_router(system.router, prefix=settings.API_PREFIX + "/system", tags=["System"])
app.include_router(admin.router, prefix=settings.API_PREFIX + "/admin", tags=["Administration"])


# Root endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational" if system_state.is_ready else "starting",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not system_state.is_ready:
        return JSONResponse(
            status_code=503,
            content={
                "status": "starting",
                "ready": False,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )
    
    try:
        # Get system statistics
        stats = await system_state.db_manager.get_system_stats() if system_state.db_manager else {}
        
        return {
            "status": "healthy",
            "ready": True,
            "timestamp": "2024-01-01T00:00:00Z",
            "version": settings.VERSION,
            "active_downloads": stats.get("active_downloads", 0),
            "cache_entries": stats.get("cache_entries", 0),
            "daily_downloads": stats.get("daily_downloads", 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "ready": False,
                "error": str(e),
                "timestamp": "2024-01-01T00:00:00Z"
            }
        )


# Development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )