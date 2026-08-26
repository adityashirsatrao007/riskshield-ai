import os
import sys
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.services import risk_engine
from app.api.transactions import router as txn_router
from app.api.alerts import router as alert_router
from app.api.analytics import router as analytics_router


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    for noisy in ("uvicorn.access", "uvicorn.error", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


setup_logging()
logger = logging.getLogger("riskshield")

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = settings.MODEL_PATH
    if os.path.exists(model_path):
        risk_engine.load_model(model_path)
        logger.info("Model loaded from %s", model_path)
    else:
        logger.warning("Model not found at %s — run ml/scripts/train.py first", model_path)
    await init_db()
    logger.info("Database initialized")
    yield
    from app.core.database import engine
    await engine.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title="RiskShield AI",
    description="Payment fraud detection and chargeback prevention for merchants",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    start = time.time()

    response = await call_next(request)
    elapsed_ms = round((time.time() - start) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.path != "/health":
        logger.info(
            "%s %s %s %s %sms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

    return response


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/health":
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    key = f"{client_ip}:{request.url.path}"

    if key not in _rate_limit_store:
        _rate_limit_store[key] = []

    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < RATE_LIMIT_WINDOW]

    if len(_rate_limit_store[key]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(int(RATE_LIMIT_WINDOW))},
        )

    _rate_limit_store[key].append(now)
    return await call_next(request)


ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)

app.include_router(txn_router, prefix=settings.API_PREFIX)
app.include_router(alert_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    from app.core.database import async_session
    from sqlalchemy import text

    db_ok = False
    model_ok = risk_engine._model is not None
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            db_ok = True
    except Exception as e:
        logger.error("Health check DB failure: %s", e)

    status = "healthy" if (db_ok and model_ok) else "degraded"
    return {
        "status": status,
        "service": "riskshield-api",
        "checks": {
            "database": "ok" if db_ok else "error",
            "model": "loaded" if model_ok else "missing",
        },
    }
