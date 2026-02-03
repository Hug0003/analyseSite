"""
SiteAuditor Backend - FastAPI Application
Main entry point for the API server
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
import sys
import asyncio

# Enforce ProactorEventLoop on Windows for Playwright compatibility
# Crucial for reloader subprocesses where run.py might not be the entry point
if sys.platform == "win32":
    try:
        if isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except ImportError:
        pass

from .config import get_settings
from .api import analyze_router, users_router, admin_router
from .api.auth import router as auth_router
from .api.audit import router as audit_router
from .api.monitors import router as monitors_router
from .services.monitoring import start_scheduler, shutdown_scheduler
from .database import create_db_and_tables
from .services.rendering import RenderingService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    # Startup
    print("[*] SiteAuditor Backend starting...")
    settings = get_settings()
    print(f"[*] Running on http://{settings.api_host}:{settings.api_port}")
    
    # Initialize database
    create_db_and_tables()
    
    # Start Scheduler
    start_scheduler()
    
    # Start Headless Browser
    try:
        await RenderingService.start()
    except Exception as e:
        logger.warning(f"Failed to start RenderingService: {e}")
    
    yield
    
    # Shutdown
    await RenderingService.stop()
    shutdown_scheduler()
    print("[*] SiteAuditor Backend shutting down...")


# Create FastAPI application
app = FastAPI(
    title="SiteAuditor API",
    description="""
    ## 🔍 SiteAuditor - Website Audit API
    
    A comprehensive website analysis tool that provides:
    
    - **SEO Analysis**: Lighthouse scores, Core Web Vitals, meta tags
    - **Security Analysis**: HTTP headers, SSL/TLS, exposed files
    - **Technology Detection**: CMS, frameworks, libraries, servers
    - **Broken Links Check**: Internal and external link validation
    
    ### Usage
    
    Send a POST request to `/api/analyze` with a JSON body:
    ```json
    {"url": "https://example.com"}
    ```
    
    ### Rate Limits
    
    - 10 requests per minute per IP
    - Analysis may take 30-60 seconds depending on the target site
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# CORS Configuration
settings = get_settings()

# In debug mode, allow all origins to make development easier
if settings.debug:
    allowed_origins = ["*"]
    logger.info("🔓 CORS: Allowing all origins (debug mode)")
else:
    allowed_origins = settings.cors_origins_list
    logger.info(f"🔒 CORS: Allowing origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    """Add response timing header and log requests"""
    # Log incoming requests in debug mode
    if settings.debug:
        logger.info(f"📥 {request.method} {request.url.path} from {request.client.host if request.client else 'unknown'}")
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 3))
    
    if settings.debug:
        logger.info(f"📤 {request.method} {request.url.path} -> {response.status_code} ({process_time:.3f}s)")
    
    return response


# Global exception handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Enhanced Exception Handling

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions with consistent JSON format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP_ERROR",
            "code": exc.status_code,
            "message": exc.detail
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors (422)"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )

@app.exception_handler(asyncio.TimeoutError)
async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    """Handle async timeouts (e.g. scan taking too long)"""
    logger.error(f"❌ Operation timed out: {exc}")
    return JSONResponse(
        status_code=408,
        content={
            "error": "SCAN_TIMEOUT",
            "message": "The analysis took too long to complete. Please try again later or with a smaller page."
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other uncaught exceptions"""
    # Log the full traceback for debugging
    logger.exception(f"❌ Uncaught exception: {exc}")
    
    error_code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred"
    
    # Specific handling for common errors could be added here
    if "connection refused" in str(exc).lower():
        error_code = "CONNECTION_REFUSED"
        message = "Could not connect to the target server."
    
    return JSONResponse(
        status_code=500,
        content={
            "error": error_code,
            "message": message,
            "detail": str(exc) if settings.debug else None
        }
    )


from .api.analyze import router as analyze_router
from .api.auth import router as auth_router
from .api.audit import router as audit_router
from .api.users import router as users_router
from .api.admin import router as admin_router
from .api.monitors import router as monitors_router
from .api.ci_cd import router as ci_cd_router
from .api.api_keys import router as api_keys_router
from .api.widget import router as widget_router
from .api.leads import router as leads_router
from .api.tasks import router as tasks_router
from .api.ai import router as ai_router
# from .api import monitoring  <-- MISSING MODULE

# Include API routes
# Note: Routers already define their own prefixes (e.g., /api/auth, /api/users), 
# so we don't need to add them here again, except for those that don't (like ai).

app.include_router(analyze_router) # Contains /api
app.include_router(auth_router)    # Contains /api/auth
app.include_router(audit_router)   # Contains /api/audits
app.include_router(users_router)   # Contains /api/users
app.include_router(admin_router)   # Contains /api/admin
app.include_router(monitors_router) # Contains /api/monitors
# app.include_router(monitoring.router) # Disabled

app.include_router(ci_cd_router)   # Contains /api/v1
app.include_router(api_keys_router) # Contains /api/api-keys (Verified assumption?)
app.include_router(widget_router)  # Contains /api/widget (Verified assumption?)
app.include_router(leads_router)   # Contains /api/leads (Verified assumption?)
app.include_router(tasks_router)   # Contains /api/tasks

app.include_router(ai_router, prefix="/api/ai", tags=["ai"]) # ai.py has NO prefix defined


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info"""
    return {
        "name": "SiteAuditor API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    """API Health Check"""
    return {"status": "ok", "timestamp": time.time()}


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="SiteAuditor API",
        version="1.0.0",
        description="Website audit and analysis API",
        routes=app.routes,
    )
    
    # Add custom logo/branding
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# Entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
