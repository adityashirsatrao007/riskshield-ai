from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    api_key_hash = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=120)
    tier = Column(String(16), default="free")
    created_at = Column(DateTime, default=_utcnow)
    last_active = Column(DateTime, default=_utcnow, onupdate=_utcnow)
