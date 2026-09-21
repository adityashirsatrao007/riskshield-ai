from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(32), unique=True, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="INR")
    merchant_id = Column(String(64), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    card_type = Column(String(16))
    is_international = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(16), default="low", index=True)
    is_flagged = Column(Boolean, default=False, index=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)

    alerts = relationship("Alert", back_populates="transaction", cascade="all, delete-orphan")
    audit_trails = relationship("AuditTrail", back_populates="transaction", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(16), nullable=False)
    explanation = Column(JSON, default=list)
    status = Column(String(16), default="open", index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    transaction = relationship("Transaction", back_populates="alerts")


class AuditTrail(Base):
    __tablename__ = "audit_trails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    action = Column(String(32), nullable=False)
    details = Column(JSON, default=dict)
    model_version = Column(String(16))
    processing_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    transaction = relationship("Transaction", back_populates="audit_trails")


class MerchantStats(Base):
    __tablename__ = "merchant_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String(16), unique=True, nullable=False, index=True)
    total_transactions = Column(Integer, default=0)
    flagged_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    total_potential_savings = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
