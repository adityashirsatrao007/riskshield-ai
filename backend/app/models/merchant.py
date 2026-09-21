from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    api_key_hash = Column(String(128), nullable=False, unique=True, index=True)
    email = Column(String(256), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    rate_limit = Column(Integer, default=120)
    tier = Column(String(16), default="free", index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)
    last_active = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
