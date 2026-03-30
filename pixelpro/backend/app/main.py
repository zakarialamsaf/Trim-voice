from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import time

from app.core.config import settings
from app.core.database import create_tables
from app.api import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PixelPro API...")
    await create_tables()
    logger.info("Database tables ready.")
    # Pre-load AI models in a background thread so the first request is fast
    import asyncio, concurrent.futures
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        try:
            from app.workers.ai_pipeline import warm_up
            await loop.run_in_executor(pool, warm_up)
        except Exception as exc:
            logger.warning("Model warm-up skipped: %s", exc)
    yield
    logger.info("Shutting down PixelPro API.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered ecommerce product image enhancement API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


# API key auth middleware for /api paths
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/v1/") and not path.startswith("/api/v1/auth"):
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Delegate to a dependency — just pass through here,
            # individual routes handle API key validation via dependency injection
            pass
    return await call_next(request)


app.include_router(api_router)

# Serve local file storage as static files in dev mode
if settings.AWS_ACCESS_KEY_ID == "dev":
    storage_path = Path(settings.LOCAL_STORAGE_DIR)
    storage_path.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(storage_path)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
