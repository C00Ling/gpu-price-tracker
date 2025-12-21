# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from api.routers import listings, stats, value, websocket
from storage.db import init_db
from core.logging import get_logger
from core.config import config
import uvicorn
import time
import os

# Setup logger
logger = get_logger("main")

# Determine if we're in production
is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("="*70)
    logger.info("🚀 STARTING GPU SERVICE API")
    logger.info("="*70)
    logger.info(f"📝 Environment: {os.getenv('ENVIRONMENT', 'development')}")

    if is_production:
        logger.info("🔒 Production mode: API docs DISABLED (/docs, /redoc)")
    else:
        logger.info("📖 Development mode: API docs ENABLED (/docs, /redoc)")

    try:
        logger.info("📦 Initializing database...")
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    logger.info(f"🌐 Server running on http://{config.api_host}:{config.api_port}")
    logger.info(f"📖 API docs: http://{config.api_host}:{config.api_port}/docs")
    logger.info(f"🎨 Dashboard: http://{config.api_host}:{config.api_port}/dashboard")

    yield

    # Shutdown
    logger.info("="*70)
    logger.info("🛑 SHUTTING DOWN GPU SERVICE API")
    logger.info("="*70)


# Create app with conditional API docs and lifespan
# 🔒 SECURITY: Hide API docs in production
app = FastAPI(
    title=config.get("api.title", "GPU Market Service API"),
    description=config.get("api.description", "API за анализ на цени на видео карти"),
    version=config.get("api.version", "1.0.0"),
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


# Global exception handlers
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
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


# Mount static files (backend static files)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found, skipping mount")


# Favicon
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    try:
        return FileResponse("static/favicon.ico")
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"detail": "Favicon not found"})


# Startup and shutdown events are now handled by the lifespan context manager above


# Include routers
app.include_router(listings.router, prefix="/api/listings", tags=["📋 Listings"])
app.include_router(stats.router, prefix="/api/stats", tags=["📊 Statistics"])
app.include_router(value.router, prefix="/api/value", tags=["💎 Value Analysis"])
app.include_router(websocket.router, prefix="/api", tags=["🔌 WebSocket"])


# Root endpoint
@app.get("/", tags=["Info"])
def root():
    """API Information"""
    return {
        "name": "GPU Market Service API",
        "message": "GPU Market Service API",
        "version": config.get("api.version", "1.0.0"),
        "description": "Анализ на цени на видео карти в България",
        "status": "operational",
        "endpoints": {
            "home": "/ - Landing page",
            "dashboard": "/dashboard - Interactive Dashboard 🎨",
            "listings": "/api/listings - Всички обяви",
            "stats": "/api/stats - Статистики по модели",
            "value": "/api/value - FPS per лв анализ",
            "docs": "/docs - API документация",
            "redoc": "/redoc - ReDoc документация"
        }
    }


# Health check
@app.get("/health", tags=["Info"])
def health_check():
    """Health check endpoint"""
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
            "message": "Service is running",
            "database": "connected",
            "models_available": model_count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": "Service is degraded",
                "error": str(e)
            }
        )


# Trigger scraper
@app.post("/api/trigger-scrape", tags=["Admin"])
async def trigger_scrape():
    """Trigger GPU scraper (runs in background)"""
    try:
        import threading
        from ingest.pipeline import run_pipeline

        def run_scraper():
            try:
                logger.info("🔥 Starting scraper in background...")
                run_pipeline()
                logger.info("✅ Scraper completed successfully")
            except Exception as e:
                logger.error(f"❌ Scraper failed: {e}", exc_info=True)

        # Start scraper in background thread
        thread = threading.Thread(target=run_scraper, daemon=True)
        thread.start()

        return {
            "status": "started",
            "message": "Scraper started in background",
            "note": "Check logs for progress. This may take 2-5 minutes."
        }
    except Exception as e:
        logger.error(f"Failed to start scraper: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to start scraper",
                "error": str(e)
            }
        )


# Landing page
@app.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def home():
    """Landing page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Landing page not found")
        return HTMLResponse(
            content="<h1>Welcome to GPU Market</h1><p>Visit <a href='/dashboard'>/dashboard</a></p>",
            status_code=200
        )


# Dashboard
@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Interactive GPU Market Dashboard"""
    try:
        with open("static/dashboard.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("Dashboard HTML not found")
        return HTMLResponse(
            content="<h1>Dashboard not found</h1><p>Please create static/dashboard.html</p>",
            status_code=404
        )


# SPA fallback - serve index.html for all unmatched routes (after all API routes)
@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    """
    Fallback for SPA routing - serves frontend/dist/index.html
    This is intentionally last so all API routes take precedence
    """
    try:
        # Check if file exists in frontend/dist
        import os
        file_path = f"frontend/dist/{full_path}"
        
        if os.path.isfile(file_path):
            # If it's a real file (asset), serve it
            return FileResponse(file_path)
        
        # Otherwise, return index.html for SPA routing
        if os.path.isfile("frontend/dist/index.html"):
            return FileResponse("frontend/dist/index.html", media_type="text/html")
        else:
            logger.warning(f"SPA index.html not found, returning root info for path: {full_path}")
            return root()
    except Exception as e:
        logger.error(f"Error serving SPA fallback for {full_path}: {e}")
        return root()


if __name__ == "__main__":
    logger.info("\n" + "="*70)
    logger.info("🚀 STARTING GPU SERVICE API")
    logger.info("="*70 + "\n")
    
    try:
        uvicorn.run(
            "main:app",
            host=config.api_host,
            port=config.api_port,
            reload=config.get("api.reload", True),
            log_level=config.log_level.lower()
        )
    except KeyboardInterrupt:
        logger.info("\n⚠️  Server stopped by user")
    except Exception as e:
        logger.error(f"\n❌ Server failed to start: {e}", exc_info=True)