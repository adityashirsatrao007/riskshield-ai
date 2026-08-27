import os
import logging
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger("riskshield")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"), override=False)


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./data/riskshield.db"),
    )
    SECRET_KEY: str = Field(
        default_factory=lambda: os.environ.get("RISKSHIELD_SECRET_KEY", ""),
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    MODEL_PATH: str = Field(
        default_factory=lambda: os.environ.get(
            "MODEL_PATH",
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "ml", "models", "fraud_detector_v2.joblib"
            ),
        ),
    )
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    LOG_LEVEL: str = Field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    RATE_LIMIT_PER_MINUTE: int = Field(
        default_factory=lambda: int(os.environ.get("RATE_LIMIT_PER_MINUTE", "120")),
    )

    RISKSHIELD_API_KEY: str = Field(
        default_factory=lambda: os.environ.get("RISKSHIELD_API_KEY", ""),
    )

    REDIS_URL: str = Field(default_factory=lambda: os.environ.get("REDIS_URL", "redis://redis:6379/0"))
    KAFKA_BROKERS: str = Field(default_factory=lambda: os.environ.get("KAFKA_BROKERS", "kafka:9092"))
    MLFLOW_TRACKING_URI: str = Field(
        default_factory=lambda: os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
    )
    CORS_ORIGINS: str = Field(
        default_factory=lambda: os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"),
    )

    RAZORPAY_KEY_ID: str = Field(default_factory=lambda: os.environ.get("RAZORPAY_KEY_ID", ""))
    RAZORPAY_KEY_SECRET: str = Field(default_factory=lambda: os.environ.get("RAZORPAY_KEY_SECRET", ""))
    RAZORPAY_WEBHOOK_SECRET: str = Field(default_factory=lambda: os.environ.get("RAZORPAY_WEBHOOK_SECRET", ""))

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @field_validator("SECRET_KEY")
    @classmethod
    def _enforce_secret_key(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "RISKSHIELD_SECRET_KEY is required. "
                "Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        if len(v) < 32:
            raise ValueError("RISKSHIELD_SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("RISKSHIELD_API_KEY")
    @classmethod
    def _enforce_admin_key(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "RISKSHIELD_API_KEY is required. "
                "Generate one with: python3 -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v


settings = Settings()
