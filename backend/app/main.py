import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.services import risk_engine
from app.api.transactions import router as txn_router
from app.api.alerts import router as alert_router
from app.api.analytics import router as analytics_router

logger = logging.getLogger("riskshield")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = settings.MODEL_PATH
    if os.path.exists(model_path):
        risk_engine.load_model(model_path)
    else:
        logger.warning("Model not found at %s. Run ml/scripts/train.py first.", model_path)
    await init_db()
    yield
    from app.core.database import engine
    await engine.dispose()


app = FastAPI(
    title="RiskShield AI",
    description="Payment fraud detection and chargeback prevention for merchants",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(txn_router, prefix=settings.API_PREFIX)
app.include_router(alert_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "riskshield-api"}
