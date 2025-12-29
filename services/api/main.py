"""
API Service - Read-Only HTTP Server
Handles web UI and REST API requests (NO scraping)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import sys
import os
import time
import signal

# Add parent directories to path to import shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

from api.routers import listings, stats, value, websocket
from storage.db import init_db
from core.logging import get_logger
from core.config import config
from core.sentry import init_sentry, capture_api_error

# Setup logger
logger = get_logger("api")

# Environment detection
is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"

# Graceful shutdown handler
shutdown_event = False


def handle_shutdown_signal(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_event
    logger.info(f"🛑 Received shutdown signal {signum}")
    shutdown_event = True


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown_signal)
signal.signal(signal.SIGINT, handle_shutdown_signal)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("=" * 70)
    logger.info("🌐 STARTING API SERVICE (READ-ONLY)")
    logger.info("=" * 70)
    logger.info(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"🔒 Production mode: {is_production}")

    # Initialize Sentry error monitoring
    init_sentry()

    if is_production:
        logger.info("🔒 Production: API docs DISABLED")
    else:
        logger.info("📖 Development: API docs ENABLED (/docs, /redoc)")

    try:
        logger.info("📦 Initializing database connection...")
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    logger.info(f"🌐 API Service listening on http://{config.api_host}:{config.api_port}")
    logger.info(f"📖 API docs: http://{config.api_host}:{config.api_port}/docs")
    logger.info(f"🎨 Dashboard: http://{config.api_host}:{config.api_port}/dashboard")
    logger.info("=" * 70)

    yield

    # Shutdown
    logger.info("=" * 70)
    logger.info("🛑 SHUTTING DOWN API SERVICE")
    logger.info("=" * 70)


# Create FastAPI app
app = FastAPI(
    title=config.get("api.title", "GPU Market Service API"),
    description=config.get("api.description", "API за анализ на цени на видео карти"),
    version=config.get("api.version", "2.0.0"),
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get("api.cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

    # Capture error in Sentry
    capture_api_error(
        exc,
        endpoint=request.url.path,
        context={
            "method": request.method,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Mount static files (frontend build)
# Try multiple paths for dev vs Docker environments
static_path_candidates = [
    os.path.join(os.path.dirname(__file__), 'static'),  # Docker: /app/static
    os.path.join(os.path.dirname(__file__), '..', '..', 'static'),  # Dev: services/api/../../static
]
static_path = None
for path in static_path_candidates:
    if os.path.exists(path):
        static_path = path
        break

if static_path:
    try:
        app.mount("/static", StaticFiles(directory=static_path), name="static")
        logger.info(f"📁 Mounted static files from {static_path}")
    except Exception as e:
        logger.warning(f"Failed to mount static files: {e}")

# Mount assets folder
if static_path:
    assets_path = os.path.join(static_path, 'assets')
    if os.path.exists(assets_path):
        try:
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
            logger.info(f"📁 Mounted assets from {assets_path}")
        except Exception as e:
            logger.warning(f"Failed to mount assets: {e}")


# Favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if static_path:
        favicon_path = os.path.join(static_path, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"detail": "Favicon not found"})


# Include API routers
app.include_router(listings.router, prefix="/api/listings", tags=["📋 Listings"])
app.include_router(stats.router, prefix="/api/stats", tags=["📊 Statistics"])
app.include_router(value.router, prefix="/api/value", tags=["💎 Value Analysis"])
app.include_router(websocket.router, prefix="/api", tags=["🔌 WebSocket"])


# Root endpoint
@app.get("/", tags=["Info"], include_in_schema=False)
async def root():
    """Serve frontend SPA"""
    if static_path:
        index_path = os.path.join(static_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path, media_type="text/html")

    return {
        "name": "GPU Market Service API",
        "version": "2.0.0",
        "description": "Read-Only API Service",
        "status": "operational",
        "service": "api",
        "endpoints": {
            "dashboard": "/dashboard",
            "health": "/health",
            "listings": "/api/listings",
            "stats": "/api/stats",
            "value": "/api/value",
            "docs": "/docs" if not is_production else "disabled"
        }
    }


# Health check
@app.get("/health", tags=["Info"])
def health_check():
    """Health check endpoint for load balancers"""
    try:
        from storage.db import SessionLocal
        from storage.repo import GPURepository

        # Test database connection
        session = SessionLocal()
        repo = GPURepository(session)
        model_count = len(repo.get_models())
        session.close()

        return {
            "status": "healthy",
            "service": "api",
            "message": "API Service is operational",
            "database": "connected",
            "models_available": model_count,
            "shutdown_pending": shutdown_event
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "api",
                "message": "Service is degraded",
                "error": str(e)
            }
        )


# Scraper status endpoint (read-only)
@app.get("/api/scrape/status", tags=["Info"])
async def get_scrape_status():
    """Get scraper status (read from shared state or database)"""
    from core.scraper_status import scraper_status
    status = scraper_status.get_status()
    status["note"] = "This API service is read-only. Scraping is handled by the scraper worker service."
    return status


# Dashboard
@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Serve dashboard SPA"""
    if static_path:
        index_path = os.path.join(static_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

    return HTMLResponse(
        content="<h1>Dashboard not found</h1><p>Please build frontend</p>",
        status_code=404
    )


# SPA catch-all
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """Serve SPA for client-side routing"""
    if full_path.startswith(("api/", "static/", "docs", "redoc", "openapi")):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    if static_path:
        index_path = os.path.join(static_path, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())

    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend not found"}
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 70)
    logger.info("🌐 STARTING API SERVICE (STANDALONE)")
    logger.info("=" * 70)

    try:
        uvicorn.run(
            "main:app",
            host=config.api_host,
            port=config.api_port,
            reload=config.get("api.reload", False),
            log_level="warning"
        )
    except KeyboardInterrupt:
        logger.info("⚠️  API Service stopped by user")
    except Exception as e:
        logger.error(f"❌ API Service failed to start: {e}", exc_info=True)
