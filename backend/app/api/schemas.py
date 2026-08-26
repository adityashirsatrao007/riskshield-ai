from typing import Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


VALID_CARD_TYPES = {"credit", "debit", "upi", "netbanking", "wallet", "prepaid"}
VALID_CARD_NETWORKS = {"visa", "mastercard", "amex", "rupay", "discover", "diners", "other"}
VALID_RISK_LEVELS = {"low", "medium", "high", "critical"}
VALID_MERCHANT_STATUSES = {"active", "suspended", "pending"}


def _validate_iso8601(v: str | None) -> str | None:
    if v is None:
        return v
    try:
        datetime.fromisoformat(v)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid ISO 8601 timestamp: {v}")
    return v


class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0, lt=1_000_000)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    merchant_id: str = Field(..., min_length=1, max_length=64)
    customer_id: str = Field(..., min_length=1, max_length=64)
    timestamp: Optional[str] = None
    card_number: Optional[str] = Field(None, max_length=24)
    card_type: str = Field(default="credit", max_length=16)
    card_network: str = Field(default="visa", max_length=16)
    is_international: bool = False
    country_code: str = Field(default="IN", min_length=2, max_length=2)
    customer_account_age_days: int = Field(default=100, ge=0, le=36500)
    customer_total_transactions: int = Field(default=10, ge=0, le=1_000_000)
    merchant_category_code: str = Field(default="electronics", max_length=64)
    merchant_avg_ticket_size: float = Field(default=1000.0, gt=0, le=1_000_000)
    shipping_address_match: bool = True
    device_fingerprint_reused: bool = False

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        return _validate_iso8601(v)

    @field_validator("card_type")
    @classmethod
    def validate_card_type(cls, v: str) -> str:
        if v.lower() not in VALID_CARD_TYPES:
            raise ValueError(f"card_type must be one of: {VALID_CARD_TYPES}")
        return v.lower()

    @field_validator("card_network")
    @classmethod
    def validate_card_network(cls, v: str) -> str:
        if v.lower() not in VALID_CARD_NETWORKS:
            raise ValueError(f"card_network must be one of: {VALID_CARD_NETWORKS}")
        return v.lower()

    @field_validator("country_code")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        if not v.isalpha() or not v.isupper():
            raise ValueError("country_code must be a 2-letter ISO 3166 uppercase code")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if not v.isalpha() or not v.isupper():
            raise ValueError("currency must be a 3-letter ISO 4217 uppercase code")
        return v


class MerchantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    rate_limit: int = Field(default=120, ge=1, le=10000)
    status: str = Field(default="active")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_MERCHANT_STATUSES:
            raise ValueError(f"status must be one of: {VALID_MERCHANT_STATUSES}")
        return v


class MerchantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    rate_limit: Optional[int] = Field(None, ge=1, le=10000)
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_MERCHANT_STATUSES:
            raise ValueError(f"status must be one of: {VALID_MERCHANT_STATUSES}")
        return v


class MerchantResponse(BaseModel):
    id: str
    name: str
    api_key: str
    rate_limit: int
    status: str
    created_at: str
    updated_at: str


class ModelInfoResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_loaded: bool
    model_version: str
    features: list[str]
    threshold: float
    model_type: str = "unknown"


class PredictionLog(BaseModel):
    transaction_id: str
    merchant_id: str
    risk_score: float
    risk_level: str
    is_flagged: bool
    processing_time_ms: float
    features_used: list[str]
    timestamp: Optional[str] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        return _validate_iso8601(v)


class AlertUpdate(BaseModel):
    status: Literal["open", "acknowledged", "dismissed", "resolved"]
    notes: Optional[str] = Field(None, max_length=500)


class BatchTransaction(BaseModel):
    transactions: list[TransactionCreate] = Field(..., min_length=1, max_length=100)

    @field_validator("transactions")
    @classmethod
    def validate_batch_size(cls, v: list[TransactionCreate]) -> list[TransactionCreate]:
        if len(v) > 100:
            raise ValueError("Batch size cannot exceed 100 transactions")
        return v


class PredictionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    transaction_id: str
    risk_score: float
    risk_level: str
    is_flagged: bool
    explanations: list[dict[str, Any]]
    processing_time_ms: float
    model_version: str


class HealthResponse(BaseModel):
    status: str
    service: str
    checks: dict[str, str]
