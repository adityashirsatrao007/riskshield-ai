import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.alerts import router as alert_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.orders import router as orders_router
from app.api.transactions import router as txn_router
from app.api.webhooks import router as webhook_router
from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.database import init_db
from app.models import Merchant
from app.services import risk_engine
from app.services.monitoring import (
    AlertManager,
    DriftDetector,
    MetricsCollector,
    PredictionLogger,
)

prediction_logger = PredictionLogger()
drift_detector = DriftDetector()
metrics_collector = MetricsCollector(prediction_logger, drift_detector)
alert_manager = AlertManager(drift_detector)

logger = logging.getLogger("riskshield")

_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60.0


def setup_logging():
    handler = logging.StreamHandler()
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


def _seed_prometheus_metrics():
    """Seed Prometheus counters with sample data so Grafana shows live metrics."""
    import random
    from app.services.monitoring import (
        PREDICTIONS_TOTAL,
        RISK_SCORE_HISTOGRAM,
        PROCESSING_TIME,
        FRAUD_DETECTED_TOTAL,
    )

    merchants = ["merchant_1", "merchant_2", "merchant_3", "demo_merchant"]
    risk_levels = ["low"] * 7 + ["medium"] * 2 + ["high"] * 1

    for i in range(50):
        merchant = random.choice(merchants)
        risk_level = random.choice(risk_levels)
        score = random.uniform(0.05, 0.95)
        latency = random.uniform(50, 200)

        PREDICTIONS_TOTAL.labels(merchant_id=merchant, risk_level=risk_level).inc()
        RISK_SCORE_HISTOGRAM.observe(score)
        PROCESSING_TIME.observe(latency)

        if risk_level in ("high", "critical"):
            FRAUD_DETECTED_TOTAL.labels(merchant_id=merchant).inc()

    logger.info("Seeded 50 predictions into Prometheus metrics")


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

    try:
        _seed_prometheus_metrics()
    except Exception as e:
        logger.warning("Failed to seed Prometheus metrics: %s", e)

    yield

    from app.core.database import engine
    await engine.dispose()
    logger.info("Database connections closed, shutdown complete")


app = FastAPI(
    title="RiskShield AI",
    description="Payment fraud detection and chargeback prevention for merchants",
    version="2.0.0",
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
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

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

    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Try again later."},
            headers={"Retry-After": str(int(RATE_LIMIT_WINDOW))},
        )

    _rate_limit_store[client_ip].append(now)

    if len(_rate_limit_store) > 5000:
        cutoff = now - RATE_LIMIT_WINDOW
        stale = [k for k, v in _rate_limit_store.items() if not v or v[-1] < cutoff]
        for k in stale:
            del _rate_limit_store[k]

    return await call_next(request)


ALLOWED_ORIGINS = [
    o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)

app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(webhook_router, prefix=settings.API_PREFIX)
app.include_router(orders_router, prefix=settings.API_PREFIX)
app.include_router(txn_router, prefix=settings.API_PREFIX)
app.include_router(alert_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    from sqlalchemy import text

    from app.core.database import async_session

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
        "version": "2.0.0",
        "checks": {
            "database": "ok" if db_ok else "error",
            "model": "loaded" if model_ok else "missing",
        },
    }


@app.get("/metrics")
async def metrics():
    return Response(
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
async def prediction_log(n: int = 100, _: str = Depends(verify_api_key)):
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
async def monitoring_stats(_: str = Depends(verify_api_key)):
    return {"success": True, "data": metrics_collector.get_prometheus_metrics()}


@app.get(f"{settings.API_PREFIX}/monitoring/alerts")
async def monitoring_alerts(_: str = Depends(verify_api_key)):
    return {"success": True, "data": alert_manager.get_recent_alerts()}


@app.get(f"{settings.API_PREFIX}/merchants")
async def list_merchants(_: str = Depends(verify_api_key)):
    from sqlalchemy import select as sa_select

    from app.core.database import async_session
    async with async_session() as session:
        result = await session.execute(sa_select(Merchant))
        merchants = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "tier": m.tier,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in merchants
        ],
    }


@app.post(f"{settings.API_PREFIX}/merchants")
async def create_merchant(
    request: Request,
    _: str = Depends(verify_api_key),
):
    import secrets as _secrets

    from app.api.schemas import MerchantCreate
    from app.core.auth import hash_api_key

    body = await request.json()
    merchant_data = MerchantCreate(**body)

    raw_key = f"rsk_{_secrets.token_urlsafe(32)}"
    hashed = hash_api_key(raw_key)

    from sqlalchemy import insert as sa_insert

    from app.core.database import async_session
    async with async_session() as session:
        result = await session.execute(
            sa_insert(Merchant).values(
                name=merchant_data.name,
                api_key_hash=hashed,
                rate_limit=merchant_data.rate_limit,
                status=merchant_data.status,
            ).returning(Merchant.id)
        )
        merchant_id = result.scalar_one()
        await session.commit()

    return {"success": True, "data": {"id": merchant_id, "api_key": raw_key}}


static_dir = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "static"
)
if os.path.isdir(static_dir):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(static_dir, "assets")),
        name="assets",
    )

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "health", "metrics", "docs", "openapi", "redoc")):
            return JSONResponse(status_code=404, detail="Not found")
        file_path = os.path.realpath(os.path.join(static_dir, full_path))
        static_real = os.path.realpath(static_dir)
        if not file_path.startswith(static_real + os.sep) and file_path != static_real:
            return JSONResponse(status_code=403, detail="Forbidden")
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))
