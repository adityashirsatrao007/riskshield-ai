from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./riskshield.db"
    SECRET_KEY: str = os.environ.get("RISKSHIELD_SECRET_KEY", "riskshield-dev-secret-key-change-in-production")
    MODEL_PATH: str = os.environ.get("MODEL_PATH", os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", "fraud_detector.joblib"))
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
