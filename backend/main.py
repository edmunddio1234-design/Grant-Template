"""
FastAPI application entry point for FOAM Grant Alignment Engine.

Configures the API with middleware, exception handlers, and endpoints.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from database import db_manager, init_db, close_db
import schemas

# Import routers
from routers import auth, boilerplate, rfp, crosswalk, plans, dashboard, ai_draft

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")
    try:
        await close_db()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# ============================================================================
# APPLICATION FACTORY
# ============================================================================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/api/docs" if not settings.is_production() else None,
        redoc_url="/api/redoc" if not settings.is_production() else None,
        openapi_url="/api/openapi.json" if not settings.is_production() else None,
        lifespan=lifespan,
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Configure trusted host middleware
    if settings.is_production():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*.foamgrants.org", "*.onrender.com"],
        )

    # Setup upload directory
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    try:
        # Mount static files for uploads (if directory exists)
        app.mount(
            "/uploads",
            StaticFiles(directory=str(upload_path)),
            name="uploads"
        )
        logger.info(f"Mounted uploads directory: {upload_path}")
    except Exception as e:
        logger.warning(f"Could not mount uploads directory: {e}")

    # Include all module routers
    app.include_router(auth.router)
    app.include_router(boilerplate.router)
    app.include_router(rfp.router)
    app.include_router(crosswalk.router)
    app.include_router(plans.router)
    app.include_router(dashboard.router)
    app.include_router(ai_draft.router)

    return app


# ============================================================================
# APPLICATION INSTANCE
# ============================================================================

app = create_app()


# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Validation error",
            "error": str(exc),
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error",
            "error": "An internal database error occurred" if settings.is_production() else str(exc),
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": "An unexpected error occurred" if settings.is_production() else str(exc),
        }
    )


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/health", response_model=schemas.HealthCheckResponse, tags=["Health"])
async def health_check() -> schemas.HealthCheckResponse:
    """
    Health check endpoint.

    Returns:
        HealthCheckResponse: Service health status.
    """
    db_status = "healthy" if await db_manager.health_check() else "unhealthy"

    return schemas.HealthCheckResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        timestamp=datetime.now(timezone.utc),
        database=db_status,
        redis="unknown",
        version=settings.APP_VERSION,
    )


@app.get("/api/v1/health", response_model=schemas.HealthCheckResponse, tags=["Health"])
async def api_health_check() -> schemas.HealthCheckResponse:
    """
    Detailed health check endpoint.

    Returns:
        HealthCheckResponse: Service health status with details.
    """
    return await health_check()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs_url": "/api/docs" if not settings.is_production() else None,
        "health_url": "/health",
    }


# ============================================================================
# API V1 STATUS
# ============================================================================

@app.get(
    f"{settings.API_PREFIX}/status",
    response_model=dict,
    tags=["Status"],
    summary="Get API status"
)
async def api_status():
    """
    Get current API status and configuration.

    Returns:
        dict: API status information.
    """
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }


# ============================================================================
# MIDDLEWARE & REQUEST LOGGING
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log HTTP requests and responses."""
    import time

    start_time = time.time()

    # Skip logging for health checks and docs
    if request.url.path not in ["/health", "/docs", "/redoc", "/openapi.json"]:
        logger.debug(f"{request.method} {request.url.path}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} - {e}")
        raise

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    if request.url.path not in ["/health", "/docs", "/redoc", "/openapi.json"]:
        logger.debug(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
