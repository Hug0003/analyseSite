import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .core.config import get_settings
from .db.session import init_db

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Initialize Scheduler
    from app.services.monitoring import start_scheduler, shutdown_scheduler
    start_scheduler()
    
    yield
    # Shutdown
    logger.info("Shutting down...")
    shutdown_scheduler()

from .api import auth, analyze, audit, billing, monitors, ai, api_keys

app = FastAPI(title="SiteAuditor API", lifespan=lifespan, redirect_slashes=False)

settings = get_settings()

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc: Exception):
    # Log full details server-side only
    logger.error(f"Unhandled exception on {request.method} {request.url.path}", exc_info=exc)
    # Return generic message to client — NEVER expose traceback
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error"},
    )

app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(audit.router)
app.include_router(billing.router)
app.include_router(monitors.router)
app.include_router(ai.router)
app.include_router(api_keys.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
