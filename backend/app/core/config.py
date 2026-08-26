from pydantic_settings import BaseSettings
from pydantic import Field
import os
import secrets


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/riskshield.db"
    SECRET_KEY: str = Field(default_factory=lambda: os.environ.get("RISKSHIELD_SECRET_KEY") or secrets.token_urlsafe(64))
    MODEL_PATH: str = os.environ.get(
        "MODEL_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", "fraud_detector.joblib"),
    )
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_PER_MINUTE: int = 120

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
