import os
import sys
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.core.database import init_db
from app.services import risk_engine
from app.services.monitoring import (
    PredictionLogger, DriftDetector, MetricsCollector, AlertManager,
)
from app.api.transactions import router as txn_router
from app.api.alerts import router as alert_router
from app.api.analytics import router as analytics_router


prediction_logger = PredictionLogger()
drift_detector = DriftDetector()
metrics_collector = MetricsCollector(prediction_logger, drift_detector)
alert_manager = AlertManager(drift_detector)

logger = logging.getLogger("riskshield")

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60.0


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = settings.MODEL_PATH
    if os.path.exists(model_path):
        risk_engine.load_model(model_path)
        logger.info("Model loaded from %s", model_path)
    else:
        logger.warning("Model not found at %s", model_path)

    await init_db()
    logger.info("Database initialized")

    yield

    from app.core.database import engine
    await engine.dispose()
    logger.info("Database connections closed, shutdown complete")


app = FastAPI(
    title="RiskShield AI",
    description="Payment fraud detection and chargeback prevention for merchants",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
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

    if request.url.path not in ("/health", "/metrics"):
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
    if request.url.path in ("/health", "/metrics"):
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    key = f"{client_ip}"

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

    if len(_rate_limit_store) > 10000:
        cutoff = now - RATE_LIMIT_WINDOW
        stale = [k for k, v in _rate_limit_store.items() if not v or v[-1] < cutoff]
        for k in stale:
            del _rate_limit_store[k]

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
    model_ok = risk_engine.is_loaded()
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


@app.get("/metrics")
async def metrics():
    return JSONResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get(f"{settings.API_PREFIX}/model/info")
async def model_info():
    from app.api.schemas import ModelInfoResponse
    info = metrics_collector.get_model_info()
    return ModelInfoResponse(
        model_loaded=info["model_loaded"],
        model_version=info["model_version"],
        features=info["features"],
        threshold=info["threshold"],
        model_type=info.get("model_type", "unknown"),
    )


@app.get(f"{settings.API_PREFIX}/predictions/log")
async def prediction_log(n: int = 100):
    from app.api.schemas import PredictionLog
    logs = prediction_logger.get_recent(n)
    validated = []
    for entry in logs:
        try:
            validated.append(PredictionLog(**entry).model_dump())
        except Exception:
            validated.append(entry)
    return {"success": True, "data": validated, "count": len(validated)}


@app.get(f"{settings.API_PREFIX}/monitoring/stats")
async def monitoring_stats():
    return {"success": True, "data": metrics_collector.get_prometheus_metrics()}


@app.get(f"{settings.API_PREFIX}/monitoring/alerts")
async def monitoring_alerts():
    return {"success": True, "data": alert_manager.get_recent_alerts()}


@app.get(f"{settings.API_PREFIX}/merchants")
async def list_merchants():
    from app.core.multi_tenant import MerchantManager
    return {"success": True, "data": MerchantManager.list_merchants()}


@app.post(f"{settings.API_PREFIX}/merchants")
async def create_merchant(request: Request):
    from app.api.schemas import MerchantCreate, MerchantResponse
    from app.core.multi_tenant import MerchantManager

    body = await request.json()
    merchant = MerchantCreate(**body)
    created = MerchantManager.create_merchant(
        name=merchant.name,
        rate_limit=merchant.rate_limit,
        status=merchant.status,
    )
    return {"success": True, "data": created}


static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.isdir(static_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
