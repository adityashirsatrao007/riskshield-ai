import os
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/riskshield.db",
        description="Async database URL. Use postgresql+asyncpg:// for PostgreSQL.",
    )
    SECRET_KEY: str = Field(
        default_factory=lambda: os.environ.get("RISKSHIELD_SECRET_KEY")
        or secrets.token_urlsafe(64)
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    MODEL_PATH: str = os.environ.get(
        "MODEL_PATH",
        os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "ml", "models", "fraud_detector.joblib"
        ),
    )
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 120
    RISKSHIELD_API_KEY: str = Field(
        default_factory=lambda: os.environ.get("RISKSHIELD_API_KEY", "riskshield-test-key-2026")
    )
    REDIS_URL: str = "redis://redis:6379/0"
    KAFKA_BROKERS: str = "kafka:9092"
    MLFLOW_TRACKING_URI: str = "http://mlflow:5000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
